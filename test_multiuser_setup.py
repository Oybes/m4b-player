import sys
import os
import shutil
import tempfile
from pathlib import Path

# Use a test data directory
test_data_dir = Path("data_test")
if test_data_dir.exists():
    shutil.rmtree(test_data_dir)
os.environ["DATA_DIR"] = str(test_data_dir)

import config
import database

def run_multiuser_tests():
    print("1. Initializing database and config...")
    database.init_db()
    
    # Check setup status
    assert not config.is_setup_completed(), "Setup should be uncompleted initially"
    print("  Setup uncompleted initially: OK")

    # 2. Complete setup
    cfg = config.mark_setup_completed("Test Vault", "audiobooks")
    admin = database.create_user("admin_user", "supersecret123", role="admin")
    assert admin["username"] == "admin_user"
    assert admin["role"] == "admin"
    print("  Admin created and setup completed: OK")

    # 3. Password verification
    admin_record = database.get_user_by_username("admin_user")
    assert database.verify_password("supersecret123", admin_record["password_hash"], admin_record["salt"])
    assert not database.verify_password("wrongpass", admin_record["password_hash"], admin_record["salt"])
    print("  Password hashing & verification: OK")

    # 4. Sessions
    token = database.create_session(admin["id"])
    session_user = database.get_user_by_session(token)
    assert session_user is not None
    assert session_user["username"] == "admin_user"
    print("  Session token verification: OK")

    # 5. Create second user
    user2 = database.create_user("listener_bob", "bobspassword", role="user")
    users = database.list_users()
    assert len(users) == 2
    print(f"  User management (created Bob): OK ({[u['username'] for u in users]})")

    # 6. Multi-user progress isolation test
    test_book_id = "test_book_123"
    database.upsert_book({
        "id": test_book_id,
        "title": "Dune",
        "author": "Frank Herbert",
        "duration": 5000.0,
        "file_path": "audiobooks/dune.m4b",
        "file_size": 1000,
        "chapters": [{"title": "Chapter 1", "start": 0.0, "end": 1000.0}]
    })

    # Admin listens up to 250s
    database.save_progress(admin["id"], test_book_id, position=250.0, playback_rate=1.0)
    # Bob listens up to 1800s
    database.save_progress(user2["id"], test_book_id, position=1800.0, playback_rate=1.25)

    # Check Admin's progress
    admin_book = database.get_book_by_id(test_book_id, user_id=admin["id"])
    assert admin_book["progress"]["position"] == 250.0, f"Expected 250.0, got {admin_book['progress']['position']}"
    assert admin_book["progress"]["playback_rate"] == 1.0

    # Check Bob's progress
    bob_book = database.get_book_by_id(test_book_id, user_id=user2["id"])
    assert bob_book["progress"]["position"] == 1800.0, f"Expected 1800.0, got {bob_book['progress']['position']}"
    assert bob_book["progress"]["playback_rate"] == 1.25

    print(f"  Progress Isolation: Admin at {admin_book['progress']['position']}s, Bob at {bob_book['progress']['position']}s: OK")

    # Clean up test dir
    if test_data_dir.exists():
        shutil.rmtree(test_data_dir, ignore_errors=True)

    print("\nALL MULTI-USER & SETUP TESTS PASSED! [PASSED]")

if __name__ == "__main__":
    run_multiuser_tests()
