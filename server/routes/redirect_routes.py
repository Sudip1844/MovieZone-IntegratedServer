# IntegratedServer/server/routes/redirect_routes.py
# Redirect routes - /m/<shortId>, ad intermediate page
# Ported from Movieweb redirect logic

from flask import request, jsonify, redirect, render_template
from routes import redirect_bp
from database.supabase_client import supabase
from datetime import datetime, timedelta


def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


# AD SESSION TRACKING CANCELLED PER USER REQUEST
# User requested removing the 5 minute restriction on Ads.

# --- Redirect endpoints ---

@redirect_bp.route('/m/<short_id>')
def movie_redirect(short_id):
    """Redirect for backwards compatibility with Telegram bot links"""
    return redirect(f"/ad_page.html?v={short_id}")

@redirect_bp.route('/api/link-info/<short_id>')
def get_link_info(short_id):
    """Get link info for SPA ad_page"""
    try:
        import json as json_mod

        movie = None
        cols = 'id, title, ads_enabled, short_id, download_type, original_link, quality_480p, quality_720p, quality_1080p, episodes, views'

        rows = supabase.select('movies', cols, {'short_id': short_id})
        if rows:
            movie = rows[0]

        if not movie:
            return jsonify({'error': 'Link not found or expired'}), 404

        # Increment views
        supabase.update('movies', {'views': (movie.get('views', 0) or 0) + 1}, {'id': movie['id']})

        return jsonify(movie)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@redirect_bp.route('/api/get-download/<short_id>')
def get_download_link(short_id):
    """Get the actual download link after ad viewing"""
    try:
        rows = supabase.select('movies', '*', {'short_id': short_id})
        if not rows:
            return jsonify({'error': 'Not found'}), 404

        movie = rows[0]
        dtype = movie.get('download_type', 'single')
        quality = request.args.get('quality', '')

        if dtype == 'single':
            link = movie.get('original_link', '')
        elif dtype == 'quality':
            if quality == '480p':
                link = movie.get('quality_480p', '')
            elif quality == '720p':
                link = movie.get('quality_720p', '')
            elif quality == '1080p':
                link = movie.get('quality_1080p', '')
            else:
                link = movie.get('quality_720p') or movie.get('quality_480p') or movie.get('quality_1080p', '')
        else:
            link = movie.get('original_link', '')

        return jsonify({'link': link, 'title': movie.get('title', '')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


