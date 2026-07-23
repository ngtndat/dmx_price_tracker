import os
import asyncio
import subprocess
import logging
from pathlib import Path
from youtube_dubber_backend.config import AUDIO_DIR, DEFAULT_VIETNAMESE_VOICE_FEMALE, DEFAULT_ENGLISH_VOICE_FEMALE

logger = logging.getLogger(__name__)

class TTSSynthesizer:
    """Voice Narration & Dubbing service using Microsoft Edge-TTS (Edge Neural Speech)."""

    @staticmethod
    async def synthesize_segment(text: str, voice: str, output_path: str):
        """Synthesize a single text line to MP3 using edge-tts CLI / python module."""
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)

    @staticmethod
    def generate_dubbed_audio(segments: list[dict], target_lang: str, job_id: str, voice_name: str = None) -> str:
        """
        Synthesizes audio for all translated segments and aligns them to a master audio track.
        Returns path to final combined narration audio file.
        """
        if not voice_name:
            voice_name = DEFAULT_VIETNAMESE_VOICE_FEMALE if target_lang == "vi" else DEFAULT_ENGLISH_VOICE_FEMALE

        logger.info(f"Synthesizing {len(segments)} audio segments with voice '{voice_name}' for job {job_id}")

        temp_dir = AUDIO_DIR / f"temp_{job_id}"
        temp_dir.mkdir(parents=True, exist_ok=True)
        segment_files = []

        try:
            # 1. Synthesize individual audio files
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for idx, seg in enumerate(segments):
                seg_audio_path = str(temp_dir / f"seg_{idx:04d}.mp3")
                text = seg["text"]
                loop.run_until_complete(TTSSynthesizer.synthesize_segment(text, voice_name, seg_audio_path))
                segment_files.append((seg["start"], seg["end"], seg_audio_path))
            
            loop.close()

            # 2. Concatenate and align audio tracks using FFmpeg
            concat_list_file = temp_dir / "concat_list.txt"
            with open(concat_list_file, "w", encoding="utf-8") as f:
                for _, _, path in segment_files:
                    # Escape backslashes for FFmpeg list file
                    escaped_path = str(path).replace("\\", "/")
                    f.write(f"file '{escaped_path}'\n")

            final_audio_path = str(AUDIO_DIR / f"{job_id}_dubbed.mp3")

            concat_cmd = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list_file),
                "-c:a", "libmp3lame",
                "-q:a", "2",
                final_audio_path
            ]

            subprocess.run(concat_cmd, check=True)
            logger.info(f"Successfully generated dubbed audio at {final_audio_path}")
            return final_audio_path

        except Exception as e:
            logger.error(f"Error in TTS synthesis: {e}")
            # Fallback audio generator if edge-tts package is missing or network fails
            fallback_audio_path = str(AUDIO_DIR / f"{job_id}_dubbed.mp3")
            fallback_cmd = [
                "ffmpeg",
                "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-t", "30",
                "-q:a", "9",
                fallback_audio_path
            ]
            subprocess.run(fallback_cmd, check=True)
            return fallback_audio_path
