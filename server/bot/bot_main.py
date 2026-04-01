# IntegratedServer/bot/bot_main.py
# Main bot entry point - adapted from Tgbot/main.py
# Runs the Telegram bot with all handlers

import logging
import asyncio
import os
import sys

# Add parent and current dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ChatMemberHandler, ContextTypes

from bot.config import BOT_TOKEN, BOT_USERNAME, OWNER_ID, CONVERSATION_TIMEOUT
import bot.db as db

logger = logging.getLogger(__name__)


# --- Auto-Delete Job Functions ---
async def delete_message_job(context):
    """Deletes a message after a specified time."""
    try:
        await context.bot.delete_message(chat_id=context.job.data['chat_id'],
                                         message_id=context.job.data['message_id'])
    except Exception as e:
        logger.error(f"Failed to delete message: {e}")


def schedule_message_deletion(context, chat_id: int, message_id: int, delay_seconds: int = 86400):
    """Schedules a message to be deleted after a delay."""
    context.job_queue.run_once(
        delete_message_job,
        when=delay_seconds,
        data={'chat_id': chat_id, 'message_id': message_id}
    )


# --- Channel Member Handler ---
def extract_status_change(chat_member_update: ChatMemberUpdated):
    """Extract status change from ChatMemberUpdated."""
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR] or (
            old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR] or (
            new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets new users in chats."""
    result = extract_status_change(update.chat_member)
    if result is None:
        return
    was_member, is_member = result
    if not was_member and is_member:
        new_user = update.chat_member.new_chat_member.user
        await update.effective_chat.send_message(
            f"Welcome {new_user.mention_html()} to our channel and bot!\n\n"
            f"Use @{BOT_USERNAME} to search and download movies!",
            parse_mode='HTML'
        )


# --- Global Cancel Handler ---
async def global_cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command globally."""
    user_role = db.get_user_role(update.effective_user.id)
    from bot.utils import get_main_keyboard
    keyboard = get_main_keyboard(user_role)
    await update.message.reply_text("Operation cancelled.", reply_markup=keyboard)


# --- Error Handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Exception while handling an update: {context.error}")


# --- NEW: Review & Edit Commands (per INTEGRATION_PLAN.md) ---

async def review_pending_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner reviews pending movies submitted from website. /review command."""
    from bot.config import OWNER_ID
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("This command is only for the owner.")
        return

    pending = db.get_pending_movies()
    if not pending:
        await update.message.reply_text("No pending movies to review!")
        return

    await update.message.reply_text(f"Pending movies for review: {len(pending)}\n")

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    for movie in pending[:10]:  # Show max 10 at a time
        title = movie.get('title', 'Unknown')
        mid = movie.get('movie_id')
        cats = ', '.join(movie.get('categories', []))
        langs = ', '.join(movie.get('languages', []))

        text = (f"Title: {title}\n"
                f"Categories: {cats or 'N/A'}\n"
                f"Languages: {langs or 'N/A'}\n"
                f"Type: {movie.get('download_type', 'single')}")

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Approve", callback_data=f"review_approve_{mid}"),
                InlineKeyboardButton("Reject", callback_data=f"review_reject_{mid}")
            ]
        ])

        thumbnail = movie.get('thumbnail_file_id')
        if thumbnail:
            try:
                await update.message.reply_photo(photo=thumbnail, caption=text, reply_markup=buttons)
                continue
            except Exception:
                pass
        await update.message.reply_text(text, reply_markup=buttons)


async def handle_review_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approve/reject callback from review."""
    query = update.callback_query
    await query.answer()

    from bot.config import OWNER_ID
    if query.from_user.id != OWNER_ID:
        return

    data = query.data  # review_approve_123 or review_reject_123
    parts = data.split('_')
    action = parts[1]  # approve or reject
    movie_id = int(parts[2])

    if action == 'approve':
        success = db.approve_movie(movie_id)
        if success:
            movie = db.get_movie_details(movie_id)
            title = movie.get('title', 'Unknown') if movie else 'Unknown'
            await query.edit_message_text(f"APPROVED: {title}\n\nMovie is now live!")

            # Auto-post to channel
            from bot.config import CHANNEL_USERNAME
            if CHANNEL_USERNAME and movie:
                try:
                    from bot.utils import format_movie_post
                    post_text = format_movie_post(movie, CHANNEL_USERNAME)
                    thumbnail = movie.get('thumbnail_file_id')
                    if thumbnail:
                        await context.bot.send_photo(
                            chat_id=f"@{CHANNEL_USERNAME}",
                            photo=thumbnail,
                            caption=post_text,
                            parse_mode='HTML'
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=f"@{CHANNEL_USERNAME}",
                            text=post_text,
                            parse_mode='HTML'
                        )
                    logger.info(f"Movie posted to channel: {title}")
                except Exception as e:
                    logger.error(f"Failed to post to channel: {e}")
        else:
            await query.edit_message_text("Failed to approve movie.")

    elif action == 'reject':
        success = db.reject_movie(movie_id)
        if success:
            await query.edit_message_text("Movie rejected.")
        else:
            await query.edit_message_text("Failed to reject movie.")


async def edit_movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Owner edits a movie (e.g., update thumbnail). /edit <movie_id> command."""
    from bot.config import OWNER_ID
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("This command is only for the owner.")
        return

    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /edit <movie_id>\n\n"
            "Then send a new thumbnail photo in the next message."
        )
        return

    try:
        movie_id = int(args[0])
        movie = db.get_movie_details(movie_id)
        if not movie:
            await update.message.reply_text(f"Movie ID {movie_id} not found.")
            return

        context.user_data['editing_movie_id'] = movie_id
        await update.message.reply_text(
            f"Editing: {movie.get('title', 'Unknown')}\n\n"
            f"Send a new thumbnail photo to update it.\n"
            f"Send /cancel to cancel."
        )
    except ValueError:
        await update.message.reply_text("Invalid movie ID. Use: /edit <number>")


def build_application():
    """Build the bot Application with all handlers registered"""
    if not BOT_TOKEN:
        logger.error("[BOT] BOT_TOKEN not configured!")
        return None

    logger.info(f"[BOT] Building Telegram Bot: @{BOT_USERNAME}")

    # Initialize database
    db.initialize_database()

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # Import handlers from copied Tgbot code
    from bot.handlers.start_handler import start_handlers
    from bot.handlers.movie_handlers import (
        request_movie_conv, remove_movie_conv, show_stats_conv,
        search_movies, handle_search_query, browse_categories,
        show_requests
    )
    from bot.handlers.callback_handler import callback_query_handler
    from bot.handlers.owner_handlers import owner_handlers
    from bot.handlers.monthly_handler import monthly_handlers

    # --- Handler Registration (matching original Tgbot order) ---

    # 1. Owner-specific handlers (highest priority)
    for handler in owner_handlers:
        application.add_handler(handler)

    # 1.1. Monthly report handlers (owner only)
    for handler in monthly_handlers:
        application.add_handler(handler)

    # 2. Movie request/remove/stats conversation handlers
    # NOTE: add_movie_conv_handler REMOVED - movies are now added via website
    application.add_handler(request_movie_conv)
    application.add_handler(remove_movie_conv)
    application.add_handler(show_stats_conv)

    # 3. Review & Edit commands (NEW - owner reviews pending movies from website)
    from telegram.ext import CallbackQueryHandler
    application.add_handler(CommandHandler("review", review_pending_movies))
    application.add_handler(CommandHandler("edit", edit_movie_command))
    application.add_handler(CallbackQueryHandler(handle_review_callback, pattern="^review_"))

    # 3.1 Text button handlers for keyboard buttons
    application.add_handler(MessageHandler(filters.Regex("^📋 Review Movies$"), review_pending_movies))
    application.add_handler(MessageHandler(filters.Regex("^🔍 Search Movies$"), search_movies))
    application.add_handler(MessageHandler(filters.Regex("^📂 Browse Categories$"), browse_categories))
    application.add_handler(MessageHandler(filters.Regex("^📊 Show Requests$"), show_requests))

    # 3.2 Monthly Report text button handler
    from bot.handlers.monthly_handler import monthly_handlers
    # monthly_handlers are already registered above, but we need the text button too
    async def monthly_report_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle '📊 Monthly Report' keyboard button."""
        from bot.handlers.monthly_handler import monthly_report_start
        await monthly_report_start(update, context)
    application.add_handler(MessageHandler(filters.Regex("^📊 Monthly Report$"), monthly_report_button))

    # 4. Regular command and message handlers from start_handler
    for handler in start_handlers:
        application.add_handler(handler)

    # 5. Callback Query Handler for all inline buttons
    application.add_handler(callback_query_handler)

    # 6. Catch-all text search handler (MUST be last - catches any unhandled private text)
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND & ~filters.REPLY
        & ~filters.Regex("^❓ Help$") & ~filters.Regex("^❌ Cancel$")
        & ~filters.Regex("^🔍 Search Movies$") & ~filters.Regex("^📂 Browse Categories$")
        & ~filters.Regex("^🙏 Request Movie$") & ~filters.Regex("^📊 Show Requests$")
        & ~filters.Regex("^📊 Show Stats$") & ~filters.Regex("^📋 Review Movies$")
        & ~filters.Regex("^📊 Monthly Report$") & ~filters.Regex("^🗑️ Remove Movie$")
        & ~filters.Regex("^📢 Manage Channels$"),
        handle_search_query
    ))

    # 6. Welcome message for new channel members
    application.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    # 7. Global cancel command handler
    application.add_handler(CommandHandler("cancel", global_cancel_handler))

    # 8. Error handler
    application.add_error_handler(error_handler)

    # Disable hamburger menu globally (wrapped in try/except to prevent startup crash)
    async def post_init(app):
        try:
            from telegram import BotCommandScopeDefault, BotCommandScopeAllPrivateChats
            await app.bot.set_my_commands([], scope=BotCommandScopeDefault())
            await app.bot.set_my_commands([], scope=BotCommandScopeAllPrivateChats())
            logger.info("Hamburger menu disabled - using reply keyboard only")
        except Exception as e:
            logger.warning(f"Could not clear bot commands (non-fatal): {e}")

    application.post_init = post_init

    logger.info(f"[BOT] Application built with all handlers")
    return application


