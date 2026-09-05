import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AUDIOBOOKS_DIR = BASE_DIR / "audiobooks"
AUDIOBOOKS_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_METADATA = """;FFMETADATA1
title=The Hitchhiker's Guide to the Galaxy
artist=Douglas Adams
album_artist=Douglas Adams
album=The Hitchhiker's Guide to the Galaxy
composer=Stephen Fry
genre=Audiobook
comment=A test audiobook generated for M4B player verification

[CHAPTER]
TIMEBASE=1/1000
START=0
END=15000
title=Chapter 1: The End of the World

[CHAPTER]
TIMEBASE=1/1000
START=15000
END=32000
title=Chapter 2: The Babel Fish

[CHAPTER]
TIMEBASE=1/1000
START=32000
END=50000
title=Chapter 3: Don't Panic
"""

def find_ffmpeg():
    # Try finding in PATH or Gyan installation
    for p in [
        "ffmpeg",
        r"C:\Users\Bruger01\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
    ]:
        try:
            res = subprocess.run([p, "-version"], capture_output=True, text=True)
            if res.returncode == 0:
                return p
        except Exception:
            continue
            
    # Search in winget directories
    winget_dir = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    for match in winget_dir.glob("**/ffmpeg.exe"):
        return str(match)
        
    return "ffmpeg"

def create_sample_book():
    ffmpeg_bin = find_ffmpeg()
    print(f"Using FFmpeg: {ffmpeg_bin}")

    metadata_path = BASE_DIR / "sample_metadata.txt"
    metadata_path.write_text(SAMPLE_METADATA, encoding="utf-8")

    out_file = AUDIOBOOKS_DIR / "sample_audiobook.m4b"
    if out_file.exists():
        print(f"Sample book already exists at: {out_file}")
        return out_file

    print("Generating 50-second test audiobook with 3 chapters...")
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "lavfi",
        # Generates a pleasant mellow test tone
        "-i", "sine=frequency=320:duration=50",
        "-i", str(metadata_path),
        "-map_metadata", "1",
        "-c:a", "aac",
        "-b:a", "64k",
        str(out_file)
    ]

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error creating sample M4B: {res.stderr}")
        return None

    if metadata_path.exists():
        metadata_path.unlink()

    print(f"Successfully generated test audiobook: {out_file} ({out_file.stat().st_size} bytes)")
    return out_file

if __name__ == "__main__":
    create_sample_book()
