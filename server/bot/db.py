# IntegratedServer/bot/database.py
# Supabase-backed database (replaces Tgbot's JSON file storage)
# Same function signatures as original so handlers work unchanged

import logging
import hashlib
import time
import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.supabase_client import supabase

logger = logging.getLogger(__name__)


def initialize_database():
    """Initialize database - just verify Supabase connection"""
    logger.info("Initializing Supabase database connection...")
    connected = supabase.test_connection()
    if connected:
        logger.info("[DB] Database initialized (Supabase)")
    else:
        logger.warning("[DB] Supabase connection test failed - some features may not work")


# --- User Management Functions ---

def user_exists(user_id: int) -> bool:
    """Check if a user exists in the database."""
    rows = supabase.select('users', '*', {'user_id': user_id})
    return len(rows) > 0


def add_user_if_not_exists(user_id: int, first_name: str, username: Optional[str] = None):
    """Add a user to the database if they don't exist."""
    if user_exists(user_id):
        return
    try:
        supabase.insert('users', {
            'user_id': user_id,
            'first_name': first_name,
            'username': username or '',
            'role': 'user'
        })
        logger.info(f"New user added: {user_id} ({first_name})")
    except Exception as e:
        logger.error(f"Error adding user {user_id}: {e}")


def get_user_role(user_id: int) -> str:
    """Get the role of a user (owner/admin/user)."""
    from bot.config import OWNER_ID
    if user_id == OWNER_ID:
        return 'owner'
    rows = supabase.select('users', 'role', {'user_id': user_id})
    if rows:
        return rows[0].get('role', 'user')
    return 'user'


# --- Admin Management Functions ---

def add_admin(admin_id: int, short_name: str, first_name: str, username: Optional[str] = None):
    """Add a new admin to the database."""
    # Update user role to admin
    try:
        existing = supabase.select('users', '*', {'user_id': admin_id})
        if existing:
            supabase.update('users', {'role': 'admin'}, {'user_id': admin_id})
        else:
            supabase.insert('users', {
                'user_id': admin_id,
                'first_name': first_name,
                'username': username or '',
                'role': 'admin'
            })
        logger.info(f"Admin added: {admin_id} ({short_name})")
        return True
    except Exception as e:
        logger.error(f"Error adding admin {admin_id}: {e}")
        return False


def get_admin_info(admin_id: int) -> Optional[Dict]:
    """Get admin information by user ID."""
    rows = supabase.select('users', '*', {'user_id': admin_id})
    if rows and rows[0].get('role') in ('admin', 'owner'):
        return rows[0]
    return None


def remove_admin(identifier: str) -> bool:
    """Remove an admin by user ID."""
    try:
        user_id = int(identifier)
        supabase.update('users', {'role': 'user'}, {'user_id': user_id})
        logger.info(f"Admin removed: {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error removing admin {identifier}: {e}")
        return False


def get_all_admins() -> List[Dict]:
    """Get all admins."""
    rows = supabase.select('users', '*', {'role': 'admin'})
    return rows


# --- Movie Management Functions ---

def add_movie(movie_data: Dict) -> Optional[int]:
    """Add a new movie to the database."""
    try:
        import secrets
        short_id = secrets.token_hex(3)  # 6-char hex

        insert_data = {
            'title': movie_data.get('title', 'Unknown'),
            'categories': movie_data.get('categories', []),
            'languages': movie_data.get('languages', []),
            'release_year': movie_data.get('release_year', 'N/A'),
            'runtime': movie_data.get('runtime', 'N/A'),
            'imdb_rating': movie_data.get('imdb_rating', 'N/A'),
            'thumbnail_file_id': movie_data.get('thumbnail_file_id', ''),
            'download_type': movie_data.get('download_type', 'single'),
            'original_link': movie_data.get('original_link', ''),
            'short_id': short_id,
            'status': movie_data.get('status', 'approved'),
            'ads_enabled': True,
            'added_by': str(movie_data.get('added_by', '')),
        }

        # Handle different download types
        files = movie_data.get('files', {})
        if files:
            # Store download links as quality fields or original_link
            qualities = [q for q in files.keys() if not q.startswith('E')]
            episodes = [q for q in files.keys() if q.startswith('E')]

            if episodes:
                insert_data['download_type'] = 'episode'
                eps_data = {}
                for ep_key in sorted(episodes):
                    eps_data[ep_key] = files[ep_key]
                insert_data['episodes'] = json.dumps(eps_data)
            elif len(qualities) > 1:
                insert_data['download_type'] = 'quality'
                for q in qualities:
                    if '480' in q:
                        insert_data['quality_480p'] = files[q]
                    elif '720' in q:
                        insert_data['quality_720p'] = files[q]
                    elif '1080' in q:
                        insert_data['quality_1080p'] = files[q]
                    else:
                        insert_data['original_link'] = files[q]
            elif qualities:
                insert_data['download_type'] = 'single'
                insert_data['original_link'] = files[qualities[0]]

        result = supabase.insert('movies', insert_data)
        if result:
            movie_id = result.get('id')
            logger.info(f"Movie added: {insert_data['title']} (ID: {movie_id})")
            return movie_id
        return None
    except Exception as e:
        logger.error(f"Error adding movie: {e}")
        return None


