#!/bin/bash

echo "🚀 Setting up 30-Minute PDF Generator for GitHub and Render deployment..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📁 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Check if .gitignore exists
if [ ! -f ".gitignore" ]; then
    echo "❌ .gitignore file not found. Please create one first."
    exit 1
else
    echo "✅ .gitignore file found"
fi

# Check if README.md exists
if [ ! -f "README.md" ]; then
    echo "❌ README.md file not found. Please create one first."
    exit 1
else
    echo "✅ README.md file found"
fi

# Check backend requirements
if [ ! -f "backend/requirements.txt" ]; then
    echo "❌ backend/requirements.txt not found"
    exit 1
else
    echo "✅ backend/requirements.txt found"
fi

# Check frontend package.json
if [ ! -f "project/package.json" ]; then
    echo "❌ project/package.json not found"
    exit 1
else
    echo "✅ project/package.json found"
fi

echo ""
echo "📋 Next steps:"
echo "1. Create a GitHub repository at https://github.com/new"
echo "2. Name it '30min-pdf-generator' (or your preferred name)"
echo "3. Make it public or private"
echo "4. Don't initialize with README (you already have one)"
echo ""
echo "5. Then run these commands:"
echo "   git add ."
echo "   git commit -m 'Initial commit'"
echo "   git remote add origin https://github.com/Supra26/30Min.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "6. Follow the deployment guide in RENDER_DEPLOYMENT.md"
echo ""
echo "🎉 Setup complete! Your project is ready for GitHub and Render deployment." 