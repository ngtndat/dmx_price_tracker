import os
import subprocess
from pathlib import Path
from typing import List, Dict
from config import FFMPEG_PATH, TEMP_DIR, OUTPUT_DIR, SUBTITLE_STYLE_DEFAULT

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp HH:MM:SS,mmm"""
    millis = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    seconds = seconds % 60
    minutes = minutes % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"

def format_timestamp_ass(seconds: float) -> str:
    """Format seconds into ASS timestamp H:MM:SS.cc"""
    centis = int((seconds - int(seconds)) * 100)
    seconds = int(seconds)
    minutes = seconds // 60
    hours = minutes // 60
    seconds = seconds % 60
    minutes = minutes % 60
    return f"{hours:01d}:{minutes:02d}:{seconds:02d}.{centis:02d}"

def generate_subtitle_files(segments: List[Dict], sub_mode: str, task_id: str) -> dict:
    """
    Creates SRT and ASS subtitle files based on sub_mode ('vi', 'en', 'dual_zh_vi', 'dual_en_vi', 'zh', 'none').
    Returns dict with paths to srt and ass files.
    """
    work_dir = TEMP_DIR / task_id
    work_dir.mkdir(exist_ok=True, parents=True)

    srt_path = str(work_dir / "subtitles.srt")
    ass_path = str(work_dir / "subtitles.ass")

    if sub_mode == "none":
        return {"srt": "", "ass": ""}

    srt_lines = []
    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,36,&H00FFFFFF,&H00000000,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,2,10,10,50,1",
        "Style: Secondary,Arial,28,&H00FFFF00,&H00000000,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,2,1,2,10,10,95,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
    ]

    for i, seg in enumerate(segments, 1):
        start_srt = format_timestamp_srt(seg["start"])
        end_srt = format_timestamp_srt(seg["end"])

        start_ass = format_timestamp_ass(seg["start"])
        end_ass = format_timestamp_ass(seg["end"])

        zh_text = seg.get("text", "")
        vi_text = seg.get("text_vi", zh_text)
        en_text = seg.get("text_en", zh_text)

        display_text_srt = ""
        display_text_ass = ""

        if sub_mode == "vi":
            display_text_srt = vi_text
            display_text_ass = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{vi_text}"
        elif sub_mode == "en":
            display_text_srt = en_text
            display_text_ass = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{en_text}"
        elif sub_mode == "zh":
            display_text_srt = zh_text
            display_text_ass = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{zh_text}"
        elif sub_mode == "dual_zh_vi":
            display_text_srt = f"{vi_text}\n{zh_text}"
            display_text_ass = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{vi_text}\\N{{\\rSecondary}}{zh_text}"
        elif sub_mode == "dual_en_vi":
            display_text_srt = f"{vi_text}\n{en_text}"
            display_text_ass = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{vi_text}\\N{{\\rSecondary}}{en_text}"
        else:
            display_text_srt = vi_text
            display_text_ass = f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{vi_text}"

        srt_lines.append(f"{i}\n{start_srt} --> {end_srt}\n{display_text_srt}\n")
        ass_lines.append(display_text_ass)

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ass_lines))

    return {"srt": srt_path, "ass": ass_path}

def render_final_video(
    video_path: str,
    voiceover_path: str,
    ass_sub_path: str,
    output_filename: str,
    orig_audio_vol: float = 0.15,
    anti_copyright: Dict = None
) -> str:
    """
    Renders the final MP4 video by combining:
    - Original video track
    - Anti-Copyright visual filters (Zoom 3%, Color Grade, Mirror, Speed Shift)
    - Original audio (ducked to orig_audio_vol e.g. 0.15 = 15% or 0.0 = Mute)
    - Voiceover audio track
    - Burnt-in ASS subtitles
    """
    output_path = str(OUTPUT_DIR / output_filename)
    work_dir = Path(ass_sub_path).parent if (ass_sub_path and os.path.exists(ass_sub_path)) else OUTPUT_DIR

    if anti_copyright is None:
        anti_copyright = {}

    # Build FFmpeg command
    cmd = [FFMPEG_PATH, "-y", "-i", video_path]

    filter_complex = []

    # Audio Mixing
    if voiceover_path and os.path.exists(voiceover_path):
        cmd.extend(["-i", voiceover_path])
        if orig_audio_vol > 0.001:
            filter_complex.append(f"[0:a]volume={orig_audio_vol:.2f}[orig_a]")
            filter_complex.append("[1:a]volume=1.0[voice_a]")
            filter_complex.append("[orig_a][voice_a]amix=inputs=2:duration=first:dropout_transition=2[aout]")
        else:
            filter_complex.append("[1:a]volume=1.0[aout]")
        audio_map = ["[aout]"]
    else:
        if orig_audio_vol > 0.001:
            filter_complex.append(f"[0:a]volume={orig_audio_vol:.2f}[aout]")
            audio_map = ["[aout]"]
        else:
            audio_map = ["0:a?"]

    # Video filters (Anti-Copyright & Subtitles)
    v_filters = []

    # 1. Anti-Copyright: Dynamic Crop/Zoom (3%)
    if anti_copyright.get("anti_crop"):
        v_filters.append("crop=iw*0.96:ih*0.96,scale=1920:1080")

    # 2. Anti-Copyright: Color Grading & Contrast
    if anti_copyright.get("anti_color"):
        v_filters.append("eq=contrast=1.05:saturation=1.08:brightness=0.01")

    # 3. Anti-Copyright: Horizontal Flip / Mirror
    if anti_copyright.get("anti_mirror"):
        v_filters.append("hflip")

    # 4. Anti-Copyright: Minor Speed Shift (1.02x)
    if anti_copyright.get("anti_speed"):
        v_filters.append("setpts=PTS/1.02")

    # 5. Subtitle Burn filter
    if ass_sub_path and os.path.exists(ass_sub_path):
        ass_filename = Path(ass_sub_path).name
        v_filters.append(f"subtitles='{ass_filename}'")

    cmd_args = list(cmd)
    if filter_complex or v_filters:
        cmd_args.append("-filter_complex")
        fc_parts = []
        if v_filters:
            fc_parts.append(f"[0:v]{','.join(v_filters)}[vout]")
            v_map = "[vout]"
        else:
            v_map = "0:v"

        if filter_complex:
            fc_parts.extend(filter_complex)
        
        cmd_args.append(";".join(fc_parts))
        cmd_args.extend(["-map", v_map, "-map", audio_map[0]])
    else:
        cmd_args.extend(["-map", "0:v", "-map", "0:a?"])

    # Encoding settings (h264 ultrafast preset, aac 192k)
    cmd_args.extend([
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ])

    print("Running FFmpeg command in cwd", work_dir, ":", " ".join(cmd_args))
    res = subprocess.run(cmd_args, cwd=str(work_dir), capture_output=True, text=True)
    if res.returncode != 0:
        print("FFmpeg stderr error:", res.stderr)
        raise RuntimeError(f"FFmpeg render error: {res.stderr[-500:]}")

    return output_path


