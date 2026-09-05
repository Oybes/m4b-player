import sys
import time
import urllib.request
import json
import threading
import uvicorn
from pathlib import Path

import database
import scanner
from main import app

def run_tests():
    print("[Test] Initializing DB and scanning...")
    database.init_db()
    count = scanner.scan_directory(Path("audiobooks"))
    print(f"[Test] Scanned {count} books.")

    # 1. Test database get all books
    books = database.get_all_books()
    assert len(books) > 0, "No books found in database!"
    book = books[0]
    book_id = book["id"]
    print(f"[Test] Found book: {book['title']} by {book['author']} (ID: {book_id})")

    # 2. Test get book by id
    detail = database.get_book_by_id(book_id)
    assert detail is not None, "Book detail should not be None"
    assert len(detail["chapters"]) == 3, f"Expected 3 chapters, got {len(detail['chapters'])}"
    print(f"[Test] Chapters verified: {[c['title'] for c in detail['chapters']]}")

    # 3. Test progress saving
    database.save_progress(book_id, position=25.5, playback_rate=1.25, completed=False)
    progress_book = database.get_book_by_id(book_id)
    assert progress_book["progress"]["position"] == 25.5, "Position not updated!"
    assert progress_book["progress"]["playback_rate"] == 1.25, "Playback rate not updated!"
    print("[Test] Progress persistence verified.")

    # 4. Spin up server on localhost:8765 to test HTTP Range Streaming
    config = uvicorn.Config(app, host="127.0.0.1", port=8765, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(1.5)

    base_url = "http://127.0.0.1:8765"

    # Test GET /api/books
    req = urllib.request.Request(f"{base_url}/api/books")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        assert len(data["books"]) > 0
        print("[Test] GET /api/books endpoint: OK (200)")

    # Test HTTP Range Request (HTTP 206 Partial Content)
    req = urllib.request.Request(f"{base_url}/api/books/{book_id}/stream")
    req.add_header("Range", "bytes=0-1023")
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        content_range = resp.headers.get("Content-Range")
        content_len = resp.headers.get("Content-Length")
        body = resp.read()
        assert status == 206, f"Expected status 206 Partial Content, got {status}"
        assert content_range.startswith("bytes 0-1023/"), f"Unexpected Content-Range: {content_range}"
        assert len(body) == 1024, f"Expected 1024 bytes, got {len(body)}"
        print(f"[Test] HTTP 206 Partial Content Range Stream: OK (Content-Range: {content_range})")

    # Test GET / (Frontend index)
    req = urllib.request.Request(f"{base_url}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        html = resp.read().decode()
        assert "M4B Streamer" in html
        print("[Test] GET / (Frontend HTML): OK (200)")

    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! [PASSED]")
    server.should_exit = True

if __name__ == "__main__":
    run_tests()
