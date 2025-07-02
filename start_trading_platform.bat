@echo off
title Angel One Trading Platform with Auto-Ngrok

echo ================================================
echo Angel One Trading Platform - Auto Setup
echo ================================================
echo.

echo Checking requirements...

REM Check if ngrok is installed
ngrok version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Ngrok not found. Installing...
    winget install ngrok.ngrok
    if %ERRORLEVEL% neq 0 (
        echo ❌ Failed to install ngrok
        echo Please install manually: winget install ngrok.ngrok
        pause
        exit /b 1
    )
)

echo ✅ Ngrok is available

REM Set environment variables for this session
set NGROK_AUTO_START=True
set NGROK_AUTH_TOKEN=2zIambSj5KfyMpM6mcBWmkvDWtq_69e8qH2wuA4jGu7A5o6RL
set ANGEL_CLIENT_ID=xhMChjlS
set ANGEL_CLIENT_SECRET=78e4798a-f35b-481f-9804-ff78557f99ed

echo ✅ Environment configured

echo.
echo 🚀 Starting Django with Auto-Ngrok...
echo ================================================
echo.
echo 📝 What will happen:
echo   1. Django server starts on localhost:8000
echo   2. Ngrok tunnel automatically starts
echo   3. Public HTTPS URL created for Angel One API
echo   4. Django settings updated with public URL
echo.
echo 🔗 Your Angel One callback URL will be displayed
echo 📋 Copy it to Angel One portal when shown
echo.
echo Press any key to continue...
pause >nul

echo.
echo Starting server...

REM Start Django with auto-ngrok
python manage.py runserver

echo.
echo ✅ Server stopped
pause
