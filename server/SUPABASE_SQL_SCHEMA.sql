-- MovieZone Complete SQL Schema for Supabase
-- Run these commands in your Supabase SQL Editor
-- Updated with IP-based Timer Skip Enhancement (2025-08-17)
-- Updated with Review Queue & Admin Management (2025-01-11)
--
-- Features included:
-- - All link types: Single movies, Quality movies, Episodes, Quality zips
-- - IP-based 5-minute timer skip system with automatic cleanup
-- - Admin authentication system
-- - API token management for external integrations
-- - Movie Review Queue System (NEW)
-- - Manual Admin Account Management (NEW)
-- - Complete RLS policies for security

-- 1. Drop existing tables if they exist (to avoid conflicts)
-- IMPORTANT: This will delete all existing data! Only run if you want to start fresh.
DROP TABLE IF EXISTS ad_view_sessions CASCADE;
DROP TABLE IF EXISTS movie_links CASCADE;
DROP TABLE IF EXISTS quality_movie_links CASCADE;
DROP TABLE IF EXISTS quality_episodes CASCADE;
DROP TABLE IF EXISTS quality_zips CASCADE;
DROP TABLE IF EXISTS admin_settings CASCADE;
DROP TABLE IF EXISTS movie_reviews CASCADE; -- NEW: Movie review queue
DROP TABLE IF EXISTS admin_accounts CASCADE; -- NEW: Manual admin account management
DROP TABLE IF EXISTS telegram_admins CASCADE; -- NEW: Telegram Bot Admins

-- 2. Create movie_links table with proper Supabase syntax
CREATE TABLE movie_links (
    id BIGSERIAL PRIMARY KEY,
    movie_name TEXT NOT NULL,
    original_link TEXT NOT NULL,
    short_id TEXT NOT NULL UNIQUE,
    views INTEGER NOT NULL DEFAULT 0,
    date_added TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ads_enabled BOOLEAN NOT NULL DEFAULT true
);

-- 3. Create quality_movie_links table for multi-quality downloads
CREATE TABLE quality_movie_links (
    id BIGSERIAL PRIMARY KEY,
    movie_name TEXT NOT NULL,
    short_id TEXT NOT NULL UNIQUE,
    quality_480p TEXT, -- URL for 480p quality (optional)
    quality_720p TEXT, -- URL for 720p quality (optional)
    quality_1080p TEXT, -- URL for 1080p quality (optional)
    views INTEGER NOT NULL DEFAULT 0,
    date_added TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ads_enabled BOOLEAN NOT NULL DEFAULT true
);

-- 4. Create quality_episodes table for episode-based series (NEW FEATURE)
CREATE TABLE quality_episodes (
    id BIGSERIAL PRIMARY KEY,
    series_name TEXT NOT NULL,
    short_id TEXT NOT NULL UNIQUE,
    start_from_episode INTEGER NOT NULL DEFAULT 1,
    episodes TEXT NOT NULL, -- JSON string containing episode data [{"episodeNumber": 1, "quality480p": "url", "quality720p": "url", "quality1080p": "url"}]
    views INTEGER NOT NULL DEFAULT 0,
    date_added TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ads_enabled BOOLEAN NOT NULL DEFAULT true
);

-- 5. Create quality_zips table for episode range downloads (NEW FEATURE)
CREATE TABLE quality_zips (
    id BIGSERIAL PRIMARY KEY,
    movie_name TEXT NOT NULL,
    short_id TEXT NOT NULL UNIQUE,
    from_episode INTEGER NOT NULL,
    to_episode INTEGER NOT NULL,
    quality_480p TEXT, -- URL for 480p quality (optional)
    quality_720p TEXT, -- URL for 720p quality (optional)
    quality_1080p TEXT, -- URL for 1080p quality (optional)
    views INTEGER NOT NULL DEFAULT 0,
    date_added TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ads_enabled BOOLEAN NOT NULL DEFAULT true
);

-- 6. Create api_tokens table for secure authentication
CREATE TABLE api_tokens (
    id BIGSERIAL PRIMARY KEY,
    token_name TEXT NOT NULL,
    token_value TEXT NOT NULL UNIQUE,
    token_type TEXT NOT NULL DEFAULT 'single', -- 'single', 'quality', 'episode', or 'zip'
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used TIMESTAMP WITH TIME ZONE
);

