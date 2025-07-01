# 30-Minute PDF Generator

A web application that generates concise study materials from PDF documents, designed to help users create focused learning content in just 30 minutes.

## Features

- **PDF Processing**: Upload and extract content from PDF documents
- **AI-Powered Summarization**: Generate concise study materials using AI
- **User Authentication**: Google OAuth integration for secure login
- **Subscription Management**: Flexible pricing plans with recurring payments
- **Study Pack Generation**: Create downloadable study materials
- **History Tracking**: View and manage your generated study packs

## Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **SQLite**: Database (can be upgraded to PostgreSQL for production)
- **Razorpay**: Payment processing
- **PyJWT**: JWT token authentication
- **PyPDF2**: PDF processing
- **NLTK**: Natural language processing

### Frontend
- **React**: UI framework with TypeScript
- **Vite**: Build tool and development server
- **Tailwind CSS**: Styling framework
- **Zustand**: State management
- **Axios**: HTTP client

## Project Structure

```
30min/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main application entry point
│   ├── models.py           # Database models
│   ├── auth.py             # Authentication logic
│   ├── pricing.py          # Payment and subscription logic
│   ├── pdf_processor.py    # PDF processing utilities
│   ├── pdf_generator.py    # Study pack generation
│   └── requirements.txt    # Python dependencies
├── project/                # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── stores/         # Zustand state stores
│   │   ├── services/       # API services
│   │   └── App.tsx         # Main app component
│   ├── package.json        # Node.js dependencies
│   └── vite.config.ts      # Vite configuration
└── README.md              # This file
```

## Local Development Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd 30min
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp env_example.txt .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"
   ```

6. **Start the backend server**
   ```bash
   python main.py
   # Or use the provided script
   python start_server.py
   ```

### Frontend Setup

1. **Navigate to the frontend directory**
   ```bash
   cd project
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

## Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
# Database
DATABASE_URL=sqlite:///./thirty_minute_pdf.db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Razorpay
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

## Deployment

### Render Deployment

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Deploy on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" and select "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name**: `30min-backend`
     - **Root Directory**: `backend`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables in the Render dashboard
   - Deploy!

3. **Deploy Frontend**
   - Create another web service for the frontend
   - **Root Directory**: `project`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run preview`
   - Set `VITE_API_URL` environment variable to your backend URL

### Environment Variables for Production

Make sure to set these in your Render dashboard:

- `DATABASE_URL`: Use PostgreSQL URL from Render
- `SECRET_KEY`: Generate a strong secret key
- `GOOGLE_CLIENT_ID`: Your Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Your Google OAuth client secret
- `RAZORPAY_KEY_ID`: Your Razorpay key ID
- `RAZORPAY_KEY_SECRET`: Your Razorpay key secret
- `FRONTEND_URL`: Your frontend URL

## API Endpoints

### Authentication
- `POST /auth/google` - Google OAuth login
- `POST /auth/refresh` - Refresh JWT token

### PDF Processing
- `POST /upload` - Upload PDF file
- `POST /generate` - Generate study pack
- `GET /history` - Get user's study pack history

### Pricing & Subscriptions
- `GET /pricing/plans` - Get available plans
- `POST /pricing/create-order` - Create payment order
- `POST /pricing/verify-payment` - Verify payment
- `POST /subscriptions/create` - Create subscription
- `POST /subscriptions/verify` - Verify subscription
- `GET /subscriptions/status` - Get subscription status
- `POST /subscriptions/cancel` - Cancel subscription

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@30minpdf.com or create an issue in this repository. 