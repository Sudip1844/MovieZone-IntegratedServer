# MovieZoneBot/handlers/start_handler.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

import bot.db as db
from bot.utils import get_main_keyboard
from bot.config import BOT_USERNAME

# লগিং সেটআপ
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    - Adds new users to the database.
    - Sends a welcome message with a keyboard based on the user's role.
    - Handles deep links from the ad page.
    """
    user = update.effective_user
    logger.info(f"/start command received from user: {user.id} ({user.first_name})")

    # Disable hamburger menu for this user
    from bot.utils import restore_default_commands
    await restore_default_commands(context, update.effective_chat.id)

    # Check if user is new and add to database if they don't exist
    is_new_user = not db.user_exists(user.id)
    db.add_user_if_not_exists(user.id, user.first_name, user.username)
    
    # context.args contains the part after the /start command (for deep linking)
    # Example: /start file_5_720p or /start <secureToken>
    if context.args:
        payload = context.args[0]
        logger.info(f"User {user.id} started with payload: {payload}")
        
        # Check if it's a file download link (format: file_<movie_id>_<quality>)
        if payload.startswith('file_'):
            try:
                # Parse the file identifier: file_5_720p or file_5_E01
                parts = payload.split('_')
                if len(parts) >= 3:
                    movie_id = int(parts[1])
                    quality = '_'.join(parts[2:])  # Handle qualities like '720p_HEVC'
                    
                    # Get movie details
                    movie_details = db.get_movie_details(movie_id)
                    if not movie_details:
                        await context.bot.send_message(
                            chat_id=user.id,
                            text="❌ Movie not found. It might have been deleted."
                        )
                        return
                    
                    # Check if the quality exists
                    files = movie_details.get("files", {})
                    if quality not in files:
                        await context.bot.send_message(
                            chat_id=user.id,
                            text="❌ This quality is no longer available."
                        )
                        return
                    
                    # Show the movie with direct download link
                    movie_title = movie_details.get('title', 'this movie')
                    direct_download_url = files[quality]
                    
                    await context.bot.send_message(
                        chat_id=user.id,
                        text=f"🍿 {movie_title} ({quality})\n\n"
                             f"📥 Direct Download Link:\n"
                             f"👉 <a href='{direct_download_url}'>Click To Download</a> 📥\n\n"
                             f"Click the link above to download directly from your browser.",
                        parse_mode=ParseMode.HTML
                    )
                    return
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"Invalid file payload format: {payload}")
        
        # If not a direct file link, show invalid link message
        logger.warning(f"Invalid download link format: {payload}")
        await context.bot.send_message(
            chat_id=user.id,
            text="⚠️ Sorry, this download link is invalid. Please generate a new one from the bot."
        )
        return  # Stop execution - don't show welcome message for invalid links

    # Only show welcome message for completely new users or normal /start command without payload  
    user_role = db.get_user_role(user.id)
    
    # Show welcome message only for new users or when explicitly calling /start without payload
    if not is_new_user and context.args:
        return  # Skip welcome for existing users coming from expired links
    welcome_message = ""
    if user_role == 'owner':
        welcome_message = f"""👑 Welcome Back, Owner {user.mention_html()}!

🎬 MovieZone Bot Management Panel

Available Powers:
• 🎭 Movie Management - Add/Remove movies
• 👥 Admin Control - Manage bot administrators  
• 📢 Channel Management - Handle movie channels
• 📊 Analytics - View detailed statistics
• 🙏 User Requests - Review & process requests

You have complete control over the bot ecosystem.
Ready to manage your movie empire!"""
        
    elif user_role == 'admin':
        welcome_message = f"""🛡️ Welcome Back, Admin {user.mention_html()}!

🎬 MovieZone Bot Admin Panel

Your Capabilities:
• 🎭 Add Movies - Upload new content to database
• 📊 View Requests - Handle user movie requests  
• 🗑️ Remove Movies - Delete outdated content
• 📈 Statistics - Monitor bot performance

You can manage the movie library and assist users.
Ready to serve the community!"""
        
    else:
        # Standard welcome message for a regular user
        welcome_message = f"""🎬 Welcome to MovieZone, {user.mention_html()}!

