import os
import re
import tempfile
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

import scanner

_WHISPER_MODEL = None

def get_whisper_model(model_size: str = "tiny.en"):
    """Lazily load faster-whisper model on CPU with int8 quantization, cached on persistent storage."""
    global _WHISPER_MODEL
    if _WHISPER_MODEL is None:
        from faster_whisper import WhisperModel
        data_dir = os.getenv("DATA_DIR", "data")
        cache_dir = Path(data_dir) / "whisper_models"
        cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Whisper] Loading Whisper model '{model_size}' (int8 on CPU) from {cache_dir}...")
        _WHISPER_MODEL = WhisperModel(model_size, device="cpu", compute_type="int8", download_root=str(cache_dir))
        print("[Whisper] Model loaded successfully.")
    return _WHISPER_MODEL

def extract_snippet_wav(file_path: str, start_sec: float, duration_sec: float = 12.0) -> Optional[Path]:
    """Extract a small 12s audio snippet to a temporary 16kHz mono WAV file via ffmpeg."""
    ffmpeg_bin = scanner.get_ffmpeg_bin()
    if not ffmpeg_bin:
        return None

    temp_wav = Path(tempfile.gettempdir()) / f"whisper_clip_{os.getpid()}_{int(start_sec * 1000)}.wav"
    
    cmd = [
        ffmpeg_bin, "-y",
        "-ss", str(max(0.0, start_sec)),
        "-t", str(duration_sec),
        "-i", str(file_path),
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(temp_wav)
    ]
    
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode == 0 and temp_wav.exists() and temp_wav.stat().st_size > 0:
        return temp_wav
    return None

def clean_extracted_title(raw_text: str, chapter_num: int) -> str:
    """
    Cleans up speech-to-text output into a clean, human-readable chapter title.
    Examples:
      'Chapter 1. The Boy Who Lived. Mr. and Mrs.' -> 'Chapter 1: The Boy Who Lived'
      'Chapter one, into the wild.' -> 'Chapter 1: Into the wild'
      'Prologue. It was a dark and...' -> 'Prologue'
    """
    text = raw_text.strip()
    if not text:
        return f"Chapter {chapter_num}"

    # Remove repeated whitespace / newlines
    text = re.sub(r"\s+", " ", text).strip()

    # Match common patterns like "Chapter 1[:.] Title" or "Prologue[:.] Title"
    # Match first sentence / phrase up to period, exclamation, or question mark
    sentences = re.split(r"[.!?]\s+", text)
    candidate = sentences[0].strip()

    # If first sentence is just "Chapter 1" and there is a second sentence that looks like a title, combine them
    if re.match(r"^chapter\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)$", candidate, re.IGNORECASE):
        if len(sentences) > 1 and len(sentences[1].strip().split()) <= 8:
            candidate = f"{candidate}: {sentences[1].strip()}"

    # Normalize "Chapter One" -> "Chapter 1"
    word_to_num = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
        "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
        "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
        "nineteen": "19", "twenty": "20"
    }
    for word, num in word_to_num.items():
        candidate = re.sub(rf"\bchapter\s+{word}\b", f"Chapter {num}", candidate, flags=re.IGNORECASE)

    # Clean up trailing punctuation
    candidate = candidate.rstrip(".,;:- ")

    # If candidate is too long (> 65 chars), truncate to first reasonable phrase
    if len(candidate) > 65:
        parts = candidate.split(":")
        if len(parts) > 1:
            candidate = parts[0] + ":" + parts[1][:45]
        else:
            candidate = candidate[:50] + "..."

    # Capitalize nicely
    if candidate.lower().startswith("chapter"):
        candidate = "Chapter" + candidate[7:]
    elif candidate.lower().startswith("prologue"):
        candidate = "Prologue" + candidate[8:]
    elif candidate.lower().startswith("epilogue"):
        candidate = "Epilogue" + candidate[8:]

    return candidate if candidate else f"Chapter {chapter_num}"

def transcribe_chapter_title(file_path: str, start_sec: float, chapter_num: int, model_size: str = "tiny.en") -> str:
    """Extract and transcribe a single chapter start."""
    clip_path = extract_snippet_wav(file_path, start_sec, duration_sec=12.0)
    if not clip_path:
        return f"Chapter {chapter_num}"

    try:
        model = get_whisper_model(model_size)
        segments, _ = model.transcribe(str(clip_path), beam_size=1, language="en", vad_filter=True)
        raw_text = " ".join([s.text for s in segments]).strip()
        return clean_extracted_title(raw_text, chapter_num)
    except Exception as e:
        print(f"[Whisper] Transcription error at {start_sec}s: {e}")
        return f"Chapter {chapter_num}"
    finally:
        if clip_path.exists():
            try:
                clip_path.unlink()
            except Exception:
                pass

def transcribe_audiobook_chapters(file_path: str, chapters: List[Dict[str, Any]], model_size: str = "tiny.en") -> List[str]:
    """Transcribe all chapter starts for an audiobook."""
    titles = []
    for i, ch in enumerate(chapters):
        start_sec = ch.get("start", 0.0)
        num = ch.get("index", i + 1)
        title = transcribe_chapter_title(file_path, start_sec, num, model_size=model_size)
        titles.append(title)
    return titles

def stream_audiobook_chapters(file_path: str, chapters: List[Dict[str, Any]], model_size: str = "tiny.en"):
    """
    Generator that yields real-time progress events as each chapter is transcribed.
    """
    total = len(chapters)
    yield {
        "step": "init",
        "message": "Initializing Whisper AI model (first run may download tiny.en ~40MB)...",
        "current": 0,
        "total": total,
        "pct": 0
    }
    
    # Pre-load model
    _ = get_whisper_model(model_size)
    yield {
        "step": "ready",
        "message": f"Whisper model ready. Transcribing {total} chapters...",
        "current": 0,
        "total": total,
        "pct": 0
    }
    
    titles = []
    for i, ch in enumerate(chapters):
        start_sec = ch.get("start", 0.0)
        num = ch.get("index", i + 1)
        title = transcribe_chapter_title(file_path, start_sec, num, model_size=model_size)
        titles.append(title)
        
        pct = round(((i + 1) / total) * 100)
        yield {
            "step": "chapter",
            "current": i + 1,
            "total": total,
            "title": title,
            "titles": titles,
            "pct": pct,
            "message": f"Recognized Chapter {i + 1} of {total}: '{title}'"
        }
        
    yield {
        "step": "done",
        "message": f"Completed transcription of {total} chapters.",
        "titles": titles,
        "total": total,
        "pct": 100
    }

