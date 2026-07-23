import os
import subprocess
from pathlib import Path
import yt_dlp
from config import FFMPEG_PATH, TEMP_DIR

def download_video_or_audio(url_or_path: str, task_id: str) -> dict:
    """
    Given a URL or local file path, extracts/downloads the video file and audio WAV file.
    Returns dict: {"video_path": str, "audio_path": str, "title": str}
    """
    work_dir = TEMP_DIR / task_id
    work_dir.mkdir(exist_ok=True, parents=True)

    video_path = work_dir / "input_video.mp4"
    audio_path = work_dir / "input_audio.wav"

    # Check if input is a local file
    if os.path.exists(url_or_path):
        input_file = Path(url_or_path)
        title = input_file.stem
        # Copy or convert to standard mp4 if needed, extract wav audio
        cmd_extract_audio = [
            FFMPEG_PATH, "-y", "-i", str(input_file),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            str(audio_path)
        ]
        subprocess.run(cmd_extract_audio, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {
            "video_path": str(input_file),
            "audio_path": str(audio_path),
            "title": title
        }

    # Options for yt-dlp to bypass YouTube 403 Forbidden / SABR streaming issues
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/bestaudio/best',
        'outtmpl': str(video_path),
        'overwrites': True,
        'ffmpeg_location': str(Path(FFMPEG_PATH).parent),
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'android', 'ios', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
        },
        'nocheckcertificate': True,
        'geo_bypass': True,
        'quiet': False
    }

    title = "downloaded_video"
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_or_path, download=True)
            if info:
                title = info.get('title', 'downloaded_video')
    except Exception as e:
        print(f"Primary download attempt failed: {e}. Retrying with fallback audio/video format...")
        # Fallback options
        ydl_opts['format'] = 'bestaudio/best'
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url_or_path, download=True)
            if info:
                title = info.get('title', 'downloaded_video')


    # Extract 16kHz mono WAV for Whisper
    cmd_extract_audio = [
        FFMPEG_PATH, "-y", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
        str(audio_path)
    ]
    subprocess.run(cmd_extract_audio, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return {
        "video_path": str(video_path),
        "audio_path": str(audio_path),
        "title": title
    }
