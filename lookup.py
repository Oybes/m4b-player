import re
import json
import os
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Dict, Any, Optional

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

def extract_asin(text: str) -> Optional[str]:
    """Extract an ASIN (10-character alphanumeric, often starting with B0) from text or URL."""
    text = text.strip()
    if re.match(r"^[A-Z0-9]{10}$", text, re.IGNORECASE):
        return text.upper()
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

def search_goodreads(query: str) -> List[Dict[str, Any]]:
    """Search Goodreads catalog by scraping search results for clean title, author, and series."""
    results = []
    clean_q = query.strip()
    if not clean_q:
        return results

    try:
        url = f"https://www.goodreads.com/search?q={urllib.parse.quote(clean_q)}"
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="replace")
            
            rows = re.findall(r'<tr itemscope itemtype="http://schema.org/Book">([\s\S]*?)</tr>', html)
            for row in rows[:8]:
                raw_title_match = re.search(r'<a class="bookTitle"[^>]*>([\s\S]*?)</a>', row)
                author_match = re.search(r'class="authorName"[^>]*>[\s\r\n]*<span[^>]*itemprop="name"[^>]*>(.*?)</span>', row)
                img_match = re.search(r'class="bookCover"[^>]*src="([^"]+)"', row)

                if not raw_title_match:
                    continue

                raw_title = re.sub(r'<[^>]+>', '', raw_title_match.group(1)).strip()
                author = author_match.group(1).strip() if author_match else ""
                cover_url = img_match.group(1).strip() if img_match else ""
                
                # Upgrade Goodreads thumbnail to high-resolution by stripping the size modifier
                if cover_url and "._S" in cover_url:
                    cover_url = re.sub(r'\._S[A-Z0-9_]+\.', '.', cover_url)

                # Extract Series from Goodreads title: e.g. "Carl's Doomsday Scenario (Dungeon Crawler Carl, #2)"
                series_name = ""
                series_seq = ""
                series_match = re.search(r'\((.*?),\s*#?([0-9.]+)\)', raw_title)
                if series_match:
                    series_name = series_match.group(1).strip()
                    series_seq = series_match.group(2).strip()
                    clean_title = re.sub(r'\s*\(.*?\)', '', raw_title).strip()
                else:
                    series_match_no_num = re.search(r'\((.*?)\)', raw_title)
                    if series_match_no_num and "Series" in series_match_no_num.group(1):
                        series_name = series_match_no_num.group(1).replace("Series", "").strip()
                        clean_title = re.sub(r'\s*\(.*?\)', '', raw_title).strip()
                    else:
                        clean_title = raw_title

                results.append({
                    "title": clean_title,
                    "author": author,
                    "narrator": "",
                    "series": series_name,
                    "series_sequence": series_seq,
                    "cover_url": cover_url,
                    "source": "Goodreads",
                    "url": f"https://www.goodreads.com/search?q={urllib.parse.quote(clean_title)}"
                })
    except Exception as e:
        print(f"[Lookup] Goodreads search warning: {e}")
    return results

