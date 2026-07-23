---
phase: implementation
title: Implementation Guide
description: Technical implementation notes, patterns, and code guidelines
---

# Implementation Guide: YouTube Chinese Story Dubbing Platform (`youtube-chinese-story-dubbing`)

## Code Structure

```
youtube_dubber_backend/
├── config.py                 # Paths, environment variables, default voice settings
├── main.py                   # FastAPI REST API & WebSocket progress endpoint
├── worker.py                 # End-to-end async dubbing task orchestrator
├── requirements.txt          # Python dependencies
├── Dockerfile                # Production Docker build spec
└── services/
    ├── youtube_downloader.py # Ingestion via yt-dlp & FFmpeg 16kHz audio extraction
    ├── asr_processor.py      # Chinese Speech-To-Text Whisper parser
    ├── translator.py         # AI story translator (Chinese -> VI / EN)
    ├── tts_synthesizer.py    # Microsoft Edge-TTS voice narrator
    └── ffmpeg_compositor.py  # FFmpeg video editor (Original vs Anti-Copyright transform)

youtube_dubber_frontend/
├── index.html                # Modern HTML5 SPA interface
├── styles.css                # Glassmorphism dark mode design system
└── app.js                    # REST API & WebSocket client logic

docker-compose.yml            # Production container orchestration
README_DEPLOYMENT.md          # Custom domain & YouTube upload guide
```

## Key Technical Decisions Implemented
1. **Edge-TTS Narration**: Defaulted to `vi-VN-HoaiMyNeural` and `vi-VN-NamMinhNeural` for Vietnamese, and `en-US-AnaNeural` for English. Zero cost for long 20-30 min audiobooks.
2. **Anti-Copyright FFmpeg Filter Stack**: Mode 2 applies `hflip, crop=iw*0.96:ih*0.96:iw*0.02:ih*0.02, setpts=PTS/1.03, eq=contrast=1.05:saturation=1.08:brightness=0.01` alongside dynamic subtitle burn-in.
3. **Real-time WebSockets**: Client receives progress percentage & active stage updates in real time over `ws://.../ws/dub/progress/{job_id}`.

## Verification
- Syntax compilation verified (`py_compile`).
- Structure validated against AI DevKit standards (`npx ai-devkit lint --feature youtube-chinese-story-dubbing`).

