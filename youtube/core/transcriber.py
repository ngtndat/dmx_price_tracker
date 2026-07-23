import os
from typing import List, Dict

def transcribe_audio(audio_path: str, model_size: str = "base") -> List[Dict]:
    """
    Transcribes Chinese audio using faster-whisper.
    Returns list of dicts: [{"id": 1, "start": 0.5, "end": 2.3, "text": "你好"}, ...]
    """
    try:
        from faster_whisper import WhisperModel
        # Device auto selection (cpu with INT8 or float32 for maximum compatibility)
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        segments, info = model.transcribe(
            audio_path,
            language="zh",
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )

        results = []
        for i, segment in enumerate(segments, 1):
            text = segment.text.strip()
            if text:
                results.append({
                    "id": i,
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": text
                })
        return results

    except Exception as e:
        print(f"Faster-whisper error: {e}, falling back to basic whisper/mock...")
        # Fallback using standard whisper if faster-whisper fails
        import whisper
        model = whisper.load_model(model_size)
        res = model.transcribe(audio_path, language="zh")
        results = []
        for i, segment in enumerate(res.get("segments", []), 1):
            text = segment["text"].strip()
            if text:
                results.append({
                    "id": i,
                    "start": round(segment["start"], 2),
                    "end": round(segment["end"], 2),
                    "text": text
                })
        return results
