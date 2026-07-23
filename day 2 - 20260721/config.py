import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Google Sheets Configuration ---
# Match service account file in day 2 folder
SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE", 
    str(BASE_DIR / "graphic-mission-503107-h2-cc040963a75b.json")
)
# Google Sheet ID (User can set in .env or default test sheet)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1tcmSZmiOwbiOjpEi0jM_lxeEeTkUcITWJ6-jTvLri88")

# --- Telegram Bot Configuration ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Scraping Configuration ---
# Price drop percentage threshold to trigger urgent Telegram Alert (e.g., 2.0 = 2% drop)
PRICE_DROP_ALERT_THRESHOLD_PCT = float(os.getenv("PRICE_DROP_ALERT_THRESHOLD_PCT", "1.0"))

# Target Điện Máy Xanh URLs to scan (Default list of main competitor categories / products)
DEFAULT_DMX_TARGETS = [
    {
        "category": "Máy Lọc Không Khí",
        "url": "https://www.dienmayxanh.com/may-loc-khong-khi"
    },
    {
        "category": "Máy Lạnh / Điều Hòa",
        "url": "https://www.dienmayxanh.com/may-lanh"
    },
    {
        "category": "Tủ Lạnh",
        "url": "https://www.dienmayxanh.com/tu-lanh"
    },
    {
        "category": "Tivi",
        "url": "https://www.dienmayxanh.com/tivi"
    },
    {
        "category": "Máy Giặt",
        "url": "https://www.dienmayxanh.com/may-giat"
    }
]

# Standard request headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cache-Control": "no-cache",
}
