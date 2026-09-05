import sqlite3
import json
import os
import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(os.getenv("DATA_DIR", "data")) / "audiobooks.db"

def get_db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Secure PBKDF2-HMAC-SHA256 password hashing."""
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        200000
    )
    return key.hex(), salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, password_hash)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Books table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT,
        narrator TEXT,
        description TEXT,
        duration REAL NOT NULL,
        file_path TEXT UNIQUE NOT NULL,
        file_size INTEGER NOT NULL,
        cover_path TEXT,
        chapters TEXT,
        chapters_customized INTEGER DEFAULT 0,
        uploaded_by TEXT DEFAULT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Check if books table has chapters_customized and uploaded_by columns (migration check)
    cursor.execute("PRAGMA table_info(books)")
    books_cols = [r["name"] for r in cursor.fetchall()]
    if "chapters_customized" not in books_cols:
        try:
            cursor.execute("ALTER TABLE books ADD COLUMN chapters_customized INTEGER DEFAULT 0")
        except Exception:
            pass
    if "uploaded_by" not in books_cols:
        try:
            cursor.execute("ALTER TABLE books ADD COLUMN uploaded_by TEXT DEFAULT NULL")
        except Exception:
            pass
    
    # 2. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        shared_library INTEGER NOT NULL DEFAULT 1,
        can_upload INTEGER NOT NULL DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Check if users table has shared_library and can_upload columns (migration check)
    cursor.execute("PRAGMA table_info(users)")
    users_cols = [r["name"] for r in cursor.fetchall()]
    if "shared_library" not in users_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN shared_library INTEGER NOT NULL DEFAULT 1")
        except Exception:
            pass
    if "can_upload" not in users_cols:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN can_upload INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
    
    # 3. Sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    """)
    
    # 4. Multi-user progress table
    # Check if table exists and has user_id column (migration check)
    cursor.execute("PRAGMA table_info(progress)")
    cols = [r["name"] for r in cursor.fetchall()]
    
    if "progress" in [t[0] for t in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        if "user_id" not in cols and len(cols) > 0:
            print("[Database Migration] Migrating progress table to composite multi-user schema...")
            cursor.execute("ALTER TABLE progress RENAME TO old_progress")
            cursor.execute("""
            CREATE TABLE progress (
                user_id TEXT NOT NULL,
                book_id TEXT NOT NULL,
                position REAL NOT NULL DEFAULT 0.0,
                playback_rate REAL NOT NULL DEFAULT 1.0,
                completed INTEGER NOT NULL DEFAULT 0,
                last_played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, book_id),
                FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
            )
            """)
            cursor.execute("DROP TABLE old_progress")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        user_id TEXT NOT NULL,
        book_id TEXT NOT NULL,
        position REAL NOT NULL DEFAULT 0.0,
        playback_rate REAL NOT NULL DEFAULT 1.0,
        completed INTEGER NOT NULL DEFAULT 0,
        last_played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, book_id),
        FOREIGN KEY (book_id) REFERENCES books (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()

# User & Session Management
def create_user(username: str, password: str, role: str = "user", shared_library: bool = True, can_upload: bool = False) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4())[:12]
    pwd_hash, salt = hash_password(password)
    
    # Admins always have access to shared library and upload permissions
    if role == "admin":
        shared_library = True
        can_upload = True
        
    cursor.execute("""
    INSERT INTO users (id, username, password_hash, salt, role, shared_library, can_upload)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username.strip().lower(), pwd_hash, salt, role, 1 if shared_library else 0, 1 if can_upload else 0))
    
    conn.commit()
    conn.close()
    return {
        "id": user_id, 
        "username": username.strip().lower(), 
        "role": role,
        "shared_library": bool(shared_library),
        "can_upload": bool(can_upload)
    }

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["shared_library"] = bool(d.get("shared_library", 1))
    d["can_upload"] = bool(d.get("can_upload", 0)) or d.get("role") == "admin"
    return d

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, shared_library, can_upload, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["shared_library"] = bool(d.get("shared_library", 1))
    d["can_upload"] = bool(d.get("can_upload", 0)) or d.get("role") == "admin"
    return d

def count_users() -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def list_users() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, shared_library, can_upload, created_at FROM users ORDER BY created_at ASC")
    rows = cursor.fetchall()
    users = []
    for r in rows:
        d = dict(r)
        d["shared_library"] = bool(d.get("shared_library", 1))
        d["can_upload"] = bool(d.get("can_upload", 0)) or d.get("role") == "admin"
        users.append(d)
    conn.close()
    return users

def update_user_permissions(user_id: str, shared_library: bool, can_upload: bool) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users 
    SET shared_library = ?, can_upload = ?
    WHERE id = ?
    """, (1 if shared_library else 0, 1 if can_upload else 0, user_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def delete_user(user_id: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def create_session(user_id: str, days: int = 30) -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=days)
    cursor.execute("""
    INSERT INTO sessions (token, user_id, expires_at)
    VALUES (?, ?, ?)
    """, (token, user_id, expires_at))
    conn.commit()
    conn.close()
    return token

def get_user_by_session(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT u.id, u.username, u.role, u.shared_library, u.can_upload
    FROM sessions s
    JOIN users u ON s.user_id = u.id
    WHERE s.token = ? AND s.expires_at > CURRENT_TIMESTAMP
    """, (token,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["shared_library"] = bool(d.get("shared_library", 1))
    d["can_upload"] = bool(d.get("can_upload", 0)) or d.get("role") == "admin"
    return d

def delete_session(token: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

# Book Operations
def is_book_indexed(book_id: str, file_size: int) -> bool:
    """Check if a book is already indexed with identical file size (fast incremental scan skip)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM books WHERE id = ? AND file_size = ?", (book_id, file_size))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def upsert_book(book_data: Dict[str, Any]):
    conn = get_db_connection()

    cursor = conn.cursor()
    
    chapters_json = json.dumps(book_data.get("chapters", []))
    uploaded_by = book_data.get("uploaded_by")
    
    cursor.execute("""
    INSERT INTO books (id, title, author, narrator, description, duration, file_path, file_size, cover_path, chapters, chapters_customized, uploaded_by, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET
        title = excluded.title,
        author = excluded.author,
        narrator = excluded.narrator,
        description = excluded.description,
        duration = excluded.duration,
        file_path = excluded.file_path,
        file_size = excluded.file_size,
        cover_path = COALESCE(excluded.cover_path, books.cover_path),
        chapters = CASE 
            WHEN books.chapters_customized = 1 THEN books.chapters 
            ELSE excluded.chapters 
        END,
        uploaded_by = COALESCE(books.uploaded_by, excluded.uploaded_by),
        updated_at = CURRENT_TIMESTAMP
    """, (
        book_data["id"],
        book_data.get("title", "Unknown Title"),
        book_data.get("author", "Unknown Author"),
        book_data.get("narrator", ""),
        book_data.get("description", ""),
        book_data.get("duration", 0.0),
        book_data["file_path"],
        book_data.get("file_size", 0),
        book_data.get("cover_path"),
        chapters_json,
        uploaded_by
    ))
    conn.commit()
    conn.close()

def get_all_books(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user = get_user_by_id(user_id) if user_id else None
    
    if user:
        if user["role"] == "admin":
            # Admin can see all audiobooks
            cursor.execute("""
            SELECT 
                b.id, b.title, b.author, b.narrator, b.duration, b.cover_path, b.uploaded_by, b.updated_at,
                p.position, p.playback_rate, p.completed, p.last_played_at
            FROM books b
            LEFT JOIN progress p ON (b.id = p.book_id AND p.user_id = ?)
            ORDER BY COALESCE(p.last_played_at, b.updated_at) DESC
            """, (user_id,))
        elif user["shared_library"]:
            # Shared library books + user's own uploads
            cursor.execute("""
            SELECT 
                b.id, b.title, b.author, b.narrator, b.duration, b.cover_path, b.uploaded_by, b.updated_at,
                p.position, p.playback_rate, p.completed, p.last_played_at
            FROM books b
            LEFT JOIN progress p ON (b.id = p.book_id AND p.user_id = ?)
            WHERE b.uploaded_by IS NULL OR b.uploaded_by = ?
            ORDER BY COALESCE(p.last_played_at, b.updated_at) DESC
            """, (user_id, user_id))
        else:
            # Personal uploads only
            cursor.execute("""
            SELECT 
                b.id, b.title, b.author, b.narrator, b.duration, b.cover_path, b.uploaded_by, b.updated_at,
                p.position, p.playback_rate, p.completed, p.last_played_at
            FROM books b
            LEFT JOIN progress p ON (b.id = p.book_id AND p.user_id = ?)
            WHERE b.uploaded_by = ?
            ORDER BY COALESCE(p.last_played_at, b.updated_at) DESC
            """, (user_id, user_id))
    else:
        cursor.execute("""
        SELECT 
            b.id, b.title, b.author, b.narrator, b.duration, b.cover_path, b.uploaded_by, b.updated_at,
            0.0 as position, 1.0 as playback_rate, 0 as completed, NULL as last_played_at
        FROM books b
        WHERE b.uploaded_by IS NULL
        ORDER BY b.updated_at DESC
        """)
    
    rows = cursor.fetchall()
    books = []
    for row in rows:
        books.append({
            "id": row["id"],
            "title": row["title"],
            "author": row["author"],
            "narrator": row["narrator"],
            "duration": row["duration"],
            "uploaded_by": row["uploaded_by"],
            "cover_url": f"/api/books/{row['id']}/cover" if row["cover_path"] else None,
            "progress": {
                "position": row["position"] or 0.0,
                "playback_rate": row["playback_rate"] or 1.0,
                "completed": bool(row["completed"]),
                "last_played_at": row["last_played_at"]
            }
        })
    conn.close()
    return books

def get_book_by_id(book_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user = get_user_by_id(user_id) if user_id else None
    
    if user_id:
        cursor.execute("""
        SELECT 
            b.*, p.position, p.playback_rate, p.completed, p.last_played_at
        FROM books b
        LEFT JOIN progress p ON (b.id = p.book_id AND p.user_id = ?)
        WHERE b.id = ?
        """, (user_id, book_id))
    else:
        cursor.execute("SELECT b.*, 0.0 as position, 1.0 as playback_rate, 0 as completed, NULL as last_played_at FROM books b WHERE b.id = ?", (book_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    # Permission verification
    if user and user["role"] != "admin":
        if not user["shared_library"] and row["uploaded_by"] != user_id:
            conn.close()
            return None
        if user["shared_library"] and row["uploaded_by"] is not None and row["uploaded_by"] != user_id:
            conn.close()
            return None
            
    chapters = []
    if row["chapters"]:
        try:
            chapters = json.loads(row["chapters"])
        except Exception:
            chapters = []
            
    book = {
        "id": row["id"],
        "title": row["title"],
        "author": row["author"],
        "narrator": row["narrator"],
        "description": row["description"],
        "duration": row["duration"],
        "file_path": row["file_path"],
        "file_size": row["file_size"],
        "uploaded_by": row["uploaded_by"],
        "cover_url": f"/api/books/{row['id']}/cover" if row["cover_path"] else None,
        "chapters": chapters,
        "progress": {
            "position": row["position"] or 0.0,
            "playback_rate": row["playback_rate"] or 1.0,
            "completed": bool(row["completed"]),
            "last_played_at": row["last_played_at"]
        }
    }
    conn.close()
    return book

def save_progress(user_id: str, book_id: str, position: float, playback_rate: float = 1.0, completed: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO progress (user_id, book_id, position, playback_rate, completed, last_played_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id, book_id) DO UPDATE SET
        position = excluded.position,
        playback_rate = excluded.playback_rate,
        completed = excluded.completed,
        last_played_at = CURRENT_TIMESTAMP
    """, (user_id, book_id, position, playback_rate, 1 if completed else 0))
    
    conn.commit()
    conn.close()

def update_book_chapters(book_id: str, chapters: List[Dict[str, Any]]):
    conn = get_db_connection()
    cursor = conn.cursor()
    chapters_json = json.dumps(chapters)
    cursor.execute("""
    UPDATE books 
    SET chapters = ?, chapters_customized = 1, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (chapters_json, book_id))
    conn.commit()
    conn.close()

def rebuild_audiobooks_database():
    """Wipes all audiobooks and listening progress from the database, preserving users and sessions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM progress")
    cursor.execute("DELETE FROM books")
    conn.commit()
    conn.isolation_level = None
    cursor.execute("VACUUM")
    conn.close()


