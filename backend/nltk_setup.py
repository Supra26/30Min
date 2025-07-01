"""
NLTK Setup and Configuration Module
Handles NLTK data download with fallback options and error handling
"""

import nltk
import os
import logging
from typing import Optional, Set

logger = logging.getLogger(__name__)

class NLTKSetup:
    """Handles NLTK data download and setup with fallback options"""
    
    def __init__(self):
        self.required_data = ['punkt', 'stopwords']
        self.downloaded_data = set()
        self.fallback_stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 
            'to', 'was', 'will', 'with', 'i', 'you', 'your', 'they', 'have', 
            'this', 'but', 'not', 'what', 'all', 'were', 'we', 'when', 'there', 
            'can', 'an', 'more', 'no', 'if', 'out', 'so', 'up', 'do', 'would', 
            'could', 'my', 'than', 'first', 'been', 'call', 'who', 'oil', 'sit', 
            'now', 'find', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 
            'part', 'over', 'new', 'sound', 'take', 'only', 'little', 'work', 
            'know', 'place', 'year', 'live', 'me', 'back', 'give', 'most', 
            'very', 'after', 'thing', 'our', 'just', 'name', 'good', 'sentence', 
            'man', 'think', 'say', 'great', 'where', 'help', 'through', 'much', 
            'before', 'line', 'right', 'too', 'mean', 'old', 'any', 'same', 
            'tell', 'boy', 'follow', 'came', 'want', 'show', 'also', 'around', 
            'form', 'three', 'small', 'set', 'put', 'end', 'does', 'another', 
            'well', 'large', 'must', 'big', 'even', 'such', 'because', 'turn', 
            'here', 'why', 'ask', 'went', 'men', 'read', 'need', 'land', 
            'different', 'home', 'us', 'move', 'try', 'kind', 'hand', 'picture', 
            'again', 'change', 'off', 'play', 'spell', 'air', 'away', 'animal', 
            'house', 'point', 'page', 'letter', 'mother', 'answer', 'found', 
            'study', 'still', 'learn', 'should', 'America', 'world', 'high', 
            'every', 'near', 'add', 'food', 'between', 'own', 'below', 'country', 
            'plant', 'last', 'school', 'father', 'keep', 'tree', 'never', 
            'start', 'city', 'earth', 'eye', 'light', 'thought', 'head', 
            'under', 'story', 'saw', 'left', 'don\'t', 'few', 'while', 
            'along', 'might', 'close', 'something', 'seem', 'next', 'hard', 
            'open', 'example', 'begin', 'life', 'always', 'those', 'both', 
            'paper', 'together', 'got', 'group', 'often', 'run', 'important', 
            'until', 'children', 'side', 'feet', 'car', 'mile', 'night', 
            'walk', 'white', 'sea', 'began', 'grow', 'took', 'river', 'four', 
            'carry', 'state', 'once', 'book', 'hear', 'stop', 'without', 
            'second', 'late', 'miss', 'idea', 'enough', 'eat', 'face', 
            'watch', 'far', 'Indian', 'real', 'almost', 'let', 'above', 
            'girl', 'sometimes', 'mountain', 'cut', 'young', 'talk', 'soon', 
            'list', 'song', 'being', 'leave', 'family', 'it\'s'
        }
    
    def setup_nltk(self) -> bool:
        """
        Set up NLTK data with fallback options
        
        Returns:
            bool: True if setup was successful (with or without fallbacks)
        """
        logger.info("Setting up NLTK data...")
        
        success = True
        
        # Try to download required NLTK data
        for data_name in self.required_data:
            if not self._download_nltk_data(data_name):
                success = False
                logger.warning(f"Failed to download {data_name}, will use fallback")
        
        if success:
            logger.info("NLTK setup completed successfully")
        else:
            logger.warning("NLTK setup completed with fallbacks")
        
        return True  # Always return True as we have fallbacks
    
    def _download_nltk_data(self, data_name: str) -> bool:
        """
        Download specific NLTK data with error handling
        
        Args:
            data_name: Name of the NLTK data to download
            
        Returns:
            bool: True if download was successful
        """
        try:
            # Check if data already exists
            nltk.data.find(f'tokenizers/{data_name}' if data_name == 'punkt' else f'corpora/{data_name}')
            logger.info(f"NLTK {data_name} data already available")
            self.downloaded_data.add(data_name)
            return True
            
        except LookupError:
            try:
                logger.info(f"Downloading NLTK {data_name} data...")
                nltk.download(data_name, quiet=True)
                self.downloaded_data.add(data_name)
                logger.info(f"Successfully downloaded NLTK {data_name} data")
                return True
                
            except Exception as e:
                logger.error(f"Failed to download NLTK {data_name} data: {e}")
                return False
    
    def get_stopwords(self) -> Set[str]:
        """
        Get English stopwords with fallback
        
        Returns:
            Set[str]: Set of stopwords
        """
        if 'stopwords' in self.downloaded_data:
            try:
                from nltk.corpus import stopwords
                return set(stopwords.words('english'))
            except Exception as e:
                logger.warning(f"Failed to load NLTK stopwords: {e}, using fallback")
        
        logger.info("Using fallback stopwords")
        return self.fallback_stopwords
    
    def get_sentence_tokenizer(self):
        """
        Get sentence tokenizer with fallback
        
        Returns:
            Function: Sentence tokenization function
        """
        if 'punkt' in self.downloaded_data:
            try:
                from nltk.tokenize import sent_tokenize
                return sent_tokenize
            except Exception as e:
                logger.warning(f"Failed to load NLTK sentence tokenizer: {e}, using fallback")
        
        logger.info("Using fallback sentence tokenizer")
        return self._fallback_sent_tokenize
    
    def get_word_tokenizer(self):
        """
        Get word tokenizer with fallback
        
        Returns:
            Function: Word tokenization function
        """
        if 'punkt' in self.downloaded_data:
            try:
                from nltk.tokenize import word_tokenize
                return word_tokenize
            except Exception as e:
                logger.warning(f"Failed to load NLTK word tokenizer: {e}, using fallback")
        
        logger.info("Using fallback word tokenizer")
        return self._fallback_word_tokenize
    
    def _fallback_sent_tokenize(self, text: str) -> list:
        """
        Fallback sentence tokenizer using simple regex
        
        Args:
            text: Text to tokenize
            
        Returns:
            list: List of sentences
        """
        import re
        # Simple sentence splitting on periods, exclamation marks, and question marks
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _fallback_word_tokenize(self, text: str) -> list:
        """
        Fallback word tokenizer using simple splitting
        
        Args:
            text: Text to tokenize
            
        Returns:
            list: List of words
        """
        import re
        # Simple word splitting on whitespace and punctuation
        words = re.findall(r'\b\w+\b', text.lower())
        return words

# Global NLTK setup instance
nltk_setup = NLTKSetup() 