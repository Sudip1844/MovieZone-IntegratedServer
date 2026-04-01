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
        # Owner: Review movies (added via website), manage channels, stats
        keyboard = [
            [KeyboardButton("📋 Review Movies"), KeyboardButton("🗑️ Remove Movie")],
            [KeyboardButton("📊 Show Requests"), KeyboardButton("📊 Show Stats")],
            [KeyboardButton("📊 Monthly Report"), KeyboardButton("📢 Manage Channels")],
            [KeyboardButton("❓ Help"), KeyboardButton("❌ Cancel")]
        ]
    elif user_role == 'admin':
        # Admin: Review movies, stats (movies added via website, admins managed via website)
        keyboard = [
            [KeyboardButton("📋 Review Movies"), KeyboardButton("📊 Show Requests")],
            [KeyboardButton("📊 Show Stats"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    else:
        # Regular users get basic commands plus cancel
        keyboard = [
            [KeyboardButton("🔍 Search Movies"), KeyboardButton("📂 Browse Categories")],
            [KeyboardButton("🙏 Request Movie"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_conversation_keyboard(user_role: str) -> ReplyKeyboardMarkup:
    """Create keyboard with cancel button during conversations, alongside main buttons."""
    
    if user_role == 'owner':
        # Owner: Review movies (added via website), manage channels, stats
        keyboard = [
            [KeyboardButton("📋 Review Movies"), KeyboardButton("🗑️ Remove Movie")],
            [KeyboardButton("📊 Show Requests"), KeyboardButton("📊 Show Stats")],
            [KeyboardButton("📊 Monthly Report"), KeyboardButton("📢 Manage Channels")],
            [KeyboardButton("❓ Help"), KeyboardButton("❌ Cancel")]
        ]
    elif user_role == 'admin':
        # Admin: Review movies, stats (movies added via website, admins managed via website)
        keyboard = [
            [KeyboardButton("📋 Review Movies"), KeyboardButton("📊 Show Requests")],
            [KeyboardButton("📊 Show Stats"), KeyboardButton("❓ Help")],
            [KeyboardButton("❌ Cancel")]
        ]
    else:
        # Regular users get basic commands plus cancel
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

def format_movie_post(movie_details: dict, channel_username: str) -> str:
    """
    ডেটাবেস থেকে প্রাপ্ত মুভির তথ্য দিয়ে একটি সুন্দর পোস্ট ফরম্যাট করে।
    স্কিপ করা ফিল্ডগুলো (N/A) প্রিভিউতে দেখানো হয় না।
    """
    files = movie_details.get('files', {})
    is_series = any('E' in quality for quality in files.keys())
    
    # ডাউনলোড লিঙ্ক তৈরি
    download_links = ""
    episode_info = ""
    if is_series:
        # Get all episode numbers to find the range
        episode_files = [quality for quality in files.keys() if quality.startswith('E')]
        if episode_files:
            # Extract episode numbers and find the range
            episode_numbers = []
            for ep_file in episode_files:
                try:
                    # Extract number from formats like "E1", "E01", "E001", etc.
                    ep_num = int(ep_file[1:])  # Remove 'E' and convert to int
                    episode_numbers.append(ep_num)
                except ValueError:
                    continue
            
            if episode_numbers:
                episode_numbers.sort()
                first_ep = min(episode_numbers)
                last_ep = max(episode_numbers)
                
                # Format episode range display
                if first_ep == last_ep:
                    episode_info = f"Available Episodes: Ep{first_ep}"
                else:
                    episode_info = f"Available Episodes: Ep{first_ep} to Ep{last_ep}"
                
                # Create download link for first episode
                first_episode = next((quality for quality in files.keys() if quality.startswith('E')), None)
                if first_episode:
                    # Use actual download URL instead of bot redirect
                    actual_download_url = files[first_episode]
                    download_links = f"👉 <a href='{actual_download_url}'>Click To Download</a> 📥"
    else:
        # সিঙ্গেল মুভির জন্য প্রতিটি কোয়ালিটির লিঙ্ক
        qualities = sorted([quality for quality in files.keys() if not quality.startswith('E')])
        for quality in qualities:
            # Use actual download URL instead of bot redirect
            actual_download_url = files[quality]
            download_links += f"{quality} || 👉 <a href='{actual_download_url}'>Click To Download</a> 📥\n"

    # Build dynamic template - only include non-N/A fields
    title = movie_details.get('title', 'Unknown')
    languages = " | ".join(movie_details.get('languages', []))
    
    # Remove emojis from categories for cleaner display
    categories_raw = movie_details.get('categories', [])
    categories_clean = []
    for category in categories_raw:
        # Remove emoji by taking only the text part before space
        if ' ' in category:
            clean_category = category.split(' ')[0]
        else:
            clean_category = category
        categories_clean.append(clean_category)
    categories = " | ".join(categories_clean)
    
    # Start building the post with "Title:" prefix
    post_text = f"🍿 Title: {title}\n\n"
    
    # Only add fields that are not N/A or empty
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
    
    # Add series-specific episode info
    if is_series and episode_info:
        post_text += f"\n{episode_info}\n"
    
    # Add download links and footer
    post_text += f"\n🔗 Download Link Below\n{download_links.strip()}\n\n"
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
    """Remove hamburger menu entirely - no commands will appear there."""
    from telegram import BotCommand, BotCommandScopeChat
    
    try:
        # Get chat_id from either update.effective_chat or callback query
        if hasattr(update, 'callback_query') and update.callback_query:
            chat_id = update.callback_query.message.chat_id
        else:
            chat_id = update.effective_chat.id
            
        # REMOVE ALL COMMANDS from hamburger menu permanently
        await context.bot.set_my_commands(
            commands=[],  # Empty array = no hamburger menu
            scope=BotCommandScopeChat(chat_id=chat_id)
        )
        logger.info(f"Hamburger menu disabled for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to disable hamburger menu: {e}")

async def restore_default_commands(context, chat_id):
    """Keep hamburger menu disabled - all commands through reply keyboard only."""
    from telegram import BotCommand, BotCommandScopeChat
    
    try:
        # Keep hamburger menu empty - all commands through reply keyboard
        await context.bot.set_my_commands(
            commands=[],  # No hamburger menu commands
            scope=BotCommandScopeChat(chat_id=chat_id)
        )
        logger.info(f"Hamburger menu kept disabled for chat {chat_id}")
    except Exception as e:
        logger.error(f"Failed to keep hamburger menu disabled: {e}")

async def set_conversation_keyboard(update: Update, context, user_role: str):
    """Use main keyboard during conversations since cancel is already included."""
    keyboard = get_main_keyboard(user_role)
    # Store the original keyboard to restore later
    context.user_data['original_keyboard'] = get_main_keyboard(user_role)
    
    # Set conversation commands (hamburger menu disabled)
    await set_conversation_commands(update, context)
    
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