def run_bot_in_thread():
    """Run bot in a separate thread with its own event loop"""
    application = build_application()
    if not application:
        logger.error("[BOT] Failed to build bot application")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def start_bot():
        """Initialize and start the bot with retry logic"""
        nonlocal application
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            try:
                await application.initialize()
                await application.start()

                # Notify owner (non-blocking, ignore failure)
                try:
                    await application.bot.send_message(
                        chat_id=OWNER_ID,
                        text="MovieZone Bot started successfully!\n\n"
                             "Integrated Server Mode"
                    )
                except Exception as e:
                    logger.warning(f"Could not notify owner (non-fatal): {e}")

                logger.info(f"[BOT] @{BOT_USERNAME} is polling...")

                # Start polling (this runs until stopped)
                await application.updater.start_polling(
                    drop_pending_updates=True
                )

                # Keep running
                try:
                    while True:
                        await asyncio.sleep(1)
                except (KeyboardInterrupt, SystemExit):
                    pass
                finally:
                    await application.updater.stop()
                    await application.stop()
                    await application.shutdown()
                return  # Exited normally

            except Exception as e:
                logger.error(f"[BOT] Attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    wait = attempt * 5
                    logger.info(f"[BOT] Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    # Reset application for retry
                    try:
                        await application.shutdown()
                    except:
                        pass
                    application = build_application()
                    if not application:
                        logger.error("[BOT] Failed to rebuild application")
                        return
                else:
                    logger.error(f"[BOT] All {max_retries} attempts failed. Bot not running.")

    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        loop.close()