def clean_html_text(raw_html: str) -> str:
    """Helper to convert HTML summaries to clean formatted text."""
    if not raw_html:
        return ""
    text = re.sub(r'<\s*br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r'</?\s*p\s*>', '\n\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace("&quot;", '"').replace("&apos;", "'").replace("&#39;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def search_audible(title: str, author: str = "") -> List[Dict[str, Any]]:
    """Search Audible catalog for candidate audiobooks, including narrators, series, cover art, and rich metadata."""
    results = []
    try:
        query = title.strip()
        if author:
            query = f"{query} {author.strip()}"
            
        encoded = urllib.parse.quote(query)
        url = f"https://api.audible.com/1.0/catalog/products?title={encoded}&num_results=6&response_groups=product_desc,contributors,media,series,product_attrs,category_ladders"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                for p in data.get("products", []):
                    authors = [a.get("name") for a in p.get("authors", []) if a.get("name")]
                    narrators = [n.get("name") for n in p.get("narrators", []) if n.get("name")]
                    
                    series_name = ""
                    series_seq = ""
                    series_list = p.get("series", [])
                    if series_list and isinstance(series_list, list):
                        series_name = series_list[0].get("title", "") or ""
                        seq_val = series_list[0].get("sequence")
                        series_seq = str(seq_val) if seq_val is not None else ""

                    # Cover artwork
                    cover_url = ""
                    images = p.get("product_images", {})
                    if images and isinstance(images, dict):
                        for k in ["1024", "500", "400", "300", "200"]:
                            if images.get(k):
                                cover_url = images[k]
                                break

                    # Publisher
                    publisher = (p.get("publisher_name") or "").strip()

                    # Publish Year
                    raw_date = p.get("release_date") or p.get("issue_date") or p.get("publication_datetime") or ""
                    publish_year = ""
                    if raw_date and len(raw_date) >= 4 and raw_date[:4].isdigit():
                        publish_year = raw_date[:4]

                    # Genres / Categories
                    genre_candidates = []
                    for cl in p.get("category_ladders", []):
                        ladder = cl.get("ladder", [])
                        if ladder:
                            names = [item["name"].strip() for item in ladder if item.get("name") and item["name"].strip() not in ("Genres", "Categories")]
                            if names:
                                genre_candidates.append(names[-1])
                    seen_g = set()
                    unique_genres = []
                    for g in genre_candidates:
                        if g.lower() not in seen_g:
                            seen_g.add(g.lower())
                            unique_genres.append(g)
                    genres_str = ", ".join(unique_genres[:4])

                    # Description / Synopsis
                    raw_summary = p.get("publisher_summary") or p.get("merchandising_summary") or p.get("summary") or ""
                    desc = clean_html_text(raw_summary)

                    asin = p.get("asin")
                    if asin:
                        results.append({
                            "title": p.get("title"),
                            "author": ", ".join(authors) if authors else "Unknown Author",
                            "narrator": ", ".join(narrators) if narrators else "",
                            "series": series_name,
                            "series_sequence": series_seq,
                            "publish_year": publish_year,
                            "publisher": publisher,
                            "genres": genres_str,
                            "description": desc,
                            "cover_url": cover_url,
                            "asin": asin,
                            "source": "Audible",
                            "url": f"https://www.audible.com/pd/{asin}"
                        })
    except Exception as e:
        print(f"[Lookup] Audible search error: {e}")
    return results

def search_google_books(query: str, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search Google Books API for candidates."""
    results = []
    clean_q = query.strip()
    if not clean_q:
        return results

    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(clean_q)}&maxResults=6"
        if api_key:
            url += f"&key={api_key}"
            
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json"
        })
        with urllib.request.urlopen(req, timeout=6) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                for item in data.get("items", []):
                    vi = item.get("volumeInfo", {})
                    title = vi.get("title", "")
                    subtitle = vi.get("subtitle", "")
                    authors = vi.get("authors", [])
                    
                    series_name = ""
                    series_seq = ""
                    full_text = f"{title} {subtitle}"
                    series_m = re.search(r'\((.*?),\s*(?:Book|#)?\s*([0-9.]+)\)', full_text, re.IGNORECASE)
                    if not series_m:
                        series_m = re.search(r'(.*?),\s*Book\s*([0-9.]+)', full_text, re.IGNORECASE)
                    if series_m:
                        series_name = series_m.group(1).strip()
                        series_seq = series_m.group(2).strip()

                    image_links = vi.get("imageLinks", {})
                    cover_url = image_links.get("thumbnail") or image_links.get("smallThumbnail") or ""
                    if cover_url.startswith("http://"):
                        cover_url = cover_url.replace("http://", "https://")

                    publisher = (vi.get("publisher") or "").strip()
                    raw_date = (vi.get("publishedDate") or "").strip()
                    publish_year = raw_date[:4] if len(raw_date) >= 4 and raw_date[:4].isdigit() else raw_date
                    categories = vi.get("categories", [])
                    genres_str = ", ".join([c.strip() for c in categories if c.strip()]) if isinstance(categories, list) else str(categories)
                    desc = clean_html_text(vi.get("description", "") or "")

                    results.append({
                        "title": title,
                        "author": ", ".join(authors) if authors else "Unknown Author",
                        "narrator": "",
                        "series": series_name,
                        "series_sequence": series_seq,
                        "publish_year": publish_year,
                        "publisher": publisher,
                        "genres": genres_str,
                        "description": desc,
                        "cover_url": cover_url,
                        "source": "Google Books",
                        "url": vi.get("infoLink", "")
                    })
    except Exception:
        pass
    return results

def search_book_matches(query: str, author: str = "") -> List[Dict[str, Any]]:
    """Query Goodreads, Audible, and Google Books concurrently and merge candidate matches."""
    clean_query = query.strip()
    if not clean_query:
        return []

    candidates: List[Dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        future_aud = executor.submit(search_audible, clean_query, author)
        future_gr = executor.submit(search_goodreads, f"{clean_query} {author}".strip())
        future_gb = executor.submit(search_google_books, f"{clean_query} {author}".strip())

        try:
            candidates.extend(future_aud.result())
        except Exception:
            pass

        try:
            candidates.extend(future_gr.result())
        except Exception:
            pass

        try:
            candidates.extend(future_gb.result())
        except Exception:
            pass

    # Deduplicate matches by normalized (title + author)
    seen = set()
    deduped = []
    for c in candidates:
        norm_title = re.sub(r'[^a-z0-9]', '', c.get("title", "").lower())
        norm_author = re.sub(r'[^a-z0-9]', '', c.get("author", "").lower()[:15])
        key = f"{norm_title}_{norm_author}"
        if key not in seen and norm_title:
            seen.add(key)
            deduped.append(c)

    # Rank results: prioritize candidates with Series info and Cover Art
    def rank_score(item: Dict[str, Any]) -> int:
        score = 0
        if item.get("series"):
            score += 5
        if item.get("series_sequence"):
            score += 3
        if item.get("cover_url"):
            score += 3
        if item.get("narrator"):
            score += 3
        if item.get("description"):
            score += 3
        if item.get("genres"):
            score += 2
        if item.get("publisher"):
            score += 2
        if item.get("publish_year"):
            score += 1
        if item.get("source") == "Goodreads":
            score += 1
        return score

    deduped.sort(key=rank_score, reverse=True)
    return deduped[:12]

def download_remote_cover(cover_url: str, book_id: str) -> Optional[str]:
    """Download a remote cover image and store it in data/covers/{book_id}.jpg."""
    if not cover_url or not book_id:
        return None

    try:
        req = urllib.request.Request(cover_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                img_bytes = resp.read()
                if len(img_bytes) < 500:
                    return None

                data_dir = Path(os.getenv("DATA_DIR", "data"))
                covers_dir = data_dir / "covers"
                covers_dir.mkdir(parents=True, exist_ok=True)
                
                target = covers_dir / f"{book_id}.jpg"
                with open(target, "wb") as f:
                    f.write(img_bytes)

                return f"/api/books/{book_id}/cover"
    except Exception as e:
        print(f"[Lookup] Failed downloading cover from {cover_url}: {e}")
    return None

def search_openlibrary_toc(title: str, author: str = "") -> Optional[List[str]]:
    """Fallback: Search OpenLibrary for print Table of Contents."""
    try:
        q = urllib.parse.quote(title)
        url = f"https://openlibrary.org/search.json?title={q}&limit=3"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=8) as resp:
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
