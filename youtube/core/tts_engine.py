import config
import asyncio
import os
import subprocess
from pathlib import Path
from typing import List, Dict
import edge_tts
from pydub import AudioSegment
from config import FFMPEG_PATH, TEMP_DIR, VOICE_PRESETS


async def generate_single_tts(text: str, voice_name: str, output_path: str):
    """
    Generate TTS audio for a single sentence using edge-tts.
    """
    communicate = edge_tts.Communicate(text, voice_name)
    await communicate.save(output_path)

def adjust_audio_speed(input_path: str, output_path: str, speed_factor: float):
    """
    Adjust audio speed using ffmpeg atempo filter.
    speed_factor > 1.0 speeds up audio (makes it shorter).
    """
    # atempo filter supports values between 0.5 and 2.0
    speed_factor = max(0.5, min(speed_factor, 2.0))
    cmd = [
        FFMPEG_PATH, "-y", "-i", input_path,
        "-filter:a", f"atempo={speed_factor:.2f}",
        output_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

async def batch_generate_tts(tasks_list: List[Dict], voice_name: str, tts_rate: str = "0%", max_concurrency: int = 10):
    """
    Generate all TTS audio clips with bounded concurrency (default max 10) to prevent 
    Windows socket / file descriptor exhaustions (too many file descriptors in select()).
    Supports custom tts_rate (e.g. '-10%', '-15%', '+10%').
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def task_wrapper(seg_id: int, text: str, raw_mp3_file: str, raw_wav_file: str):
        async with semaphore:
            try:
                communicate = edge_tts.Communicate(text, voice_name, rate=tts_rate)
                await communicate.save(raw_mp3_file)
                if os.path.exists(raw_mp3_file) and os.path.getsize(raw_mp3_file) > 0:
                    cmd_conv = [
                        FFMPEG_PATH, "-y", "-i", raw_mp3_file,
                        "-acodec", "pcm_s16le", "-ar", "24000", "-ac", "1",
                        raw_wav_file
                    ]
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        lambda: subprocess.run(cmd_conv, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    )
            except Exception as e:
                print(f"TTS Error for seg {seg_id}: {e}")

    await asyncio.gather(*[
        task_wrapper(item["id"], item["text"], item["raw_mp3_file"], item["raw_wav_file"])
        for item in tasks_list
    ])

def run_async_safe(coro):
    """Safely run async coroutine from sync context using Windows Proactor loop on Windows"""
    import sys
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except Exception:
            pass

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            future = executor.submit(lambda: asyncio.run(coro))
            return future.result()
    else:
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()


def generate_voiceover_track(segments: List[Dict], lang: str, voice_key: str, task_id: str, tts_rate: str = "0%") -> str:
    """
    Generates a full synchronized voiceover audio file matching the video segment timestamps.
    Returns path to the combined voiceover WAV file.
    """
    work_dir = TEMP_DIR / task_id / "tts"
    work_dir.mkdir(exist_ok=True, parents=True)

    # Determine voice name
    preset_dict = VOICE_PRESETS.get(lang, VOICE_PRESETS["vi"])
    voice_info = preset_dict.get(voice_key, list(preset_dict.values())[0])
    voice_name = voice_info["name"]

    text_key = f"text_{lang}"

    if not segments:
        return ""
    
    # Prepare TTS task list
    tts_tasks = []
    for seg in segments:
        text = seg.get(text_key, seg.get("text", "")).strip()
        if not text:
            continue
        seg_id = seg["id"]
        raw_mp3_file = str(work_dir / f"seg_{seg_id}_raw.mp3")
        raw_wav_file = str(work_dir / f"seg_{seg_id}_raw.wav")
        tts_tasks.append({
            "id": seg_id,
            "text": text,
            "raw_mp3_file": raw_mp3_file,
            "raw_wav_file": raw_wav_file,
            "seg": seg
        })

    if not tts_tasks:
        return ""

    # Concurrently generate all TTS audio files with custom rate and convert to WAV
    run_async_safe(batch_generate_tts(tts_tasks, voice_name, tts_rate=tts_rate))

    max_time = max(seg["end"] for seg in segments) + 2.0
    master_audio = AudioSegment.silent(duration=int(max_time * 1000))

    for item in tts_tasks:
        seg = item["seg"]
        seg_id = item["id"]
        raw_wav_file = item["raw_wav_file"]
        proc_wav_file = str(work_dir / f"seg_{seg_id}_proc.wav")

        if not os.path.exists(raw_wav_file) or os.path.getsize(raw_wav_file) == 0:
            continue

        start_ms = int(seg["start"] * 1000)
        dur_target_sec = max(0.5, seg["end"] - seg["start"])

        # Load WAV directly without calling ffprobe
        audio_seg = AudioSegment.from_wav(raw_wav_file)
        actual_dur_sec = len(audio_seg) / 1000.0

        if actual_dur_sec > (dur_target_sec * 1.15):
            speed_ratio = actual_dur_sec / dur_target_sec
            try:
                adjust_audio_speed(raw_wav_file, proc_wav_file, speed_ratio)
                if os.path.exists(proc_wav_file):
                    audio_seg = AudioSegment.from_wav(proc_wav_file)
            except Exception as e:
                print(f"Speed adjustment failed for seg {seg_id}: {e}")

        master_audio = master_audio.overlay(audio_seg, position=start_ms)

    final_voiceover_path = str(TEMP_DIR / task_id / f"voiceover_{lang}.wav")
    master_audio.export(final_voiceover_path, format="wav")
    return final_voiceover_path



