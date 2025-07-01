# Fix Google OAuth 401 Error

## The Problem
You're getting "Error 401: invalid_client" because the Google Client ID in your code is not valid.

## Solution: Get a Real Google Client ID

### Step 1: Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/apis/credentials
2. Sign in with your Google account

### Step 2: Create/Select Project
1. Create a new project or select an existing one
2. Make sure you're in the correct project

### Step 3: Enable Required APIs
1. Go to "APIs & Services" > "Library"
2. Search for and enable these APIs:
   - "Google+ API" (or "Google Identity Services")
   - "Google OAuth2 API"

### Step 4: Create OAuth Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Web application"
4. Fill in the details:
   - **Name**: "Thirty-Minute PDF App"
   - **Authorized JavaScript origins**:
     - `http://localhost:5173`
     - `http://localhost:3000`
   - **Authorized redirect URIs**:
     - `http://localhost:5173`
     - `http://localhost:3000`
5. Click "Create"

### Step 5: Copy the Client ID
You'll see a popup with your Client ID. It looks like:
`1234567890-abc123def456.apps.googleusercontent.com`

## Update Your Code

### Step 6: Update Frontend
Edit `project/src/components/GoogleLogin.tsx`:
```javascript
client_id: 'YOUR_ACTUAL_CLIENT_ID_HERE', // Replace with your real Client ID
```

### Step 7: Update Backend
Create a `.env` file in the `backend` folder:
```env
GOOGLE_CLIENT_ID=your-actual-client-id-here
SECRET_KEY=your-secret-key-here
```

### Step 8: Restart Servers
1. Stop both servers (Ctrl+C)
2. Restart backend: `cd backend && python main.py`
3. Restart frontend: `cd project && npm run dev`

## Test
1. Go to http://localhost:5173
2. Click "Sign in with Google"
3. The 401 error should be gone!

## Common Issues
- **Wrong Client ID**: Make sure you copied the entire Client ID
- **Wrong Origins**: Make sure localhost:5173 is in authorized origins
- **API not enabled**: Make sure Google+ API is enabled
- **Wrong project**: Make sure you're in the correct Google Cloud project 