---
phase: testing
title: Testing Strategy
description: Define testing approach, test cases, and quality assurance
---

# Testing Strategy: YouTube Chinese Story Dubbing Platform (`youtube-chinese-story-dubbing`)

## Test Coverage Goals
- **Unit & Pipeline Test Target**: 100% logic coverage for downing, ASR parser, translation prompt builder, Edge-TTS audio generator, and FFmpeg command builder.
- **Integration Scope**: End-to-end processing pipeline from YouTube URL to MP4/SRT artifact output.

## Unit & Integration Test Checklist

### 1. Ingestion & YouTube Downloader
- [ ] Test YouTube URL validation (valid vs invalid URLs).
- [ ] Test `yt-dlp` metadata extraction and stream resolution.

### 2. ASR & Translation Engine
- [ ] Test Whisper output parser (converting Chinese timestamped text to SRT data structures).
- [ ] Test LLM story translation prompt (preserves timestamp ranges and literary story tone).

### 3. Audio & Voice Synthesizer (Edge-TTS)
- [ ] Test Vietnamese voice generation (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`).
- [ ] Test English voice generation (`en-US-AnaNeural`).
- [ ] Test audio timestamp synchronization.

### 4. FFmpeg Video Compositor
- [ ] Test Mode 1 (Original video assembly + audio replace + SRT burn-in).
- [ ] Test Mode 2 (Anti-Copyright: speed 1.03x, hflip, color shift, margin crop, background music ducking).

### 5. API & WebSocket Status Streamer
- [ ] Test `POST /api/v1/dub/create` endpoint.
- [ ] Test WebSocket connection & progress updates (0% -> 100%).
- [ ] Test download endpoints for MP4 and SRT files.

## End-to-End Test Scenario
- [ ] Paste sample 20-30 min YouTube Chinese story URL -> Select Vietnamese + Full Dubbing + Anti-Copyright On -> Verify progress bar updates -> Inspect output video playback quality & SRT accuracy.

