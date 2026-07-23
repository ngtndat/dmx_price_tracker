import config
import asyncio
import os
import uuid
import threading
from typing import Dict, List, Optional
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from config import BASE_DIR, OUTPUT_DIR, TEMP_DIR, VOICE_PRESETS

from core.downloader import download_video_or_audio
from core.transcriber import transcribe_audio
from core.translator import translate_dual
from core.tts_engine import generate_voiceover_track
from core.video_processor import generate_subtitle_files, render_final_video
from core.metadata_gen import generate_youtube_metadata

app = FastAPI(title="YouTube Chinese Short Drama Translator Studio")

# Mount Static & Template files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Task state storage in memory
import json

TASKS: Dict[str, Dict] = {}

def save_task_to_disk(task_id: str):
    """Save task info to JSON file in temp directory for resilience across server restarts."""
    if task_id not in TASKS:
        return
    task_dir = TEMP_DIR / task_id
    task_dir.mkdir(exist_ok=True, parents=True)
    task_file = task_dir / "task_info.json"
    try:
        with open(task_file, "w", encoding="utf-8") as f:
            json.dump(TASKS[task_id], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving task {task_id} to disk: {e}")

def get_or_restore_task(task_id: str) -> Optional[Dict]:
    """Retrieve task from memory or restore from disk / temp files."""
    if task_id in TASKS:
        return TASKS[task_id]

    task_dir = TEMP_DIR / task_id
    task_file = task_dir / "task_info.json"
    if task_file.exists():
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                TASKS[task_id] = data
                return data
        except Exception as e:
            print(f"Error loading task_info.json for {task_id}: {e}")

    # Fallback auto-recovery: If video file exists on disk, recover task
    video_file = task_dir / "input_video.mp4"
    if video_file.exists():
        audio_file = task_dir / "input_audio.wav"
        recovered_data = {
            "task_id": task_id,
            "status": "transcribed",
            "progress": 80,
            "message": "Đã khôi phục công việc từ dữ liệu lưu trữ.",
            "req": {"sub_lang": "vi", "voice_lang": "vi", "voice_key": "female_1", "orig_audio_vol": 0.0},
            "media_info": {
                "video_path": str(video_file),
                "audio_path": str(audio_file) if audio_file.exists() else str(video_file),
                "title": "Truyện Ngắn Trung Quốc"
            },
            "segments": []
        }
        TASKS[task_id] = recovered_data
        save_task_to_disk(task_id)
        return recovered_data

    return None

class ProcessRequest(BaseModel):
    source: str
    sub_lang: str = "vi"         # 'vi', 'en', 'dual_zh_vi', 'dual_en_vi', 'zh', 'none'
    voice_lang: str = "vi"       # 'vi', 'en', 'none'
    voice_key: str = "female_1"  # 'female_1', 'male_1', etc.
    tts_rate: str = "0%"         # '-15%', '-8%', '0%', '+8%'
    orig_audio_vol: float = 0.15
    anti_copyright: Optional[Dict] = None

class RenderRequest(BaseModel):
    task_id: str
    segments: List[Dict]
    tts_rate: Optional[str] = "0%"
    anti_copyright: Optional[Dict] = None

def background_process_pipeline(task_id: str, req: ProcessRequest):
    try:
        TASKS[task_id]["status"] = "processing"
        TASKS[task_id]["progress"] = 10
        TASKS[task_id]["message"] = "Đang tải video & trích xuất file âm thanh..."
        save_task_to_disk(task_id)

        # 1. Download & extract audio
        media_info = download_video_or_audio(req.source, task_id)
        TASKS[task_id]["media_info"] = media_info

        # 2. Transcribe speech using Whisper
        TASKS[task_id]["progress"] = 35
        TASKS[task_id]["message"] = "Đang nhận dạng lời thoại tiếng Trung bằng AI Whisper..."
        save_task_to_disk(task_id)
        segments = transcribe_audio(media_info["audio_path"], model_size="base")

        # 3. Translate to Vietnamese and English
        TASKS[task_id]["progress"] = 65
        TASKS[task_id]["message"] = "Đang dịch kịch bản hội thoại sang Tiếng Việt & Tiếng Anh..."
        save_task_to_disk(task_id)
        segments = translate_dual(segments)

        TASKS[task_id]["segments"] = segments
        TASKS[task_id]["progress"] = 80
        TASKS[task_id]["status"] = "transcribed"
        TASKS[task_id]["message"] = "Đã dịch xong kịch bản! Hãy kiểm tra và hiệu chỉnh trên bảng kịch bản."
        save_task_to_disk(task_id)

    except Exception as e:
        print(f"Task {task_id} error: {e}")
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["message"] = str(e)
        save_task_to_disk(task_id)

@app.get("/")
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "voices": VOICE_PRESETS})

