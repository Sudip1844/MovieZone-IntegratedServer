# MovieZoneBot/handlers/movie_handlers.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler
from telegram.constants import ParseMode

import bot.db as db
from bot.utils import get_category_keyboard, get_movie_search_results_markup, restricted, create_category_keyboard, create_movie_grid_markup
from bot.config import CATEGORIES

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# Conversation states
REQUEST_MOVIE_NAME, DELETE_MOVIE_NAME, SHOW_STATS_MOVIE_NAME, SHOW_STATS_OPTION, SHOW_STATS_CATEGORY, SHOW_STATS_ADMIN, SHOW_STATS_MOVIE_LIST = range(7)

# --- Search Movies ---

async def search_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle movie search functionality."""
    await update.message.reply_text(
        "🔍 Search Movies\n\n"
        "Please type the name of the movie you're looking for:"
    )

async def handle_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the actual search query from user."""
    query = update.message.text
    
    # Skip if this is a keyboard button or command
    if query in ["🔍 Search Movies", "📂 Browse Categories", "🙏 Request Movie", "➕ Add Movie", "🗑️ Remove Movie", "📊 Show Requests", "📊 Show Stats", "👥 Manage Admins", "📢 Manage Channels", "❓ Help"]:
        return
    
    if query.startswith('/'):
        return
    
    # Check if user is in a conversation - if so, don't handle as search
    if context.user_data and ('conversation_state' in context.user_data or 'new_admin' in context.user_data or 'new_channel' in context.user_data):
        return
    
    # Check if user is using alphabet filter (single letter after selecting "All" category)
    if len(query) == 1 and query.isalpha():
        logger.info(f"User {update.effective_user.id} requested alphabet filter for letter: {query}")
        movies = db.get_movies_by_first_letter(query.upper(), limit=30)
        
        if not movies:
            await update.message.reply_text(f"❌ No movies found starting with '{query.upper()}'.")
            return
        
        # Show movies in grid format like category browsing
        from bot.utils import create_movie_grid_markup
        reply_markup = create_movie_grid_markup(movies, prefix="view")
        await update.message.reply_html(
            f"🌐 Movies starting with '{query.upper()}' ({len(movies)} found):",
            reply_markup=reply_markup
        )
        return
    
    logger.info(f"User {update.effective_user.id} searched for: {query}")
    
    movies = db.search_movies(query, limit=10)
    
    if not movies:
        await update.message.reply_text(f"❌ No movies found for '{query}'. Try using different keywords or request it using the 'Request Movie' button.")
        return
    
    if len(movies) == 1:
        # Only one movie found, show details directly
        movie = movies[0]
        await show_movie_details(update, context, movie)
    else:
        # Multiple movies found, show selection
        message_text = f"🎬 Found {len(movies)} movies for '{query}':\n\n"
        for i, movie in enumerate(movies, 1):
            message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
        
        reply_markup = get_movie_search_results_markup(movies)
        await update.message.reply_html(message_text, reply_markup=reply_markup)

