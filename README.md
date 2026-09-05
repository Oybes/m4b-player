# 🎧 Lightweight Self-Hosted M4B Audiobook Player

A modern, fast, self-hosted web player and server for `.m4b` and `.m4a` audiobooks with **first-run onboarding setup wizard**, **multi-user permissions**, **Whisper AI chapter enrichment**, and **mobile lockscreen controls**.

Designed to run locally or self-hosted in Docker on Linux, VPS, and NAS systems (**TrueNAS SCALE**, Unraid, Synology).

---

## ✨ Key Features

### 🚀 First-Run Setup Wizard
- **No manual configuration files required!**
- On first launch, a friendly setup wizard automatically guides the administrator:
  1. **Site & Library Branding**: Choose your custom site title (e.g. *"My Family Audiobook Vault"*).
  2. **Storage Location**: Specify your audiobooks directory (e.g. `/app/audiobooks` or a local path).
  3. **Master Admin Account**: Set your administrator credentials.
- Upon completion, the server indexes your audiobooks and logs you straight into your library!

---

### 👥 Multi-User & Family Permissions System
- **Independent Progress Tracking**: Multiple family members can listen to the exact same audiobook at different speeds without overwriting each other's timestamps or completed status!
- **Granular Library Access Modes**:
  - **Shared Library (`shared`)**: User can browse the server's shared audiobook collection plus their own uploads.
  - **Personal Only (`personal`)**: User *only* sees and can *only* stream audiobooks they upload themselves.
- **Upload Permissions**: Administrators can toggle whether individual users are allowed to upload audiobooks.
- **Admin Control Panel**: View all users, edit permissions on-the-fly, update server configuration, or trigger database maintenance.

---

### 🤖 Chapter Enrichment: Whisper AI & Audnexus Lookup
Enrich files missing proper chapter names (e.g. *"Chapter 1, Chapter 2"*):
- **Local Whisper AI**: Listens to the first 12 seconds of each chapter and uses speech-to-text to detect spoken chapter titles (e.g. *"Chapter Three: The Babel Fish"*). Runs smoothly on CPU (`faster-whisper` int8 quantization) with persistent model caching.
- **Audible / Audnexus Search**: Search online databases by book title, author, or ASIN to fetch exact official chapter titles in 1 click.
- **Lossless In-Place Remuxing**: Optionally write new chapter names directly back into your `.m4b` file metadata on disk via `ffmpeg` stream copy without re-encoding audio.

---

### 📱 Responsive Mobile & Lockscreen Player
- **Optimized Mobile Layout**: 2-row mobile portrait layout that fits all controls (Previous/Next Chapter, 15s Rewind, 30s Fast-forward, Play/Pause, Sleep Timer, Speed selector, and Chapter drawer) on any screen size without clipping.
- **Touch Scrubber**: Smooth finger dragging across the progress bar to seek instantly.
- **Mobile Lockscreen MediaSession API**: Control playback, seek, view cover art, and see live chapter titles directly from your iOS / Android lockscreen and Bluetooth car stereos.
- **Sleep Timer & Speed Control**: 15m, 30m, 45m, 60m sleep timer with remaining-time countdown badge, plus 0.75x to 2.0x playback speeds.
- **PWA Ready**: Add to Home Screen on mobile browsers for a full-screen, standalone app experience.

---

### 📤 Chunked Audiobook Uploads
- Direct in-browser upload modal for `.m4b`, `.m4a`, and `.mp4` audiobooks.
- Streams files in 1MB chunks to support multi-gigabyte audiobooks with low RAM consumption and live percentage progress indicators.

---

### 🛠️ Library Database Maintenance
- **Rebuild Database & Rescan**: Clear all audiobooks, customized chapter titles, listening progress, and cached artwork from the database for a clean fresh start, while keeping user accounts and settings safe.
- **CLI Utility**: Included `rebuild_db.py` to trigger database rebuilds directly from your SSH or NAS terminal (`python rebuild_db.py`).

---

## 🐳 Quick Start with Docker (Recommended)

The easiest way to run the player is with Docker Compose.

### 1. Clone the repository
```bash
git clone https://github.com/Oybes/m4b-player.git
cd m4b-player
```

### 2. Configure `docker-compose.yml`
```yaml
version: '3.8'

services:
  m4b-player:
    build: .
    container_name: m4b-player
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - PORT=8765
      - DATA_DIR=/app/data
      - AUDIOBOOKS_DIR=/app/audiobooks
      - HF_HOME=/app/data/whisper_models
    volumes:
      # Mount your audiobooks folder (read/write recommended for chapter remuxing)
      - /path/to/my/audiobooks:/app/audiobooks
      # Stores persistent SQLite database, config, uploads, and AI models
      - ./data:/app/data
      # Live-mount static files for instant UI updates without container rebuilds
      - ./static:/app/static:ro
```

### 3. Launch
```bash
docker compose up -d --build
```

Open **`http://<SERVER_IP>:8765`** in your browser. The First-Run Setup Wizard will greet you immediately!

---

## 🖥️ Local Installation (Without Docker)

### Prerequisites
- Python 3.10+
- `ffmpeg` installed on your system PATH

### Installation
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start server
python main.py
```
Open **`http://localhost:8765`** to complete setup.

---

## ⌨️ Desktop Keyboard Shortcuts

| Key | Action |
| --- | --- |
| `Space` | Play / Pause |
| `Left Arrow` | Rewind 15 seconds |
| `Right Arrow` | Fast-forward 30 seconds |
| `Up Arrow` | Volume Up (+10%) |
| `Down Arrow` | Volume Down (-10%) |

---

## 📖 TrueNAS SCALE Deployment Guide

For full step-by-step instructions on setting up datasets, permissions, and deploying via TrueNAS WebUI or Shell, see [TRUENAS_GUIDE.md](TRUENAS_GUIDE.md).
