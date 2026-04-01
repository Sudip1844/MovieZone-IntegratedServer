#!/bin/bash

# MovieZone Integrated Server - Setup Script for Linux/Mac

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   MovieZone Integrated Server - Setup Script              ║"
echo "║                                                            ║"
echo "║   এই স্ক্রিপ্ট সম্পূর্ণ সেটআপ করবে                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found! Please install Python first."
    echo "   Download from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip -q

# Install requirements
echo ""
echo "📦 Installing dependencies from requirements.txt..."
pip install -r requirements.txt -q
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo "✅ Dependencies installed"

# Test database connection
echo ""
echo "🧪 Testing database connection..."
python -c "from config import DATABASE_URL; print('Database URL configured: ' + DATABASE_URL[:50] + '...')"
if [ $? -ne 0 ]; then
    echo "❌ Database configuration error"
    exit 1
fi

# Initialize database
echo ""
echo "💾 Initializing database..."
python -c "from database import init_db; result = init_db(); print('✅ Database initialized' if result else '❌ Database initialization failed')"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ SETUP COMPLETE!                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 স্টার্ট করতে এই কমান্ড রান করুন:"
echo ""
echo "   python main.py"
echo ""
echo "📊 তারপর ব্রাউজারে খুলুন:"
echo "   http://localhost:5000"
echo ""