async def show_movie_details(update: Update, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Show detailed information about a movie with consistent formatting."""
    # Build response with Title: prefix and no Description field
    response_text = f"🎬 Title: {movie.get('title', 'N/A')}\n\n"
    
    # Only include non-N/A fields
    release_year = movie.get('release_year', 'N/A')
    if release_year != 'N/A':
        response_text += f"📅 Release Year: {release_year}\n"
    
    runtime = movie.get('runtime', 'N/A')
    if runtime != 'N/A':
        response_text += f"⏰ Runtime: {runtime}\n"
    
    imdb_rating = movie.get('imdb_rating', 'N/A')
    if imdb_rating != 'N/A':
        response_text += f"⭐ IMDb: {imdb_rating}/10\n"
    
    languages = movie.get('languages', [])
    if languages:
        response_text += f"🎭 Languages: {', '.join(languages)}\n"
    
    categories = movie.get('categories', [])
    if categories:
        response_text += f"🎪 Categories: {', '.join(categories)}"
    
    # Use movie post format with direct download links
    from bot.utils import format_movie_post
    from bot.config import CHANNEL_USERNAME
    
    # Format as movie post with direct download links
    post_text = format_movie_post(movie, CHANNEL_USERNAME)
    
    thumbnail_id = movie.get('thumbnail_file_id')
    if thumbnail_id:
        try:
            await update.message.reply_photo(
                photo=thumbnail_id, 
                caption=post_text, 
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send photo for movie {movie['movie_id']}: {e}")
            await update.message.reply_text(post_text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(post_text, parse_mode=ParseMode.HTML)

# --- Browse Categories ---

async def browse_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show movie categories for browsing."""
    keyboard = get_category_keyboard()
    await update.message.reply_text(
        "📂 Browse by Categories\n\n"
        "Select a category to see available movies:",
        reply_markup=keyboard
    )

# --- Request Movie ---

async def request_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the movie request conversation."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands
    await set_conversation_commands(update, context)
    
    await update.message.reply_text("🙏 Type movie name to request:", reply_markup=keyboard)
    return REQUEST_MOVIE_NAME

async def get_movie_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the movie request from user."""
    movie_name = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Check if user sent /cancel command (strict checking)
    if movie_name.lower() in ['/cancel', 'cancel', '❌ cancel'] or movie_name == '❌ Cancel':
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Movie request cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    # Store the movie name for potential request
    context.user_data['requested_movie'] = movie_name
    
    # First check if the movie already exists
    existing_movies = db.search_movies(movie_name, limit=3)
    if existing_movies:
        buttons = []
        for movie in existing_movies:
            buttons.append([InlineKeyboardButton(f"🎬 {movie.get('title', 'Unknown')}", callback_data=f"view_{movie['movie_id']}")])
        
        buttons.append([InlineKeyboardButton("📝 Still Request Movie", callback_data=f"force_request")])
        
        message_text = f"🎬 Found {len(existing_movies)} similar movies. Still want to request?"
        await update.message.reply_html(message_text, reply_markup=InlineKeyboardMarkup(buttons))
        return REQUEST_MOVIE_NAME
    else:
        # Movie not found, add to requests directly
        request_id = db.add_movie_request(user_id, movie_name)
        
        result_text = f"✅ Request submitted for '{movie_name}'\nRequest ID: {request_id}"
        await update.message.reply_text(result_text)
        
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("Done.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END

async def force_request_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Force add a movie request even if similar movies exist."""
    query = update.callback_query
    await query.answer()
    
    movie_name = context.user_data.get('requested_movie')
    if not movie_name:
        await query.edit_message_text("❌ Error: Movie name not found.")
        return ConversationHandler.END
    
    user_id = query.from_user.id
    request_id = db.add_movie_request(user_id, movie_name)
    
    result_text = f"✅ Request submitted for '{movie_name}'\nRequest ID: {request_id}"
    await query.edit_message_text(result_text)
    
    from bot.utils import restore_main_keyboard
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    await query.message.reply_text("Done.", reply_markup=keyboard)
    context.user_data.clear()
    return ConversationHandler.END

# --- Show Requests (Admin/Owner) ---

@restricted(allowed_roles=['owner', 'admin'])
async def show_requests(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show pending movie requests to admins/owners with pagination."""
    page = context.user_data.get('requests_page', 1)
    offset = (page - 1) * 5
    
    pending_requests = db.get_pending_requests(limit=5, offset=offset)
    total_requests = db.get_total_pending_requests_count()
    
    if not pending_requests:
        if page == 1:
            await update.message.reply_text("🎉 No pending movie requests at the moment!")
        else:
            await update.message.reply_text("❌ No more requests to show.")
        return
    
    # Show header with current page info
    total_pages = (total_requests + 4) // 5  # Round up
    await update.message.reply_text(f"📋 Showing {len(pending_requests)} movie requests (Page {page}/{total_pages}):\n")
    
    # Send each request as individual message
    for i, req in enumerate(pending_requests, 1):
        user_id = req.get('user_id', 'Unknown')
        user_info = f"ID: {user_id}"
        
        message_text = f"Request #{offset + i}: {req['movie_name']}\n"
        message_text += f"👤 Requested by: {user_info}\n"
        requested_at = req.get('requested_at', req.get('timestamp', ''))
        message_text += f"🗓️ On: {requested_at[:10] if requested_at else 'N/A'}"
        
        # Individual buttons for each request
        buttons = [
            [
                InlineKeyboardButton("✅ Done", callback_data=f"req_done_{req['request_id']}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"req_del_{req['request_id']}")
            ]
        ]
        
        await update.message.reply_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    # Add pagination controls only if total requests > 5
    if total_requests > 5:
        nav_buttons = []
        
        # Previous button
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"requests_page_{page-1}"))
        
        # Next button
        if len(pending_requests) == 5 and offset + 5 < total_requests:
            nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"requests_page_{page+1}"))
        
        # Cancel button
        nav_buttons.append(InlineKeyboardButton("❌ Cancel", callback_data="requests_cancel"))
        
        if nav_buttons:
            # Split into rows for better layout
            button_rows = []
            if len(nav_buttons) == 3:  # Previous, Next, Cancel
                button_rows.append([nav_buttons[0], nav_buttons[1]])
                button_rows.append([nav_buttons[2]])
            elif len(nav_buttons) == 2:  # Two buttons (either prev+cancel or next+cancel)
                button_rows.append(nav_buttons)
            else:  # Only cancel
                button_rows.append(nav_buttons)
            
            await update.message.reply_text(
                "Navigation:",
                reply_markup=InlineKeyboardMarkup(button_rows)
            )

# --- Remove Movie (Owner Only) ---

@restricted(allowed_roles=['owner'])
async def remove_movie_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the remove movie conversation."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands
    await set_conversation_commands(update, context)
    
    await update.message.reply_text(
        "🗑️ Remove Movie\n\n"
        "Please enter the name of the movie you want to remove:\n\n"
        "To cancel, press ❌ Cancel button.",
        reply_markup=keyboard
    )
    return DELETE_MOVIE_NAME

async def get_movie_to_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie deletion."""
    movie_name = update.message.text
    
    # Check if user sent /cancel command or pressed cancel button
    if (movie_name.lower() == '/cancel' or 
        movie_name.lower() == 'cancel' or
        movie_name == '❌ Cancel'):
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Movie deletion cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    movies = db.search_movies(movie_name, limit=10)
    if not movies:
        await update.message.reply_text(f"❌ No movies found with name '{movie_name}'. Please try again or /cancel.")
        return DELETE_MOVIE_NAME
    
    if len(movies) == 1:
        # Only one movie found, show confirmation
        movie = movies[0]
        context.user_data['movie_to_delete'] = movie
        
        keyboard = [
            [InlineKeyboardButton("✅ Yes, Delete", callback_data="confirm_delete")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")]
        ]
        
        await update.message.reply_html(
            f"🗑️ Confirm Deletion\n\n"
            f"Are you sure you want to delete:\n"
            f"<b>{movie.get('title', 'Unknown')}</b>\n\n"
            f"This action cannot be undone!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return DELETE_MOVIE_NAME
    else:
        # Multiple movies found
        message_text = f"🎬 Found {len(movies)} movies:\n\n"
        buttons = []
        
        for i, movie in enumerate(movies, 1):
            message_text += f"{i}. {movie.get('title', 'Unknown')}\n"
            buttons.append([InlineKeyboardButton(f"🗑️ Delete: {movie.get('title', 'Unknown')}", callback_data=f"delete_{movie['movie_id']}")])
        
        buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_delete")])
        
        await update.message.reply_html(
            message_text + "\nSelect the movie you want to delete:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return DELETE_MOVIE_NAME

async def confirm_movie_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie deletion confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_delete":
        from bot.utils import restore_default_commands
        await restore_default_commands(context, query.message.chat_id)
        await query.edit_message_text("❌ Movie deletion cancelled.")
        return ConversationHandler.END
    elif query.data == "confirm_delete":
        movie = context.user_data.get('movie_to_delete')
        if movie:
            success = db.delete_movie(movie['movie_id'])
            if success:
                await query.edit_message_text(f"✅ Movie '{movie.get('title', 'Unknown')}' has been deleted successfully.")
            else:
                await query.edit_message_text("❌ Failed to delete the movie. Please try again.")
        else:
            await query.edit_message_text("❌ Error: Movie information not found.")
        
        from bot.utils import restore_default_commands
        await restore_default_commands(context, query.message.chat_id)
        return ConversationHandler.END
    elif query.data.startswith("delete_"):
        movie_id = int(query.data.split("_")[1])
        movie = db.get_movie_details(movie_id)
        if movie:
            success = db.delete_movie(movie_id)
            if success:
                await query.edit_message_text(f"✅ Movie '{movie.get('title', 'Unknown')}' has been deleted successfully.")
            else:
                await query.edit_message_text("❌ Failed to delete the movie. Please try again.")
        else:
            await query.edit_message_text("❌ Error: Movie not found.")
        
        from bot.utils import restore_default_commands
        await restore_default_commands(context, query.message.chat_id)
        return ConversationHandler.END
    
    # Default fallback - should not reach here
    return ConversationHandler.END



async def cancel_movie_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel movie-related conversation."""
    from bot.utils import restore_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    
    await update.message.reply_text("❌ Movie action cancelled.", reply_markup=keyboard)
    context.user_data.clear()
    return ConversationHandler.END

# Conversation Handlers
request_movie_conv = ConversationHandler(
    entry_points=[
        CommandHandler("request", request_movie_start),
        MessageHandler(filters.Regex("^🙏 Request Movie$"), request_movie_start)
    ],
    states={
        REQUEST_MOVIE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_request),
            CallbackQueryHandler(force_request_movie, pattern="^force_request$")
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_movie_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_movie_conversation)
    ],
    per_message=False
)

remove_movie_conv = ConversationHandler(
    entry_points=[
        CommandHandler("removemovie", remove_movie_start),
        MessageHandler(filters.Regex("^🗑️ Remove Movie$"), remove_movie_start)
    ],
    states={
        DELETE_MOVIE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_to_delete),
            CallbackQueryHandler(confirm_movie_deletion, pattern="^(confirm_delete|cancel_delete|delete_)")
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_movie_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_movie_conversation)
    ]
)

# Main handler list to be imported
movie_handlers = [
    # Conversation handlers first
    request_movie_conv,
    remove_movie_conv,
    # Regular handlers
    MessageHandler(filters.Regex("^🔍 Search Movies$"), search_movies),
    MessageHandler(filters.Regex("^📂 Browse Categories$"), browse_categories),
    MessageHandler(filters.Regex("^📊 Show Requests$"), show_requests),
    # Text search handler (should be last to catch search queries)
    # Only respond in private chats, exclude channels and groups
    # Exclude help button and other main menu buttons
    MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND & ~filters.REPLY & ~filters.Regex("^❓ Help$") & ~filters.Regex("^❌ Cancel$"), handle_search_query)
]
