import os
from pathlib import Path

# Base Directory Paths
BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
RAW_DIR = STORAGE_DIR / "raw"
AUDIO_DIR = STORAGE_DIR / "audio"
SUBTITLES_DIR = STORAGE_DIR / "subtitles"
EXPORT_DIR = STORAGE_DIR / "export"

# Create directories if not exist
for dir_path in [STORAGE_DIR, RAW_DIR, AUDIO_DIR, SUBTITLES_DIR, EXPORT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Redis & Celery Config
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Default Voice Models
DEFAULT_VIETNAMESE_VOICE_FEMALE = "vi-VN-HoaiMyNeural"
DEFAULT_VIETNAMESE_VOICE_MALE = "vi-VN-NamMinhNeural"
DEFAULT_ENGLISH_VOICE_FEMALE = "en-US-AnaNeural"
DEFAULT_ENGLISH_VOICE_MALE = "en-US-ChristopherNeural"

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