-- 7. Create admin_settings table for login credentials
CREATE TABLE admin_settings (
    id BIGSERIAL PRIMARY KEY,
    admin_id TEXT NOT NULL UNIQUE,
    admin_password TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- 8. Create telegram_admins table for minimal Telegram Admin info
CREATE TABLE telegram_admins (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    short_name TEXT NOT NULL
);

-- 8. Create ad_view_sessions table for IP-based timer skip system (5-minute skip)
CREATE TABLE ad_view_sessions (
    id BIGSERIAL PRIMARY KEY,
    ip_address TEXT NOT NULL,
    short_id TEXT NOT NULL,
    link_type TEXT NOT NULL DEFAULT 'single', -- 'single', 'quality', 'episode', or 'zip'
    viewed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (NOW() + INTERVAL '5 minutes')
);

-- 9. Create indexes for better performance (after all tables are created)
CREATE INDEX idx_movie_links_short_id ON movie_links(short_id);
CREATE INDEX idx_movie_links_date_added ON movie_links(date_added DESC);
CREATE INDEX idx_quality_movie_links_short_id ON quality_movie_links(short_id);
CREATE INDEX idx_quality_movie_links_date_added ON quality_movie_links(date_added DESC);
CREATE INDEX idx_quality_episodes_short_id ON quality_episodes(short_id);
CREATE INDEX idx_quality_episodes_date_added ON quality_episodes(date_added DESC);
CREATE INDEX idx_quality_zips_short_id ON quality_zips(short_id);
CREATE INDEX idx_quality_zips_date_added ON quality_zips(date_added DESC);
CREATE INDEX idx_api_tokens_token_value ON api_tokens(token_value);
CREATE INDEX idx_api_tokens_active ON api_tokens(is_active);
CREATE INDEX idx_ad_view_sessions_ip ON ad_view_sessions(ip_address);
CREATE INDEX idx_ad_view_sessions_expires ON ad_view_sessions(expires_at);
CREATE INDEX idx_ad_view_sessions_short_id ON ad_view_sessions(short_id);

-- Create unique constraint to prevent duplicate sessions for same IP and link
CREATE UNIQUE INDEX idx_ad_view_sessions_unique ON ad_view_sessions(ip_address, short_id, link_type);

-- 10. Insert default admin credentials
INSERT INTO admin_settings (admin_id, admin_password) 
VALUES ('sbiswas1844', 'save@184455') 
ON CONFLICT (admin_id) DO NOTHING;

-- 11. API tokens table is ready for manual creation through admin panel
-- No sample tokens inserted - create them through the admin interface

-- 12. Enable Row Level Security (RLS) - Optional but recommended
ALTER TABLE movie_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_movie_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_zips ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_view_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE telegram_admins ENABLE ROW LEVEL SECURITY;

-- 12. Create policies for public access to movie_links (for redirect functionality)
CREATE POLICY "Allow public read access to movie_links" ON movie_links
    FOR SELECT USING (true);

CREATE POLICY "Allow public update views on movie_links" ON movie_links
    FOR UPDATE USING (true);

CREATE POLICY "Allow public insert to movie_links" ON movie_links
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public delete from movie_links" ON movie_links
    FOR DELETE USING (true);

-- 13. Create policies for public access to quality_movie_links
CREATE POLICY "Allow public read access to quality_movie_links" ON quality_movie_links
    FOR SELECT USING (true);

CREATE POLICY "Allow public update views on quality_movie_links" ON quality_movie_links
    FOR UPDATE USING (true);

CREATE POLICY "Allow public insert to quality_movie_links" ON quality_movie_links
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public delete from quality_movie_links" ON quality_movie_links
    FOR DELETE USING (true);

-- 15. Create policies for public access to quality_episodes (NEW FEATURE)
CREATE POLICY "Allow public read access to quality_episodes" ON quality_episodes
    FOR SELECT USING (true);

CREATE POLICY "Allow public update views on quality_episodes" ON quality_episodes
    FOR UPDATE USING (true);

CREATE POLICY "Allow public insert to quality_episodes" ON quality_episodes
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public delete from quality_episodes" ON quality_episodes
    FOR DELETE USING (true);

-- 16. Create policies for public access to quality_zips (NEW FEATURE)
CREATE POLICY "Allow public read access to quality_zips" ON quality_zips
    FOR SELECT USING (true);

CREATE POLICY "Allow public update views on quality_zips" ON quality_zips
    FOR UPDATE USING (true);

CREATE POLICY "Allow public insert to quality_zips" ON quality_zips
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public delete from quality_zips" ON quality_zips
    FOR DELETE USING (true);

-- 17. Create policies for api_tokens (allow all operations for admin)
CREATE POLICY "Allow read access to api_tokens" ON api_tokens
    FOR SELECT USING (true);

CREATE POLICY "Allow insert access to api_tokens" ON api_tokens
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow update access to api_tokens" ON api_tokens
    FOR UPDATE USING (true);

CREATE POLICY "Allow delete access to api_tokens" ON api_tokens
    FOR DELETE USING (true);

-- 18. Create policies for admin_settings
CREATE POLICY "Allow read access to admin_settings" ON admin_settings
    FOR SELECT USING (true);

CREATE POLICY "Allow update access to admin_settings" ON admin_settings
    FOR UPDATE USING (true);

-- 19. Create policies for ad_view_sessions
CREATE POLICY "Allow all access to ad_view_sessions" ON ad_view_sessions
    FOR ALL USING (true);

-- 20. Create policies for telegram_admins
CREATE POLICY "Allow all access to telegram_admins" ON telegram_admins
    FOR ALL USING (true);

-- ===== End of Schema ===== 
-- All tables created with proper indexes and RLS policies
-- Remember to update your SUPABASE_SERVICE_ROLE_KEY in .env file

-- 18. Grant necessary permissions for public access
GRANT ALL ON movie_links TO anon;
GRANT ALL ON movie_links TO authenticated;
GRANT ALL ON quality_movie_links TO anon;
GRANT ALL ON quality_movie_links TO authenticated;
GRANT ALL ON quality_episodes TO anon;
GRANT ALL ON quality_episodes TO authenticated;
GRANT ALL ON quality_zips TO anon;
GRANT ALL ON quality_zips TO authenticated;
GRANT ALL ON api_tokens TO anon;
GRANT ALL ON api_tokens TO authenticated;
GRANT ALL ON admin_settings TO anon;
GRANT ALL ON admin_settings TO authenticated;
GRANT ALL ON ad_view_sessions TO anon;
GRANT ALL ON ad_view_sessions TO authenticated;
GRANT ALL ON telegram_admins TO anon;
GRANT ALL ON telegram_admins TO authenticated;
GRANT USAGE ON SEQUENCE movie_links_id_seq TO anon;
GRANT USAGE ON SEQUENCE movie_links_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE quality_movie_links_id_seq TO anon;
GRANT USAGE ON SEQUENCE quality_movie_links_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE quality_episodes_id_seq TO anon;
GRANT USAGE ON SEQUENCE quality_episodes_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE quality_zips_id_seq TO anon;
GRANT USAGE ON SEQUENCE quality_zips_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE api_tokens_id_seq TO anon;
GRANT USAGE ON SEQUENCE api_tokens_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE admin_settings_id_seq TO anon;
GRANT USAGE ON SEQUENCE admin_settings_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE ad_view_sessions_id_seq TO anon;
GRANT USAGE ON SEQUENCE ad_view_sessions_id_seq TO authenticated;
GRANT USAGE ON SEQUENCE telegram_admins_id_seq TO anon;
GRANT USAGE ON SEQUENCE telegram_admins_id_seq TO authenticated;

-- 19. Create a function to clean up expired ad view sessions
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS void 
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    DELETE FROM ad_view_sessions 
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 20. Optional: Create a function to automatically update views
CREATE OR REPLACE FUNCTION increment_movie_views(short_id_param TEXT)
RETURNS void 
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    UPDATE movie_links 
    SET views = views + 1 
    WHERE short_id = short_id_param;
END;
$$ LANGUAGE plpgsql;

-- 21. Optional: Create a function to generate random short IDs
CREATE OR REPLACE FUNCTION generate_short_id()
RETURNS TEXT 
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    RETURN encode(gen_random_bytes(3), 'hex');
END;
$$ LANGUAGE plpgsql;

-- 22. Grant execute permissions on functions
GRANT EXECUTE ON FUNCTION cleanup_expired_sessions() TO anon;
GRANT EXECUTE ON FUNCTION cleanup_expired_sessions() TO authenticated;
GRANT EXECUTE ON FUNCTION increment_movie_views(TEXT) TO anon;
GRANT EXECUTE ON FUNCTION increment_movie_views(TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION generate_short_id() TO anon;
GRANT EXECUTE ON FUNCTION generate_short_id() TO authenticated;

-- 23. Verify the tables were created successfully
SELECT 'All tables created successfully including quality_episodes for episode-based series' as status;

-- End of SQL Schema
