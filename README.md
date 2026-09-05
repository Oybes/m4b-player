# Lightweight Self-Hosted M4B Audiobook Player

A minimalist, high-performance web player for `.m4b` and `.m4a` audiobooks written in Python (FastAPI).

## Features

- **Instant Seeking (HTTP 206 Range Requests)**: Streams gigabyte-sized M4B files without buffering into memory.
- **Embedded Metadata & Chapter Marks**: Extracts title, author, narrator, cover artwork, and chapter timestamps (Nero & QuickTime).
- **Persistent Progress**: Remembers playback position to the second in a lightweight SQLite database.
- **Mobile & Lockscreen Ready**: MediaSession API integration provides phone lock-screen controls (artwork, chapter titles, 15s back / 30s forward).
- **Audiobook Ergonomics**: Speed controls (0.75x–2.0x), sleep timer, chapter jump drawer, and keyboard shortcuts.
- **PWA Ready**: Add to Home Screen on mobile browsers for an app-like experience.
- **Lightweight Footprint**: Consumes ~35–50MB RAM with zero bloated background workers.

---

## Quick Start (Local)

### 1. Requirements
Python 3.10+ installed.

### 2. Run
Double-click `start.bat` or run:
```bash
pip install -r requirements.txt
python main.py
```
Open your browser at **`http://localhost:8000`**.

Place any `.m4b` or `.m4a` files into the `audiobooks/` folder and click **Rescan Library** in the web UI.

---

## Self-Hosting with Docker

Deploy with 1 command on any server, VPS, NAS (Unraid/TrueNAS/Synology):

```bash
docker compose up -d
```

### `docker-compose.yml` Configuration
```yaml
version: '3.8'

services:
  m4b-player:
    image: python:3.12-slim
    build: .
    container_name: m4b-player
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      # Point to your library on your host
      - /path/to/my/audiobooks:/app/audiobooks:ro
      # Stores SQLite database & extracted artwork
      - ./data:/app/data
    environment:
      - PORT=8000
```

---

## Keyboard Shortcuts
- `Space`: Play / Pause
- `Left Arrow`: Rewind 15 seconds
- `Right Arrow`: Fast-forward 30 seconds
- `Up Arrow` / `Down Arrow`: Volume adjustment
