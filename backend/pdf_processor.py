import fitz  # PyMuPDF
import re
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import openai
import os
from typing import List, Dict, Tuple, Optional
import logging
from models import Chunk, OutlineItem, KeyPoint, QuizQuestion, SummaryResponse, TimeLimit
from dotenv import load_dotenv
from nltk_setup import nltk_setup

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Setup NLTK with fallbacks
nltk_setup.setup_nltk()

logger = logging.getLogger(__name__)

print("OpenAI version:", openai.__version__)
print("OpenAI API Key at import:", openai.api_key)
print("OpenAI API Key:", openai.api_key)

logging.basicConfig(level=logging.INFO)

# Create OpenAI client for new API
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PDFProcessor:
    """Main class for processing PDFs and generating time-based summaries"""
    
    def __init__(self):
        self.words_per_minute = 250
        self.stop_words = nltk_setup.get_stopwords()
        self.sent_tokenize = nltk_setup.get_sentence_tokenizer()
        self.word_tokenize = nltk_setup.get_word_tokenizer()
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=100,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def process_pdf(self, pdf_content: bytes, time_limit: TimeLimit, plan_type: str = 'free') -> SummaryResponse:
        """
        Main method to process a PDF and generate a summary
        
        Args:
            pdf_content: Raw PDF bytes
            time_limit: Time limit in minutes
            plan_type: Plan type (free, starter, unlimited)
            
        Returns:
            SummaryResponse: Complete summary with all components
        """
        logger.info(f'Processing PDF for plan_type={plan_type}')
        logger.info(f"Starting PDF processing with {time_limit} minute limit")
        
        # Step 1: Extract text from PDF
        raw_text = self._extract_text_from_pdf(pdf_content)
        logger.info(f'Extracted {len(raw_text)} characters of text')
        
        # Step 2: Split into chunks
        chunks = self._split_into_chunks(raw_text)
        logger.info(f'Created {len(chunks)} chunks')
        
        # Step 3: Score chunks for importance
        scored_chunks = self._score_chunks(chunks)
        
        # Ensure time_limit is a float for all comparisons
        if hasattr(time_limit, 'value'):
            time_limit_value = float(time_limit.value)
        else:
            time_limit_value = float(time_limit)
        
        # Step 4: Select chunks within time limit
        selected_chunks = self._select_chunks_within_limit(scored_chunks, time_limit_value)
        logger.info(f'Selected {len(selected_chunks)} chunks for summary')
        
        # Step 5: Summarize long chunks
        if plan_type in ['starter', 'unlimited']:
            logger.info('Using OpenAI for summarization (paid plan)')
            if time_limit == TimeLimit.SIXTY:
                processed_chunks = self._summarize_long_chunks_enhanced(selected_chunks, aggressive=False)
            else:
                processed_chunks = self._summarize_long_chunks(selected_chunks)
        else:
            logger.info('Using local NLTK summarization (free plan)')
            processed_chunks = []
            for chunk in selected_chunks:
                # Always use NLTK for free plan
                if chunk.reading_time_minutes > 5.0:
                    summarized_text = self._summarize_with_nltk(chunk.text)
                    summarized_chunk = Chunk(
                        text=summarized_text,
                        page_number=chunk.page_number,
                        word_count=len(self.word_tokenize(summarized_text)),
                        reading_time_minutes=len(self.word_tokenize(summarized_text)) / self.words_per_minute,
                        importance_score=chunk.importance_score,
                        headings=chunk.headings,
                        keywords=chunk.keywords
                    )
                    processed_chunks.append(summarized_chunk)
                else:
                    processed_chunks.append(chunk)
        
        # Step 6: Generate outline
        outline = self._generate_outline(processed_chunks)
        
        # Step 7: Extract key points (only for paid plans)
        key_points = []
        if plan_type in ['starter', 'unlimited']:
            logger.info('Calling OpenAI for key points')
            key_points = self._extract_key_points_with_ai_or_local(processed_chunks)
        else:
            logger.info('Skipping key points for free plan')
        
        # Step 8: Generate quiz (only for paid plans)
        quiz = []
        if plan_type in ['starter', 'unlimited']:
            logger.info('Calling OpenAI for quiz')
            quiz = self._generate_quiz(processed_chunks)
        else:
            logger.info('Skipping quiz for free plan')
        
        # Calculate totals
        total_reading_time = sum(chunk.reading_time_minutes for chunk in processed_chunks)
        total_word_count = sum(chunk.word_count for chunk in processed_chunks)
        
        # Generate key points warning
        key_points_warning = self._get_key_points_warning(key_points)
        
        # Create processing notes
        processing_notes = [f"Processed for {time_limit} minute reading time"]
        if time_limit == TimeLimit.SIXTY:
            processing_notes.append("📚 Deep summary mode: More comprehensive content included")
        if key_points_warning:
            processing_notes.append(key_points_warning)
        
        return SummaryResponse(
            outline=outline,
            condensed_content=processed_chunks,
            key_points=key_points,
            total_reading_time_minutes=total_reading_time,
            total_word_count=total_word_count,
            quiz=quiz,
            original_filename="uploaded_pdf.pdf",
            processing_notes=processing_notes,
            key_points_warning=key_points_warning
        )
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract raw text from PDF using PyMuPDF"""
        try:
            # type: ignore[attr-defined]
            doc = fitz.open(stream=pdf_content, filetype="pdf")  # type: ignore[attr-defined]
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise Exception(f"Failed to extract text from PDF: {e}")
    
    def _split_into_chunks(self, text: str) -> List[Chunk]:
        """Split text into manageable chunks (1 page or ~500-700 words)"""
        # Split by pages first (if page markers exist)
        page_pattern = r'Page \d+|^\d+$'
        pages = re.split(page_pattern, text, flags=re.MULTILINE)
        
        chunks = []
        current_chunk = ""
        current_page = 1
        word_count = 0
        
        for page_text in pages:
            if not page_text.strip():
                continue
                
            # If adding this page would exceed ~700 words, create a new chunk
            page_words = len(self.word_tokenize(page_text))
            
            if word_count + page_words > 700 and current_chunk:
                # Create chunk from current content
                chunk = Chunk(
                    text=current_chunk.strip(),
                    page_number=current_page,
                    word_count=word_count,
                    reading_time_minutes=word_count / self.words_per_minute,
                    importance_score=0.0
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = page_text
                word_count = page_words
                current_page += 1
            else:
                current_chunk += "\n" + page_text if current_chunk else page_text
                word_count += page_words
        
        # Add the last chunk
        if current_chunk.strip():
            chunk = Chunk(
                text=current_chunk.strip(),
                page_number=current_page,
                word_count=word_count,
                reading_time_minutes=word_count / self.words_per_minute,
                importance_score=0.0
            )
            chunks.append(chunk)
        
        return chunks
    
    def _score_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Score chunks based on headings, bold text, and keyword density"""
        # Extract all text for TF-IDF analysis
        all_texts = [chunk.text for chunk in chunks]
        
        # Calculate TF-IDF scores
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(all_texts)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
        except:
            # Fallback if TF-IDF fails
            tfidf_matrix = None
            feature_names = []
        
        for i, chunk in enumerate(chunks):
            score = 0.0
            
            # Score based on headings (lines that are short and end with numbers or are all caps)
            lines = chunk.text.split('\n')
            heading_count = 0
            for line in lines:
                line = line.strip()
                if (len(line) < 100 and 
                    (line.isupper() or re.search(r'\d+$', line) or 
                     re.match(r'^[A-Z][A-Za-z\s]+:', line))):
                    heading_count += 1
                    score += 0.3
            
            # Score based on keyword density (using TF-IDF if available)
            if tfidf_matrix is not None:
                try:
                    chunk_tfidf = tfidf_matrix[i]
                    # Convert to numpy array safely using try/except
                    try:
                        chunk_tfidf = chunk_tfidf.toarray().flatten()  # type: ignore[attr-defined]
                    except AttributeError:
                        try:
                            chunk_tfidf = chunk_tfidf.A1  # type: ignore[attr-defined]
                        except AttributeError:
                            try:
                                chunk_tfidf = chunk_tfidf.flatten()  # type: ignore[attr-defined]
                            except AttributeError:
                                # If all conversions fail, skip this chunk
                                continue
                    
                    # Only proceed if we have a valid array
                    try:
                        top_keywords = [str(feature_names[j]) for j in chunk_tfidf.argsort()[-10:]]  # type: ignore[attr-defined]
                        chunk.keywords = top_keywords
                        score += float(chunk_tfidf.sum()) * 0.1  # type: ignore[attr-defined]
                    except (AttributeError, IndexError):
                        # Skip if argsort or sum methods don't exist
                        pass
                except (AttributeError, IndexError, TypeError):
                    # Skip TF-IDF scoring if anything goes wrong
                    pass
            
            # Score based on sentence length (shorter sentences often indicate important content)
            sentences = self.sent_tokenize(chunk.text)
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            if avg_sentence_length < 20:
                score += 0.2
            
            # Score based on presence of numbers (often indicates important data)
            number_count = len(re.findall(r'\d+', chunk.text))
            score += min(number_count * 0.01, 0.3)
            
            # Normalize score
            chunk.importance_score = min(score, 1.0)
            
            # Extract headings for the chunk
            chunk.headings = [line.strip() for line in lines 
                            if len(line.strip()) < 100 and 
                            (line.strip().isupper() or re.search(r'\d+$', line.strip()))]
        
        return chunks
    
    def _select_chunks_within_limit(self, chunks: List[Chunk], time_limit_value: float) -> List[Chunk]:
        """Select the most important chunks that fit within the time limit"""
        # First, try to use AI to select the most important chunks
        if client.api_key:
            try:
                logger.info("[AI] Using OpenAI GPT to select most important chunks.")
                selected_chunks = self._select_chunks_with_ai(chunks, time_limit_value)
                if selected_chunks:
                    return selected_chunks
            except Exception as e:
                logger.warning(f"AI chunk selection failed, falling back to scoring: {e}")
        
        # Fallback to scoring-based selection
        logger.info("[AI] Using scoring-based chunk selection.")
        return self._select_chunks_with_scoring(chunks, time_limit_value)
    
    def _select_chunks_with_ai(self, chunks: List[Chunk], time_limit_value: float) -> List[Chunk]:
        """Use AI to select the most important chunks within the time limit"""
        try:
            # Prepare chunk information for AI
            chunk_info = []
            for i, chunk in enumerate(chunks):
                chunk_info.append(f"Chunk {i+1}: {chunk.headings[0] if chunk.headings else 'No heading'} - {chunk.word_count} words ({chunk.reading_time_minutes:.1f} min) - Score: {chunk.importance_score:.2f}")
            
            combined_info = "\n".join(chunk_info)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at selecting the most important content from academic documents. Given a list of text chunks, select the most important ones that can be read within the specified time limit. Return ONLY a JSON array of chunk numbers (1-based) to include."},
                    {"role": "user", "content": f"Select the most important chunks that can be read in {time_limit_value} minutes. Focus on chunks with high importance scores and meaningful content.\n\nAvailable chunks:\n{combined_info}\n\nReturn JSON array of chunk numbers to include, e.g., [1, 3, 5]"}
                ],
                max_tokens=200,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if content:
                import json
                selected_indices = json.loads(content)
                # Convert to 0-based indices and get selected chunks
                selected_chunks = [chunks[i-1] for i in selected_indices if 1 <= i <= len(chunks)]
                
                # Verify total reading time is within limit
                total_time = sum(chunk.reading_time_minutes for chunk in selected_chunks)
                if total_time <= time_limit_value:
                    logger.info(f"[AI] Selected {len(selected_chunks)} chunks with {total_time:.1f} minutes total reading time")
                    return selected_chunks
                else:
                    logger.warning(f"[AI] Selected chunks exceed time limit ({total_time:.1f} > {time_limit_value}), falling back to scoring")
                    return []
            else:
                logger.warning("[AI] OpenAI returned empty content for chunk selection")
                return []
        except Exception as e:
            logger.warning(f"AI chunk selection failed: {e}")
            return []
    
    def _select_chunks_with_scoring(self, chunks: List[Chunk], time_limit_value: float) -> List[Chunk]:
        """Select chunks using scoring-based approach"""
        # Sort chunks by importance score (highest first)
        sorted_chunks = sorted(chunks, key=lambda x: x.importance_score, reverse=True)
        
        selected_chunks = []
        total_time = 0.0
        
        for chunk in sorted_chunks:
            if float(total_time) + float(chunk.reading_time_minutes) <= time_limit_value:
                selected_chunks.append(chunk)
                total_time += float(chunk.reading_time_minutes)
            else:
                break
        
        # Sort selected chunks by page number for logical order
        selected_chunks.sort(key=lambda x: x.page_number)
        
        return selected_chunks
    
    def _summarize_long_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        """Summarize chunks that are too long using GPT-3.5"""
        processed_chunks = []
        
        for chunk in chunks:
            # If chunk takes more than 5 minutes to read, summarize it
            if chunk.reading_time_minutes > 5.0:
                try:
                    summarized_text = self._summarize_with_gpt_or_nltk(chunk.text)
                    
                    # Create new chunk with summarized content
                    summarized_chunk = Chunk(
                        text=summarized_text,
                        page_number=chunk.page_number,
                        word_count=len(self.word_tokenize(summarized_text)),
                        reading_time_minutes=len(self.word_tokenize(summarized_text)) / self.words_per_minute,
                        importance_score=chunk.importance_score,
                        headings=chunk.headings,
                        keywords=chunk.keywords
                    )
                    processed_chunks.append(summarized_chunk)
                    
                except Exception as e:
                    logger.warning(f"Failed to summarize chunk: {e}")
                    processed_chunks.append(chunk)
            else:
                processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _summarize_long_chunks_enhanced(self, chunks: List[Chunk], aggressive: bool = True) -> List[Chunk]:
        """Enhanced summarization with different strategies for different time limits"""
        processed_chunks = []
        
        for chunk in chunks:
            # For 1-hour summaries, only summarize very long chunks (>10 minutes)
            # For shorter summaries, summarize chunks >5 minutes
            threshold = 10.0 if not aggressive else 5.0
            
            if chunk.reading_time_minutes > threshold:
                try:
                    summarized_text = self._summarize_with_gpt_or_nltk(chunk.text)
                    
                    # Create new chunk with summarized content
                    summarized_chunk = Chunk(
                        text=summarized_text,
                        page_number=chunk.page_number,
                        word_count=len(self.word_tokenize(summarized_text)),
                        reading_time_minutes=len(self.word_tokenize(summarized_text)) / self.words_per_minute,
                        importance_score=chunk.importance_score,
                        headings=chunk.headings,
                        keywords=chunk.keywords
                    )
                    processed_chunks.append(summarized_chunk)
                    
                except Exception as e:
                    logger.warning(f"Failed to summarize chunk: {e}")
                    processed_chunks.append(chunk)
            else:
                processed_chunks.append(chunk)
        
        return processed_chunks
    
    def _summarize_with_gpt_or_nltk(self, text: str) -> str:
        print("[AI] Should be using OpenAI GPT for summarization.")
        if client.api_key:
            try:
                logger.info("[AI] Using OpenAI GPT for summarization.")
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes academic text for students. Provide clear, concise summaries that capture the main ideas and key concepts."},
                        {"role": "user", "content": f"Summarize the following academic text for a student, focusing on the main ideas and key concepts:\n\n{text[:3000]}"}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            except Exception as e:
                logger.warning(f"OpenAI failed, falling back to NLTK: {e}")
        logger.info("[AI] Using NLTK fallback for summarization.")
        return self._summarize_with_nltk(text)

    def _summarize_with_nltk(self, text: str) -> str:
        # Simple fallback: first 3 sentences
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
        return ' '.join(sentences[:3]) if sentences else text
    
    def _generate_outline(self, chunks: List[Chunk]) -> List[OutlineItem]:
        """Generate an outline from the selected chunks"""
        outline = []
        
        for chunk in chunks:
            # Use the first heading as the title, or generate one from the text
            title = chunk.headings[0] if chunk.headings else self._generate_title(chunk.text)
            
            outline_item = OutlineItem(
                title=title,
                page_number=chunk.page_number,
                reading_time_minutes=chunk.reading_time_minutes
            )
            outline.append(outline_item)
        
        return outline
    
    def _generate_title(self, text: str) -> str:
        """Generate a title from chunk text"""
        # Take the first sentence or first 50 characters
        sentences = self.sent_tokenize(text)
        if sentences:
            title = sentences[0][:50]
            if len(title) == 50:
                title += "..."
            return title
        else:
            return text[:50] + "..." if len(text) > 50 else text
    
    def _extract_key_points_with_ai_or_local(self, chunks: List[Chunk]) -> List[KeyPoint]:
        if client.api_key:
            try:
                logger.info("[AI] Using OpenAI GPT for key points extraction.")
                combined_text = "\n\n".join([chunk.text for chunk in chunks])
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an expert at extracting key points from academic documents. Extract the 10 most important concepts, findings, or insights. Return ONLY a JSON array of strings, each containing one key point."},
                        {"role": "user", "content": f"Extract the 10 most important key points from this academic text. Focus on main concepts, findings, and insights that a student should remember:\n\n{combined_text[:3000]}\n\nReturn as JSON array: [\"point 1\", \"point 2\", ...]"}
                    ],
                    max_tokens=800,
                    temperature=0.2
                )
                import json
                content = response.choices[0].message.content
                if content:
                    key_points_list = json.loads(content)
                    return [KeyPoint(point=kp) for kp in key_points_list]
            except Exception as e:
                logger.warning(f"OpenAI key points failed, falling back to local: {e}")
        logger.info("[AI] Using NLTK fallback for key points extraction.")
        return self._extract_key_points(chunks)
    
    def _get_key_points_warning(self, key_points: List[KeyPoint]) -> Optional[str]:
        """Generate warning if there are more than 10 key points"""
        if len(key_points) > 10:
            return f"⚠️ This document has {len(key_points)} key takeaways. Consider using the 1-hour option for a more comprehensive summary."
        return None
    
    def _generate_quiz(self, chunks: List[Chunk]) -> List[QuizQuestion]:
        if not client.api_key:
            logger.info("[AI] No OpenAI API key found, using static quiz fallback.")
            return []
        try:
            logger.info("[AI] Using OpenAI GPT for quiz generation.")
            combined_text = "\n\n".join([chunk.text for chunk in chunks])
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at creating educational quiz questions. Generate 3 multiple choice questions based on the academic content. Each question should have 4 options (A, B, C, D) and include an explanation for the correct answer. Return ONLY valid JSON."},
                    {"role": "user", "content": f"Create 3 multiple choice questions based on this academic text. Format as JSON array:\n\n{combined_text[:2000]}\n\nReturn as JSON:\n[\n  {{\n    \"question\": \"Question text?\",\n    \"options\": [\"Option A\", \"Option B\", \"Option C\", \"Option D\"],\n    \"correct_answer\": \"Option A\",\n    \"explanation\": \"Explanation why this is correct\"\n  }}\n]"}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            import json
            content = response.choices[0].message.content
            if content:
                quiz_data = json.loads(content)
                quiz = [QuizQuestion(**q) for q in quiz_data]
                return quiz
            else:
                logger.warning("OpenAI returned empty content for quiz generation")
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            logger.info("[AI] Using static quiz fallback.")
        
        # Return fallback quiz
        return [
            QuizQuestion(
                question="What is the main topic of this document?",
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answer="Option A",
                explanation="This is the main topic based on the content."
            )
        ]

    def _extract_key_points(self, chunks: list) -> list:
        # Local fallback: extract first 10 sentences as key points
        key_points = []
        for chunk in chunks:
            sentences = self.sent_tokenize(chunk.text)
            for sentence in sentences:
                if len(key_points) < 10 and len(sentence) > 20:
                    key_points.append(KeyPoint(point=sentence.strip()))
            if len(key_points) >= 10:
                break
        return key_points

print("OpenAI API Key:", client.api_key) 