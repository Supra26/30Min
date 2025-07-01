# Thirty-Minute PDF Backend

A FastAPI backend service that processes PDF documents and generates time-based summaries. The service extracts the most important content that can be read within a specified time limit (10, 20, or 30 minutes).

## Features

- **PDF Text Extraction**: Uses PyMuPDF for reliable text extraction
- **Smart Content Chunking**: Splits content into manageable chunks (~500-700 words)
- **Importance Scoring**: Scores chunks based on headings, keywords, and content structure
- **Time-Based Selection**: Selects content that fits within the specified reading time
- **AI Summarization**: Uses GPT-3.5 to summarize long chunks
- **Quiz Generation**: Automatically generates quiz questions about the content
- **Structured Output**: Returns outline, key points, and reading time estimates

## Installation

1. **Clone the repository and navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_actual_openai_api_key_here
   ```

## Usage

### Starting the Server

```bash
python main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### Health Check
```bash
GET /
```
Returns a simple health check message.

#### Process PDF
```bash
POST /process-pdf
```

**Parameters:**
- `file`: PDF file (multipart/form-data)
- `time_limit`: Time limit in minutes (10, 20, or 30)

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/process-pdf" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_document.pdf" \
     -F "time_limit=20"
```

**Response Format:**
```json
{
  "outline": [
    {
      "title": "Chapter 1: Introduction",
      "page_number": 1,
      "reading_time_minutes": 2.5
    }
  ],
  "condensed_content": [
    {
      "text": "Content text...",
      "page_number": 1,
      "word_count": 625,
      "reading_time_minutes": 2.5,
      "importance_score": 0.8,
      "headings": ["Chapter 1"],
      "keywords": ["important", "key", "concept"]
    }
  ],
  "key_points": [
    {
      "point": "This is a key point from the document.",
      "category": "important"
    }
  ],
  "total_reading_time_minutes": 20.0,
  "total_word_count": 5000,
  "quiz": [
    {
      "question": "What is the main topic?",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "A",
      "explanation": "Explanation here"
    }
  ],
  "original_filename": "document.pdf",
  "processing_notes": ["Processed for 20 minute reading time"]
}
```

## Processing Logic

1. **Text Extraction**: Uses PyMuPDF to extract raw text from the PDF
2. **Chunking**: Splits text into ~500-700 word chunks
3. **Scoring**: Scores each chunk based on:
   - Presence of headings and titles
   - Keyword density (TF-IDF analysis)
   - Sentence structure and length
   - Presence of numbers and data
4. **Selection**: Selects the most important chunks that fit within the time limit
5. **Summarization**: Uses GPT-3.5 to summarize chunks longer than 5 minutes
6. **Output Generation**: Creates structured output with outline, key points, and quiz

## Configuration

Key configuration options in `.env`:

- `OPENAI_API_KEY`: Your OpenAI API key for GPT-3.5 access
- `WORDS_PER_MINUTE`: Reading speed assumption (default: 250)
- `MAX_CHUNK_SIZE`: Maximum words per chunk (default: 700)
- `MAX_SUMMARY_LENGTH`: Maximum characters for GPT summarization (default: 3000)

## Dependencies

- **FastAPI**: Web framework
- **PyMuPDF**: PDF text extraction
- **OpenAI**: GPT-3.5 API for summarization and quiz generation
- **NLTK**: Natural language processing
- **scikit-learn**: TF-IDF analysis for keyword extraction
- **python-dotenv**: Environment variable management

## Error Handling

The API includes comprehensive error handling for:
- Invalid file types (non-PDF files)
- PDF processing errors
- OpenAI API failures
- Memory and processing timeouts

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Structure
```
backend/
├── main.py              # FastAPI application and endpoints
├── models.py            # Pydantic data models
├── pdf_processor.py     # Core PDF processing logic
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables template
└── README.md           # This file
```

## License

This project is licensed under the MIT License. 