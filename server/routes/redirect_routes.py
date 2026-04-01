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
        target_link = ''
        link_label = 'Download'

        # 1. Check main short_id field
        rows = supabase.select('movies', '*', {'short_id': short_id})
        if rows:
            movie = rows[0]
            dtype = movie.get('download_type', 'single')
            if dtype == 'single':
                target_link = movie.get('original_link', '')
            elif dtype == 'quality':
                target_link = movie.get('quality_720p') or movie.get('quality_480p') or movie.get('quality_1080p', '')
            else:
                target_link = movie.get('original_link', '')

        # 2. If not found, search short_ids JSON across all movies
        if not movie:
            all_movies = supabase.select('movies', '*')
            for m in all_movies:
                sids_raw = m.get('short_ids', '{}')
                try:
                    sids = json_mod.loads(sids_raw) if isinstance(sids_raw, str) else (sids_raw or {})
                except:
                    sids = {}
                for key, sid in sids.items():
                    if sid == short_id:
                        movie = m
                        # Resolve the actual link based on key
                        if key == 'original':
                            target_link = m.get('original_link', '')
                            link_label = 'Download'
                        elif key in ('480p', 'zip_480p'):
                            target_link = m.get('quality_480p', '')
                            link_label = '480p Download'
                        elif key in ('720p', 'zip_720p'):
                            target_link = m.get('quality_720p', '')
                            link_label = '720p Download'
                        elif key in ('1080p', 'zip_1080p'):
                            target_link = m.get('quality_1080p', '')
                            link_label = '1080p Download'
                        elif key.startswith('e') and '_' in key:
                            # Episode link e.g. e1_480p
                            ep_num, quality = key.split('_', 1)
                            link_label = f'{ep_num.upper()} {quality} Download'
                            try:
                                eps = json_mod.loads(m.get('episodes', '[]')) if isinstance(m.get('episodes'), str) else (m.get('episodes') or [])
                                ep_n = int(ep_num[1:])
                                for ep in eps:
                                    if ep.get('episodeNumber') == ep_n:
                                        target_link = ep.get(f'quality{quality}') or ep.get(f'quality{quality.capitalize()}', '')
                                        break
                            except:
                                pass
                        break
                if movie:
                    break

        if not movie:
            return jsonify({"error": "Movie not found"}), 404

        # Increment views
        supabase.update('movies', {'views': (movie.get('views', 0) or 0) + 1}, {'id': movie['id']})

        return jsonify({
            'success': True,
            'title': movie.get('title'),
            'target_link': target_link,
            'link_label': link_label,
            'ads_enabled': movie.get('ads_enabled', True)
        })
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


