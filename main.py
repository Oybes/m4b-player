import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks, Depends, Cookie, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import database
import scanner
import lookup
import config

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize config, directories, and DB
    cfg = config.load_config()
    data_dir = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    audiobooks_dir = Path(os.getenv("AUDIOBOOKS_DIR", BASE_DIR / cfg.get("audiobooks_dir", "audiobooks")))
    
    data_dir.mkdir(parents=True, exist_ok=True)
    audiobooks_dir.mkdir(parents=True, exist_ok=True)
    database.init_db()
    
    # If setup was already completed, run library scan
    if config.is_setup_completed():
        scan_dir = cfg.get("audiobooks_dir")
        if scan_dir and os.path.exists(scan_dir):
            print(f"[Lifespan] Scanning audiobooks from: {scan_dir}")
            scanner.scan_directory(Path(scan_dir))
        
    yield

app = FastAPI(title="M4B Audiobook Server", lifespan=lifespan)

# Helper Dependency for Auth & Roles
def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("session_token")
    if not token:
        # Check Authorization header (Bearer token) or query parameter (useful for audio element stream)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        elif "token" in request.query_params:
            token = request.query_params["token"]
            
    if not token:
        return None
        
    return database.get_user_by_session(token)

def require_user(request: Request) -> Dict[str, Any]:
    # If setup is not completed, we don't block with 401 yet so frontend can check setup
    if not config.is_setup_completed():
        raise HTTPException(status_code=428, detail="Setup required")
        
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_admin(request: Request) -> Dict[str, Any]:
    user = require_user(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin permissions required")
    return user

# Pydantic Payloads
class SetupPayload(BaseModel):
    site_name: str
    audiobooks_dir: str
    admin_username: str
    admin_password: str

class LoginPayload(BaseModel):
    username: str
    password: str

class CreateUserPayload(BaseModel):
    username: str
    password: str
    role: Optional[str] = "user"
    shared_library: Optional[bool] = True
    can_upload: Optional[bool] = False

class UpdatePermissionsPayload(BaseModel):
    shared_library: bool
    can_upload: bool

class UpdateConfigPayload(BaseModel):
    site_name: str
    audiobooks_dir: str

class ProgressPayload(BaseModel):
    position: float
    playback_rate: Optional[float] = 1.0
    completed: Optional[bool] = False

class EnrichChaptersPayload(BaseModel):
    titles: Optional[List[str]] = None
    chapters: Optional[List[dict]] = None
    write_to_file: Optional[bool] = False

# Setup & Onboarding Endpoints
@app.get("/api/setup/status")
def setup_status():
    """Checks whether the first-run setup wizard is required."""
    cfg = config.load_config()
    is_done = config.is_setup_completed() and database.count_users() > 0
    return {
        "setup_required": not is_done,
        "site_name": cfg.get("site_name", "M4B Audiobook Vault"),
        "audiobooks_dir": cfg.get("audiobooks_dir", "audiobooks")
    }

@app.post("/api/setup/initialize")
def setup_initialize(payload: SetupPayload, response: Response, background_tasks: BackgroundTasks):
    """Initializes the server with admin credentials, site name, and audiobooks path."""
    if config.is_setup_completed() and database.count_users() > 0:
        raise HTTPException(status_code=400, detail="Setup has already been completed.")
        
    if len(payload.admin_password.strip()) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters.")
        
    # 1. Create Admin user
    admin_user = database.create_user(payload.admin_username, payload.admin_password, role="admin")
    
    # 2. Save config
    cfg = config.mark_setup_completed(payload.site_name, payload.audiobooks_dir)
    
    # 3. Create session & set cookie
    token = database.create_session(admin_user["id"])
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax"
    )
    
    # 4. Trigger initial scan
    books_path = Path(payload.audiobooks_dir.strip())
    if not books_path.is_absolute():
        books_path = BASE_DIR / books_path
    background_tasks.add_task(scanner.scan_directory, books_path)
    
    return {
        "status": "ok",
        "user": admin_user,
        "config": cfg,
        "token": token
    }

