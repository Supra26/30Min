#!/usr/bin/env python3
"""
NLTK Fix Script - Diagnoses and fixes NLTK data issues
"""

import sys
import os
import subprocess

def check_python_version():
    """Check Python version"""
    print(f"Python version: {sys.version}")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print("✓ Python version OK")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def test_nltk_import():
    """Test NLTK import"""
    print("\n🧪 Testing NLTK import...")
    try:
        import nltk
        print(f"✓ NLTK version: {nltk.__version__}")
        return True
    except ImportError as e:
        print(f"❌ NLTK import failed: {e}")
        return False

def download_nltk_data():
    """Download NLTK data"""
    print("\n📥 Downloading NLTK data...")
    try:
        import nltk
        
        # Download punkt tokenizer
        print("Downloading punkt tokenizer...")
        nltk.download('punkt', quiet=True)
        print("✓ punkt downloaded")
        
        # Download stopwords
        print("Downloading stopwords...")
        nltk.download('stopwords', quiet=True)
        print("✓ stopwords downloaded")
        
        return True
    except Exception as e:
        print(f"❌ Failed to download NLTK data: {e}")
        return False

def test_nltk_functionality():
    """Test NLTK functionality"""
    print("\n🧪 Testing NLTK functionality...")
    try:
        import nltk
        from nltk.tokenize import word_tokenize, sent_tokenize
        from nltk.corpus import stopwords
        
        # Test tokenization
        text = "This is a test sentence. It has multiple sentences."
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        stop_words = set(stopwords.words('english'))
        
        print(f"✓ Sentence tokenization: {len(sentences)} sentences")
        print(f"✓ Word tokenization: {len(words)} words")
        print(f"✓ Stopwords loaded: {len(stop_words)} words")
        
        return True
    except Exception as e:
        print(f"❌ NLTK functionality test failed: {e}")
        return False

def test_our_nltk_setup():
    """Test our NLTK setup module"""
    print("\n🧪 Testing our NLTK setup module...")
    try:
        from nltk_setup import nltk_setup  # type: ignore[import-untyped]
        
        # Test setup
        success = nltk_setup.setup_nltk()
        print(f"✓ NLTK setup: {'Success' if success else 'With fallbacks'}")
        
        # Test stopwords
        stopwords = nltk_setup.get_stopwords()
        print(f"✓ Stopwords: {len(stopwords)} words")
        
        # Test tokenizers
        sent_tokenizer = nltk_setup.get_sentence_tokenizer()
        word_tokenizer = nltk_setup.get_word_tokenizer()
        
        test_text = "This is a test. It has multiple sentences."
        sentences = sent_tokenizer(test_text)
        words = word_tokenizer(test_text)
        
        print(f"✓ Sentence tokenizer: {len(sentences)} sentences")
        print(f"✓ Word tokenizer: {len(words)} words")
        
        return True
    except Exception as e:
        print(f"❌ Our NLTK setup test failed: {e}")
        return False

def main():
    """Main function"""
    print("=== NLTK Fix Script ===\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("\n💡 Try running: pip install -r requirements.txt manually")
        sys.exit(1)
    
    # Test NLTK import
    if not test_nltk_import():
        print("\n💡 Try running: pip install nltk")
        sys.exit(1)
    
    # Download NLTK data
    if not download_nltk_data():
        print("\n⚠️  NLTK data download failed, but we have fallbacks")
    
    # Test NLTK functionality
    if not test_nltk_functionality():
        print("\n⚠️  NLTK functionality test failed, but we have fallbacks")
    
    # Test our setup
    if not test_our_nltk_setup():
        print("\n❌ Our NLTK setup failed")
        sys.exit(1)
    
    print("\n🎉 NLTK setup completed successfully!")
    print("You can now run the server with: python start_server.py")

if __name__ == "__main__":
    main() 