Your Ultimate Movie Destination

What We Offer:
🔍 Search Movies - Find any movie instantly
📂 Browse Categories - Explore by genre & language  
🙏 Request Movies - Ask for movies you can't find
📥 Direct Downloads - Fast & secure downloads

Movie Collection:
• 🎭 Bollywood & Bengali Movies
• 🧑‍🎤 Latest Hollywood Blockbusters
• 🎪 South Indian Dubbed Movies  
• 📺 Popular Web Series
• 🎨 Animation & Kids Content

Download Process:
1. 🔍 Search or browse for your movie
2. 📱 Select your preferred quality
3. 👀 View a quick ad (helps us grow!)
4. 📥 Download instantly!

🚀 Ready to explore? Use the buttons below!

Join our channel: @moviezone969"""

    keyboard = get_main_keyboard(user_role)
    sent_message = await update.message.reply_html(welcome_message, reply_markup=keyboard)
    
    # Schedule cleanup for welcome message (preserve for users if it's first time)
    from main import schedule_user_message_cleanup
    if is_new_user and user_role == 'user':
        # Don't auto-delete welcome message for new users
        pass
    else:
        schedule_user_message_cleanup(context, update.effective_chat.id, sent_message.message_id, user_role)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message for the /help command."""
    user = update.effective_user
    user_role = db.get_user_role(user.id)
    
    if user_role == 'owner':
        help_text = """❓ Owner Help & Commands

Available Features:
• 📋 Review Movies - Review pending movies submitted from website
• 📊 Show Requests - View user movie requests  
• 👥 Manage Admins - Add or remove admins
• 📢 Manage Channels - Add or remove channels
• 🗑️ Remove Movie - Delete a movie quickly
• 📊 Weekly Report - Generate performance reports

You have full access to all bot features and can manage admins and channels."""
        
    elif user_role == 'admin':
        help_text = """❓ Admin Help & Commands

Available Features:
• 📊 Show Requests - View and manage user requests

You can handle user movie requests from the bot. 
Please log in to the MovieZone Admin Panel website to add new movies!"""
        
    else:
        help_text = """❓ How to Use MovieZone Bot

Main Features:
🔍 Search - Find movies by name
🎭 Request - Request new movies to admin

Download Process:
1. 🔍 Search or browse for a movie in our channel @moviezone969
2. 📱 Select quality (480p/720p/1080p) links or Series download link 
3. 👀 Watch ads
4. 📥 Get your movie!

Tips:
• Use specific movie names for better search results in channel 
• Check our channel for latest uploads
• Report any issues to admins

Support: 
Join: @moviezone969

🎬 Happy watching!"""
        
    await update.message.reply_text(help_text)

# This is the welcome message for new channel members.
# It will be triggered by a different handler in main.py
NEW_MEMBER_WELCOME_MESSAGE = """
Welcome {user_mention} to our channel & bot!

❓ How to Use MovieZone Bot

Main Features:
- 🔍 Search: Find movies by name.
- 📂 Category: Browse by genre.
- 🙏 Request: Request new movies.

Download Process:
1.  🔍 Search or browse for a movie.
2.  📲 Select quality (480p/720p/1080p).
3.  👀 Watch a short ad to support us.
4.  📥 Download your movie instantly!

Tips:
- Use specific movie names for better search results.
- Check our channel for the latest uploads.
- Report any issues to admins via the bot.

Support:
- Join: @moviezone969
- Contact: Use the /request command in the bot.

🎬 Happy watching!
"""


async def cancel_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel button press from reply keyboard."""
    from bot.utils import get_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = get_main_keyboard(user_role)
    
    # Clear any ongoing conversation
    context.user_data.clear()
    
    await update.message.reply_text("❌ Action cancelled.", reply_markup=keyboard)

# Handlers list to be imported in main.py
start_handlers = [
    CommandHandler("start", start),
    CommandHandler("help", help_command),
    MessageHandler(filters.Regex('^❓ Help$'), help_command), # Also works from the keyboard button
    MessageHandler(filters.Regex('^❌ Cancel$'), cancel_button_handler) # Handle cancel button
]