# Auth Endpoints
@app.post("/api/auth/login")
def login(payload: LoginPayload, response: Response):
    user = database.get_user_by_username(payload.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    if not database.verify_password(payload.password, user["password_hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    token = database.create_session(user["id"])
    response.set_cookie(
        key="session_token",
        value=token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax"
    )
    
    return {
        "status": "ok",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "shared_library": user.get("shared_library", True),
            "can_upload": user.get("can_upload", False) or user.get("role") == "admin"
        },
        "token": token
    }

@app.post("/api/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("session_token")
    if token:
        database.delete_session(token)
    response.delete_cookie(key="session_token")
    return {"status": "ok"}

@app.get("/api/auth/me")
def get_me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not logged in")
    return {"user": user}

# Admin Management Endpoints
@app.get("/api/admin/users")
def get_users(admin: Dict[str, Any] = Depends(require_admin)):
    return {"users": database.list_users()}

@app.post("/api/admin/users")
def create_new_user(payload: CreateUserPayload, admin: Dict[str, Any] = Depends(require_admin)):
    existing = database.get_user_by_username(payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = database.create_user(
        payload.username, 
        payload.password, 
        role=payload.role or "user",
        shared_library=True if payload.shared_library is None else payload.shared_library,
        can_upload=False if payload.can_upload is None else payload.can_upload
    )
    return {"status": "ok", "user": user}

@app.put("/api/admin/users/{user_id}/permissions")
def update_user_permissions(user_id: str, payload: UpdatePermissionsPayload, admin: Dict[str, Any] = Depends(require_admin)):
    target_user = database.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user["role"] == "admin":
        raise HTTPException(status_code=400, detail="Admin permissions cannot be restricted")
    database.update_user_permissions(user_id, payload.shared_library, payload.can_upload)
    return {"status": "ok", "user": database.get_user_by_id(user_id)}

@app.delete("/api/admin/users/{user_id}")
def remove_user(user_id: str, admin: Dict[str, Any] = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete your own admin account")
    deleted = database.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}

@app.get("/api/admin/config")
def get_admin_config(admin: Dict[str, Any] = Depends(require_admin)):
    return {"config": config.load_config()}

@app.put("/api/admin/config")
def update_admin_config(payload: UpdateConfigPayload, admin: Dict[str, Any] = Depends(require_admin)):
    cfg = config.load_config()
    cfg["site_name"] = payload.site_name.strip() or cfg.get("site_name")
    cfg["audiobooks_dir"] = payload.audiobooks_dir.strip() or cfg.get("audiobooks_dir")
    config.save_config(cfg)
    return {"status": "ok", "config": cfg}

@app.post("/api/admin/rebuild-db")
def rebuild_database(background_tasks: BackgroundTasks, rescan: bool = True, admin: Dict[str, Any] = Depends(require_admin)):
    """Wipes all audiobooks and listening progress from the database, and optionally rescans the audiobooks directory."""
    database.rebuild_audiobooks_database()
    scanner.clean_covers()
    
    if rescan:
        cfg = config.load_config()
        audiobooks_dir = os.getenv("AUDIOBOOKS_DIR") or cfg.get("audiobooks_dir", "audiobooks")
        books_path = Path(audiobooks_dir)
        if not books_path.is_absolute():
            books_path = BASE_DIR / books_path
        background_tasks.add_task(scanner.scan_directory, books_path)
        return {
            "status": "ok", 
            "message": "Library database successfully rebuilt! Rescanning audiobooks folder in background..."
        }
    
    return {
        "status": "ok", 
        "message": "Library database cleared. Audiobooks and progress have been reset."
    }


# Library & Audio Streaming Endpoints
@app.get("/api/books")
def list_books(user: Dict[str, Any] = Depends(require_user)):
    """List all audiobooks with user-specific progress."""
    books = database.get_all_books(user_id=user["id"])
    return {"books": books}

@app.get("/api/books/{book_id}")
def get_book(book_id: str, user: Dict[str, Any] = Depends(require_user)):
    """Get single audiobook details with user-specific progress."""
    book = database.get_book_by_id(book_id, user_id=user["id"])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.get("/api/books/{book_id}/stream")
async def stream_book(book_id: str, request: Request):
    """Stream audio with full HTTP 206 Partial Content (Range) support."""
    # Allow authentication via cookie or token query parameter
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to stream")
        
    book = database.get_book_by_id(book_id, user_id=user["id"])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    file_path = Path(book["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audiobook file missing on disk")
        
    return FileResponse(
        path=file_path,
        media_type="audio/mp4",
        filename=file_path.name,
        headers={"Accept-Ranges": "bytes"}
    )

@app.get("/api/books/{book_id}/cover")
def get_cover(book_id: str):
    """Serve embedded cover art or placeholder."""
    data_dir = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    if book_id != "cover":
        book = database.get_book_by_id(book_id)
        if book and book.get("cover_url"):
            for ext in [".jpg", ".png", ".jpeg"]:
                cov_file = data_dir / "covers" / f"{book_id}{ext}"
                if cov_file.exists():
                    media = "image/png" if ext == ".png" else "image/jpeg"
                    return FileResponse(cov_file, media_type=media)
                
    # Fallback SVG
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="400" height="400">
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#1e1b4b;stop-opacity:1" />
        </linearGradient>
      </defs>
      <rect width="400" height="400" rx="16" fill="url(#grad)"/>
      <circle cx="200" cy="200" r="45" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="4"/>
      <polygon points="190,180 220,200 190,220" fill="rgba(255,255,255,0.85)"/>
      <text x="200" y="340" fill="#f8fafc" font-family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif" font-size="20" font-weight="600" text-anchor="middle">Audiobook</text>
    </svg>"""
    return Response(content=svg, media_type="image/svg+xml")

@app.post("/api/books/{book_id}/progress")
def update_progress(book_id: str, payload: ProgressPayload, user: Dict[str, Any] = Depends(require_user)):
    """Persist playback position for the current authenticated user."""
    database.save_progress(
        user_id=user["id"],
        book_id=book_id,
        position=payload.position,
        playback_rate=payload.playback_rate or 1.0,
        completed=bool(payload.completed)
    )
    return {"status": "ok"}

@app.post("/api/books/{book_id}/chapters")
def enrich_chapters(book_id: str, payload: EnrichChaptersPayload, user: Dict[str, Any] = Depends(require_user)):
    """Enriches or edits chapter titles for an audiobook."""
    book = database.get_book_by_id(book_id, user_id=user["id"])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    current_chapters = book.get("chapters", [])
    updated_chapters = []
    
    if payload.chapters:
        updated_chapters = payload.chapters
    elif payload.titles is not None:
        for i, ch in enumerate(current_chapters):
            new_title = payload.titles[i].strip() if i < len(payload.titles) and payload.titles[i].strip() else ch.get("title", f"Chapter {i + 1}")
            updated_chapters.append({
                "index": ch.get("index", i + 1),
                "title": new_title,
                "start": ch["start"],
                "end": ch.get("end")
            })
    else:
        raise HTTPException(status_code=400, detail="Must provide 'titles' or 'chapters'")
        
    database.update_book_chapters(book_id, updated_chapters)
    
    file_updated = False
    if payload.write_to_file:
        try:
            scanner.write_chapters_to_m4b(book["file_path"], updated_chapters)
            file_updated = True
        except Exception as e:
            return {
                "status": "ok", 
                "message": f"Updated database, but file rewrite failed: {str(e)}", 
                "chapters": updated_chapters,
                "file_updated": False
            }
            
    return {
        "status": "ok", 
        "message": "Chapters updated successfully" + (" (and saved to M4B file)" if file_updated else ""),
        "chapters": updated_chapters,
        "file_updated": file_updated
    }

@app.get("/api/books/{book_id}/whisper-stream")
def stream_whisper_progress(book_id: str, model_size: Optional[str] = "tiny.en", user: Dict[str, Any] = Depends(require_user)):
    """Streams real-time Server-Sent Events (SSE) as each chapter is transcribed by Whisper AI."""
    book = database.get_book_by_id(book_id, user_id=user["id"])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    chapters = book.get("chapters", [])
    if not chapters:
        raise HTTPException(status_code=400, detail="No chapter markers present in this book")
        
    file_path = book["file_path"]
    
    def event_stream():
        import json
        import whisper_extractor
        try:
            for event in whisper_extractor.stream_audiobook_chapters(file_path, chapters, model_size=model_size or "tiny.en"):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            err_event = {"step": "error", "message": f"Whisper error: {str(e)}"}
            yield f"data: {json.dumps(err_event)}\n\n"
            
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/lookup/search")
def lookup_search(query: str, author: Optional[str] = "", user: Dict[str, Any] = Depends(require_user)):
    """Search online catalog (Audible/Audnexus) for matching audiobooks."""
    direct_asin = lookup.extract_asin(query)
    if direct_asin:
        return {
            "results": [{
                "asin": direct_asin,
                "title": f"Direct ASIN: {direct_asin}",
                "author": "",
                "url": f"https://www.audible.com/pd/{direct_asin}"
            }]
        }
        
    results = lookup.search_audible(query, author or "")
    return {"results": results}

@app.get("/api/lookup/chapters")
def lookup_chapters(asin: str, user: Dict[str, Any] = Depends(require_user)):
    """Fetch chapters from Audnexus for a given ASIN."""
    clean_asin = lookup.extract_asin(asin) or asin.strip()
    chapters = lookup.fetch_chapters_by_asin(clean_asin)
    if not chapters:
        raise HTTPException(status_code=404, detail=f"No chapter data found on Audnexus for ASIN: {clean_asin}")
        
    return {
        "asin": clean_asin,
        "chapters": chapters,
        "titles": [c["title"] for c in chapters]
    }

@app.post("/api/scan")
def trigger_scan(background_tasks: BackgroundTasks, user: Dict[str, Any] = Depends(require_user)):
    """Trigger library re-scan."""
    cfg = config.load_config()
    books_path = Path(cfg.get("audiobooks_dir", "audiobooks"))
    if not books_path.is_absolute():
        books_path = BASE_DIR / books_path
        
    background_tasks.add_task(scanner.scan_directory, books_path)
    return {"message": "Scan triggered in background"}

@app.post("/api/books/upload")
async def upload_audiobook(file: UploadFile = File(...), user: Dict[str, Any] = Depends(require_user)):
    """Upload an .m4b / .m4a / .mp4 audiobook with streaming chunked write and automatic indexing."""
    if not user.get("can_upload") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="You do not have permission to upload audiobooks")
        
    filename = file.filename or "audiobook.m4b"
    ext = Path(filename).suffix.lower()
    if ext not in [".m4b", ".m4a", ".mp4"]:
        raise HTTPException(status_code=400, detail="Only .m4b, .m4a, and .mp4 files are supported")
        
    data_dir = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean filename
    clean_stem = "".join(c for c in Path(filename).stem if c.isalnum() or c in " -_().").strip() or "audiobook"
    target_path = uploads_dir / f"{clean_stem}{ext}"
    if target_path.exists():
        import secrets
        target_path = uploads_dir / f"{clean_stem}_{secrets.token_hex(3)}{ext}"
        
    try:
        with open(target_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024) # 1MB chunk
                if not chunk:
                    break
                buffer.write(chunk)
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")
        
    # Index the uploaded file
    try:
        book_data = scanner.scan_file(target_path, uploaded_by=user["id"])
        if not book_data:
            if target_path.exists():
                target_path.unlink()
            raise HTTPException(status_code=400, detail="Could not read or parse audio metadata from uploaded file")
            
        full_book = database.get_book_by_id(book_data["id"], user_id=user["id"])
        return {
            "status": "ok",
            "message": f"Successfully uploaded '{book_data['title']}'!",
            "book": full_book
        }
    except Exception as e:
        if target_path.exists():
            try:
                target_path.unlink()
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Error indexing uploaded file: {str(e)}")

# Mount frontend static files
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8765))
    uvicorn.run("main:app", host="0.0.0.0", port=port, timeout_graceful_shutdown=1, timeout_keep_alive=5)
