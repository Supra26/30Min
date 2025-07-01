# Render Deployment Guide

This guide will walk you through deploying your 30-Minute PDF Generator application on Render.

## Prerequisites

1. **GitHub Account**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **Environment Variables**: Prepare your API keys and secrets

## Step 1: Prepare Your GitHub Repository

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```

2. **Create GitHub Repository**:
   - Go to [GitHub](https://github.com)
   - Click "New repository"
   - Name it `30Min` (or your preferred name)
   - Make it public or private
   - Don't initialize with README (you already have one)

3. **Push to GitHub**:
   ```bash
   git remote add origin https://github.com/Supra26/30Min.git
   git branch -M main
   git push -u origin main
   ```

## Step 2: Deploy Backend on Render

1. **Go to Render Dashboard**:
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Sign in with your account

2. **Create New Web Service**:
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub account if not already connected
   - Select your repository: `30Min`

3. **Configure Backend Service**:
   - **Name**: `30min-backend`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or choose paid plan for better performance)

4. **Add Environment Variables**:
   Click "Environment" tab and add these variables:

   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   SECRET_KEY=your-super-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   RAZORPAY_KEY_ID=your-razorpay-key-id
   RAZORPAY_KEY_SECRET=your-razorpay-key-secret
   FRONTEND_URL=https://your-frontend-url.onrender.com
   ```

5. **Create Database** (Optional):
   - Go back to dashboard
   - Click "New +" → "PostgreSQL"
   - Name: `30min-db`
   - Plan: Free
   - Copy the connection string and update `DATABASE_URL`

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for build to complete (usually 2-5 minutes)
   - Note your backend URL: `https://30min-backend.onrender.com`

## Step 3: Deploy Frontend on Render

1. **Create Another Web Service**:
   - Click "New +" → "Web Service"
   - Select the same repository: `30Min`

2. **Configure Frontend Service**:
   - **Name**: `30min-frontend`
   - **Root Directory**: `project`
   - **Runtime**: `Node`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run preview`
   - **Plan**: Free

3. **Add Environment Variables**:
   ```
   VITE_API_URL=https://30min-backend.onrender.com
   ```

4. **Deploy**:
   - Click "Create Web Service"
   - Wait for build to complete
   - Your frontend will be available at: `https://30min-frontend.onrender.com`

## Step 4: Update Environment Variables

1. **Update Backend Environment**:
   - Go to your backend service dashboard
   - Click "Environment" tab
   - Update `FRONTEND_URL` to your frontend URL
   - Update `DATABASE_URL` if you created a PostgreSQL database

2. **Update Frontend Environment**:
   - Go to your frontend service dashboard
   - Click "Environment" tab
   - Update `VITE_API_URL` to your backend URL

## Step 5: Configure Google OAuth

1. **Update Google OAuth Settings**:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to "APIs & Services" → "Credentials"
   - Edit your OAuth 2.0 Client ID
   - Add your Render URLs to authorized origins:
     - `https://30min-frontend.onrender.com`
   - Add your Render URLs to authorized redirect URIs:
     - `https://30min-backend.onrender.com/auth/google/callback`

## Step 6: Configure Razorpay

1. **Update Razorpay Webhook**:
   - Go to [Razorpay Dashboard](https://dashboard.razorpay.com)
   - Navigate to "Settings" → "Webhooks"
   - Add webhook URL: `https://30min-backend.onrender.com/webhooks/razorpay`
   - Select events: `subscription.activated`, `subscription.charged`, `subscription.halted`

## Step 7: Test Your Deployment

1. **Test Backend**:
   - Visit: `https://30min-backend.onrender.com/docs`
   - You should see the FastAPI documentation

2. **Test Frontend**:
   - Visit: `https://30min-frontend.onrender.com`
   - Try uploading a PDF and generating a study pack

3. **Test Authentication**:
   - Try logging in with Google
   - Verify the OAuth flow works

## Troubleshooting

### Common Issues:

1. **Build Fails**:
   - Check the build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`
   - Verify Python version compatibility

2. **Environment Variables Not Working**:
   - Double-check variable names (case-sensitive)
   - Redeploy after adding new environment variables
   - Check for typos in values

3. **Database Connection Issues**:
   - Verify `DATABASE_URL` format
   - Ensure database is accessible from Render
   - Check if database tables are created

4. **CORS Errors**:
   - Verify `FRONTEND_URL` in backend environment
   - Check that frontend URL matches exactly

5. **Payment Issues**:
   - Verify Razorpay keys are correct
   - Check webhook configuration
   - Ensure webhook endpoint is accessible

### Useful Commands:

```bash
# Check build logs
# Go to Render dashboard → Your service → Logs

# Redeploy manually
# Go to Render dashboard → Your service → Manual Deploy

# Check environment variables
# Go to Render dashboard → Your service → Environment
```

## Monitoring

1. **Health Checks**:
   - Render automatically monitors your service
   - Check "Metrics" tab for performance data

2. **Logs**:
   - View real-time logs in the "Logs" tab
   - Useful for debugging issues

3. **Uptime**:
   - Free tier services sleep after 15 minutes of inactivity
   - First request after sleep may take 30-60 seconds

## Scaling (Paid Plans)

If you need better performance:

1. **Upgrade Backend**:
   - Choose "Starter" or higher plan
   - Services stay awake 24/7
   - Better CPU and memory allocation

2. **Upgrade Database**:
   - Choose "Starter" or higher PostgreSQL plan
   - Better performance and reliability

3. **Custom Domain**:
   - Add custom domain in Render dashboard
   - Configure DNS settings

## Security Considerations

1. **Environment Variables**:
   - Never commit secrets to Git
   - Use Render's environment variable system
   - Rotate keys regularly

2. **HTTPS**:
   - Render provides free SSL certificates
   - All traffic is encrypted

3. **Database**:
   - Use strong passwords
   - Restrict database access
   - Regular backups (paid plans)

## Support

- **Render Documentation**: [docs.render.com](https://docs.render.com)
- **Render Community**: [community.render.com](https://community.render.com)
- **GitHub Issues**: Create issues in your repository for code-specific problems 