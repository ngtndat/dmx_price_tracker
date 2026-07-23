import logging
import asyncio
from youtube_dubber_backend.services.youtube_downloader import YouTubeDownloader
from youtube_dubber_backend.services.asr_processor import ASRProcessor
from youtube_dubber_backend.services.translator import StoryTranslator
from youtube_dubber_backend.services.tts_synthesizer import TTSSynthesizer
from youtube_dubber_backend.services.ffmpeg_compositor import FFmpegCompositor
from youtube_dubber_backend.config import SUBTITLES_DIR

logger = logging.getLogger(__name__)

# Global in-memory job status tracker (for single-node / development / fallback execution)
JOBS_DB = {}

def process_dubbing_job(job_id: str, youtube_url: str, target_lang: str, anti_copyright: bool, progress_callback=None):
    """
    Complete end-to-end Dubbing Pipeline:
    1. Download YouTube video & extract audio (15% progress)
    2. Run Chinese Speech-To-Text ASR (35% progress)
    3. Run AI Story Translation CN -> VI/EN (55% progress)
    4. Generate Edge-TTS Dubbed Narration (75% progress)
    5. Render FFmpeg Video Compositing (100% progress)
    """
    def notify(pct: int, stage: str):
        JOBS_DB[job_id] = {
            "job_id": job_id,
            "status": "processing" if pct < 100 else "completed",
            "progress": pct,
            "stage": stage,
            "artifacts": JOBS_DB.get(job_id, {}).get("artifacts", {})
        }
        if progress_callback:
            progress_callback(job_id, pct, stage)

    try:
        # Step 1: Download
        notify(15, "Đang tải video & trích xuất âm thanh từ YouTube...")
        dl_res = YouTubeDownloader.download(youtube_url, job_id)

        # Step 2: ASR Transcription
        notify(35, "Đang nhận dạng tiếng Trung (Speech-To-Text)...")
        segments_cn = ASRProcessor.transcribe_chinese_audio(dl_res["audio_path"], job_id)

        # Step 3: Translation
        notify(55, f"Đang dịch thuật văn phong truyện sang {'Tiếng Việt' if target_lang == 'vi' else 'Tiếng Anh'}...")
        segments_trans = StoryTranslator.translate_segments(segments_cn, target_lang=target_lang)

        # Save translated SRT
        srt_translated_path = str(SUBTITLES_DIR / f"{job_id}_{target_lang}.srt")
        ASRProcessor.save_srt(segments_trans, srt_translated_path)

        # Step 4: TTS Narration
        notify(75, "Đang sinh âm thanh lồng tiếng/thuyết minh (Edge-TTS)...")
        dubbed_audio_path = TTSSynthesizer.generate_dubbed_audio(segments_trans, target_lang, job_id)

        # Step 5: Render Video
        notify(90, "Đang biên tập video & áp dụng bộ lọc chống bản quyền...")
        final_mp4_path = FFmpegCompositor.render_final_video(
            raw_video_path=dl_res["video_path"],
            dubbed_audio_path=dubbed_audio_path,
            srt_path=srt_translated_path,
            job_id=job_id,
            anti_copyright=anti_copyright
        )

        # Complete
        JOBS_DB[job_id]["artifacts"] = {
            "final_mp4": final_mp4_path,
            "srt_translated": srt_translated_path,
            "dubbed_audio": dubbed_audio_path,
            "video_title": dl_res["title"]
        }
        notify(100, "Xử lý thành công! Video đã sẵn sàng tải về.")
        return JOBS_DB[job_id]

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}")
        JOBS_DB[job_id] = {
            "job_id": job_id,
            "status": "failed",
            "progress": 0,
            "stage": f"Lỗi xử lý: {str(e)}",
            "artifacts": {}
        }
        raise e