def get_movie_details(movie_id: int) -> Optional[Dict]:
    """Get movie details by ID."""
    rows = supabase.select('movies', '*', {'id': movie_id})
    if not rows:
        return None

    movie = rows[0]
    # Convert to format expected by handlers
    return _format_movie_for_bot(movie)


def _format_movie_for_bot(movie: Dict) -> Dict:
    """Convert Supabase movie row to bot-expected format"""
    files = {}
    dtype = movie.get('download_type', 'single')

    if dtype == 'single' and movie.get('original_link'):
        files['Download'] = movie['original_link']
    elif dtype == 'quality':
        if movie.get('quality_480p'):
            files['480p'] = movie['quality_480p']
        if movie.get('quality_720p'):
            files['720p'] = movie['quality_720p']
        if movie.get('quality_1080p'):
            files['1080p'] = movie['quality_1080p']
    elif dtype == 'episode' and movie.get('episodes'):
        eps = movie['episodes']
        if isinstance(eps, str):
            eps = json.loads(eps)
        files = eps

    categories = movie.get('categories', [])
    if isinstance(categories, str):
        try:
            categories = json.loads(categories)
        except:
            categories = [categories]

    languages = movie.get('languages', [])
    if isinstance(languages, str):
        try:
            languages = json.loads(languages)
        except:
            languages = [languages]

    return {
        'movie_id': movie['id'],
        'title': movie.get('title', 'Unknown'),
        'categories': categories,
        'languages': languages,
        'release_year': movie.get('release_year', 'N/A'),
        'runtime': movie.get('runtime', 'N/A'),
        'imdb_rating': movie.get('imdb_rating', 'N/A'),
        'thumbnail_file_id': movie.get('thumbnail_file_id', ''),
        'files': files,
        'downloads': movie.get('downloads', 0),
        'views': movie.get('views', 0),
        'short_id': movie.get('short_id', ''),
        'status': movie.get('status', 'approved'),
        'added_by': movie.get('added_by', ''),
        'created_at': movie.get('created_at', ''),
    }


def search_movies(query: str, limit: int = 10) -> List[Dict]:
    """Search movies by title."""
    rows = supabase.select(
        'movies', '*',
        {'title': f'ilike.%{query}%', 'status': 'approved'},
        order='created_at.desc',
        limit=limit
    )
    return [_format_movie_for_bot(m) for m in rows]


def get_movies_by_first_letter(letter: str, limit: int = 30) -> List[Dict]:
    """Get movies that start with a specific letter."""
    rows = supabase.select(
        'movies', '*',
        {'title': f'ilike.{letter}%', 'status': 'approved'},
        order='title.asc',
        limit=limit
    )
    return [_format_movie_for_bot(m) for m in rows]


def get_movies_by_category(category: str, limit: int = 10, offset: int = 0) -> List[Dict]:
    """Get movies by category."""
    # Supabase array contains: use cs operator
    clean_cat = category.split(' ')[0] if ' ' in category else category
    rows = supabase.select(
        'movies', '*',
        {'categories': f'cs.{{{clean_cat}}}', 'status': 'approved'},
        order='created_at.desc',
        limit=limit
    )
    return [_format_movie_for_bot(m) for m in rows]


def delete_movie(movie_id: int) -> bool:
    """Delete a movie from the database."""
    try:
        supabase.delete('movies', {'id': movie_id})
        logger.info(f"Movie deleted: {movie_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting movie {movie_id}: {e}")
        return False


def increment_download_count(movie_id: int):
    """Increment the download count for a movie."""
    try:
        rows = supabase.select('movies', 'downloads', {'id': movie_id})
        if rows:
            current = rows[0].get('downloads', 0)
            supabase.update('movies', {'downloads': current + 1}, {'id': movie_id})
    except Exception as e:
        logger.error(f"Error incrementing downloads for {movie_id}: {e}")


# --- Channel Management Functions ---

