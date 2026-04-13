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
        await update.message.reply_text("No approved movies waiting for review!")
        return

    await update.message.reply_text(f"📋 Approved movies for final review: {len(pending)}\n(Showing 5 at a time)\n\n✅ = Post to all channels\n❌ = Send back to Pending")

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.utils import format_movie_post
    from bot.config import CHANNEL_USERNAME

    for movie in pending[:5]:  # Show max 5 at a time
        mid = movie.get('movie_id')

        # Use format_movie_post for proper channel-style preview
        try:
            post_text = format_movie_post(movie, CHANNEL_USERNAME or "yourchannel")
        except Exception as e:
            logger.error(f"format_movie_post failed: {e}")
            # Fallback to simple text
            cats = ', '.join(movie.get('categories', []))
            langs = ', '.join(movie.get('languages', []))
            post_text = (f"🎬 <b>{movie.get('title', 'Unknown')}</b>\n"
                        f"👤 Added By: {movie.get('added_by', 'owner')}\n"
                        f"📁 Type: {movie.get('download_type', 'single')}\n"
                        f"🏷️ Categories: {cats or 'N/A'}\n"
                        f"🌐 Languages: {langs or 'N/A'}")

        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"review_approve_{mid}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"review_reject_{mid}")
            ]
        ])

        thumbnail = movie.get('thumbnail_file_id')
        if thumbnail:
            try:
                await update.message.reply_photo(
                    photo=thumbnail,
                    caption=post_text,
                    reply_markup=buttons,
                    parse_mode='HTML'
                )
                continue
            except Exception as e:
                logger.error(f"Failed to send photo: {e}")
        # Fallback: send as text
        await update.message.reply_text(post_text, reply_markup=buttons, parse_mode='HTML')


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

    # Helper to edit message regardless of whether it's a photo or text
    async def edit_reply(text: str):
        try:
            # Photo messages need edit_message_caption
            if query.message.photo:
                await query.edit_message_caption(caption=text)
            else:
                await query.edit_message_text(text)
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            # Try sending a new message as fallback
            try:
                await query.message.reply_text(text)
            except Exception:
                pass

    if action == 'approve':
        # Mark as 'posted' so it doesn't show up in review again
        success = db.approve_movie(movie_id)
        if success:
            movie = db.get_movie_details(movie_id)
            title = movie.get('title', 'Unknown') if movie else 'Unknown'
            await edit_reply(f"✅ APPROVED: {title}\n\nPosting to all channels...")

            # Auto-post to all configured channels
            if movie:
                try:
                    from bot.utils import format_movie_post
                    from bot.config import CHANNEL_USERNAME, DUMP_CHAT_ID
                    post_text = format_movie_post(movie, CHANNEL_USERNAME or "yourchannel")
                    thumbnail = movie.get('thumbnail_file_id')

                    # ──────────────────────────────────────────────────
                    # STEP 1: Send a clean "Master Post" to DUMP_CHAT
                    # This gives us a stable message_id that:
                    #   - Looks clean (no "APPROVED" admin text)
                    #   - Can be copy_message'd to channels without re-upload
                    #   - Can be forwarded to users on search
                    # ──────────────────────────────────────────────────
                    master_message_id = None
                    try:
                        if thumbnail:
                            master_msg = await context.bot.send_photo(
                                chat_id=DUMP_CHAT_ID,
                                photo=thumbnail,
                                caption=post_text,
                                parse_mode='HTML'
                            )
                        else:
                            master_msg = await context.bot.send_message(
                                chat_id=DUMP_CHAT_ID,
                                text=post_text,
                                parse_mode='HTML'
                            )
                        master_message_id = master_msg.message_id
                        # Save the master post ID to database
                        db.update_telegram_message_id(movie_id, master_message_id)
                        logger.info(f"Master post created: message_id={master_message_id} for movie '{title}'")
                    except Exception as e:
                        logger.error(f"Failed to create master post in DUMP_CHAT: {e}")

                    # ──────────────────────────────────────────────────
                    # STEP 2: Copy master post to all connected channels
                    # Using copy_message is faster and avoids re-uploading
                    # ──────────────────────────────────────────────────
                    channels = db.get_all_channels()
                    posted_count = 0
                    failed_channels = []
                    if channels:
                        for channel in channels:
                            channel_id = str(channel.get('channel_id', '')).strip()
                            # Auto-fix IDs missing the negative sign (channels start with -100)
                            if channel_id.startswith('100') and len(channel_id) >= 13:
                                channel_id = f"-{channel_id}"
                            if not channel_id:
                                continue
                            if str(channel_id) == str(DUMP_CHAT_ID):
                                continue
                            # Detect invite links — bot cannot post to invite links
                            ch_str = str(channel_id).strip()
                            if '+' in ch_str and not ch_str.lstrip('-').isdigit():
                                logger.error(f"⚠️ Channel '{ch_str}' is an INVITE LINK — use @username or numeric ID")
                                failed_channels.append(f"{ch_str} (invite link)")
                                continue
                            try:
                                success = False
                                if master_message_id:
                                    try:
                                        # Use copy_message: no re-upload, instant, clean
                                        await context.bot.copy_message(
                                            chat_id=channel_id,
                                            from_chat_id=DUMP_CHAT_ID,
                                            message_id=master_message_id
                                        )
                                        success = True
                                        posted_count += 1
                                        logger.info(f"Movie posted to channel: {title} → {channel_id}")
                                    except Exception as copy_err:
                                        logger.warning(f"copy_message failed: {copy_err}. Attempting fallback...")
                                
                                if not success:
                                    if thumbnail:
                                        # Fallback if master post failed
                                        await context.bot.send_photo(
                                            chat_id=channel_id,
                                            photo=thumbnail,
                                            caption=post_text,
                                            parse_mode='HTML'
                                        )
                                    else:
                                        await context.bot.send_message(
                                            chat_id=channel_id,
                                            text=post_text,
                                            parse_mode='HTML'
                                        )
                                    posted_count += 1
                                    logger.info(f"Movie posted (fallback) to channel: {title} → {channel_id}")
                            except Exception as e:
                                logger.error(f"Failed to post to channel {channel_id}: {e}")
                                failed_channels.append(f"{channel_id} ({str(e)[:50]})")

                    db.mark_movie_as_posted(movie_id)
                    # Update the review message with final status
                    status_text = f"✅ POSTED: {title}\n\nPosted to {posted_count} channel(s)!"
                    if failed_channels:
                        status_text += f"\n⚠️ Failed: {len(failed_channels)} channel(s)"
                    try:
                        if query.message.photo:
                            await query.edit_message_caption(caption=status_text)
                        else:
                            await query.edit_message_text(status_text)
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"Failed to post to channels: {e}")
        else:
            await edit_reply("Failed to approve movie.")

    elif action == 'reject':
        # Send back to pending so owner panel can re-review
        success = db.reject_movie(movie_id, 'pending')
        if success:
            await edit_reply("🔄 Movie sent back to Pending queue for re-review.")
        else:
            await edit_reply("Failed to reject movie.")


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

    # Create application with increased timeouts to prevent 'Timed out' errors
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )

    # Import handlers from copied Tgbot code
    from bot.handlers.start_handler import start_handlers
    from bot.handlers.movie_handlers import (
        request_movie_conv,
        search_movies, handle_search_query, browse_categories,
        show_requests
    )
    from bot.handlers.callback_handler import callback_query_handler
    from bot.handlers.owner_handlers import owner_handlers
    
    # Check Manage Admins function from owner handler directly
    from bot.handlers.owner_handlers import manage_admins

    # --- Handler Registration (matching original Tgbot order) ---

    # 1. Owner-specific handlers (highest priority)
    for handler in owner_handlers:
        application.add_handler(handler)

    # 2. Movie request conversation handlers
    application.add_handler(request_movie_conv)

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
    application.add_handler(MessageHandler(filters.Regex("^👥 Manage Admins$"), manage_admins))

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
        & ~filters.Regex("^👥 Manage Admins$") & ~filters.Regex("^📋 Review Movies$")
        & ~filters.Regex("^🗑️ Remove Movie$")
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
                    drop_pending_updates=False
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