@echo off
title AccVaults Sellauth Integration Server
color 0A

echo ========================================
echo   AccVaults Sellauth Integration
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [INFO] Checking dependencies...
pip install -r requirements.txt --quiet

echo.
echo [INFO] Starting Flask server...
echo [INFO] Server will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the Flask application
python app.py

pause
