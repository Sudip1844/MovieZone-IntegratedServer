# IntegratedServer/setup_tables.py
# Drop ALL old Supabase tables and create new unified tables
# Uses Supabase REST API (HTTPS) - no direct PostgreSQL needed

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load env
load_dotenv(Path(__file__).parent / '.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

HEADERS = {
    'apikey': SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}


def execute_sql_via_rest(sql_statements):
    """Execute SQL using Supabase's pg_net or direct table operations"""
    # Try using the query endpoint (available in newer Supabase)
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    try:
        resp = requests.post(url, headers=HEADERS, json={"query": sql_statements}, timeout=30)
        if resp.ok:
            return True, resp.text
        else:
            return False, f"Status {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, str(e)


def check_table_exists(table_name):
    """Check if a table exists by trying to query it"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?limit=0"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        return resp.status_code != 404
    except:
        return False


def delete_all_rows(table_name):
    """Delete all rows from a table"""
    # Supabase REST API needs a filter to delete, use a broad one
    url = f"{SUPABASE_URL}/rest/v1/{table_name}?id=gt.0"
    try:
        resp = requests.delete(url, headers=HEADERS, timeout=10)
        return resp.ok
    except:
        return False


def create_table_via_insert(table_name, sample_data):
    """Create a table by inserting data (Supabase auto-creates if using Dashboard)"""
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    try:
        resp = requests.post(url, headers=HEADERS, json=sample_data, timeout=10)
        return resp.ok, resp.text
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("  MovieZone - Supabase Table Setup")
    print("=" * 60)
    
    if not SUPABASE_URL or not SERVICE_ROLE_KEY:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
        sys.exit(1)
    
    print(f"\n🔗 Supabase URL: {SUPABASE_URL}")
    
    # Test connection
    print("\n📡 Testing connection...")
    try:
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=HEADERS, timeout=10)
        print(f"   Status: {resp.status_code}")
        if resp.status_code in (200, 401):
            print("   ✅ Connection successful")
        else:
            print(f"   ⚠️ Unexpected status: {resp.status_code}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        sys.exit(1)
    
    # Check which old tables exist
    old_tables = ['movie_links', 'quality_movie_links', 'quality_episodes', 
                  'quality_zips', 'api_tokens', 'admin_settings', 'ad_view_sessions']
    new_tables = ['movies', 'users', 'admin_accounts', 'channels', 
                  'movie_requests', 'telegram_admins']
    
    print("\n📊 Checking existing tables...")
    for table in old_tables + new_tables:
        exists = check_table_exists(table)
        status = "✅ exists" if exists else "⬜ not found"
        print(f"   {table}: {status}")
    
    # Try to clean old tables
    print("\n🗑️  Cleaning old table data...")
    for table in old_tables:
        if check_table_exists(table):
            success = delete_all_rows(table)
            print(f"   {table}: {'✅ cleared' if success else '⚠️ could not clear'}")
    
    # The SQL for creating tables needs to be run via Supabase Dashboard
    # since the REST API doesn't support DDL operations directly
    print("\n" + "=" * 60)
    print("  ⚠️  TABLE CREATION REQUIRES SUPABASE DASHBOARD")
    print("=" * 60)
    print("""
Direct PostgreSQL connection is not available from this network.
Please run the following SQL in your Supabase Dashboard:

  1. Go to: https://supabase.com/dashboard
  2. Select your project
  3. Go to SQL Editor
  4. Run the SQL from: IntegratedServer/create_tables.sql

The SQL file has been generated for you.
""")


# Generate the SQL file
SQL_CONTENT = """
-- ====================================
-- MovieZone Unified Tables
-- Run this in Supabase SQL Editor
-- ====================================

-- DROP OLD TABLES
DROP TABLE IF EXISTS ad_view_sessions CASCADE;
DROP TABLE IF EXISTS api_tokens CASCADE;
DROP TABLE IF EXISTS admin_settings CASCADE;
DROP TABLE IF EXISTS quality_zips CASCADE;
DROP TABLE IF EXISTS quality_episodes CASCADE;
DROP TABLE IF EXISTS quality_movie_links CASCADE;
DROP TABLE IF EXISTS movie_links CASCADE;
DROP TABLE IF EXISTS movie_reviews CASCADE;
DROP TABLE IF EXISTS movies CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS admin_accounts CASCADE;
DROP TABLE IF EXISTS channels CASCADE;
DROP TABLE IF EXISTS movie_requests CASCADE;
DROP TABLE IF EXISTS monthly_stats CASCADE;
DROP TABLE IF EXISTS telegram_admins CASCADE;

-- ====================================
-- MOVIES - Unified movie data
-- ====================================
CREATE TABLE movies (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    categories TEXT[] DEFAULT '{}',
    languages TEXT[] DEFAULT '{}',
    release_year TEXT DEFAULT 'N/A',
    runtime TEXT DEFAULT 'N/A',
    imdb_rating TEXT DEFAULT 'N/A',
    thumbnail_file_id TEXT,
    download_type TEXT NOT NULL DEFAULT 'single',
    original_link TEXT,
    quality_480p TEXT,
    quality_720p TEXT,
    quality_1080p TEXT,
    episodes JSONB,
    start_from_episode INTEGER DEFAULT 1,
    from_episode INTEGER,
    to_episode INTEGER,
    short_id TEXT UNIQUE,
    status TEXT DEFAULT 'pending',
    views INTEGER DEFAULT 0,
    downloads INTEGER DEFAULT 0,
    ads_enabled BOOLEAN DEFAULT TRUE,
    added_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================
-- USERS - Telegram bot users
-- ====================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    first_name TEXT,
    username TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================
-- ADMIN_ACCOUNTS - Website admin logins
-- ====================================
CREATE TABLE admin_accounts (
    id SERIAL PRIMARY KEY,
    admin_id TEXT UNIQUE NOT NULL,
    admin_password TEXT NOT NULL,
    display_name TEXT,
    role TEXT DEFAULT 'admin',
    is_active BOOLEAN DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert Default Owner Credentials (do not hardcode in backend env)
INSERT INTO admin_accounts (admin_id, admin_password, display_name, role) 
VALUES ('sbiswas1844', 'save@184455', 'Owner', 'owner')
ON CONFLICT (admin_id) DO NOTHING;

-- ====================================
-- CHANNELS - Managed Telegram channels
-- ====================================
CREATE TABLE channels (
    id SERIAL PRIMARY KEY,
    channel_id TEXT UNIQUE NOT NULL,
    channel_name TEXT NOT NULL,
    short_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================
-- MOVIE_REQUESTS - User movie requests
-- ====================================
CREATE TABLE movie_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    movie_name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ====================================
-- AD_VIEW_SESSIONS - Ad tracking
-- ====================================
CREATE TABLE ad_view_sessions (
    id SERIAL PRIMARY KEY,
    ip_address TEXT NOT NULL,
    short_id TEXT NOT NULL,
    link_type TEXT DEFAULT 'single',
    viewed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(ip_address, short_id, link_type)
);

-- ====================================
-- MONTHLY_STATS - Removed
-- ====================================

-- ====================================
-- TELEGRAM_ADMINS - Admin accounts for bot
-- ====================================
CREATE TABLE telegram_admins (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    short_name TEXT NOT NULL
);

-- ====================================
-- Insert default owner
-- ====================================
INSERT INTO admin_accounts (admin_id, admin_password, display_name, is_active, created_by)
VALUES ('sbiswas1844', 'save@184455', 'Owner', TRUE, 'system')
ON CONFLICT (admin_id) DO NOTHING;

INSERT INTO users (user_id, first_name, role)
VALUES (5379553841, 'Owner', 'owner')
ON CONFLICT (user_id) DO NOTHING;

-- Enable Row Level Security (recommended)
ALTER TABLE movies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE movie_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_view_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_admins ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "service_role_all" ON movies FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON admin_accounts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON channels FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON movie_requests FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON ad_view_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all" ON telegram_admins FOR ALL USING (true) WITH CHECK (true);
"""

if __name__ == '__main__':
    # Write SQL file
    sql_path = Path(__file__).parent / 'create_tables.sql'
    sql_path.write_text(SQL_CONTENT.strip(), encoding='utf-8')
    print(f"📄 SQL file written to: {sql_path}")
    main()
