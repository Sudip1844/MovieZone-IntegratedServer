# MovieZoneBot/utils.py

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update
)
from bot.config import CATEGORIES, BOT_USERNAME, SINGLE_MOVIE_POST_TEMPLATE, SERIES_POST_TEMPLATE
import bot.db as db
import logging
from typing import List

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# --- Role Verification Decorator ---
def restricted(allowed_roles: List[str]):
    """
    একটি ডেকোরেটর যা একটি কমান্ডকে নির্দিষ্ট ভূমিকার (role) ব্যবহারকারীদের জন্য সীমাবদ্ধ করে।
    উদাহরণ: @restricted(allowed_roles=['owner', 'admin'])
    """
    def decorator(func):
        async def wrapped(update: Update, context, *args, **kwargs):
            # Handle both regular messages and callback queries
            if hasattr(update, 'callback_query') and update.callback_query:
                user_id = update.callback_query.from_user.id
                message = update.callback_query.message
            else:
                user_id = update.effective_user.id
                message = update.message
                
            user_role = db.get_user_role(user_id)
            
            if user_role not in allowed_roles:
                await message.reply_text("❌ দুঃখিত, এই কমান্ডটি ব্যবহার করার অনুমতি আপনার নেই।")
                logger.warning(f"Unauthorized access attempt by user {user_id} ({user_role}) for a '{', '.join(allowed_roles)}' command.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapped
    return decorator

# --- Keyboard and Button Generation ---

def get_main_keyboard(user_role: str) -> ReplyKeyboardMarkup:
    """Create role-based main menu keyboard for users with cancel button always available."""
    
    if user_role == 'owner':
        # Owner: Review movies, manage channels, stats (6 buttons -> 2 per row)
        keyboard = [
            [KeyboardButton("📋 Review Movies"), KeyboardButton("📊 Show Requests")],
            [KeyboardButton("👥 Manage Admins"), KeyboardButton("📢 Manage Channels")],
            [KeyboardButton("❓ Help"), KeyboardButton("❌ Cancel")]
        ]
    elif user_role == 'admin':
        # Admin: stats, requests (3 buttons -> 2 in first row, 1 in second)
        keyboard = [
            [KeyboardButton("📊 Show Requests"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    else:
        # Regular users get basic commands plus cancel (5 buttons -> 2 per row)
        keyboard = [
            [KeyboardButton("🔍 Search Movies"), KeyboardButton("📂 Browse Categories")],
            [KeyboardButton("🙏 Request Movie"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_conversation_keyboard(user_role: str) -> ReplyKeyboardMarkup:
    """Create keyboard with cancel button during conversations, alongside main buttons."""
    
    if user_role == 'owner':
        # Owner: Review movies, manage channels, stats (6 buttons -> 2 per row)
        keyboard = [
            [KeyboardButton("📋 Review Movies"), KeyboardButton("📊 Show Requests")],
            [KeyboardButton("👥 Manage Admins"), KeyboardButton("📢 Manage Channels")],
            [KeyboardButton("❓ Help"), KeyboardButton("❌ Cancel")]
        ]
    elif user_role == 'admin':
        # Admin: stats, requests (3 buttons -> 2 in first row, 1 in second)
        keyboard = [
            [KeyboardButton("📊 Show Requests"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    else:
        # Regular users get basic commands plus cancel (5 buttons -> 2 per row)
        keyboard = [
            [KeyboardButton("🔍 Search Movies"), KeyboardButton("📂 Browse Categories")],
            [KeyboardButton("🙏 Request Movie"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_category_keyboard() -> InlineKeyboardMarkup:
    """Creates an inline keyboard for browsing movie categories."""
    from bot.config import BROWSE_CATEGORIES
    buttons = []
    row = []
    for category in BROWSE_CATEGORIES:
        # Create button for each category
        # callback_data uses 'cat_' prefix to distinguish from other buttons
        clean_category = category.replace("✅ ", "").replace(" ", "_")
        row.append(InlineKeyboardButton(category, callback_data=f"cat_{clean_category}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
        
    return InlineKeyboardMarkup(buttons)

def get_quality_buttons(movie_id: int, files: dict) -> InlineKeyboardMarkup:
    """একটি মুভির জন্য উপলব্ধ কোয়ালিটির বাটন তৈরি করে।"""
    buttons = []
    for quality in files.keys():
        # বাটনগুলো 'quality' প্রিফিক্স দিয়ে শুরু হবে
        callback_data = f"quality_{movie_id}_{quality}"
        buttons.append([InlineKeyboardButton(f"🎬 {quality}", callback_data=callback_data)])
    
    return InlineKeyboardMarkup(buttons)

def generate_direct_download_button(movie_id: int, quality: str) -> InlineKeyboardMarkup:
    """একটি 'Direct Download' বাটন তৈরি করে।"""
    # Create direct download callback
    callback_data = f"download_{movie_id}_{quality}"
    button = [[InlineKeyboardButton("📥 Download Now", callback_data=callback_data)]]
    return InlineKeyboardMarkup(button)

def generate_download_buttons(movie_id: int, files: dict) -> InlineKeyboardMarkup:
    """Generate download buttons for all available qualities to avoid external link popup."""
    buttons = []
    
    # Check if it's a series (has episode files)
    is_series = any('E' in quality for quality in files.keys())
    
    if is_series:
        # For series, show first episode download button
        episode_files = [quality for quality in files.keys() if quality.startswith('E')]
        if episode_files:
            first_episode = sorted(episode_files)[0]  # Get first episode
            buttons.append([InlineKeyboardButton(f"📥 Download {first_episode}", callback_data=f"download_{movie_id}_{first_episode}")])
    else:
        # For movies, show quality buttons in 2 columns
        qualities = sorted([quality for quality in files.keys() if not quality.startswith('E')])
        for i in range(0, len(qualities), 2):
            row = []
            for j in range(2):
                if i + j < len(qualities):
                    quality = qualities[i + j]
                    row.append(InlineKeyboardButton(f"📥 {quality}", callback_data=f"download_{movie_id}_{quality}"))
            buttons.append(row)
    
    return InlineKeyboardMarkup(buttons)

def format_movie_post(movie_details: dict, channel_username: str, base_url: str = None) -> str:
    """
    ডেটাবেস থেকে প্রাপ্ত মুভির তথ্য দিয়ে একটি সুন্দর পোস্ট ফরম্যাট করে।
    Download link goes through /m/<short_id> for ad page, not direct URL.

    Supported download_type:
      - single  : একটা ডাউনলোড লিংক
      - quality : 480p / 720p / 1080p আলাদা আলাদা লিংক
      - zip     : episode range (E1-E6) + quality links
      - episode : প্রতিটা episode × প্রতিটা quality আলাদা লিংক
    """
    from bot.config import WEBSITE_BASE_URL
    if not base_url:
        base_url = WEBSITE_BASE_URL

    dtype        = movie_details.get('download_type', 'single')
    files        = movie_details.get('files', {})
    short_id     = movie_details.get('short_id', '')
    from_ep      = movie_details.get('from_episode')
    to_ep        = movie_details.get('to_episode')

    download_links = ""
    episode_info   = ""
    dl_header      = "🔗 Download Link Below"

    # ── SINGLE ────────────────────────────────────────────────────────────
    if dtype == 'single':
        redirect_url = f"{base_url}/m/{short_id}" if short_id else files.get('Download', '#')
        download_links = f'Download || 👉 <a href="{redirect_url}">Click To Download</a> 📥\n'

    # ── QUALITY ───────────────────────────────────────────────────────────
    elif dtype == 'quality':
        qualities = sorted([q for q in files if q not in ('__episodes__',)])
        for q in qualities:
            redirect_url = f"{base_url}/m/{short_id}?q={q}" if short_id else files.get(q, '#')
            redirect_url = redirect_url.replace('&', '&amp;')
            download_links += f'{q} || 👉 <a href="{redirect_url}">Click To Download</a> 📥\n'

    # ── ZIP ───────────────────────────────────────────────────────────────
    elif dtype == 'zip':
        dl_header = "🔗 ZIP Download Link Below"
        # Episode range label  (e.g.  E1-E6)
        if from_ep and to_ep:
            ep_range = f"E{from_ep}-E{to_ep}"
        elif from_ep:
            ep_range = f"E{from_ep}"
        else:
            ep_range = "All Episodes"

        qualities = sorted([q for q in files if q not in ('__episodes__',)])
        for q in qualities:
            redirect_url = f"{base_url}/m/{short_id}?q={q}" if short_id else files.get(q, '#')
            redirect_url = redirect_url.replace('&', '&amp;')
            download_links += f'{ep_range} || {q} || 👉 <a href="{redirect_url}">Click To Download</a> 📥\n'

    # ── EPISODE ───────────────────────────────────────────────────────────
    elif dtype == 'episode':
        episodes = files.get('__episodes__', [])
        if isinstance(episodes, list) and episodes:
            # Sort episodes by episode number
            def ep_sort_key(ep):
                try:
                    return int(ep.get('episodeNumber', 0))
                except:
                    return 0
            episodes = sorted(episodes, key=ep_sort_key)

            ep_nums = [ep.get('episodeNumber') for ep in episodes if ep.get('episodeNumber')]
            if ep_nums:
                if len(ep_nums) == 1:
                    episode_info = f"Available Episodes: Ep{ep_nums[0]}"
                else:
                    episode_info = f"Available Episodes: Ep{ep_nums[0]} to Ep{ep_nums[-1]}"

            quality_order = ['480p', '720p', '1080p']
            for ep in episodes:
                ep_num = ep.get('episodeNumber', '?')
                ep_label = f"E{ep_num}"
                ep_links = ""

                for q in quality_order:
                    # DB keys can be quality480p or quality_480p
                    raw_url = (ep.get(f'quality{q}') or
                               ep.get(f'quality_{q}') or
                               ep.get(q, ''))
                    if raw_url:
                        # Each episode+quality gets its own redirect
                        if short_id:
                            redirect_url = f"{base_url}/m/{short_id}?ep={ep_num}&amp;q={q}"
                        else:
                            redirect_url = raw_url
                        
                        redirect_url = redirect_url.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
                        ep_links += f'{ep_label} || {q} || 👉 <a href="{redirect_url}">Click To Download</a> 📥\n'

                if ep_links:
                    download_links += ep_links + "\n"

    # ── BUILD POST ────────────────────────────────────────────────────────
    title      = movie_details.get('title', 'Unknown')
    languages  = " | ".join(movie_details.get('languages', []))

    categories_raw   = movie_details.get('categories', [])
    categories_clean = []
    for cat in categories_raw:
        clean = cat.split(' ')[0] if ' ' in cat else cat
        categories_clean.append(clean)
    categories = " | ".join(categories_clean)

    post_text = f"🍿 Title: {title}\n\n"

    if languages:
        post_text += f"📌 Language: {languages}\n"
    if categories:
        post_text += f"☘️ Genre: {categories}\n"

    release_year = movie_details.get('release_year', 'N/A')
    if release_year != 'N/A':
        post_text += f"🗓️ Release Year: {release_year}\n"

    runtime = movie_details.get('runtime', 'N/A')
    if runtime != 'N/A':
        post_text += f"⏰ Runtime: {runtime}\n"

    imdb_rating = movie_details.get('imdb_rating', 'N/A')
    if imdb_rating != 'N/A':
        post_text += f"⭐️ IMDb Rating: {imdb_rating}/10\n"

    if episode_info:
        post_text += f"\n{episode_info}\n"

    post_text += f"\n{dl_header}\n{download_links.strip()}\n\n"
    post_text += "🔥 Ultra Fast • Direct Access\n"
    post_text += f"🛰️ Join Now: @{channel_username}\n"
    post_text += "🔔 New Movies Uploaded Daily!"

    return post_text


def get_movie_search_results_markup(movies: List[dict]) -> InlineKeyboardMarkup:
    """Create inline keyboard for movie search results."""
    buttons = []
    for movie in movies:
        button_text = f"🎬 {movie.get('title', 'Unknown')}"
        callback_data = f"view_{movie['movie_id']}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    return InlineKeyboardMarkup(buttons)

def create_movie_grid_markup(movies: List[dict], prefix: str = "view") -> InlineKeyboardMarkup:
    """Create a 3-column grid layout for movies like in category browsing."""
    buttons = []
    
    # Group movies into rows of 3
    for i in range(0, len(movies), 3):
        row = []
        for j in range(3):
            if i + j < len(movies):
                movie = movies[i + j]
                title = movie.get('title', 'Unknown')
                # Truncate long titles for button display
                if len(title) > 15:
                    title = title[:12] + "..."
                row.append(InlineKeyboardButton(f"🎬 {title}", callback_data=f"{prefix}_{movie['movie_id']}"))
        if row:
            buttons.append(row)
    
    return InlineKeyboardMarkup(buttons)

def create_category_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Create inline keyboard for category selection."""
    buttons = []
    
    # Group categories into rows of 2
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                # Remove emoji for callback data, keep for display
                callback_category = category.split(' ')[0] if ' ' in category else category
                row.append(InlineKeyboardButton(category, callback_data=f"cat_{callback_category}"))
        if row:
            buttons.append(row)
    
    return InlineKeyboardMarkup(buttons)

# --- Dynamic Bot Commands Management ---
async def set_conversation_commands(update: Update, context):
    """No-op: hamburger menu is disabled globally at startup, not per-message."""
    pass  # Removed per-message API call — was causing spam & unnecessary load

async def restore_default_commands(context, chat_id):
    """No-op: hamburger menu stays disabled globally."""
    pass  # Removed per-message API call — was causing spam & unnecessary load

async def set_conversation_keyboard(update: Update, context, user_role: str):
    """Use main keyboard during conversations since cancel is already included."""
    keyboard = get_main_keyboard(user_role)
    # Store the original keyboard to restore later
    context.user_data['original_keyboard'] = get_main_keyboard(user_role)
    
    # Hamburger menu is handled globally at startup — no per-message call needed
    
    return keyboard

async def restore_main_keyboard(update: Update, context, user_role: str):
    """Restore main keyboard and commands when conversation ends."""
    keyboard = context.user_data.get('original_keyboard', get_main_keyboard(user_role))
    
    # Get chat_id from either update.effective_chat or callback query
    if hasattr(update, 'callback_query') and update.callback_query:
        chat_id = update.callback_query.message.chat_id
    elif hasattr(update, 'effective_chat') and update.effective_chat:
        chat_id = update.effective_chat.id
    else:
        chat_id = update.message.chat_id if update.message else None
    
    # Restore default commands if we have a valid chat_id
    if chat_id:
        await restore_default_commands(context, chat_id)
    
    return keyboard
