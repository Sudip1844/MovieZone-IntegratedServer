# Monthly Reports System for MovieZone Bot

import asyncio
import schedule
import time
import logging
from datetime import datetime
from telegram import Bot
import bot.db as db
from bot.config import BOT_TOKEN, OWNER_ID

# Setup logging
logger = logging.getLogger(__name__)

class MonthlyReporter:
    def __init__(self, bot_token: str, owner_id: int):
        self.bot = Bot(token=bot_token)
        self.owner_id = owner_id
    
    async def send_monthly_report(self):
        """Send monthly report to owner."""
        try:
            # Get previous month data
            year, month = db.get_previous_month_date()
            
            # Generate report
            report = db.generate_monthly_report(year, month)
            
            # Send report to owner
            await self.bot.send_message(
                chat_id=self.owner_id,
                text=report,
                parse_mode='Markdown'
            )
            
            logger.info(f"Monthly report sent for {month:02d}/{year}")
            
        except Exception as e:
            logger.error(f"Failed to send monthly report: {e}")
            
            # Send error notification to owner
            try:
                await self.bot.send_message(
                    chat_id=self.owner_id,
                    text=f"❌ Failed to generate monthly report: {str(e)}"
                )
            except:
                pass
    
    def schedule_monthly_reports(self):
        """Schedule monthly reports to be sent on the last day of each month."""
        # Check daily at 23:59 if it's the last day of month
        schedule.every().day.at("23:59").do(self.check_and_send_monthly_report)
        
        logger.info("Monthly reports scheduled successfully")
    
    def check_and_send_monthly_report(self):
        """Check if today is last day of month and send report."""
        try:
            from datetime import datetime, timedelta
            
            today = datetime.now()
            tomorrow = today + timedelta(days=1)
            
            # Check if tomorrow is first day of next month
            if tomorrow.day == 1:
                logger.info(f"Last day of month detected: {today.strftime('%Y-%m-%d')}")
                self.run_async_report()
            else:
                logger.debug(f"Not last day of month: {today.strftime('%Y-%m-%d')}")
                
        except Exception as e:
            logger.error(f"Error checking month end: {e}")
    
    def run_async_report(self):
        """Run async report function in sync context."""
        try:
            # Create new event loop for async execution
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_monthly_report())
            loop.close()
        except Exception as e:
            logger.error(f"Error in async report execution: {e}")

def start_monthly_reporter():
    """Start the monthly reporting system."""
    if not BOT_TOKEN or not OWNER_ID:
        logger.error("BOT_TOKEN or OWNER_ID not configured for monthly reports")
        return
    
    reporter = MonthlyReporter(BOT_TOKEN, OWNER_ID)
    reporter.schedule_monthly_reports()
    
    # Keep the scheduler running
    while True:
        schedule.run_pending()
        time.sleep(3600)  # Check every hour

if __name__ == "__main__":
    start_monthly_reporter()