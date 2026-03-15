@echo off
REM Update yt-dlp script for CloudTube (Windows)
REM This script updates yt-dlp to the latest version

echo Updating yt-dlp to latest version...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Update yt-dlp
pip install --upgrade yt-dlp

echo.
echo yt-dlp updated successfully!
echo.
echo Current yt-dlp version:
yt-dlp --version

echo.
echo Please restart the bot manually to apply changes
echo.
pause
