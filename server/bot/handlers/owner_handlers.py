# MovieZoneBot/handlers/owner_handlers.py

import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode

import bot.db as db
from bot.utils import restricted
from bot.config import OWNER_ID

# লগিং সেটআপ
logger = logging.getLogger(__name__)

# Conversation states for adding/removing admins and channels
(
    ASK_ADMIN_USERID, GET_ADMIN_USERID, GET_ADMIN_SHORT_NAME, CONFIRM_ADD_ADMIN,
    ASK_ADMIN_TO_REMOVE, CONFIRM_REMOVE_ADMIN,
    GET_CHANNEL_LINK, GET_CHANNEL_SHORT_NAME, CONFIRM_ADD_CHANNEL,
    ASK_CHANNEL_TO_REMOVE, CONFIRM_REMOVE_CHANNEL
) = range(11)


# --- Add Admin Conversation ---

@restricted(allowed_roles=['owner'])
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new admin."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    # Simple message without storing for editing
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("👤 Please send the User ID (numeric) of the new admin:")
    else:
        await update.message.reply_text("👤 Please send the User ID (numeric) of the new admin:", reply_markup=keyboard)
    return GET_ADMIN_USERID

async def get_admin_userid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the user ID of the potential admin."""
    # Check if user sent cancel command or pressed cancel button
    if update.message.text and (
        update.message.text.lower() == '/cancel' or 
        update.message.text.lower() == 'cancel' or
        update.message.text == '❌ Cancel'
    ):
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Admin addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    user_id = None
    first_name = None
    username = None
    
    if update.message.text and update.message.text.isdigit():
        user_id = int(update.message.text)
    else:
        await update.message.reply_text("Invalid input. Please send a valid User ID (only numbers).")
        return GET_ADMIN_USERID
    
    context.user_data['new_admin'] = {'id': user_id, 'first_name': f"User_{user_id}", 'username': f"user{user_id}"}
    
    # Simple message without editing
    await update.message.reply_text(f"✅ User ID: {user_id}\n\nEnter short name (e.g., 'Sudip'):")
    return GET_ADMIN_SHORT_NAME

async def get_admin_short_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the short name for the admin."""
    short_name = update.message.text
    
    # Check if user sent cancel command or pressed cancel button
    if (short_name.lower() == '/cancel' or 
        short_name.lower() == 'cancel' or
        short_name == '❌ Cancel'):
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Admin addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    context.user_data['new_admin']['short_name'] = short_name
    
    # Add admin directly and show result
    admin_info = context.user_data['new_admin']
    success = db.add_admin(admin_info['id'], admin_info['short_name'], admin_info.get('first_name', 'Unknown'), admin_info.get('username'))
    
    if success:
        result_text = f"✅ {admin_info['short_name']} added as admin\nUser ID: {admin_info['id']}"
    else:
        result_text = f"❌ Failed to add {admin_info['short_name']} as admin"
    
    from bot.utils import restore_main_keyboard
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    await update.message.reply_text(result_text, reply_markup=keyboard)
    
    context.user_data.clear()
    return ConversationHandler.END


# --- Remove Admin Conversation ---

