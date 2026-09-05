import re
import json
import urllib.request
import urllib.parse
from typing import List, Dict, Any, Optional

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def extract_asin(text: str) -> Optional[str]:
    """Extract an ASIN (10-character alphanumeric, often starting with B0) from text or URL."""
    text = text.strip()
    # Check if direct ASIN
    if re.match(r"^[A-Z0-9]{10}$", text, re.IGNORECASE):
        return text.upper()
    # Check if URL
    match = re.search(r"/(?:dp|pd|product)/([A-Z0-9]{10})", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    match = re.search(r"([A-Z0-9]{10})", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def fetch_chapters_by_asin(asin: str) -> Optional[List[Dict[str, Any]]]:
    """Fetch chapter list from Audnexus by ASIN."""
    try:
        url = f"https://api.audnex.us/books/{asin}/chapters"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                raw_chaps = data.get("chapters", [])
                chapters = []
                for i, c in enumerate(raw_chaps):
                    title = c.get("title", f"Chapter {i + 1}").strip()
                    chapters.append({
                        "index": i + 1,
                        "title": title,
                        "start": c.get("startOffsetSec", 0.0),
                        "duration": c.get("durationSec", 0.0)
                    })
                return chapters
    except Exception as e:
        print(f"[Lookup] Audnexus fetch error for {asin}: {e}")
    return None

def search_audible(title: str, author: str = "") -> List[Dict[str, Any]]:
    """Search Audible catalog for candidates."""
    try:
        query = title.strip()
        if author:
            query = f"{query} {author.strip()}"
            
        encoded = urllib.parse.quote(query)
        url = f"https://api.audible.com/1.0/catalog/products?title={encoded}&num_results=5&response_groups=product_desc,contributors"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                results = []
                for p in data.get("products", []):
                    authors = [a.get("name") for a in p.get("authors", []) if a.get("name")]
                    narrators = [n.get("name") for n in p.get("narrators", []) if n.get("name")]
                    asin = p.get("asin")
                    if asin:
                        results.append({
                            "asin": asin,
                            "title": p.get("title"),
                            "author": ", ".join(authors) if authors else "Unknown",
                            "narrator": ", ".join(narrators) if narrators else "",
                            "url": f"https://www.audible.com/pd/{asin}"
                        })
                return results
    except Exception as e:
        print(f"[Lookup] Audible search error: {e}")
    return []

def search_openlibrary_toc(title: str, author: str = "") -> Optional[List[str]]:
    """Fallback: Search OpenLibrary for print Table of Contents."""
    try:
        q = urllib.parse.quote(title)
        url = f"https://openlibrary.org/search.json?title={q}&limit=3"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                docs = data.get("docs", [])
                for doc in docs:
                    toc = doc.get("table_of_contents", [])
                    if toc and isinstance(toc, list):
                        return [str(t).strip() for t in toc if str(t).strip()]
    except Exception:
        pass
    return None
