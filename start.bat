@echo off
REM Cargo - Quick Start Script for Windows
echo.
echo ========================================
echo   Cargo - Bulk Content Generator
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

REM Check if dependencies are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Start the application
echo Starting Cargo...
echo.
echo Open your browser and navigate to:
echo   http://localhost:5000
echo.
echo Press CTRL+C to stop the server
echo.
python run.py
