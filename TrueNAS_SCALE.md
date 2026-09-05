# Self-Hosting M4B Player on TrueNAS SCALE

A complete guide to deploying the lightweight M4B Audiobook Player on **TrueNAS SCALE** (TrueNAS 24.04+ / Electric Eel or Dragonfish) using Docker Compose.

---

## 1. Prepare Your TrueNAS Datasets

Create two datasets on your ZFS storage pool (e.g., `tank` or your primary data pool):

1. **Audiobooks Dataset** (where your `.m4b` / `.m4a` files live):
   - Path: `/mnt/<POOL>/audiobooks`
   - Share type: SMB (optional, so you can easily transfer audiobooks from your PC/Mac)
2. **AppData Dataset** (where the app code, database, cover cache, and Whisper AI models reside):
   - Path: `/mnt/<POOL>/appdata/m4b-player`

---

## 2. Deploy via Git Clone (Recommended)

TrueNAS SCALE includes `git` and Docker Compose natively.

1. Open the **TrueNAS Shell** (in TrueNAS WebUI under **System** $\rightarrow$ **Shell**, or via SSH).
2. Navigate to your appdata dataset:
   ```bash
   cd /mnt/<POOL>/appdata
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/<YOUR_GITHUB_USERNAME>/m4b-player.git
   cd m4b-player
   ```
4. Set proper file ownership (`568:568` is the standard TrueNAS `apps` user):
   ```bash
   chown -R 568:568 /mnt/<POOL>/appdata/m4b-player
   chmod -R 755 /mnt/<POOL>/appdata/m4b-player
   ```

---

## 3. Configure `docker-compose.yml`

Inside `/mnt/<POOL>/appdata/m4b-player/`, inspect or edit your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  m4b-player:
    build:
      context: /mnt/<POOL>/appdata/m4b-player
      dockerfile: Dockerfile
    container_name: m4b-player
    restart: unless-stopped
    ports:
      - "8765:8765"
    environment:
      - PORT=8765
      - DATA_DIR=/app/data
      - AUDIOBOOKS_DIR=/app/audiobooks
      - HF_HOME=/app/data/whisper_models
      - PUID=568    # TrueNAS apps user ID
      - PGID=568    # TrueNAS apps group ID
    volumes:
      # Mount your audiobooks dataset (read/write recommended for chapter metadata remuxing)
      - /mnt/<POOL>/audiobooks:/app/audiobooks
      # Mount persistent database, config, uploads, and Whisper AI models
      - /mnt/<POOL>/appdata/m4b-player/data:/app/data
      # Live-mount static files for instant UI updates without rebuilding
      - /mnt/<POOL>/appdata/m4b-player/static:/app/static:ro
```

*(Replace `<POOL>` with the name of your actual TrueNAS storage pool).*

---

## 4. Launch the Container

In the **TrueNAS Shell**:
```bash
cd /mnt/<POOL>/appdata/m4b-player
docker compose up -d --build
```

*(Because of the included `.dockerignore` file, the build will complete in **under 3 seconds**).*

---

## 5. First-Run Setup Wizard

Once the container is running:
1. Open your browser to: **`http://<TRUENAS_IP>:8765`**
2. The **First-Run Setup Wizard** will automatically appear:
   - **Step 1: Library Name**: Choose your custom library title (e.g. *"Home Audiobook Vault"*).
   - **Step 2: Audiobooks Path**: Leave as `/app/audiobooks` (matching your container mount).
   - **Step 3: Create Admin Account**: Enter your chosen administrator username and secure password.
3. Click **Complete Setup & Launch Library**.
4. The server creates your master admin account, indexes your audiobooks dataset, and logs you straight into your library!

---

## 6. Install as a Mobile App (PWA)

The player includes native Progressive Web App (PWA) support with background audio and lockscreen controls:

- **iPhone (iOS Safari)**: Open `http://<TRUENAS_IP>:8765` in Safari $\rightarrow$ Tap the **Share** button (`⎋`) $\rightarrow$ Tap **"Add to Home Screen"**.
- **Android (Chrome)**: Open in Chrome $\rightarrow$ Tap the **Install** banner at the bottom (or tap the **⋮** menu $\rightarrow$ **"Install app"**).

Once installed, it opens in fullscreen standalone mode with its own dedicated app icon and no browser address bar!

---

## 7. Multi-User & Family Accounts

- Click the **Admin** button in the top navigation bar to open the User Management panel.
- Create accounts for family members with independent progress tracking.
- Set library access mode:
  - **Shared Library**: User can browse the server collection and their own uploads.
  - **Personal Only**: User only sees and streams books they personally upload.
- Toggle **Allow Uploads** per user.

---

## 8. Updating in the Future

Whenever new updates are pushed to your GitHub repository, updating TrueNAS takes just two commands:

```bash
cd /mnt/<POOL>/appdata/m4b-player
git pull
docker compose up -d --build
```

Your database, listening progress, and user accounts in `data/` remain 100% safe and untouched.

---

## 9. Rebuilding the Database (Fresh Start)

If you reorganize your audiobooks folder or want to wipe all records for a clean slate:

### Method A: From the Web UI
1. Log in with your Admin account.
2. Click **Admin** $\rightarrow$ scroll to **Library Database Maintenance**.
3. Click **Rebuild Database & Rescan**.

### Method B: From TrueNAS Shell
```bash
docker exec -it m4b-player python rebuild_db.py
```