@restricted(allowed_roles=['owner'])
async def remove_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to remove an admin with button selection."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    admins = db.get_all_admins()
    if not admins:
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ No admins to remove.")
        else:
            await update.message.reply_text("❌ No admins to remove.")
        return ConversationHandler.END

    # Create buttons for each admin - only show short name as requested
    buttons = []
    for admin in admins:
        admin_display = admin['short_name']  # Only use short name as requested
        buttons.append([InlineKeyboardButton(admin_display, callback_data=f"remove_admin_{admin['user_id']}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        context.user_data['admin_remove_message'] = query.message
        await query.edit_message_text("🗑️ Select admin to remove:", reply_markup=reply_markup)
    else:
        sent_msg = await update.message.reply_text("🗑️ Select admin to remove:", reply_markup=reply_markup)
        context.user_data['admin_remove_message'] = sent_msg
    
    return CONFIRM_REMOVE_ADMIN

async def confirm_remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows confirmation buttons for admin removal."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("remove_admin_"):
        admin_id_str = query.data.split("_")[2]
        admin_id = int(admin_id_str)
        admin_info = db.get_admin_info(admin_id)
        admin_name = admin_info.get('short_name', f'Admin-{admin_id}') if admin_info else f'Admin-{admin_id}'
        
        # Store admin info for final confirmation
        context.user_data['admin_to_remove'] = {'id': admin_id, 'name': admin_name}
        
        # Create confirm/cancel buttons
        buttons = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_admin_remove_{admin_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_admin_remove")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await query.edit_message_text(f"🗑️ Remove {admin_name} as admin?", reply_markup=reply_markup)
    
    return CONFIRM_REMOVE_ADMIN

async def final_admin_removal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles final confirm/cancel for admin removal."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("confirm_admin_remove_"):
        admin_id = int(query.data.split("_")[3])
        admin_info = context.user_data.get('admin_to_remove', {})
        admin_name = admin_info.get('name', f'Admin-{admin_id}')
        
        success = db.remove_admin(str(admin_id))
        
        if success:
            result_text = f"✅ {admin_name} removed as admin"
        else:
            result_text = f"❌ Failed to remove {admin_name}"
            
        await query.edit_message_text(result_text)
        
    elif query.data == "cancel_admin_remove":
        await query.edit_message_text("❌ Admin removal cancelled.")
    
    from bot.utils import restore_main_keyboard
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    await query.message.reply_text("Done.", reply_markup=keyboard)
    
    context.user_data.clear()
    return ConversationHandler.END


# --- Add Channel Conversation ---

@restricted(allowed_roles=['owner'])
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new channel."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    # Simple message without storing for editing
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("📺 Send channel link (e.g., https://t.me/moviezone969):")
    else:
        await update.message.reply_text("📺 Send channel link (e.g., https://t.me/moviezone969):", reply_markup=keyboard)
    return GET_CHANNEL_LINK

async def get_channel_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the channel link."""
    channel_link = update.message.text
    
    # Check if user sent cancel command or pressed cancel button
    if (channel_link.lower() == '/cancel' or 
        channel_link.lower() == 'cancel' or
        channel_link == '❌ Cancel'):
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Channel addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    # Edit original message with link confirmation and ask for short name
    channel_message = context.user_data.get('channel_message')
    
    # Extract channel username from link
    if "t.me/" in channel_link:
        channel_username = channel_link.split("t.me/")[-1].replace("@", "")
        
        context.user_data['new_channel'] = {'link': channel_link, 'username': channel_username}
        
        # Simple message without editing
        await update.message.reply_text(f"✅ Channel: {channel_link}\n\nEnter short name (e.g., 'Main'):")
        return GET_CHANNEL_SHORT_NAME
    else:
        await update.message.reply_text("❌ Invalid link format. Send channel link:")
        return GET_CHANNEL_LINK

async def get_channel_short_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gets the short name for the channel."""
    short_name = update.message.text
    
    # Check if user sent cancel command or pressed cancel button
    if (short_name.lower() == '/cancel' or 
        short_name.lower() == 'cancel' or
        short_name == '❌ Cancel'):
        from bot.utils import restore_main_keyboard
        user_role = db.get_user_role(update.effective_user.id)
        keyboard = await restore_main_keyboard(update, context, user_role)
        await update.message.reply_text("❌ Channel addition cancelled.", reply_markup=keyboard)
        context.user_data.clear()
        return ConversationHandler.END
    
    # Add channel directly and show final result in original message
    channel_info = context.user_data['new_channel']
    channel_info['short_name'] = short_name
    
    # Bypass bot channel access check as requested by User
    channel_id = f"@{channel_info['username']}"
    channel_name = channel_info['username']
    
    # Add channel to database  
    success = db.add_channel(channel_id, channel_name or "Unknown", short_name or "Unknown")
    
    if success:
        result_text = f"✅ {short_name} added as channel\nID: {channel_id}"
    else:
        result_text = f"❌ Failed to add {short_name} channel"
    
    from bot.utils import restore_main_keyboard
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    await update.message.reply_text(result_text, reply_markup=keyboard)
    
    context.user_data.clear()
    return ConversationHandler.END


# --- Remove Channel Conversation ---

@restricted(allowed_roles=['owner'])
async def remove_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to remove a channel with button selection."""
    from bot.utils import set_conversation_keyboard, set_conversation_commands
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await set_conversation_keyboard(update, context, user_role)
    
    # Set conversation commands for both message and callback query
    await set_conversation_commands(update, context)
    
    channels = db.get_all_channels()
    if not channels:
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ No channels to remove.")
        else:
            await update.message.reply_text("❌ No channels to remove.")
        return ConversationHandler.END

    # Create buttons for each channel - only show short name as requested
    buttons = []
    for channel in channels:
        channel_display = channel['short_name']  # Only use short name as requested
        # Use channel_id as unique identifier but simplify for callback data
        channel_id_clean = channel['channel_id'].replace('@', '').replace('-', '_')
        buttons.append([InlineKeyboardButton(channel_display, callback_data=f"remove_channel_{channel['channel_id']}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Handle both message and callback query
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        context.user_data['channel_remove_message'] = query.message
        await query.edit_message_text("🗑️ Select channel to remove:", reply_markup=reply_markup)
    else:
        sent_msg = await update.message.reply_text("🗑️ Select channel to remove:", reply_markup=reply_markup)
        context.user_data['channel_remove_message'] = sent_msg
    
    return CONFIRM_REMOVE_CHANNEL

async def confirm_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows confirmation buttons for channel removal."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("remove_channel_"):
        channel_id = query.data.replace("remove_channel_", "")
        channel_info = db.get_channel_info(channel_id)
        channel_name = channel_info.get('short_name', channel_id) if channel_info else channel_id
        
        # Store channel info for final confirmation
        context.user_data['channel_to_remove'] = {'id': channel_id, 'name': channel_name}
        
        # Create confirm/cancel buttons
        buttons = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_channel_remove_{channel_id}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel_channel_remove")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        
        await query.edit_message_text(f"🗑️ Remove {channel_name} channel?", reply_markup=reply_markup)
    
    return CONFIRM_REMOVE_CHANNEL

async def final_channel_removal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles final confirm/cancel for channel removal."""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("confirm_channel_remove_"):
        channel_id = query.data.split("_")[3]
        channel_info = context.user_data.get('channel_to_remove', {})
        channel_name = channel_info.get('name', channel_id)
        
        success = db.remove_channel(channel_id)
        
        if success:
            result_text = f"✅ {channel_name} removed as channel"
        else:
            result_text = f"❌ Failed to remove {channel_name}"
            
        await query.edit_message_text(result_text)
        
    elif query.data == "cancel_channel_remove":
        await query.edit_message_text("❌ Channel removal cancelled.")
    
    from bot.utils import restore_main_keyboard
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    await query.message.reply_text("Done.", reply_markup=keyboard)
    
    context.user_data.clear()
    return ConversationHandler.END


# --- General Management Commands ---

@restricted(allowed_roles=['owner'])
async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides buttons to add or remove admins."""
    keyboard = [
        [InlineKeyboardButton("➕ Add New Admin", callback_data="admin_add")],
        [InlineKeyboardButton("➖ Remove an Admin", callback_data="admin_remove")]
    ]
    await update.message.reply_text("Select an option to manage admins:", reply_markup=InlineKeyboardMarkup(keyboard))

@restricted(allowed_roles=['owner'])
async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provides buttons to add or remove channels."""
    keyboard = [
        [InlineKeyboardButton("➕ Add New Channel", callback_data="channel_add")],
        [InlineKeyboardButton("➖ Remove a Channel", callback_data="channel_remove")]
    ]
    await update.message.reply_text("Select an option to manage channels:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_admin_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle admin management button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_add":
        await query.edit_message_text("Starting add admin process...")
        # Create a fake update object for add_admin_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await add_admin_start(fake_update, context)
    elif query.data == "admin_remove":
        await query.edit_message_text("Starting remove admin process...")
        # Create a fake update object for remove_admin_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await remove_admin_start(fake_update, context)




async def handle_channel_management(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle channel management button callbacks."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "channel_add":
        await query.edit_message_text("Starting add channel process...")
        # Create a fake update object for add_channel_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await add_channel_start(fake_update, context)
    elif query.data == "channel_remove":
        await query.edit_message_text("Starting remove channel process...")
        # Create a fake update object for remove_channel_start since it expects message not callback
        fake_update = type('obj', (object,), {
            'message': query.message,
            'effective_chat': query.message.chat,
            'effective_user': query.from_user
        })()
        await remove_channel_start(fake_update, context)

async def cancel_admin_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel admin management conversation."""
    from bot.utils import restore_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    
    await update.message.reply_text("❌ Admin management cancelled.", reply_markup=keyboard)
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_channel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel channel management conversation."""
    from bot.utils import restore_main_keyboard
    
    user_role = db.get_user_role(update.effective_user.id)
    keyboard = await restore_main_keyboard(update, context, user_role)
    
    await update.message.reply_text("❌ Channel management cancelled.", reply_markup=keyboard)
    context.user_data.clear()
    return ConversationHandler.END

# Conversation Handlers
add_admin_conv = ConversationHandler(
    entry_points=[
        CommandHandler("addadmin", add_admin_start),
        CallbackQueryHandler(add_admin_start, pattern='^admin_add$')
    ],
    states={
        GET_ADMIN_USERID: [MessageHandler(filters.TEXT | filters.FORWARDED, get_admin_userid)],
        GET_ADMIN_SHORT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_admin_short_name)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_admin_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_admin_conversation)
    ],
    per_message=False
)
remove_admin_conv = ConversationHandler(
    entry_points=[
        CommandHandler("removeadmin", remove_admin_start),
        CallbackQueryHandler(remove_admin_start, pattern='^admin_remove$')
    ],
    states={
        CONFIRM_REMOVE_ADMIN: [
            CallbackQueryHandler(confirm_remove_admin, pattern='^remove_admin_.*$'),
            CallbackQueryHandler(final_admin_removal, pattern='^(confirm_admin_remove_.*|cancel_admin_remove)$')
        ],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_admin_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_admin_conversation)
    ],
    per_message=True
)

add_channel_conv = ConversationHandler(
    entry_points=[
        CommandHandler("addchannel", add_channel_start),
        CallbackQueryHandler(add_channel_start, pattern='^channel_add$')
    ],
    states={
        GET_CHANNEL_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_link)],
        GET_CHANNEL_SHORT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_channel_short_name)],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_channel_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_channel_conversation)
    ],
    per_message=False
)

remove_channel_conv = ConversationHandler(
    entry_points=[
        CommandHandler("removechannel", remove_channel_start),
        CallbackQueryHandler(remove_channel_start, pattern='^channel_remove$')
    ],
    states={
        CONFIRM_REMOVE_CHANNEL: [
            CallbackQueryHandler(confirm_remove_channel, pattern='^remove_channel_.*$'),
            CallbackQueryHandler(final_channel_removal, pattern='^(confirm_channel_remove_.*|cancel_channel_remove)$')
        ],
    },
    fallbacks=[
        CommandHandler('cancel', cancel_channel_conversation),
        MessageHandler(filters.Regex("^❌ Cancel$"), cancel_channel_conversation)
    ],
    per_message=True
)


# Main handler list to be imported
owner_handlers = [
    add_admin_conv,
    remove_admin_conv,
    add_channel_conv,
    remove_channel_conv,
    # Manage Admins and Channels
    MessageHandler(filters.Regex("^👥 Manage Admins$"), manage_admins),
    MessageHandler(filters.Regex("^📢 Manage Channels$"), manage_channels),
    CallbackQueryHandler(handle_channel_management, pattern="^channel_remove$")
]
