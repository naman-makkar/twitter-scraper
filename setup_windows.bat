@echo off
echo Twitter Scraper - Windows Setup
echo ===============================
echo.

echo Checking for Python installation...
python --version 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH. Please install Python 3.7+ and try again.
    echo You can download Python from https://www.python.org/downloads/
    exit /b 1
)

echo Creating a Python virtual environment...
python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Failed to create virtual environment. Make sure venv module is available.
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate
if %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment.
    exit /b 1
)

echo Installing required dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install dependencies.
    exit /b 1
)

echo.
echo Checking for Chrome browser...
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Chrome browser doesn't seem to be installed.
    echo Please install Google Chrome and try again.
    echo You can download Chrome from https://www.google.com/chrome/
    exit /b 1
)

echo.
echo Installing specific version of Chrome WebDriver...
pip install webdriver-manager==4.0.1
if %ERRORLEVEL% NEQ 0 (
    echo Failed to install WebDriver Manager.
    exit /b 1
)

echo.
echo Setup complete! Run the Twitter scraper using:
echo venv\Scripts\python run_scraper.py username --max-scrolls 500
echo.
echo For more options, run: venv\Scripts\python run_scraper.py --help
echo.
echo To deactivate the virtual environment when done, run: deactivate

pause 