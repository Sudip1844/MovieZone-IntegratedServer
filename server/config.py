# IntegratedServer/config.py
# Centralized Configuration for Flask server and Supabase
# NOTE: Bot-specific config (BOT_TOKEN, CATEGORIES, etc.) is in bot/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# ============================================
# FLASK CONFIGURATION
# ============================================

# CORS
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(',')

class Config:
    """Base configuration"""
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Server
    HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    PORT = int(os.getenv('FLASK_PORT', 5000))

# ============================================
# SUPABASE CONFIGURATION
# ============================================

SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
SUPABASE_DB_HOST = os.getenv('SUPABASE_DB_HOST', '')
SUPABASE_DB_NAME = os.getenv('SUPABASE_DB_NAME', 'postgres')
SUPABASE_DB_USER = os.getenv('SUPABASE_DB_USER', 'postgres')
SUPABASE_DB_PASSWORD = os.getenv('SUPABASE_DB_PASSWORD', '')
SUPABASE_DB_PORT = int(os.getenv('SUPABASE_DB_PORT', 5432))

# Database connection string for SQLAlchemy
DATABASE_URL = f"postgresql://{SUPABASE_DB_USER}:{SUPABASE_DB_PASSWORD}@{SUPABASE_DB_HOST}:{SUPABASE_DB_PORT}/{SUPABASE_DB_NAME}"

# ============================================
# ADMIN CONFIGURATION (Owner Panel Login)
# ============================================

ADMIN_ID = os.getenv('ADMIN_ID', 'sbiswas1844')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'save@184455')

# ============================================
# API CONFIGURATION
# ============================================

API_PREFIX = '/api'
SHORT_ID_LENGTH = 6

