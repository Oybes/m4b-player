import os
import hashlib
import struct
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from mutagen.mp4 import MP4, MP4Cover
except ImportError:
    MP4 = None

from database import upsert_book, is_book_indexed


DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
COVERS_DIR = DATA_DIR / "covers"
COVERS_DIR.mkdir(parents=True, exist_ok=True)

def generate_book_id(file_path: str) -> str:
    """Generate a consistent unique ID based on the file path."""
    return hashlib.sha256(os.path.abspath(file_path).encode("utf-8")).hexdigest()[:16]

def parse_mp4_nero_chapters(file_path: str) -> List[Dict[str, Any]]:
    """
    Pure Python parser for Nero-style MP4 chapters ('chpl' atom).
    Scans the MP4 atom tree without external dependencies.
    """
    chapters = []
    try:
        with open(file_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_len = f.tell()
            f.seek(0)
            
            # Recursive atom search
            def find_atom(start: int, end: int, target_fourcc: bytes) -> Optional[tuple]:
                curr = start
                while curr < end - 8:
                    f.seek(curr)
                    header = f.read(8)
                    if len(header) < 8:
                        break
                    atom_size, atom_type = struct.unpack(">I4s", header)
                    
                    if atom_size == 1: # 64-bit size
                        ext_size_bytes = f.read(8)
                        if len(ext_size_bytes) < 8:
                            break
                        atom_size = struct.unpack(">Q", ext_size_bytes)[0]
                        header_size = 16
                    elif atom_size == 0:
                        atom_size = end - curr
                        header_size = 8
                    else:
                        header_size = 8
                        
                    if atom_size < 8:
                        break
                        
                    if atom_type == target_fourcc:
                        return (curr + header_size, curr + atom_size)
                    
                    # Container atoms we should descend into
                    if atom_type in (b"moov", b"udta", b"trak", b"mdia", b"minf", b"stbl"):
                        res = find_atom(curr + header_size, curr + atom_size, target_fourcc)
                        if res:
                            return res
                            
                    curr += atom_size
                return None

            chpl_loc = find_atom(0, file_len, b"chpl")
            if chpl_loc:
                data_start, data_end = chpl_loc
                f.seek(data_start)
                atom_data = f.read(data_end - data_start)
                if len(atom_data) > 8:
                    version = atom_data[0]
                    # version 1 or 0
                    if version == 1:
                        # 4 bytes reserved, 1 byte count (or 4 bytes)
                        # Usually: [0: version(1)][1..4: flags(3)][4..8: reserved(4)][8: count(1)]
                        # Let's inspect length
                        if len(atom_data) >= 9:
                            count = atom_data[8]
                            offset = 9
                            raw_chaps = []
                            for _ in range(count):
                                if offset + 9 > len(atom_data):
                                    break
                                start_100ns = struct.unpack(">Q", atom_data[offset:offset+8])[0]
                                title_len = atom_data[offset+8]
                                offset += 9
                                title_bytes = atom_data[offset:offset+title_len]
                                offset += title_len
                                title = title_bytes.decode("utf-8", errors="replace")
                                start_sec = start_100ns / 10_000_000.0
                                raw_chaps.append({"title": title, "start": start_sec})
                            
                            for i, chap in enumerate(raw_chaps):
                                next_start = raw_chaps[i+1]["start"] if i + 1 < len(raw_chaps) else None
                                chapters.append({
                                    "index": i + 1,
                                    "title": chap["title"] or f"Chapter {i + 1}",
                                    "start": round(chap["start"], 2),
                                    "end": round(next_start, 2) if next_start is not None else None
                                })
    except Exception as e:
        # Silently fail back if parsing encounters non-standard MP4 container
        pass
    return chapters

_CACHED_FFPROBE = None

def get_ffprobe_bin() -> Optional[str]:
    global _CACHED_FFPROBE
    if _CACHED_FFPROBE is not None:
        return _CACHED_FFPROBE
        
    import subprocess
    ffprobe_candidates = ["ffprobe"]
    winget_dir = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    if winget_dir.exists():
        for match in winget_dir.glob("**/ffprobe.exe"):
            ffprobe_candidates.append(str(match))
            
    for cand in ffprobe_candidates:
        try:
            res = subprocess.run([cand, "-version"], capture_output=True)
            if res.returncode == 0:
                _CACHED_FFPROBE = cand
                return _CACHED_FFPROBE
        except Exception:
            continue
            
    _CACHED_FFPROBE = ""
    return None

_CACHED_FFMPEG = None

def get_ffmpeg_bin() -> Optional[str]:
    global _CACHED_FFMPEG
    if _CACHED_FFMPEG is not None:
        return _CACHED_FFMPEG
        
    import subprocess
    candidates = ["ffmpeg"]
    winget_dir = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    if winget_dir.exists():
        for match in winget_dir.glob("**/ffmpeg.exe"):
            candidates.append(str(match))
            
    for cand in candidates:
        try:
            res = subprocess.run([cand, "-version"], capture_output=True)
            if res.returncode == 0:
                _CACHED_FFMPEG = cand
                return _CACHED_FFMPEG
        except Exception:
            continue
            
    _CACHED_FFMPEG = ""
    return None

def write_chapters_to_m4b(file_path: str, chapters: List[Dict[str, Any]]) -> bool:
    """
    Rewrites chapter markers inside an M4B file without re-encoding audio.
    Uses ffmpeg with -codec copy.
    """
    import subprocess
    import tempfile
    
    ffmpeg_bin = get_ffmpeg_bin()
    if not ffmpeg_bin:
        raise RuntimeError("ffmpeg binary not found on system")
        
    orig_path = Path(file_path).resolve()
    if not orig_path.exists():
        raise FileNotFoundError(f"File not found: {orig_path}")
        
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = Path(tmpdir)
        meta_file = tmp_dir / "metadata.txt"
        
        # Dump current metadata
        dump_cmd = [ffmpeg_bin, "-y", "-i", str(orig_path), "-f", "ffmetadata", str(meta_file)]
        subprocess.run(dump_cmd, capture_output=True, check=True)
        
        # Read dumped metadata and strip existing [CHAPTER] sections
        existing_lines = meta_file.read_text(encoding="utf-8", errors="replace").splitlines()
        clean_lines = []
        in_chap = False
        for line in existing_lines:
            if line.strip().startswith("[CHAPTER]"):
                in_chap = True
                continue
            if in_chap:
                if line.strip().startswith("["):
                    in_chap = False
                    clean_lines.append(line)
                continue
            clean_lines.append(line)
            
        # Append new chapters
        for chap in chapters:
            start_ms = int(round(chap["start"] * 1000))
            end_val = chap.get("end")
            end_ms = int(round(end_val * 1000)) if end_val is not None else start_ms + 60000
            title = chap.get("title", f"Chapter {chap.get('index', 1)}")
            
            clean_lines.append("\n[CHAPTER]")
            clean_lines.append("TIMEBASE=1/1000")
            clean_lines.append(f"START={start_ms}")
            clean_lines.append(f"END={end_ms}")
            clean_lines.append(f"title={title}")
            
        meta_file.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")
        
        # Remux with copy (no audio re-encoding)
        out_temp = orig_path.parent / f".temp_{orig_path.name}"
        remux_cmd = [
            ffmpeg_bin, "-y",
            "-i", str(orig_path),
            "-i", str(meta_file),
            "-map_metadata", "1",
            "-map_chapters", "1",
            "-codec", "copy",
            str(out_temp)
        ]
        res = subprocess.run(remux_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0:
            if out_temp.exists():
                out_temp.unlink()
            raise RuntimeError(f"FFmpeg remux failed: {res.stderr}")
            
        # Replace original file atomically
        os.replace(out_temp, orig_path)
        return True

def parse_chapters_with_ffprobe(file_path: str) -> List[Dict[str, Any]]:

    """Industry-standard chapter extraction using ffprobe (supports QuickTime & Nero)."""
    import subprocess
    import json
    ffprobe_bin = get_ffprobe_bin()
    if not ffprobe_bin:
        return []
        
    chapters = []
    try:
        cmd = [
            ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_chapters",
            file_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode == 0:
            data = json.loads(res.stdout)
            for i, c in enumerate(data.get("chapters", [])):
                start = float(c.get("start_time", 0))
                end = float(c.get("end_time", 0))
                raw_title = c.get("tags", {}).get("title", "")
                title = str(raw_title).strip() if raw_title else f"Chapter {i + 1}"
                chapters.append({
                    "index": i + 1,
                    "title": title,
                    "start": round(start, 2),
                    "end": round(end, 2)
                })
    except Exception as e:
        print(f"[Scanner] ffprobe chapter extraction error: {e}")
        
    return chapters


def scan_file(file_path: Path, uploaded_by: Optional[str] = None, force: bool = False) -> Optional[Dict[str, Any]]:
    if not file_path.is_file() or file_path.suffix.lower() not in [".m4b", ".m4a", ".mp4"]:
        return None
        
    book_id = generate_book_id(str(file_path))
    file_size = file_path.stat().st_size
    
    # Fast incremental skip: if already in database with identical size, don't re-probe or re-extract
    if not force and is_book_indexed(book_id, file_size):
        return {"id": book_id, "skipped": True}
        
    title = file_path.stem
    author = "Unknown Author"
    narrator = ""
    description = ""
    duration = 0.0
    cover_path = None
    chapters = []
    
    # 1. Try ffprobe first (handles QuickTime text chapter tracks + Nero chpl atoms)
    chapters = parse_chapters_with_ffprobe(str(file_path))

    
    # 2. Fallback to pure-Python Nero chpl atom parser if ffprobe not available
    if not chapters:
        chapters = parse_mp4_nero_chapters(str(file_path))

    
    if MP4 is not None:
        try:
            audio = MP4(str(file_path))
            duration = audio.info.length if hasattr(audio, "info") else 0.0
            
            tags = audio.tags or {}
            
            # Title
            if "\xa9nam" in tags and tags["\xa9nam"]:
                title = str(tags["\xa9nam"][0])
                
            # Author / Artist / Album Artist
            if "\xa9ART" in tags and tags["\xa9ART"]:
                author = str(tags["\xa9ART"][0])
            elif "aART" in tags and tags["aART"]:
                author = str(tags["aART"][0])
            elif "\xa9alb" in tags and tags["\xa9alb"]:
                author = str(tags["\xa9alb"][0])
                
            # Narrator / Composer / Writer
            if "----:com.apple.iTunes:NARRATOR" in tags:
                narr_val = tags["----:com.apple.iTunes:NARRATOR"][0]
                narrator = narr_val.decode("utf-8", errors="replace") if isinstance(narr_val, bytes) else str(narr_val)
            elif "\xa9wrt" in tags and tags["\xa9wrt"]:
                narrator = str(tags["\xa9wrt"][0])
                
            # Description
            if "desc" in tags and tags["desc"]:
                description = str(tags["desc"][0])
            elif "\xa9des" in tags and tags["\xa9des"]:
                description = str(tags["\xa9des"][0])
                
            # Embedded Cover Art
            if "covr" in tags and tags["covr"]:
                cover_data = tags["covr"][0]
                ext = ".png" if getattr(cover_data, "imageformat", None) == MP4Cover.FORMAT_PNG else ".jpg"
                cover_file = COVERS_DIR / f"{book_id}{ext}"
                with open(cover_file, "wb") as cov_f:
                    cov_f.write(bytes(cover_data))
                cover_path = str(cover_file.relative_to(DATA_DIR))
                
        except Exception as e:
            print(f"[Scanner] Warning reading tags from {file_path.name}: {e}")
            
    # If no duration was detected from mutagen, fallback estimate or 0
    # Also adjust last chapter end to duration
    if duration > 0 and chapters:
        for i, ch in enumerate(chapters):
            if ch["end"] is None:
                ch["end"] = round(duration, 2)
                
    # If no chapters found, create single chapter
    if not chapters:
        chapters = [{
            "index": 1,
            "title": title,
            "start": 0.0,
            "end": round(duration, 2) if duration > 0 else None
        }]

    book_data = {
        "id": book_id,
        "title": title,
        "author": author,
        "narrator": narrator,
        "description": description,
        "duration": duration,
        "file_path": str(file_path.resolve()),
        "file_size": file_size,
        "cover_path": cover_path,
        "chapters": chapters,
        "uploaded_by": uploaded_by
    }
    
    upsert_book(book_data)
    return book_data

def scan_directory(audiobooks_dir: Path, force: bool = False) -> int:
    """Scans directory recursively and indexes all M4B files incrementally."""
    if not audiobooks_dir.exists():
        audiobooks_dir.mkdir(parents=True, exist_ok=True)
        return 0
        
    scanned = 0
    skipped = 0
    for root, _, files in os.walk(audiobooks_dir):
        for f in files:
            p = Path(root) / f
            if p.suffix.lower() in [".m4b", ".m4a", ".mp4"]:
                try:
                    res = scan_file(p, force=force)
                    if res:
                        if res.get("skipped"):
                            skipped += 1
                        else:
                            scanned += 1
                except Exception as e:
                    print(f"[Scanner] Error indexing {p}: {e}")
    if scanned > 0 or skipped > 0:
        print(f"[Scanner] Scan complete: {scanned} newly indexed/updated, {skipped} unchanged audiobooks.")
    return scanned + skipped


def clean_covers() -> int:
    """Removes cached/extracted cover images from disk."""
    removed = 0
    if COVERS_DIR.exists():
        for item in COVERS_DIR.glob("*"):
            if item.is_file():
                try:
                    item.unlink()
                    removed += 1
                except Exception as e:
                    print(f"[Scanner] Error removing cover {item}: {e}")
    return removed

