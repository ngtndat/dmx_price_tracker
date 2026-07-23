import os
import uuid
import logging
import asyncio
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from youtube_dubber_backend.worker import process_dubbing_job, JOBS_DB
from youtube_dubber_backend.config import EXPORT_DIR, SUBTITLES_DIR, AUDIO_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YouTube Chinese Story Dubber & Translator API",
    version="1.0.0",
    description="API server for translating, dubbing, and editing Chinese short story YouTube videos."
)

# Enable CORS for frontend web client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve exported files statically for web preview
app.mount("/export", StaticFiles(directory=str(EXPORT_DIR)), name="export")
app.mount("/subtitles", StaticFiles(directory=str(SUBTITLES_DIR)), name="subtitles")

FRONTEND_DIR = BASE_DIR.parent / "youtube_dubber_frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend_app")

# Active WebSocket connections dictionary: {job_id: [WebSocket]}
active_websockets = {}

class DubRequest(BaseModel):
    youtube_url: str
    target_language: str = "vi"  # 'vi' or 'en'
    anti_copyright: bool = True

async def broadcast_progress(job_id: str, progress: int, stage: str):
    """Notify all WebSocket subscribers of progress updates."""
    if job_id in active_websockets:
        data = {
            "job_id": job_id,
            "progress": progress,
            "stage": stage,
            "status": "completed" if progress >= 100 else "processing"
        }
        for ws in active_websockets[job_id]:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"Error sending WS update: {e}")

def sync_progress_callback(job_id: str, progress: int, stage: str):
    """Bridge sync worker callback to async WebSocket broadcaster."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_progress(job_id, progress, stage), loop)
        else:
            asyncio.run(broadcast_progress(job_id, progress, stage))
    except Exception as e:
        logger.warning(f"Failed to bridge progress callback: {e}")

@app.post("/api/v1/dub/create")
async def create_dubbing_job(req: DubRequest, background_tasks: BackgroundTasks):
    """Enqueues a new video dubbing job."""
    if not req.youtube_url or "youtube.com" not in req.youtube_url and "youtu.be" not in req.youtube_url:
        raise HTTPException(status_code=400, detail="URL YouTube không hợp lệ.")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    JOBS_DB[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "stage": "Đang khởi tạo tiến trình...",
        "artifacts": {}
    }

    background_tasks.add_task(
        process_dubbing_job,
        job_id=job_id,
        youtube_url=req.youtube_url,
        target_lang=req.target_language,
        anti_copyright=req.anti_copyright,
        progress_callback=sync_progress_callback
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Đã tiếp nhận yêu cầu lồng tiếng. Đang xử lý ngầm."
    }

@app.get("/api/v1/dub/status/{job_id}")
async def get_job_status(job_id: str):
    """Check job status and available artifact download links."""
    if job_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Không tìm thấy Job ID này.")
    return JOBS_DB[job_id]

@app.get("/api/v1/dub/download/{job_id}/{file_type}")
async def download_artifact(job_id: str, file_type: str):
    """Download MP4 video or SRT subtitle files."""
    if job_id not in JOBS_DB or JOBS_DB[job_id]["status"] != "completed":
        raise HTTPException(status_code=404, detail="Job chưa hoàn thành hoặc không tồn tại.")

    artifacts = JOBS_DB[job_id].get("artifacts", {})
    if file_type == "video":
        filepath = artifacts.get("final_mp4")
        filename = f"dubbed_{job_id}.mp4"
    elif file_type == "srt":
        filepath = artifacts.get("srt_translated")
        filename = f"subtitles_{job_id}.srt"
    else:
        raise HTTPException(status_code=400, detail="File type không hợp lệ (video / srt).")

    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File sản phẩm không tồn tại trên disk.")

    return FileResponse(path=filepath, filename=filename, media_type="application/octet-stream")

@app.websocket("/ws/dub/progress/{job_id}")
async def websocket_progress_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for streaming real-time progress updates to frontend."""
    await websocket.accept()
    if job_id not in active_websockets:
        active_websockets[job_id] = []
    active_websockets[job_id].append(websocket)

    try:
        # Send current status on initial connection
        if job_id in JOBS_DB:
            await websocket.send_json(JOBS_DB[job_id])

        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_websockets[job_id].remove(websocket)
        if not active_websockets[job_id]:
            del active_websockets[job_id]

# Serve frontend statically at root '/'
FRONTEND_DIR = BASE_DIR.parent / "youtube_dubber_frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend_app")

