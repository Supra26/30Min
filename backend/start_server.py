#!/usr/bin/env python3
"""
Startup script for the Thirty-Minute PDF API server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import fitz
        import openai
        import nltk
        import sklearn
        print("✓ All required dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists and has OpenAI API key"""
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  No .env file found")
        print("Creating .env file from template...")
        
        # Copy from env_example.txt if it exists
        example_path = Path("env_example.txt")
        if example_path.exists():
            with open(example_path, 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
            print("✓ Created .env file from template")
        else:
            print("❌ No env_example.txt found")
            return False
    
    # Check if OpenAI API key is set
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("⚠️  OpenAI API key not set in .env file")
        print("Please edit .env and add your OpenAI API key")
        print("You can still run the server, but AI features will be disabled")
    else:
        print("✓ OpenAI API key configured")
    
    return True

def download_nltk_data():
    """Download required NLTK data"""
    try:
        import nltk
        
        # Check and download punkt tokenizer
        try:
            nltk.data.find('tokenizers/punkt')
            print("✓ NLTK punkt tokenizer already downloaded")
        except LookupError:
            print("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt')
            print("✓ NLTK punkt tokenizer downloaded")
        
        # Check and download stopwords
        try:
            nltk.data.find('corpora/stopwords')
            print("✓ NLTK stopwords already downloaded")
        except LookupError:
            print("Downloading NLTK stopwords...")
            nltk.download('stopwords')
            print("✓ NLTK stopwords downloaded")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not download NLTK data: {e}")

def start_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting Thirty-Minute PDF API server...")
    print("Server will be available at: http://localhost:8000")
    print("API documentation: http://localhost:8000/docs")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        # Import and run the server
        from main import app
        import uvicorn
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("=== Thirty-Minute PDF API Startup ===\n")
    
    # Check Python version
    check_python_version()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment file
    check_env_file()
    
    # Download NLTK data
    download_nltk_data()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main() 