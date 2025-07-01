# Thirty-Minute PDF - Setup Guide

## Features Added
✅ **Google Authentication** - Sign up/login with Google  
✅ **User History** - Track all processed PDFs  
✅ **PDF Download** - Download study packs as PDF files  
✅ **Database Storage** - SQLite database for user data  

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the `backend` folder:
```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here

# JWT Configuration  
SECRET_KEY=your-super-secret-key-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///./thirty_minute_pdf.db

# OpenAI Configuration (if needed)
OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Get Google Client ID
1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing one
3. Go to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth client ID"
5. Choose "Web application"
6. Add authorized origins: `http://localhost:5173`
7. Copy the Client ID and add it to your `.env` file

### 4. Generate Secret Key
Generate a strong secret key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

## Frontend Setup

### 1. Install Dependencies
```bash
cd project
npm install
```

### 2. Update Google Client ID
In `src/components/GoogleLogin.tsx`, replace:
```javascript
client_id: 'YOUR_GOOGLE_CLIENT_ID'
```
with your actual Google Client ID.

## Running the Application

### 1. Start Backend
```bash
cd backend
python main.py
```
Backend will run on: http://localhost:8000

### 2. Start Frontend
```bash
cd project
npm run dev
```
Frontend will run on: http://localhost:5173

## How to Use

1. **Sign In**: Click "Sign in with Google" on the login page
2. **Upload PDF**: Select any PDF file to process
3. **Choose Time**: Select 10, 20, or 30 minutes
4. **Get Study Pack**: View your personalized study pack
5. **Download PDF**: Click "Download PDF" to save the study pack
6. **View History**: Click "History" in the header to see all your processed PDFs

## API Endpoints

- `POST /auth/google` - Google authentication
- `GET /auth/me` - Get current user info
- `GET /history` - Get user's processing history
- `GET /history/{id}` - Get specific history item
- `POST /process-pdf` - Process PDF file
- `GET /download-pdf/{id}` - Download PDF study pack

## Database Schema

The application uses SQLite with two main tables:
- `users` - User authentication data
- `user_history` - Processing history and results

## Troubleshooting

### Common Issues:
1. **Import errors**: Make sure all dependencies are installed
2. **Google auth fails**: Verify your Google Client ID is correct
3. **Database errors**: The database will be created automatically on first run
4. **CORS errors**: Backend is configured to allow localhost origins

### Testing:
Run the test script to verify everything works:
```bash
python test_frontend_backend.py
``` 