# IntegratedServer/server/routes/movie_routes.py
# Movie CRUD routes - ported from Movieweb/server/routes.ts
# NO API token system - direct access since same server

import secrets
from flask import request, jsonify
from routes import movie_bp
from database.supabase_client import supabase


def generate_short_id():
    return secrets.token_hex(3)  # 6-char hex


# --- Movie Links (single) ---

@movie_bp.route('/api/movie-links', methods=['GET'])
def get_movie_links():
    """Get all movies (approved only by default, ?all=true for everything)"""
    try:
        show_all = request.args.get('all', 'false').lower() == 'true'
        if show_all:
            movies = supabase.select('movies', '*', order='created_at.desc')
        else:
            movies = supabase.select('movies', '*', {'status': 'approved'}, order='created_at.desc')
        return jsonify(movies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movie-links', methods=['POST'])
def create_movie_link():
    """Create a new movie (from website admin panel) - generates per-link short URLs"""
    try:
        import json as json_mod
        
        # Handle form data (multipart)
        if 'data' in request.form:
            data = json_mod.loads(request.form.get('data'))
        else:
            data = request.get_json()

        if not data or not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400

        # Upload thumbnail to Telegram
        thumbnail_file_id = None
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file and file.filename != '':
                from bot.config import BOT_TOKEN, DUMP_CHAT_ID
                import requests
                
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                payload = {'chat_id': DUMP_CHAT_ID, 'disable_notification': True}
                files = {'photo': (file.filename, file.read(), file.content_type)}
                
                try:
                    resp = requests.post(url, data=payload, files=files, timeout=15)
                    resp_data = resp.json()
                    if resp_data.get('ok'):
                        photos = resp_data['result'].get('photo', [])
                        if photos:
                            thumbnail_file_id = photos[-1]['file_id']
                except Exception as e:
                    print(f"Failed to upload photo to Telegram: {e}")

        dtype = data.get('downloadType', data.get('download_type', 'single'))
        short_id = generate_short_id()  # main short_id for backwards compat

        # Generate per-link short IDs
        short_ids = {}
        short_urls = {}
        host = request.host_url.rstrip('/')

        if dtype == 'single':
            sid = generate_short_id()
            short_ids['original'] = sid
            short_urls['original'] = f"{host}/m/{sid}"
        # Removed multiple short_ids generation for quality/zip/episode.
        # We now only use the master short_id for the whole movie.

        insert_data = {
            'title': data.get('title', data.get('movieName', data.get('movie_name', ''))),
            'original_link': data.get('originalLink', data.get('original_link', '')),
            'thumbnail_file_id': thumbnail_file_id,
            'short_id': short_id,
            'short_ids': short_ids,
            'download_type': dtype,
            'quality_480p': data.get('quality480p', data.get('quality_480p')),
            'quality_720p': data.get('quality720p', data.get('quality_720p')),
            'quality_1080p': data.get('quality1080p', data.get('quality_1080p')),
            'categories': data.get('categories', []),
            'languages': data.get('languages', []),
            'release_year': data.get('releaseYear', data.get('release_year', 'N/A')),
            'runtime': data.get('runtime', 'N/A'),
            'imdb_rating': data.get('imdbRating', data.get('imdb_rating', 'N/A')),
            'ads_enabled': data.get('adsEnabled', data.get('ads_enabled', True)),
            'status': data.get('status', 'pending'),
            'added_by': data.get('addedBy', data.get('added_by', 'owner')),
        }

        # Handle episodes
        if data.get('episodes'):
            insert_data['episodes'] = data['episodes']
            insert_data['download_type'] = 'episode'
            insert_data['start_from_episode'] = data.get('startFromEpisode', 1)

        # Handle zip
        if data.get('fromEpisode') is not None:
            insert_data['from_episode'] = data['fromEpisode']
            insert_data['to_episode'] = data.get('toEpisode')
            insert_data['download_type'] = 'zip'

        result = None
        try:
            result = supabase.insert('movies', insert_data)
        except Exception as e:
            # If it fails, log the error and try without short_ids for backward compatibility
            print(f"Insert failed with short_ids: {e}. Trying without...")
            insert_data.pop('short_ids', None)
            result = supabase.insert('movies', insert_data)

        if result:
            return jsonify({
                'success': True,
                'shortId': short_id,
                'shortUrl': f"{host}/m/{short_id}",
                'id': result.get('id'),
                'movie': result
            }), 201

        return jsonify({'error': 'Failed to create'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movie-links/<short_id>', methods=['GET'])
def get_movie_link(short_id):
    """Get movie by short ID"""
    try:
        rows = supabase.select('movies', '*', {'short_id': short_id})
        if not rows:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(rows[0])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movie-links/<int:movie_id>', methods=['PATCH'])
def update_movie_link(movie_id):
    """Update a movie"""
    try:
        data = request.get_json()
        update_data = {}
        field_map = {
            'originalLink': 'original_link',
            'adsEnabled': 'ads_enabled',
            'title': 'title',
            'original_link': 'original_link',
            'ads_enabled': 'ads_enabled',
            'quality_480p': 'quality_480p',
            'quality_720p': 'quality_720p',
            'quality_1080p': 'quality_1080p',
            'categories': 'categories',
            'languages': 'languages',
            'status': 'status',
            'release_year': 'release_year',
            'runtime': 'runtime',
            'imdb_rating': 'imdb_rating',
            'is_active': 'is_active'
        }
        for key, db_key in field_map.items():
            if key in data:
                update_data[db_key] = data[key]

        if not update_data:
            return jsonify({'error': 'No update data'}), 400

        result = supabase.update('movies', update_data, {'id': movie_id})
        return jsonify(result or {'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movie-links/<short_id>/views', methods=['PATCH'])
def update_views(short_id):
    """Increment views"""
    try:
        rows = supabase.select('movies', 'id,views', {'short_id': short_id})
        if rows:
            supabase.update('movies', {'views': (rows[0].get('views', 0) or 0) + 1}, {'id': rows[0]['id']})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movie-links/<int:movie_id>', methods=['DELETE'])
def delete_movie_link(movie_id):
    """Delete a movie"""
    try:
        supabase.delete('movies', {'id': movie_id})
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- Review Queue ---

@movie_bp.route('/api/pending-movies', methods=['GET'])
def get_pending_movies():
    """Get movies pending review"""
    try:
        movies = supabase.select('movies', '*', {'status': 'pending'}, order='created_at.desc')
        return jsonify(movies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movies/<int:movie_id>/approve', methods=['POST'])
def approve_movie(movie_id):
    """Approve a movie from Owner Panel - does NOT auto-post to channels.
    Channel posting happens only via TG bot review (📋 Review Movies command).
    Flow: Website approve → status:approved → Bot review → Bot approve → posts to channels
    """
    try:
        supabase.update('movies', {'status': 'approved'}, {'id': movie_id})
        return jsonify({'success': True, 'message': 'Movie approved! Use bot Review Movies to post to channels.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movies/<int:movie_id>/reject', methods=['POST'])
def reject_movie(movie_id):
    """Reject a movie"""
    try:
        supabase.update('movies', {'status': 'rejected'}, {'id': movie_id})
        return jsonify({'success': True, 'message': 'Movie rejected'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@movie_bp.route('/api/movies/<int:movie_id>/repost', methods=['POST'])
def repost_movie(movie_id):
    """Manually repost a movie to all currently linked channels.
    
    Uses the saved telegram_message_id (master post in DUMP_CHAT) to 
    copy_message to all channels — fast, no re-upload needed.
    Falls back to rebuilding and sending the post if no master ID exists.
    """
    try:
        from bot.config import BOT_TOKEN, CHANNEL_USERNAME, DUMP_CHAT_ID
        import requests as http_requests

        # Get movie details
        rows = supabase.select('movies', '*', {'id': movie_id})
        if not rows:
            return jsonify({'error': 'Movie not found'}), 404
        movie = rows[0]

        # Get all channels
        channels = supabase.select('channels', '*')
        if not channels:
            return jsonify({'error': 'No channels configured'}), 400

        master_message_id = movie.get('telegram_message_id')
        dump_chat = str(DUMP_CHAT_ID)
        posted_count = 0
        failed = []

        for channel in channels:
            channel_id = str(channel.get('channel_id', '')).strip()
            # Auto-fix IDs missing the negative sign (channels start with -100)
            if channel_id.startswith('100') and len(channel_id) >= 13:
                channel_id = f"-{channel_id}"
                
            if not channel_id or channel_id == dump_chat:
                continue
            # Skip invite links
            if '+' in channel_id and not channel_id.lstrip('-').isdigit():
                failed.append(f"{channel_id} (invite link)")
                continue

            try:
                success = False
                error_desc = "unknown"
                if master_message_id:
                    # Use copyMessage API — instant, no re-upload
                    resp = http_requests.post(
                        f"https://api.telegram.org/bot{BOT_TOKEN}/copyMessage",
                        json={
                            'chat_id': channel_id,
                            'from_chat_id': dump_chat,
                            'message_id': int(master_message_id)
                        },
                        timeout=15
                    )
                    if resp.json().get('ok'):
                        posted_count += 1
                        success = True
                    else:
                        error_desc = resp.json().get('description', 'copyMessage failed')

                if not success:
                    # Fallback: rebuild post text and send
                    title = movie.get('title', 'Unknown')
                    thumbnail = movie.get('thumbnail_file_id', '')
                    # Simple fallback post
                    from bot.utils import format_movie_post
                    from bot.db import _format_movie_for_bot
                    fmt_movie = _format_movie_for_bot(movie)
                    post_text = format_movie_post(fmt_movie, CHANNEL_USERNAME or 'yourchannel')

                    if thumbnail:
                        resp = http_requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                            json={'chat_id': channel_id, 'photo': thumbnail, 'caption': post_text, 'parse_mode': 'HTML'},
                            timeout=15
                        )
                    else:
                        resp = http_requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            json={'chat_id': channel_id, 'text': post_text, 'parse_mode': 'HTML'},
                            timeout=15
                        )
                    if resp.json().get('ok'):
                        posted_count += 1
                        success = True
                    else:
                        error_desc = resp.json().get('description', error_desc)
                
                if not success:
                    failed.append(f"{channel_id} ({error_desc})")
                    
            except Exception as e:
                failed.append(f"{channel_id} ({str(e)[:60]})")

        return jsonify({
            'success': True,
            'posted_to': posted_count,
            'failed': failed,
            'used_master_id': bool(master_message_id),
            'message': f"Reposted to {posted_count} channel(s)!" + (f" Failed: {len(failed)}" if failed else "")
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
