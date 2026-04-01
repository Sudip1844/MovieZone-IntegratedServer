@echo off
REM MovieZone Integrated Server - Setup Script for Windows

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   MovieZone Integrated Server - Setup Script              ║
echo ║                                                            ║
echo ║   এই স্ক্রিপ্ট সম্পূর্ণ সেটআপ করবে                         ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python first.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo.
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo.
echo 📦 Upgrading pip...
python -m pip install --upgrade pip -q

REM Install requirements
echo.
echo 📦 Installing dependencies from requirements.txt...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Test database connection
echo.
echo 🧪 Testing database connection...
python -c "from config import DATABASE_URL; print('Database URL configured: ' + DATABASE_URL[:50] + '...')"
if errorlevel 1 (
    echo ❌ Database configuration error
    pause
    exit /b 1
)

REM Initialize database
echo.
echo 💾 Initializing database...
python -c "from database import init_db; result = init_db(); print('✅ Database initialized' if result else '❌ Database initialization failed')"

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                  ✅ SETUP COMPLETE!                        ║
echo ╚════════════════════════════════════════════════════════════╝
echo.
echo 🚀 স্টার্ট করতে এই কমান্ড রান করুন:
echo.
echo    python main.py
echo.
echo 📊 তারপর ব্রাউজারে খুলুন:
echo    http://localhost:5000
echo.
pause
