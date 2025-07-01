@echo off
echo 🚀 Setting up 30-Minute PDF Generator for GitHub and Render deployment...

REM Check if git is initialized
if not exist ".git" (
    echo 📁 Initializing Git repository...
    git init
    echo ✅ Git repository initialized
) else (
    echo ✅ Git repository already exists
)

REM Check if .gitignore exists
if not exist ".gitignore" (
    echo ❌ .gitignore file not found. Please create one first.
    pause
    exit /b 1
) else (
    echo ✅ .gitignore file found
)

REM Check if README.md exists
if not exist "README.md" (
    echo ❌ README.md file not found. Please create one first.
    pause
    exit /b 1
) else (
    echo ✅ README.md file found
)

REM Check backend requirements
if not exist "backend\requirements.txt" (
    echo ❌ backend\requirements.txt not found
    pause
    exit /b 1
) else (
    echo ✅ backend\requirements.txt found
)

REM Check frontend package.json
if not exist "project\package.json" (
    echo ❌ project\package.json not found
    pause
    exit /b 1
) else (
    echo ✅ project\package.json found
)

echo.
echo 📋 Next steps:
echo 1. Create a GitHub repository at https://github.com/new
echo 2. Name it '30min-pdf-generator' ^(or your preferred name^)
echo 3. Make it public or private
echo 4. Don't initialize with README ^(you already have one^)
echo.
echo 5. Then run these commands:
echo    git add .
echo    git commit -m "Initial commit"
echo    git remote add origin https://github.com/Supra26/30Min.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 6. Follow the deployment guide in RENDER_DEPLOYMENT.md
echo.
echo 🎉 Setup complete! Your project is ready for GitHub and Render deployment.
pause 