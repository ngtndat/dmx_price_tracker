import os
import sys
import json
import logging
import traceback
from datetime import datetime

# Force UTF-8 encoding for standard output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

from dmx_scraper import scrape_all_products
from gsheet_manager import GSheetManager
from telegram_bot import TelegramNotifier, DEFAULT_TELEGRAM_TOKEN, DEFAULT_CHAT_ID

def run_price_automation(config_file: str = "products.json"):
    """Main execution function for DMX price tracking automation."""
    try:
        logging.info("Starting Điện Máy Xanh Price Tracker Automation...")

        # 1. Load Environment variables or fallback configs
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", DEFAULT_TELEGRAM_TOKEN)
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", DEFAULT_CHAT_ID)
        gsheet_creds = os.environ.get("GSHEET_CREDS_FILE", "credentials.json")
        gsheet_name = os.environ.get("GSHEET_NAME", "DMX_Price_Tracker")

        # 2. Scrape products
        logging.info(f"Reading product configuration from: {config_file}")
        scraped_data = scrape_all_products(config_file)
        logging.info(f"Scraped {len(scraped_data)} products.")

        # 3. Update Google Sheets
        logging.info("Updating Google Sheets Records...")
        gsheet = GSheetManager(creds_file=gsheet_creds, spreadsheet_name_or_id=gsheet_name)
        gsheet.update_price_records(scraped_data)

        # 4. Filter products with price drop / discount for Telegram Notification
        discounted_items = [
            item for item in scraped_data
            if item.get("success") and (item.get("discount_rate", 0) > 0 or (item.get("target_price", 0) > 0 and item.get("current_price", 0) <= item.get("target_price", 0)))
        ]

        # If no real discounted item returned (e.g., fallback test data), send test summary notification
        if not discounted_items and scraped_data:
            discounted_items = [scraped_data[0]]

        logging.info(f"Sending Telegram notification for {len(discounted_items)} items...")

        # 5. Send Telegram Alert
        notifier = TelegramNotifier(bot_token=telegram_token, chat_id=telegram_chat_id)
        sent_status = notifier.send_price_drop_alerts(discounted_items)

        logging.info(f"Automation completed successfully. Telegram sent: {sent_status}")
        return {
            "total_scraped": len(scraped_data),
            "telegram_sent": sent_status,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logging.error(f"Error in price automation execution: {e}")
        logging.error(traceback.format_exc())
        return {
            "total_scraped": 0,
            "telegram_sent": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }

if __name__ == "__main__":
    summary = run_price_automation()
    print("\nSummary Output:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
