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

# --- Show Stats (Owner/Admin) ---

@restricted(allowed_roles=['owner', 'admin'])
async def show_stats_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the show stats conversation with three options."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands
    await set_conversation_commands(update, context)
    
    # Create inline keyboard for three options
    stats_options = [
        [InlineKeyboardButton("🔍 Search by Movie Name", callback_data="stats_movie_name")],
        [InlineKeyboardButton("📂 Search from Category", callback_data="stats_category")],
        [InlineKeyboardButton("👤 Search by Admin Name", callback_data="stats_admin")]
    ]
    
    await update.message.reply_text(
        "📊 Movie Statistics\n\n"
        "Choose how you want to search for movies:\n\n"
        "• Search by Movie Name - Type movie name to find\n"
        "• Search from Category - Browse movies by category\n"
        "• Search by Admin Name - See movies uploaded by specific admin\n\n"
        "To cancel, press ❌ Cancel button.",
        reply_markup=InlineKeyboardMarkup(stats_options)
    )
    return SHOW_STATS_OPTION

async def handle_stats_option(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle stats option selection."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "stats_movie_name":
        await query.edit_message_text("🔍 Type movie name to see statistics:")
        return SHOW_STATS_MOVIE_NAME
    
    elif query.data == "stats_category":
        from bot.config import BROWSE_CATEGORIES
        from bot.utils import create_category_keyboard
        
        keyboard = create_category_keyboard(BROWSE_CATEGORIES)
        await query.edit_message_text(
            "📂 Select category:",
            reply_markup=keyboard
        )
        return SHOW_STATS_CATEGORY
    
    elif query.data == "stats_admin":
        # Get all admins
        admins = db.get_all_admins()
        if not admins:
            await query.edit_message_text("❌ No admins found.")
            return ConversationHandler.END
        
        # Create admin selection keyboard
        admin_buttons = []
        for admin in admins:
            short_name = admin.get('short_name', f"Admin-{admin['user_id']}")
            admin_buttons.append([InlineKeyboardButton(f"👤 {short_name}", callback_data=f"admin_{admin['user_id']}")])
        
        # Add Owner option
        from bot.config import OWNER_ID
        admin_buttons.insert(0, [InlineKeyboardButton("👑 Owner", callback_data=f"admin_{OWNER_ID}")])
        
        await query.edit_message_text(
            "👤 Select admin:",
            reply_markup=InlineKeyboardMarkup(admin_buttons)
        )
        return SHOW_STATS_ADMIN
    
    # Default fallback return - should not reach here
    return ConversationHandler.END

async def handle_stats_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection for stats."""
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("cat_", "")
    
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Stats category callback received: '{query.data}', extracted category: '{category}'")
    
    # Map callback category to full category name with emoji
    from bot.config import BROWSE_CATEGORIES
    full_category = None
    for browse_cat in BROWSE_CATEGORIES:
        if browse_cat.startswith(category + " ") or browse_cat == category:
            full_category = browse_cat
            break
    
    if not full_category:
        full_category = category
    
    logger.info(f"Using full category name: '{full_category}' for search")
    movies = db.get_movies_by_category(full_category, limit=30)
    
    if not movies:
        await query.edit_message_text(f"❌ No movies in '{full_category}'.")
        return ConversationHandler.END
    
    # Create movie grid markup similar to browse categories
    from bot.utils import create_movie_grid_markup
    reply_markup = create_movie_grid_markup(movies, prefix="stats_view")
    
    await query.edit_message_text(
        f"📂 {full_category} ({len(movies)} movies):",
        reply_markup=reply_markup
    )
    return SHOW_STATS_MOVIE_LIST

async def handle_stats_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle admin selection for stats."""
    query = update.callback_query
    await query.answer()
    
    admin_id = int(query.data.replace("admin_", ""))
    movies = db.get_movies_by_uploader(admin_id, limit=30)
    
    from bot.config import OWNER_ID
    if str(admin_id) == str(OWNER_ID):
        admin_name = "Owner"
    else:
        admin_info = db.get_admin_info(admin_id)
        admin_name = admin_info.get('short_name', f"Admin-{admin_id}") if admin_info else f"Admin-{admin_id}"
    
    if not movies:
        await query.edit_message_text(f"❌ No movies by {admin_name}.")
        return ConversationHandler.END
    
    # Create movie grid markup
    from bot.utils import create_movie_grid_markup
    reply_markup = create_movie_grid_markup(movies, prefix="stats_view")
    
    await query.edit_message_text(
        f"👤 {admin_name} ({len(movies)} movies):",
        reply_markup=reply_markup
    )
    return SHOW_STATS_MOVIE_LIST

async def handle_stats_movie_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie selection from list to show stats."""
    query = update.callback_query
    await query.answer()
    
    movie_id = int(query.data.replace("stats_view_", ""))
    movie = db.get_movie_details(movie_id)
    
    if not movie:
        await query.edit_message_text("❌ Error: Movie not found.")
        return ConversationHandler.END
    
    await show_movie_stats_query(query, context, movie)
    return ConversationHandler.END

async def get_movie_for_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle movie stats request."""
    movie_name = update.message.text
    
    # Check if user sent cancel command or pressed cancel button
    if (movie_name.lower() == '/cancel' or 
        movie_name.lower() == 'cancel' or
        movie_name == '❌ Cancel'):
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Stats cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    movies = db.search_movies(movie_name, limit=10)
    if not movies:
        await update.message.reply_text(f"❌ No movies found: '{movie_name}'. Try again or /cancel.")
        return SHOW_STATS_MOVIE_NAME
    
    if len(movies) == 1:
        # Only one movie found, show stats directly
        movie = movies[0]
        await show_movie_stats(update, context, movie)
        return ConversationHandler.END
    else:
        # Multiple movies found - show selection
        buttons = []
        for movie in movies:
            buttons.append([InlineKeyboardButton(f"📊 {movie.get('title', 'Unknown')}", callback_data=f"stats_{movie['movie_id']}")])
        
        message_text = f"🎬 Found {len(movies)} movies:"
        await update.message.reply_html(message_text, reply_markup=InlineKeyboardMarkup(buttons))
        return SHOW_STATS_MOVIE_NAME

async def show_movie_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Show statistics for a specific movie."""
    from bot.config import OWNER_ID
    
    stats_text = f"📊 Statistics for {movie.get('title', 'Unknown')}\n\n"
    stats_text += f"🎬 Movie ID: {movie['movie_id']}\n"
    stats_text += f"📅 Added on: {movie.get('added_at', 'Unknown')[:10]}\n"
    
    # Get uploader information
    added_by_id = movie.get('added_by')
    if added_by_id:
        if str(added_by_id) == str(OWNER_ID):
            uploader_name = "Owner"
        else:
            # Check if it's an admin and get their short name
            admin_info = db.get_admin_info(added_by_id)
            if admin_info:
                uploader_name = admin_info.get('short_name', f"Admin-{added_by_id}")
            else:
                uploader_name = f"User-{added_by_id}"
    else:
        uploader_name = "Unknown"
    
    stats_text += f"👤 Uploaded by: {uploader_name}\n"
    
    # Get accurate download count
    download_count = movie.get('download_count', 0)
    # Ensure download count is properly calculated
    if isinstance(download_count, dict):
        # If download_count is stored as dict per quality, sum them up
        total_downloads = sum(download_count.values()) if download_count else 0
    else:
        total_downloads = download_count or 0
    
    stats_text += f"📥 Total Downloads: {total_downloads}\n"
    
    # Show available qualities and episodes
    files = movie.get('files', {})
    qualities = [q for q in files.keys() if not q.startswith('E')]
    episodes = [q for q in files.keys() if q.startswith('E')]
    
    if qualities:
        stats_text += f"🗂️ Available Qualities: {', '.join(qualities)}\n"
    
    if episodes:
        # Count total episodes
        episode_count = len(episodes)
        stats_text += f"📺 Available Episodes: {episode_count} episodes\n"
    
    await update.message.reply_html(stats_text)

async def show_movie_stats_in_message(message, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Show statistics for a specific movie in an existing message."""
    from bot.config import OWNER_ID
    
    stats_text = f"📊 Statistics for {movie.get('title', 'Unknown')}\n\n"
    stats_text += f"🎬 Movie ID: {movie['movie_id']}\n"
    stats_text += f"📅 Added on: {movie.get('added_at', 'Unknown')[:10]}\n"
    
    # Get uploader information
    added_by_id = movie.get('added_by')
    if added_by_id:
        if str(added_by_id) == str(OWNER_ID):
            uploader_name = "Owner"
        else:
            # Check if it's an admin and get their short name
            admin_info = db.get_admin_info(added_by_id)
            if admin_info:
                uploader_name = admin_info.get('short_name', f"Admin-{added_by_id}")
            else:
                uploader_name = f"User-{added_by_id}"
    else:
        uploader_name = "Unknown"
    
    stats_text += f"👤 Uploaded by: {uploader_name}\n"
    
    # Get accurate download count
    download_count = movie.get('download_count', 0)
    # Ensure download count is properly calculated
    if isinstance(download_count, dict):
        # If download_count is stored as dict per quality, sum them up
        total_downloads = sum(download_count.values()) if download_count else 0
    else:
        total_downloads = download_count or 0
    
    stats_text += f"📥 Total Downloads: {total_downloads}\n"
    
    # Show available qualities and episodes
    files = movie.get('files', {})
    qualities = [q for q in files.keys() if not q.startswith('E')]
    episodes = [q for q in files.keys() if q.startswith('E')]
    
    if qualities:
        stats_text += f"🗂️ Available Qualities: {', '.join(qualities)}\n"
    
    if episodes:
        # Count total episodes
        episode_count = len(episodes)
        stats_text += f"📺 Available Episodes: {episode_count} episodes\n"
    
    try:
        await message.edit_text(stats_text, parse_mode=ParseMode.HTML)
    except:
        # Fallback to sending new message if edit fails
        await message.reply_html(stats_text)

async def show_movie_stats_query(query, context: ContextTypes.DEFAULT_TYPE, movie: dict):
    """Show statistics for a specific movie (for callback queries)."""
    from bot.config import OWNER_ID
    
    stats_text = f"📊 Statistics for {movie.get('title', 'Unknown')}\n\n"
    stats_text += f"🎬 Movie ID: {movie['movie_id']}\n"
    stats_text += f"📅 Added on: {movie.get('added_at', 'Unknown')[:10]}\n"
    
    # Get uploader information
    added_by_id = movie.get('added_by')
    if added_by_id:
        if str(added_by_id) == str(OWNER_ID):
            uploader_name = "Owner"
        else:
            # Check if it's an admin and get their short name
            admin_info = db.get_admin_info(added_by_id)
            if admin_info:
                uploader_name = admin_info.get('short_name', f"Admin-{added_by_id}")
            else:
                uploader_name = f"User-{added_by_id}"
    else:
        uploader_name = "Unknown"
    
    stats_text += f"👤 Uploaded by: {uploader_name}\n"
    
    # Get accurate download count
    download_count = movie.get('download_count', 0)
    # Ensure download count is properly calculated
    if isinstance(download_count, dict):
        # If download_count is stored as dict per quality, sum them up
        total_downloads = sum(download_count.values()) if download_count else 0
    else:
        total_downloads = download_count or 0
    
    stats_text += f"📥 Total Downloads: {total_downloads}\n"
    
    # Show available qualities and episodes
    files = movie.get('files', {})
    qualities = [q for q in files.keys() if not q.startswith('E')]
    episodes = [q for q in files.keys() if q.startswith('E')]
    
    if qualities:
        stats_text += f"🗂️ Available Qualities: {', '.join(qualities)}\n"
    
    if episodes:
        # Count total episodes
        episode_count = len(episodes)
        stats_text += f"📺 Available Episodes: {episode_count} episodes\n"
    
    await query.edit_message_text(stats_text, parse_mode=ParseMode.HTML)

async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle stats callback from inline buttons."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("stats_"):
        movie_id = int(query.data.split("_")[1])
        movie = db.get_movie_details(movie_id)
        if movie:
            await show_movie_stats(query, context, movie)
        else:
            await query.edit_message_text("❌ Error: Movie not found.")
    
    from bot.utils import restore_default_commands
    await restore_default_commands(context, query.message.chat_id)
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

show_stats_conv = ConversationHandler(
    entry_points=[
        CommandHandler("showstats", show_stats_start),
        MessageHandler(filters.Regex("^📊 Show Stats$"), show_stats_start)
    ],
    states={
        SHOW_STATS_OPTION: [
            CallbackQueryHandler(handle_stats_option, pattern="^stats_(movie_name|category|admin)$")
        ],
        SHOW_STATS_MOVIE_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie_for_stats),
            CallbackQueryHandler(handle_stats_callback, pattern="^stats_")
        ],
        SHOW_STATS_CATEGORY: [
            CallbackQueryHandler(handle_stats_category, pattern="^cat_")
        ],
        SHOW_STATS_ADMIN: [
            CallbackQueryHandler(handle_stats_admin, pattern="^admin_")
        ],
        SHOW_STATS_MOVIE_LIST: [
            CallbackQueryHandler(handle_stats_movie_selection, pattern="^stats_view_")
        ]
    },
    fallbacks=[
        CommandHandler('cancel', cancel_movie_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_movie_conversation)
    ],
    per_message=False
)

# Main handler list to be imported
movie_handlers = [
    # Conversation handlers first
    request_movie_conv,
    remove_movie_conv,
    show_stats_conv,
    # Regular handlers
    MessageHandler(filters.Regex("^🔍 Search Movies$"), search_movies),
    MessageHandler(filters.Regex("^📂 Browse Categories$"), browse_categories),
    MessageHandler(filters.Regex("^📊 Show Requests$"), show_requests),
    # Text search handler (should be last to catch search queries)
    # Only respond in private chats, exclude channels and groups
    # Exclude help button and other main menu buttons
    MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND & ~filters.REPLY & ~filters.Regex("^❓ Help$") & ~filters.Regex("^❌ Cancel$"), handle_search_query)
]
