import os
from pathlib import Path
import imageio_ffmpeg

# Paths
BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
OUTPUT_DIR = BASE_DIR / "output"

TEMP_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# FFmpeg Executable path from imageio_ffmpeg or system path
def get_ffmpeg_path():
    try:
        path = imageio_ffmpeg.get_ffmpeg_exe()
        if os.path.exists(path):
            return path
    except Exception:
        pass
    return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()

# Automatically add FFmpeg binary folder to OS PATH so subprocess & pydub detect it cleanly
ffmpeg_dir = str(Path(FFMPEG_PATH).parent)
if ffmpeg_dir and os.path.exists(ffmpeg_dir):
    os.environ["PATH"] = ffmpeg_dir + os.path.pathsep + os.environ.get("PATH", "")

import warnings
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        import pydub
        pydub.AudioSegment.converter = FFMPEG_PATH
        pydub.AudioSegment.ffmpeg = FFMPEG_PATH
except Exception:
    pass



# Edge TTS Voice presets
VOICE_PRESETS = {
    "vi": {
        "female_1": {"name": "vi-VN-HoaiMyNeural", "label": "Tiếng Việt - Nữ (Hoài My - Truyền cảm)"},
        "male_1": {"name": "vi-VN-NamMinhNeural", "label": "Tiếng Việt - Nam (Nam Minh - Ấm áp)"}
    },
    "en": {
        "female_1": {"name": "en-US-AnaNeural", "label": "English - Female (Ana - Clear)"},
        "female_2": {"name": "en-US-JennyNeural", "label": "English - Female (Jenny - Natural)"},
        "male_1": {"name": "en-US-GuyNeural", "label": "English - Male (Guy - Deep)"},
        "male_2": {"name": "en-US-ChristopherNeural", "label": "English - Male (Christopher - Storytelling)"}
    }
}

# Default Subtitle Style (ASS format styling)
# FontName, FontSize, PrimaryColour (&H00FFFFFF = white), OutlineColour (&H00000000 = black outline), BackColour, Bold, Italic, Outline, Shadow, Alignment (2=Bottom Center), MarginV
SUBTITLE_STYLE_DEFAULT = (
    "Fontname=Arial,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
    "BackColour=&H80000000,Bold=1,Italic=0,Outline=2,Shadow=1,Alignment=2,MarginV=30"
)
