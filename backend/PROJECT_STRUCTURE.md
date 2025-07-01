# Thirty-Minute PDF Backend - Project Structure

## Overview
This is a FastAPI backend service that processes PDF documents and generates time-based summaries. The service intelligently extracts the most important content that can be read within a specified time limit.

## File Structure

```
backend/
├── main.py                 # FastAPI application and API endpoints
├── models.py               # Pydantic data models for request/response
├── pdf_processor.py        # Core PDF processing logic
├── requirements.txt        # Python dependencies
├── env_example.txt         # Environment variables template
├── README.md              # Comprehensive documentation
├── start_server.py        # Smart startup script with dependency checks
├── start_server.bat       # Windows batch file for easy startup
├── start_server.sh        # Unix/Linux/Mac shell script for easy startup
├── test_api.py            # Simple API testing script
└── PROJECT_STRUCTURE.md   # This file
```

## Core Components

### 1. main.py
- FastAPI application setup with CORS middleware
- File upload endpoint (`/process-pdf`)
- Health check endpoints
- Error handling and logging

### 2. models.py
- `TimeLimit`: Enum for time options (10, 20, 30 minutes)
- `Chunk`: Represents text chunks with metadata
- `OutlineItem`: Document outline structure
- `KeyPoint`: Important points extracted from content
- `QuizQuestion`: Generated quiz questions
- `SummaryResponse`: Complete API response structure

### 3. pdf_processor.py
- `PDFProcessor` class with all core logic:
  - Text extraction using PyMuPDF
  - Smart chunking (~500-700 words per chunk)
  - Importance scoring using TF-IDF and heuristics
  - Time-based content selection
  - GPT-3.5 summarization for long chunks
  - Quiz generation
  - Key point extraction

## Processing Pipeline

1. **Text Extraction**: PyMuPDF extracts raw text from PDF
2. **Chunking**: Text split into manageable chunks
3. **Scoring**: Each chunk scored for importance
4. **Selection**: Most important chunks selected within time limit
5. **Summarization**: Long chunks summarized using GPT-3.5
6. **Output Generation**: Structured response with outline, key points, quiz

## Key Features

- **Intelligent Content Selection**: Uses multiple scoring factors
- **Time-Aware Processing**: Respects user's time constraints
- **AI Integration**: GPT-3.5 for summarization and quiz generation
- **Robust Error Handling**: Graceful handling of various failure modes
- **Comprehensive Logging**: Detailed processing logs
- **Easy Setup**: Automated dependency management and environment setup

## API Endpoints

- `GET /`: Health check
- `GET /health`: Detailed health status
- `POST /process-pdf`: Main PDF processing endpoint

## Configuration

Environment variables (via `.env` file):
- `OPENAI_API_KEY`: Required for AI features
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `WORDS_PER_MINUTE`: Reading speed assumption (default: 250)

## Dependencies

- **FastAPI**: Web framework
- **PyMuPDF**: PDF text extraction
- **OpenAI**: GPT-3.5 API integration
- **NLTK**: Natural language processing
- **scikit-learn**: TF-IDF analysis
- **python-dotenv**: Environment management

## Getting Started

1. **Quick Start (Windows)**:
   ```cmd
   cd backend
   start_server.bat
   ```

2. **Quick Start (Unix/Linux/Mac)**:
   ```bash
   cd backend
   ./start_server.sh
   ```

3. **Manual Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   python start_server.py
   ```

## Testing

Run the test script to verify the API:
```bash
python test_api.py
```

## API Documentation

Once the server is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Integration with Frontend

The backend is designed to work with the React frontend in the `project/` directory. CORS is configured to allow requests from common development ports (3000, 5173). 