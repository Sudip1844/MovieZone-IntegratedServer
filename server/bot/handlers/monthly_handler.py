# Monthly Report Handler for Owner Commands

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
import bot.db as db
from bot.utils import restricted
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@restricted(allowed_roles=['owner'])
async def show_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show monthly report for owner."""
    try:
        # Get current month or specified month
        args = context.args
        
        if args and len(args) >= 2:
            # Manual month/year specified: /monthlyreport 8 2025
            try:
                month = int(args[0])
                year = int(args[1])
            except ValueError:
                await update.message.reply_text("❌ Invalid format. Use: /monthlyreport <month> <year>\nExample: /monthlyreport 8 2025")
                return
        else:
            # Use previous month by default
            year, month = db.get_previous_month_date()
        
        # Validate month and year
        if month < 1 or month > 12:
            await update.message.reply_text("❌ Invalid month. Month must be between 1-12.")
            return
        
        if year < 2020 or year > datetime.now().year + 1:
            await update.message.reply_text("❌ Invalid year.")
            return
        
        await update.message.reply_text("📊 Generating monthly report... Please wait.")
        
        # Generate report
        report = db.generate_monthly_report(year, month)
        
        # Split large reports if needed (Telegram has 4096 char limit)
        if len(report) <= 4096:
            await update.message.reply_text(report, parse_mode='Markdown')
        else:
            # Split the report into chunks
            chunks = [report[i:i+4000] for i in range(0, len(report), 4000)]
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await update.message.reply_text(f"📊 Monthly Report Part {i+1}/{len(chunks)}\n\n{chunk}", parse_mode='Markdown')
                else:
                    await update.message.reply_text(f"📊 Part {i+1}/{len(chunks)}\n\n{chunk}", parse_mode='Markdown')
        
        logger.info(f"Monthly report generated for {month:02d}/{year}")
        
    except Exception as e:
        logger.error(f"Error generating monthly report: {e}")
        await update.message.reply_text(f"❌ Error generating monthly report: {str(e)}")

@restricted(allowed_roles=['owner'])
async def test_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test monthly report generation - for debugging."""
    try:
        current_date = datetime.now()
        year, month = current_date.year, current_date.month
        
        await update.message.reply_text(f"🧪 Testing monthly report for current month {month:02d}/{year}...")
        
        report = db.generate_monthly_report(year, month)
        
        if len(report) <= 4096:
            await update.message.reply_text(report, parse_mode='Markdown')
        else:
            chunks = [report[i:i+4000] for i in range(0, len(report), 4000)]
            for i, chunk in enumerate(chunks):
                await update.message.reply_text(f"🧪 Test Report Part {i+1}\n\n{chunk}", parse_mode='Markdown')
        
        logger.info(f"Test monthly report generated for {month:02d}/{year}")
        
    except Exception as e:
        logger.error(f"Error in test monthly report: {e}")
        await update.message.reply_text(f"❌ Error in test report: {str(e)}")

# Handler list for registration
monthly_handlers = [
    CommandHandler('monthlyreport', show_monthly_report),
    CommandHandler('testmonthlyreport', test_monthly_report),
]