@app.get("/api/voices")
def get_voices():
    return VOICE_PRESETS

@app.post("/api/process-video")
def start_processing(req: ProcessRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())[:8]
    TASKS[task_id] = {
        "task_id": task_id,
        "status": "pending",
        "progress": 0,
        "message": "Đang khởi tạo công việc...",
        "req": req.dict(),
        "segments": []
    }
    save_task_to_disk(task_id)
    background_tasks.add_task(background_process_pipeline, task_id, req)
    return {"task_id": task_id}

@app.get("/api/task-status/{task_id}")
def get_task_status(task_id: str):
    task_data = get_or_restore_task(task_id)
    if not task_data:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task_data

@app.post("/api/render-video")
def render_video_endpoint(req: RenderRequest):
    task_id = req.task_id
    task_data = get_or_restore_task(task_id)
    if not task_data:
        return JSONResponse(status_code=400, content={"error": f"Không tìm thấy công việc (Task ID: {task_id}). Vui lòng bấm 'Bắt Đầu' lại."})

    try:
        process_req = task_data.get("req", {})
        media_info = task_data.get("media_info", {})
        segments = req.segments

        if not media_info or "video_path" not in media_info or not os.path.exists(media_info["video_path"]):
            return JSONResponse(status_code=400, content={"error": "File video gốc không tồn tại hoặc đã bị xóa. Vui lòng bấm 'Bắt Đầu' lại."})

        sub_lang = process_req.get("sub_lang", "vi")
        voice_lang = process_req.get("voice_lang", "vi")
        voice_key = process_req.get("voice_key", "female_1")
        orig_audio_vol = process_req.get("orig_audio_vol", 0.15)
        tts_rate = req.tts_rate or process_req.get("tts_rate", "0%")
        anti_copyright = req.anti_copyright or process_req.get("anti_copyright", {})

        voiceover_path = ""
        # 1. Generate Voiceover track if requested
        if voice_lang in ["vi", "en"]:
            voiceover_path = generate_voiceover_track(segments, voice_lang, voice_key, task_id, tts_rate=tts_rate)

        # 2. Generate Subtitle ASS/SRT files
        sub_files = generate_subtitle_files(segments, sub_lang, task_id)

        # 3. Render final MP4
        output_filename = f"translated_video_{task_id}.mp4"
        final_mp4 = render_final_video(
            video_path=media_info["video_path"],
            voiceover_path=voiceover_path,
            ass_sub_path=sub_files.get("ass", ""),
            output_filename=output_filename,
            orig_audio_vol=orig_audio_vol,
            anti_copyright=anti_copyright
        )

        video_url = f"/output/{output_filename}"

        # 4. Generate YouTube Metadata suggestions
        title_hint = media_info.get("title", "Truyện Ngắn Trung Quốc")
        metadata = generate_youtube_metadata(title_hint, segments, lang=voice_lang if voice_lang != "none" else "vi")

        TASKS[task_id]["status"] = "completed"
        TASKS[task_id]["video_url"] = video_url
        TASKS[task_id]["metadata"] = metadata
        save_task_to_disk(task_id)

        return {
            "status": "completed",
            "video_url": video_url,
            "metadata": metadata
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"error": f"Lỗi Render Video: {str(e)}"})



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

