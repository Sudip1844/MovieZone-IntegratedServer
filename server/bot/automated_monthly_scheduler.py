# Automated Monthly Report Scheduler
# This runs as a separate background process

import asyncio
import time
import logging
from datetime import datetime, timedelta
from telegram import Bot
import bot.db as db
from bot.config import BOT_TOKEN, OWNER_ID

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedMonthlyReporter:
    def __init__(self, bot_token: str, owner_id: int):
        self.bot = Bot(token=bot_token)
        self.owner_id = owner_id
        self.last_report_date = None
    
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
                text=f"🤖 **Automated Monthly Report**\n\n{report}",
                parse_mode='Markdown'
            )
            
            logger.info(f"Automated monthly report sent for {month:02d}/{year}")
            self.last_report_date = datetime.now().strftime("%Y-%m")
            
        except Exception as e:
            logger.error(f"Failed to send automated monthly report: {e}")
            
            # Send error notification to owner
            try:
                await self.bot.send_message(
                    chat_id=self.owner_id,
                    text=f"❌ Automated monthly report failed: {str(e)}"
                )
            except:
                pass
    
    def is_last_day_of_month(self):
        """Check if today is the last day of the month."""
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        return tomorrow.day == 1
    
    def should_send_report(self):
        """Check if we should send the monthly report."""
        current_month = datetime.now().strftime("%Y-%m")
        
        # Send if it's last day of month and we haven't sent for this month yet
        return (
            self.is_last_day_of_month() and 
            self.last_report_date != current_month
        )
    
    async def run_scheduler(self):
        """Main scheduler loop."""
        logger.info("Automated monthly report scheduler started")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check at 23:59 every day
                if current_time.hour == 23 and current_time.minute >= 59:
                    if self.should_send_report():
                        logger.info("Sending automated monthly report...")
                        await self.send_monthly_report()
                        
                        # Wait until next day to avoid duplicate sends
                        await asyncio.sleep(3600)  # Sleep 1 hour
                
                # Check every 5 minutes
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in automated scheduler: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry

async def start_automated_scheduler():
    """Start the automated monthly reporting system."""
    if not BOT_TOKEN or not OWNER_ID:
        logger.error("BOT_TOKEN or OWNER_ID not configured for automated reports")
        return
    
    reporter = AutomatedMonthlyReporter(BOT_TOKEN, OWNER_ID)
    await reporter.run_scheduler()

if __name__ == "__main__":
    asyncio.run(start_automated_scheduler())