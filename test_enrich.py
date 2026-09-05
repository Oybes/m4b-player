import sys
import json
import urllib.request
from pathlib import Path

import database
import scanner
from main import app

def test_enrich():
    database.init_db()
    books = database.get_all_books()
    assert len(books) > 0, "No books found"
    book_id = books[0]["id"]
    book = database.get_book_by_id(book_id)
    file_path = book["file_path"]

    print(f"Original chapters in DB: {[c['title'] for c in book['chapters']]}")

    new_titles = [
        "Enriched Ch 1: The Galactic Journey Begins",
        "Enriched Ch 2: Decoding the Fish",
        "Enriched Ch 3: Arthur's Revelation"
    ]

    # Test direct file remuxing
    print("Testing M4B file remux with write_chapters_to_m4b...")
    updated_chaps = []
    for i, ch in enumerate(book["chapters"]):
        updated_chaps.append({
            "index": i + 1,
            "title": new_titles[i],
            "start": ch["start"],
            "end": ch.get("end")
        })

    success = scanner.write_chapters_to_m4b(file_path, updated_chaps)
    assert success, "M4B file rewrite failed"
    print("M4B file remux successful!")

    # Verify using ffprobe that the file on disk has the new chapter titles
    probed = scanner.parse_chapters_with_ffprobe(file_path)
    probed_titles = [c["title"] for c in probed]
    print(f"Probed titles from M4B file: {probed_titles}")
    assert probed_titles == new_titles, f"Expected {new_titles}, got {probed_titles}"

    # Update database
    database.update_book_chapters(book_id, updated_chaps)
    db_book = database.get_book_by_id(book_id)
    db_titles = [c["title"] for c in db_book["chapters"]]
    assert db_titles == new_titles, "Database titles do not match"

    print("\nCHAPTER ENRICHMENT TEST PASSED! [PASSED]")

if __name__ == "__main__":
    test_enrich()
