# Self-Hosting M4B Player on TrueNAS SCALE

This guide walks you through deploying your lightweight M4B Audiobook Player on **TrueNAS SCALE** (TrueNAS 24.04+ / Electric Eel or Dragonfish).

---

## 1. Prepare Your TrueNAS Datasets

Create two datasets on your storage pool (e.g. `tank`):

1. **Audiobooks Dataset** (where your `.m4b` library lives):
   - Path: `/mnt/tank/audiobooks`
   - Share type: SMB (so you can drag-and-drop new audiobooks from your PC/Mac)
2. **AppData Dataset** (where the app service files, database, and config live):
   - Path: `/mnt/tank/appdata/m4b-player`

---

## 2. Transfer the Service Files onto TrueNAS

Choose whichever method is easiest for you to copy the `m4b-player` project files from your Windows PC to your TrueNAS server:

### Option A: Via Windows Network Share (SMB) — *Easiest & Graphical*
If you have an SMB share configured on TrueNAS (e.g. sharing your `appdata` dataset):
1. On your Windows PC, press `Win + R`, enter `\\<TRUENAS_IP>\appdata` (replace with your TrueNAS IP), and press Enter.
2. Copy the entire `m4b-player` folder from:
   ```
   C:\Users\Bruger01\.gemini\antigravity\scratch\m4b-player
   ```
   into your TrueNAS share folder so it sits at:
   ```
   \\<TRUENAS_IP>\appdata\m4b-player
   ```

### Option B: Via Windows PowerShell (`scp`) — *Fastest 1-Command Method*
If SSH is enabled on TrueNAS (**System Settings** $\rightarrow$ **Services** $\rightarrow$ **SSH**):
1. Open PowerShell on your Windows PC and run:
   ```powershell
   scp -r "C:\Users\Bruger01\.gemini\antigravity\scratch\m4b-player" admin@<TRUENAS_IP>:/mnt/tank/appdata/m4b-player
   ```
   *(Replace `<TRUENAS_IP>` and `admin` with your TrueNAS IP and username).*

### Option C: Via WinSCP / FileZilla (SFTP)
1. Open WinSCP or FileZilla and connect to `<TRUENAS_IP>` using SFTP with your TrueNAS credentials.
2. Navigate to `/mnt/tank/appdata/` on the remote side.
3. Drag the `m4b-player` directory from your local PC to the remote server.

### Set Proper File Ownership on TrueNAS
TrueNAS SCALE runs container apps under user/group `568` (`apps`). Open the **TrueNAS Shell** (**System** $\rightarrow$ **Shell**) and run:
```bash
chown -R 568:568 /mnt/tank/appdata/m4b-player
chmod -R 755 /mnt/tank/appdata/m4b-player
```

---

## 3. Deployment via Docker Compose

TrueNAS SCALE 24.04+ (Electric Eel) natively supports Docker Compose.

Inside `/mnt/tank/appdata/m4b-player/`, the `docker-compose.yml` file is configured as follows:

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
      - PUID=568    # TrueNAS apps user ID
      - PGID=568    # TrueNAS apps group ID
    volumes:
      # Mount your audiobooks dataset (read-only recommended, or read/write for M4B remuxing)
      - /mnt/tank/audiobooks:/app/audiobooks
      # Mount persistent database, config, uploads, and Whisper models
      - /mnt/tank/appdata/m4b-player/data:/app/data
```

### Launch the Container
In the **TrueNAS Shell** (or via SSH):
```bash
cd /mnt/tank/appdata/m4b-player
docker compose up -d --build
```
*(Or in TrueNAS WebUI under **Apps** $\rightarrow$ **Custom App**, set name `m4b-player` and point to this compose file).*

---

## 4. First-Run Setup Wizard

Once the container is running:
1. Open your browser to: **`http://<TRUENAS_IP>:8765`**
2. The **First-Run Setup Wizard** will automatically greet you:
   - **Step 1: Library Name**: Give your library a title (e.g. *"TrueNAS Audiobooks"*).
   - **Step 2: Audiobooks Path**: Leave as `/app/audiobooks` (matching your container mount).
   - **Step 3: Create Admin Account**: Enter your chosen administrator username and secure password.
3. Click **Complete Setup & Launch Library**.
4. The server creates your admin account, scans your mounted audiobooks dataset, and logs you directly into your library!

---

## 5. Multi-User & Family Features
- As Admin, click the **Admin** button in the top navigation bar.
- Add additional family member accounts (role: `User`).
- Configure **Library Access** (*Shared Library* vs. *Personal Only*) and toggle **Allow Uploads**.
- Each user gets their own **independent playback timestamps and progress**, so multiple people can listen to the same audiobook without overwriting each other's place!

---

## 6. Whisper AI on TrueNAS (How it Works & Specs)

**Yes, Whisper AI will work out-of-the-box on your TrueNAS server!**

Here is what you need to know:
- **No GPU Required**: The player uses `faster-whisper` (CTranslate2) optimized for x86_64 CPUs with **`int8` quantization**. It runs smoothly on any modern NAS CPU (Intel Celeron, Core i3/i5/i7, Xeon, AMD Ryzen).
- **RAM Footprint**: The default `tiny.en` model requires only **~150MB to 200MB of RAM** during transcription and is only ~75MB in file size.
- **Persistent Model Caching**: The model files are automatically saved to your persistent AppData dataset (`/mnt/tank/appdata/m4b-player/whisper_models`). The model is downloaded **only once** on first run, and is reused forever (even if the container is recreated or updated).
- **Speed**: Transcribing the first 12 seconds of each chapter typically takes **0.5 to 1.5 seconds per chapter** on a NAS CPU. For a typical 25-chapter book, the entire book is enriched in about 20–30 seconds.
- **Audio Slicing (`ffmpeg`)**: The container includes `ffmpeg` to extract small 12-second audio snippets without touching the rest of the multi-gigabyte audiobook file.

---

## 7. Rebuilding the Database (Fresh Start)

If you reorganize your audiobook folder, rename files, or want to wipe all library records and start completely fresh:

### Method A: Via the Web UI (Admin Panel)
1. Log in with your Admin account.
2. Click the **Admin** button in the top navigation bar.
3. Scroll down to **Library Database Maintenance**.
4. Click **Rebuild Database & Rescan**.
5. Confirm the dialog prompt. The system clears all audiobooks, chapter customizations, progress, and cached covers, then immediately rescans your audiobooks directory. User accounts and server configurations are preserved!

### Method B: Via TrueNAS Shell / SSH (CLI)
You can run the rebuild tool directly from the TrueNAS Shell:
```bash
# Inside the docker container:
docker exec -it m4b-player python rebuild_db.py

# Or if you don't want to immediately rescan:
docker exec -it m4b-player python rebuild_db.py --no-rescan
```

