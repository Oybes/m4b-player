import sys
from pathlib import Path
import whisper_extractor

def test_whisper():
    print("Testing clean_extracted_title heuristics...")
    
    cases = [
        ("Chapter one. The boy who lived. Mr. and Mrs. Dursley were proud to say...", 1, "Chapter 1: The boy who lived"),
        ("Prologue. A shadow fell across the northern reaches.", 1, "Prologue"),
        ("Chapter 14. Into the fire. The flames roared loudly.", 14, "Chapter 14: Into the fire"),
        ("Chapter Twelve. Return of the King.", 12, "Chapter 12: Return of the King"),
        ("", 5, "Chapter 5")
    ]
    
    for raw, num, expected_start in cases:
        cleaned = whisper_extractor.clean_extracted_title(raw, num)
        print(f"  Raw: '{raw[:35]}...' -> Cleaned: '{cleaned}'")
        assert cleaned.startswith(expected_start[:10]), f"Expected start with {expected_start}, got {cleaned}"
        
    print("\nWhisper heuristics unit test PASSED! [PASSED]")

if __name__ == "__main__":
    test_whisper()
