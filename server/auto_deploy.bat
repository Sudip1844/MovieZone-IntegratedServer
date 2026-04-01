@echo off
REM MovieZone Integrated Server - Complete Auto Setup & Deploy
REM This script does EVERYTHING automatically

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   MovieZone - Complete Automated Setup & Deploy           ║
echo ║                                                            ║
echo ║   এই স্ক্রিপ্ট সম্পূর্ণ প্রক্রিয়া স্বয়ংক্রিয় করবে:      ║
echo ║   - SQL Schema চালাবে                                     ║
echo ║   - Python setup করবে                                     ║
echo ║   - Connection test করবে                                  ║
echo ║   - Server চালু করবে                                      ║
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

echo ✅ Python found: 
python --version

REM Create virtual environment
echo.
echo 📦 Step 1: Creating Python virtual environment...
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
echo 📦 Step 2: Upgrading pip...
python -m pip install --upgrade pip -q

REM Install requirements
echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Deploy SQL Schema
echo.
echo 🗄️ Step 2: Deploying SQL Schema to Supabase...
echo    Running execute_sql.py...
python execute_sql.py
if errorlevel 1 (
    echo ❌ SQL deployment failed
    echo    But continuing with setup...
) else (
    echo ✅ SQL Schema deployed successfully
)

REM Test connection
echo.
echo 🧪 Step 3: Testing database connection...
python test_connection.py
if errorlevel 1 (
    echo ❌ Connection test failed
    pause
    exit /b 1
)

echo ✅ All connections working

REM Start server
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                  ✅ SETUP COMPLETE!                        ║
echo ║                                                            ║
echo ║         🚀 STARTING SERVER...                              ║
echo ║                                                            ║
echo ║    Open browser: http://localhost:5000                    ║
echo ║    To stop: Press Ctrl+C                                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

python main.py