def add_channel(channel_id: str, channel_name: str, short_name: str) -> bool:
    """Add a new channel to the database."""
    try:
        supabase.insert('channels', {
            'channel_id': channel_id,
            'channel_name': channel_name,
            'short_name': short_name
        })
        logger.info(f"Channel added: {channel_name}")
        return True
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        return False


def remove_channel(identifier: str) -> bool:
    """Remove a channel by ID or short name."""
    try:
        # Try by channel_id first
        rows = supabase.select('channels', '*', {'channel_id': identifier})
        if not rows:
            rows = supabase.select('channels', '*', {'short_name': identifier})
        if rows:
            supabase.delete('channels', {'id': rows[0]['id']})
            logger.info(f"Channel removed: {identifier}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        return False


def get_channel_info(channel_id: str) -> Optional[Dict]:
    """Get channel information by channel ID."""
    rows = supabase.select('channels', '*', {'channel_id': channel_id})
    return rows[0] if rows else None


def get_all_channels() -> List[Dict]:
    """Get all channels."""
    return supabase.select('channels', '*')


# --- Request Management Functions ---

def add_movie_request(user_id: int, movie_name: str) -> bool:
    """Add a new movie request."""
    try:
        supabase.insert('movie_requests', {
            'user_id': user_id,
            'movie_name': movie_name,
            'status': 'pending'
        })
        logger.info(f"Movie request added by {user_id}: {movie_name}")
        return True
    except Exception as e:
        logger.error(f"Error adding request: {e}")
        return False


def get_pending_requests(limit: int = 10, offset: int = 0) -> List[Dict]:
    """Get pending movie requests."""
    rows = supabase.select(
        'movie_requests', '*',
        {'status': 'pending'},
        order='created_at.desc',
        limit=limit
    )
    # Format to match what handlers expect
    result = []
    for r in rows:
        result.append({
            'request_id': r['id'],
            'user_id': r['user_id'],
            'movie_name': r['movie_name'],
            'status': r['status'],
            'timestamp': r.get('created_at', '')
        })
    return result


def get_total_pending_requests_count() -> int:
    """Get total count of pending movie requests."""
    rows = supabase.select('movie_requests', 'id', {'status': 'pending'})
    return len(rows)


def update_request_status(request_id: int, status: str):
    """Update the status of a movie request. Returns the request info dict or None on failure."""
    try:
        # First get the request details before updating
        rows = supabase.select('movie_requests', '*', {'id': request_id})
        if not rows:
            return None
        request_data = rows[0]
        
        # Update the status
        supabase.update('movie_requests', {'status': status}, {'id': request_id})
        
        # Return request info for notification
        return {
            'request_id': request_data['id'],
            'user_id': request_data['user_id'],
            'movie_name': request_data['movie_name'],
            'status': status
        }
    except Exception as e:
        logger.error(f"Error updating request {request_id}: {e}")
        return None


# --- Stats Functions ---

def get_movies_by_uploader(admin_id: int, limit: int = 30) -> List[Dict]:
    """Get movies uploaded by specific admin/owner."""
    rows = supabase.select(
        'movies', '*',
        {'added_by': str(admin_id)},
        order='created_at.desc',
        limit=limit
    )
    return [_format_movie_for_bot(m) for m in rows]


# --- Monthly Statistics Functions ---

def track_movie_addition(movie_id: int, movie_data: Dict):
    """Track movie addition for monthly statistics."""
    month_year = datetime.now().strftime('%Y-%m')
    try:
        rows = supabase.select('monthly_stats', '*', {'month_year': month_year})
        if rows:
            current = rows[0]
            supabase.update('monthly_stats', {
                'movies_added': current.get('movies_added', 0) + 1,
                'updated_at': datetime.now().isoformat()
            }, {'month_year': month_year})
        else:
            supabase.insert('monthly_stats', {
                'month_year': month_year,
                'movies_added': 1,
                'total_downloads': 0,
                'total_views': 0,
            })
    except Exception as e:
        logger.error(f"Error tracking movie addition: {e}")


def track_movie_addition_for_date(movie_id: int, movie_data: dict, date_obj):
    """Track movie addition for a specific date."""
    month_year = date_obj.strftime('%Y-%m')
    try:
        rows = supabase.select('monthly_stats', '*', {'month_year': month_year})
        if rows:
            current = rows[0]
            supabase.update('monthly_stats', {
                'movies_added': current.get('movies_added', 0) + 1,
            }, {'month_year': month_year})
        else:
            supabase.insert('monthly_stats', {
                'month_year': month_year,
                'movies_added': 1,
            })
    except Exception as e:
        logger.error(f"Error tracking movie addition for date: {e}")


def track_movie_download(movie_id: int):
    """Track movie download for monthly statistics."""
    month_year = datetime.now().strftime('%Y-%m')
    try:
        rows = supabase.select('monthly_stats', '*', {'month_year': month_year})
        if rows:
            current = rows[0]
            supabase.update('monthly_stats', {
                'total_downloads': current.get('total_downloads', 0) + 1,
            }, {'month_year': month_year})
        else:
            supabase.insert('monthly_stats', {
                'month_year': month_year,
                'total_downloads': 1,
            })
    except Exception as e:
        logger.error(f"Error tracking download: {e}")


def get_monthly_stats(month_year: str = None) -> Optional[Dict]:
    """Get monthly stats."""
    if not month_year:
        month_year = datetime.now().strftime('%Y-%m')
    rows = supabase.select('monthly_stats', '*', {'month_year': month_year})
    return rows[0] if rows else None


def get_all_monthly_stats() -> List[Dict]:
    """Get all monthly stats."""
    return supabase.select('monthly_stats', '*', order='month_year.desc')


# --- Review Functions (NEW for IntegratedServer) ---

def get_pending_movies() -> List[Dict]:
    """Get movies pending review."""
    rows = supabase.select(
        'movies', '*',
        {'status': 'pending'},
        order='created_at.desc'
    )
    return [_format_movie_for_bot(m) for m in rows]


def approve_movie(movie_id: int) -> bool:
    """Approve a movie for posting."""
    try:
        supabase.update('movies', {'status': 'approved'}, {'id': movie_id})
        return True
    except:
        return False


def reject_movie(movie_id: int) -> bool:
    """Reject a movie."""
    try:
        supabase.update('movies', {'status': 'rejected'}, {'id': movie_id})
        return True
    except:
        return False


def get_previous_month_date():
    """Get year and month for previous month."""
    current_date = datetime.now()
    if current_date.month == 1:
        return current_date.year - 1, 12
    else:
        return current_date.year, current_date.month - 1


def generate_monthly_report(year: int, month: int) -> str:
    """Generate monthly report for owner (Supabase-backed version)."""
    try:
        from bot.config import OWNER_ID
        month_key = f"{year}-{month:02d}"

        report = f"Monthly Report - {month:02d}/{year}\n\n"

        # Get monthly stats
        stats_row = get_monthly_stats(month_key)

        # Get all movies added this month
        # Use date range filtering
        month_start = f"{year}-{month:02d}-01"
        if month == 12:
            month_end = f"{year + 1}-01-01"
        else:
            month_end = f"{year}-{month + 1:02d}-01"

        all_movies = supabase.select(
            'movies', '*',
            {'created_at': f'gte.{month_start}T00:00:00'},
            order='created_at.desc'
        )
        # Filter to this month only
        month_movies = [m for m in all_movies if m.get('created_at', '') < month_end + 'T00:00:00']

        if not month_movies and not stats_row:
            return f"Monthly Report - {month:02d}/{year}\n\nNo activity recorded for this month."

        # Group by uploader
        uploaders = {}
        for movie in month_movies:
            uploader_id = movie.get('added_by', 'unknown')
            if uploader_id not in uploaders:
                uploaders[uploader_id] = []
            uploaders[uploader_id].append(movie)

        for uploader_id, movies in uploaders.items():
            try:
                uid = int(uploader_id)
            except (ValueError, TypeError):
                uid = 0

            if uid == OWNER_ID:
                name = "Owner"
                role = "Owner"
            else:
                admin_info = get_admin_info(uid)
                name = admin_info.get('first_name', f'Admin-{uploader_id}') if admin_info else f'User-{uploader_id}'
                role = "Admin"

            report += f">> {name} ({role})\n"
            report += f"  Movies Uploaded This Month: {len(movies)}\n"

            movie_titles = [m.get('title', 'Unknown') for m in movies]
            report += f"  Uploaded Movies: {', '.join(movie_titles)}\n"

            # Total downloads for these movies
            total_downloads = sum(m.get('downloads', 0) for m in movies)
            report += f"  Total Downloads This Month: {total_downloads}\n"

            # Total movies ever by this uploader
            all_by_user = get_movies_by_uploader(uid, limit=1000)
            report += f"  Total Movies Ever Uploaded: {len(all_by_user)}\n"
            report += "\n" + "-" * 40 + "\n\n"

        # Summary stats
        if stats_row:
            report += f"Summary:\n"
            report += f"  Total Movies Added: {stats_row.get('movies_added', 0)}\n"
            report += f"  Total Downloads: {stats_row.get('total_downloads', 0)}\n"
            report += f"  Total Views: {stats_row.get('total_views', 0)}\n"

        return report

    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        return f"Error generating monthly report: {str(e)}"
