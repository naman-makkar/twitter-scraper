@echo off
echo Twitter Scraper - Windows Runner
echo ==============================
echo.

if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found. Setting up environment first...
    call setup_windows.bat
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Running Twitter scraper with undetected ChromeDriver...
echo This version works better for Windows users.
echo.

if "%1"=="" (
    echo No username provided. Please specify a Twitter username.
    echo Usage: %0 username [options]
    echo Example: %0 elonmusk --max-scrolls 500
    exit /b 1
) else (
    echo Scraping tweets for: %1
    venv\Scripts\python twitter_scraper_undetected.py %*
)

echo.
echo When finished, deactivate the virtual environment by typing: deactivate
echo. 