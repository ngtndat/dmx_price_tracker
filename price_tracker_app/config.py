import os
from dotenv import load_dotenv

# Load from .env in parent directory (fallback to same dir)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(_env_path)

class Config:
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "8000"))
    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

    # Affiliate
    ACCESSTRADE_PUB_ID = os.getenv("ACCESSTRADE_PUB_ID", "")
    INVOLVE_ASIA_PUB_ID = os.getenv("INVOLVE_ASIA_PUB_ID", "")
    SHOPEE_AFFILIATE_TAG = os.getenv("SHOPEE_AFFILIATE_TAG", "")
    LAZADA_AFFILIATE_TAG = os.getenv("LAZADA_AFFILIATE_TAG", "")
    TRAVELOKA_AFFILIATE_TAG = os.getenv("TRAVELOKA_AFFILIATE_TAG", "")
    TRIPDOTCOM_AFFILIATE_TAG = os.getenv("TRIPDOTCOM_AFFILIATE_TAG", "")
