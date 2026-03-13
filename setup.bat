@echo off
REM Setup script for CloudTube (Windows)
REM Created by Kir
REM Requirements: Python 3.11+, FFmpeg

echo ============================================
echo CloudTube - Setup Script (Windows)
echo Your YouTube in the Cloud
echo ============================================
echo.

REM Check Python version
echo Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo.

REM Check FFmpeg
echo Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: FFmpeg is not installed or not in PATH
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo The bot will not work without FFmpeg!
    echo.
    pause
)
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists, skipping...
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Create directories
echo Creating directories...
if not exist data mkdir data
if not exist logs mkdir logs
if not exist temp mkdir temp
echo Directories created: data, logs, temp
echo.

REM Create .env file
if exist .env (
    echo .env file already exists, skipping...
) else (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file and fill in your configuration:
    echo   - TELEGRAM_BOT_TOKEN (get from @BotFather)
    echo   - TELEGRAM_OWNER_ID (get from @userinfobot)
    echo.
    echo Opening .env file in notepad...
    timeout /t 2 >nul
    notepad .env
)
echo.

REM Initialize database
echo Initializing database...
python -c "import asyncio; from bot.database import Database; from bot.config import AppConfig; asyncio.run((lambda: Database(AppConfig.load_from_env().database_path).initialize())())" 2>nul
if %errorlevel% equ 0 (
    echo Database initialized successfully
) else (
    echo Database will be initialized on first run
)
echo.

echo ============================================
echo Setup complete!
echo ============================================
echo.
echo Next steps:
echo   1. Edit .env file with your configuration (if not done yet)
echo   2. Activate virtual environment: venv\Scripts\activate.bat
echo   3. Run the bot: python -m bot.main
echo.
echo Useful commands:
echo   - Run tests: pytest
echo   - Check configuration: python -c "from bot.config import AppConfig; AppConfig.load_from_env()"
echo   - View logs: type logs\bot.log
echo.
pause
