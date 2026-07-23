import os
import subprocess
import logging
from youtube_dubber_backend.config import EXPORT_DIR

logger = logging.getLogger(__name__)

class FFmpegCompositor:
    """Video compositing engine supporting Original mode & Anti-Copyright transformations."""

    @staticmethod
    def render_final_video(
        raw_video_path: str,
        dubbed_audio_path: str,
        srt_path: str,
        job_id: str,
        anti_copyright: bool = True
    ) -> str:
        """
        Renders the final MP4 video.
        - anti_copyright = False: Replaces original audio with dubbed audio and burns in subtitles.
        - anti_copyright = True: Applies speed shift (1.03x), horizontal flip, 4% crop, color grading, and audio ducking.
        """
        output_mp4_path = str(EXPORT_DIR / f"{job_id}_final.mp4")
        logger.info(f"Rendering final video for job {job_id}. Anti-copyright mode: {anti_copyright}")

        # Escape path for FFmpeg subtitles filter
        escaped_srt = srt_path.replace("\\", "/").replace(":", "\\:")

        if not anti_copyright:
            # Mode 1: Exact Original Video
            cmd = [
                "ffmpeg",
                "-y",
                "-i", raw_video_path,
                "-i", dubbed_audio_path,
                "-vf", f"subtitles='{escaped_srt}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3'",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_mp4_path
            ]
        else:
            # Mode 2: Anti-Copyright Transform Pipeline
            # 1.03x speed, hflip, crop viền 4%, eq contrast/saturation shift
            vf_filters = (
                f"hflip, "
                f"crop=iw*0.96:ih*0.96:iw*0.02:ih*0.02, "
                f"setpts=PTS/1.03, "
                f"eq=contrast=1.05:saturation=1.08:brightness=0.01, "
                f"subtitles='{escaped_srt}':force_style='FontSize=20,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=3'"
            )
            af_filters = "atempo=1.03, volume=1.2"

            cmd = [
                "ffmpeg",
                "-y",
                "-i", raw_video_path,
                "-i", dubbed_audio_path,
                "-vf", vf_filters,
                "-af", af_filters,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                output_mp4_path
            ]

        try:
            logger.info(f"Executing FFmpeg render command: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            return output_mp4_path

        except Exception as e:
            logger.error(f"FFmpeg render error: {e}")
            # Fallback simple remux command if complex filters encounter hardware issues
            fallback_cmd = [
                "ffmpeg",
                "-y",
                "-i", raw_video_path,
                "-i", dubbed_audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-shortest",
                output_mp4_path
            ]
            subprocess.run(fallback_cmd, check=True)
            return output_mp4_path
