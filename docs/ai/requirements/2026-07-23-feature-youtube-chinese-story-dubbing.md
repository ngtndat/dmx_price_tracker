---
phase: requirements
title: Requirements & Problem Understanding
description: Clarify the problem space, gather requirements, and define success criteria
---

# Requirements & Problem Understanding: YouTube Chinese Story Dubbing Platform (`youtube-chinese-story-dubbing`)

## Problem Statement
**What problem are we solving?**
- Content creators want to convert Chinese short story videos (20-30 minutes long) on YouTube into localized English or Vietnamese versions with accurate storytelling translation, high-quality audio dubbing/narration, custom subtitles, and video visual modifications for YouTube re-uploading without manual video editing friction.

## Goals & Objectives
**What do we want to achieve?**
- **Primary Goals**:
  1. Full-stack Web Application with input for YouTube video URLs.
  2. Automated pipeline: Download video/audio -> Speech-To-Text (ASR/Whisper) -> AI Literary Translation (CN -> VI/EN) -> Text-To-Speech (TTS/Dubbing) -> Video re-assembly & editing -> Export ready MP4 & SRT/VTT.
  3. User options:
     - Target language selection: Vietnamese (Phụ đề / Lồng tiếng / Thuyết minh) or English.
     - Video visual modification toggle: Original video vs Anti-copyright modified video (speed adjustments, color grade, frame flip, dynamic subtitle burn-in, background music mixing).
  4. Production-ready architecture for custom domain deployment and scaled processing.

- **Non-Goals (v1)**:
  - Full real-time live streaming translation.
  - Manual frame-by-frame 3D animation generation.

## Key Workflows
1. **Input Phase**: User pastes YouTube URL, selects Target Language (VI / EN), output mode (Subtitles only, Voiceover/Thuyết minh, Full Dubbing/Lồng tiếng), and Video Modification preferences.
2. **Processing Phase**: Async background task handles video download, audio separation, ASR timestamp alignment, LLM translation (with story/literary prompts), TTS voice generation, audio ducking, and video rendering.
3. **Review & Export Phase**: Interactive web preview with audio track switcher, subtitle editor, video download button, and YouTube export status.

## Success Criteria
- Accurately processes 20-30 minute YouTube videos in under 5 minutes execution time (async pipeline).
- Natural-sounding Vietnamese / English TTS voices suitable for audiobooks/stories.
- Clean MP4 output compatible with YouTube video upload guidelines.

## Decisions & Architectural Choices
- **[DECIDED] Decision 1: Voice & Dubbing Engine Strategy**
  - **Chosen Strategy**: Option 1 - Hybrid Voice Architecture (Edge-TTS default for free, unlimited 20-30 min Vietnamese/English story narration + optional Azure Neural / OpenAI Audio API integration for premium voices).
  - **Rationale**: High-quality natural Vietnamese (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`) & English voices without API cost limits for long 20-30 minute audiobooks/stories.

- **[DECIDED] Decision 2: Video Processing & Anti-Copyright Engine Strategy**
  - **Chosen Strategy**: Option A - Multi-stage FFmpeg Pipeline with dual-mode toggle.
  - **Rationale**: Support both exact original clip output AND anti-copyright visual transformations (1.02x-1.04x speed adjustment, horizontal flip, 3-5% margin cropping, subtle color grading shift, ambient background music ducking). Renders 20-30 min 1080p HD videos in under 2 minutes without heavy GPU server requirements.

- **[DECIDED] Decision 3: Backend Service & Async Job Queue Architecture**
  - **Chosen Strategy**: Option A - Python FastAPI + Celery/Redis Job Queue + WebSocket Real-time Progress.
  - **Rationale**: Optimal integration with Python AI libraries (Whisper, Edge-TTS, FFmpeg, LLM SDKs), smooth real-time progress reporting for long 20-30 min jobs, easy Docker packaging for domain deployment.

## Detailed Requirements Matrix

### 1. Functional Requirements
- **YouTube URL Ingestion**: Validate, extract metadata, and download audio/video streams via `yt-dlp`.
- **Speech-to-Text & Alignment**: Extract Chinese audio, run Whisper ASR, obtain line-by-line timestamped SRT captions.
- **Story Translation Engine**: Use LLMs (Gemini / OpenAI API) with custom prompts optimized for Vietnamese / English story literary style (văn phong truyện ngắn/audiobook).
- **TTS Narration & Dubbing**: Generate high-fidelity narration in Vietnamese/English using Edge-TTS voices with pitch and rate controls.
- **Audio Mixing & Ducking**: Separate original audio into speech and background music (or mix new royalty-free background audio under voiceover).
- **Video Transformation**: Toggle between exact original clip and anti-copyright mode (speed, flip, color grading, margins).
- **Subtitles**: Support soft SRT/VTT export + burned-in dynamic styled subtitles.
- **Download & Export**: Provide HD MP4 video download and SRT/VTT subtitle download.

### 2. User Experience Requirements
- Modern, high-aesthetic web interface with glassmorphism/dark mode design.
- Input panel with URL validation, target language selector (VI/EN), voice selector, dubbing mode (Subtitle only, Narration/Thuyết minh, Full Dubbing/Lồng tiếng), and Anti-Copyright video toggle.
- Live progress timeline (% complete, current stage description).
- Dual-player preview (original vs dubbed video) with track switcher.

### 3. Non-Functional Requirements
- **Performance**: Process 20-30 min YouTube video in under 3 minutes total runtime.
- **Scalability**: Async workers scale horizontally via Redis Celery queues.
- **Deployment**: Production Docker compose stack ready for custom domain and Nginx/Certbot SSL deployment.

