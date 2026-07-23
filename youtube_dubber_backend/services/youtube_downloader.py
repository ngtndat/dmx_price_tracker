import os
import subprocess
import json
import logging
from pathlib import Path
from youtube_dubber_backend.config import RAW_DIR, AUDIO_DIR

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """Service to handle downloading YouTube videos and extracting audio streams using yt-dlp."""

    @staticmethod
    def extract_info(url: str) -> dict:
        """Fetch video metadata without downloading."""
        cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-warnings",
            url
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            return {
                "title": info.get("title", "Untitled Video"),
                "duration": info.get("duration", 0),
                "uploader": info.get("uploader", "Unknown"),
                "thumbnail": info.get("thumbnail", "")
            }
        except Exception as e:
            logger.error(f"Error fetching YouTube info for {url}: {e}")
            return {
                "title": "Short Story Video",
                "duration": 1800,
                "uploader": "YouTube",
                "thumbnail": ""
            }

    @staticmethod
    def download(url: str, job_id: str) -> dict:
        """Download video (1080p max MP4) and extract WAV audio for ASR processing."""
        video_out_template = str(RAW_DIR / f"{job_id}.%(ext)s")
        audio_out_path = str(AUDIO_DIR / f"{job_id}_raw.wav")

        # 1. Download Video
        video_cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "-o", video_out_template,
            "--no-playlist",
            "--overwrite",
            url
        ]

        logger.info(f"Downloading video from {url} to {video_out_template}")
        subprocess.run(video_cmd, check=True)

        video_file = RAW_DIR / f"{job_id}.mp4"
        if not video_file.exists():
            # Search for downloaded file in case ext differed
            matching = list(RAW_DIR.glob(f"{job_id}.*"))
            if matching:
                video_file = matching[0]

        # 2. Extract Audio (WAV 16kHz mono for Whisper ASR)
        audio_cmd = [
            "ffmpeg",
            "-y",
            "-i", str(video_file),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_out_path
        ]

        logger.info(f"Extracting 16kHz WAV audio to {audio_out_path}")
        subprocess.run(audio_cmd, check=True)

        metadata = YouTubeDownloader.extract_info(url)

        return {
            "video_path": str(video_file),
            "audio_path": audio_out_path,
            "title": metadata["title"],
            "duration": metadata["duration"]
        }
