@echo off
echo.
echo Starting Stock Analysis Application...
echo.

REM Check if MongoDB is running
tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MongoDB is already running
) else (
    echo [WARNING] MongoDB is not running
    echo Starting MongoDB...
    
    REM Check if MongoDB is installed
    where mongod >nul 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] MongoDB is not installed!
        echo.
        echo Please install MongoDB from: https://www.mongodb.com/try/download/community
        echo.
        pause
        exit /b 1
    )
    
    REM Create data directory
    if not exist "data\db" mkdir data\db
    
    REM Start MongoDB
    start "MongoDB" mongod --dbpath data\db --logpath data\mongodb.log
    timeout /t 3 /nobreak >nul
    
    tasklist /FI "IMAGENAME eq mongod.exe" 2>NUL | find /I /N "mongod.exe">NUL
    if "%ERRORLEVEL%"=="0" (
        echo [OK] MongoDB started successfully
    ) else (
        echo [ERROR] Could not start MongoDB
        echo Please start MongoDB manually and run this script again.
        pause
        exit /b 1
    )
)

echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [WARNING] No virtual environment found
    echo Continuing with system Python...
)

echo.

REM Check if dependencies are installed
python -c "import streamlit" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Dependencies not installed
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Test MongoDB connection
echo Testing MongoDB connection...
python -c "from modules.mongodb_cache import MongoDBCache; MongoDBCache()" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] MongoDB connection successful
) else (
    echo [ERROR] Could not connect to MongoDB
    echo Please check your MongoDB installation and try again.
    pause
    exit /b 1
)

echo.
echo Starting Streamlit application...
echo Access the app at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the application
echo.

REM Run Streamlit
streamlit run app.py
