#!/usr/bin/env python3
"""
scrape_saints_catholic_org.py — Scrapes the top 250 saints from Catholic.org and
downloads their portrait images.

Outputs:
    content/saints/en/saints.json              (250+ saints, English)
    content/saints/{es,fr,lt,pt-BR,pt-PT,zh-CN}/saints.json  (new saints seeded with EN text)
    app/src/main/assets/saints/<id>.webp       (portrait images, ~150px wide)

Usage:
    pip install requests beautifulsoup4 pillow
    python scripts/scrape_saints_catholic_org.py

Notes:
    - Images from https://www.catholic.org/files/images/saints/ are classical religious
      artwork reproductions (paintings, icons, engravings). Most depicted works are
      centuries old and in the public domain. Catholic.org's /saints/ paths are not
      disallowed in robots.txt.
    - Existing saint bios (the original 53) are kept as-is; only images are added for them.
    - A 1-second delay is used between HTTP requests to be polite to the server.
"""

import base64
import io
import json
import os
import re
import sys
import time
import unicodedata

import requests
from bs4 import BeautifulSoup
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")
IMAGE_OUT_DIR = os.path.join(REPO_ROOT, "app", "src", "main", "assets", "saints")
EN_JSON = os.path.join(CONTENT_DIR, "saints", "en", "saints.json")
OTHER_LANGS = ["es", "fr", "lt", "pt-BR", "pt-PT", "zh-CN"]

BASE_URL = "https://www.catholic.org"
POPULAR_URL = f"{BASE_URL}/saints/popular.php"
REQUEST_DELAY = 1.0
IMAGE_MAX_WIDTH = 160
IMAGE_WEBP_QUALITY = 85

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DeFideApp/1.0)"}

# Prepositions to strip when building slug IDs
SLUG_STOP_WORDS = {"of", "the", "de", "di", "da", "del", "von", "van", "le", "la", "des"}


def slugify(name: str) -> str:
    """Convert a saint name to a URL-slug-style ID, stripping title prefixes
    and filler prepositions to match the existing naming convention."""
    name = re.sub(r"^(Saint|St\.|Blessed|Bl\.|Venerable|Ven\.)\s+", "", name, flags=re.I).strip()
    parts = name.split()
    parts = [p for p in parts if p.lower() not in SLUG_STOP_WORDS]
    name = " ".join(parts)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-z0-9\s]", "", name.lower())
    name = re.sub(r"\s+", "-", name.strip())
    name = re.sub(r"-+", "-", name)
    return name


def clean_name(raw: str) -> str:
    """Normalise 'St. X' to 'Saint X'; keep 'Blessed X' as-is."""
    raw = raw.strip()
    raw = re.sub(r"^St\.\s+", "Saint ", raw)
    raw = re.sub(r"^Bl\.\s+", "Blessed ", raw)
    return raw


def first_sentences(text: str, n: int = 2) -> str:
    """Return the first n sentences of text."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(sentences[:n]).strip()


def infer_category(bio: str, name: str) -> str:
    b = bio.lower()
    if any(w in b for w in ["martyr", "martyrdom", "martyred", "stoned to death",
                              "beheaded", "burned at the stake", "crucified", "put to death"]):
        return "martyr"
    if any(w in b for w in ["apostle", "twelve apostles", "one of the twelve"]):
        return "apostle"
    if "doctor of the church" in b:
        return "doctor"
    if any(w in b for w in ["virgin", "virginity", "vowed chastity", "consecrated virgin"]):
        return "virgin"
    if any(w in b for w in ["bishop", "archbishop", "patriarch", "cardinal"]):
        return "bishop"
    return "confessor"


def get_soup(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def scrape_popular_page() -> list[tuple[str, str]]:
    """Return list of (name, detail_url) for top 250 saints."""
    print("Fetching popular saints page...")
    soup = get_soup(POPULAR_URL)
    links = soup.find_all("a", href=lambda h: h and "saint.php?saint_id=" in h)
    seen_ids = set()
    results = []
    for a in links:
        href = a["href"]
        if not href.startswith("http"):
            href = BASE_URL + href
        sid = re.search(r"saint_id=(\d+)", href)
        if not sid:
            continue
        sid = sid.group(1)
        if sid in seen_ids:
            continue
        seen_ids.add(sid)
        name = a.get_text(strip=True)
        if name:
            results.append((name, href))
        if len(results) >= 250:
            break
    print(f"  Found {len(results)} saints.")
    return results


def scrape_saint_detail(url: str) -> dict:
    """Scrape a saint detail page and return extracted fields."""
    soup = get_soup(url)

    # Name
    h1 = soup.find("h1")
    name_raw = h1.get_text(strip=True) if h1 else ""

    # Feast day and patronage from the structured facts section
    text_lines = [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]
    feast_date = None
    patronage = None
    for i, line in enumerate(text_lines):
        if line.lower() == "feastday:" and i + 1 < len(text_lines):
            feast_date = text_lines[i + 1].strip()
        if line.lower() == "patron:" and i + 1 < len(text_lines):
            pat = text_lines[i + 1].strip()
            # Strip trailing site navigation text
            pat = re.split(r"\s+Author and Publisher", pat)[0]
            pat = re.split(r"\s+Catholic Online", pat)[0]
            patronage = pat if len(pat) < 300 else pat[:300]

    # Bio paragraphs: skip the first paragraph (author/nav boilerplate)
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 80]
    # Drop the first para if it looks like site nav
    if paras and ("Author and Publisher" in paras[0] or "Catholic Online" in paras[0]):
        paras = paras[1:]

    full_bio = " ".join(paras).strip() if paras else ""
    short_bio = first_sentences(paras[0], 2) if paras else ""

    # Image URL
    image_url = None
    for m in re.finditer(r"https?://[^\s\"']+/files/images/saints/[^\s\"']+\.(?:jpg|jpeg|png|webp)", soup.decode()):
        image_url = m.group(0)
        break

    return {
        "name_raw": name_raw,
        "feast_date": feast_date,
        "patronage": patronage,
        "short_bio": short_bio,
        "full_bio": full_bio,
        "image_url": image_url,
    }


def download_image(url: str, saint_id: str) -> bool:
    """Download and save a saint portrait as WebP. Returns True on success."""
    out_path = os.path.join(IMAGE_OUT_DIR, f"{saint_id}.webp")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        # Resize maintaining aspect ratio
        w, h = im.size
        if w > IMAGE_MAX_WIDTH:
            new_h = int(h * IMAGE_MAX_WIDTH / w)
            im = im.resize((IMAGE_MAX_WIDTH, new_h), Image.LANCZOS)
        im.save(out_path, "WEBP", quality=IMAGE_WEBP_QUALITY)
        return True
    except Exception as e:
        print(f"    WARNING: image download failed for {saint_id}: {e}")
        return False


def main():
    os.makedirs(IMAGE_OUT_DIR, exist_ok=True)

    # Load existing English saints
    with open(EN_JSON, encoding="utf-8") as f:
        existing_saints: list[dict] = json.load(f)
    existing_by_id = {s["id"]: s for s in existing_saints}
    print(f"Loaded {len(existing_saints)} existing saints.")

    # Scrape popular page
    popular = scrape_popular_page()

    new_saints_ordered = []   # saints in top-250 order
    processed_ids = set()

    for rank, (name_raw, url) in enumerate(popular, start=1):
        slug = slugify(name_raw)
        print(f"\n[{rank}/250] {name_raw!r} -> slug={slug!r}")

        # Check if we already have this saint
        if slug in existing_by_id:
            saint = existing_by_id[slug].copy()
            print(f"  Matched existing saint: {slug}")
            need_scrape = True   # still need image URL
        else:
            saint = None
            need_scrape = True

        image_url = None
        if need_scrape:
            time.sleep(REQUEST_DELAY)
            try:
                detail = scrape_saint_detail(url)
                image_url = detail["image_url"]
                if saint is None:
                    # Brand new saint
                    clean = clean_name(detail["name_raw"] or name_raw)
                    full_bio = detail["full_bio"]
                    saint = {
                        "id": slug,
                        "name": clean,
                        "feast_date": detail["feast_date"],
                        "short_bio": detail["short_bio"] or f"{clean}, venerated as a saint in the Catholic Church.",
                        "full_bio": full_bio or f"{clean} is honored as a saint in the Catholic Church.",
                        "patronage": detail["patronage"],
                        "category": infer_category(full_bio, clean),
                    }
                    print(f"  New saint: {clean!r}, feast={detail['feast_date']}, category={saint['category']}")
                else:
                    print(f"  Using existing bio; image_url={image_url!r}")
            except Exception as e:
                print(f"  ERROR scraping {url}: {e}")
                if saint is None:
                    saint = {
                        "id": slug,
                        "name": clean_name(name_raw),
                        "feast_date": None,
                        "short_bio": f"{clean_name(name_raw)}, venerated as a saint in the Catholic Church.",
                        "full_bio": f"{clean_name(name_raw)} is honored as a saint in the Catholic Church.",
                        "patronage": None,
                        "category": "confessor",
                    }

        # Download image
        if image_url:
            ok = download_image(image_url, slug)
            print(f"  Image {'saved' if ok else 'FAILED'}: {slug}.webp")

        new_saints_ordered.append(saint)
        processed_ids.add(slug)

    # Append any existing saints not in the top 250
    for s in existing_saints:
        if s["id"] not in processed_ids:
            print(f"\nRetaining existing saint not in top 250: {s['id']!r}")
            new_saints_ordered.append(s)

    # Write English JSON
    with open(EN_JSON, "w", encoding="utf-8") as f:
        json.dump(new_saints_ordered, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {len(new_saints_ordered)} saints to {EN_JSON}")

    # Seed other language files: add new saints (using English text) while
    # preserving existing translated entries.
    for lang in OTHER_LANGS:
        lang_path = os.path.join(CONTENT_DIR, "saints", lang, "saints.json")
        if not os.path.exists(lang_path):
            print(f"Skipping {lang}: file not found")
            continue
        with open(lang_path, encoding="utf-8") as f:
            lang_saints = json.load(f)
        lang_by_id = {s["id"]: s for s in lang_saints}
        merged = list(lang_saints)
        added = 0
        for s in new_saints_ordered:
            if s["id"] not in lang_by_id:
                merged.append(s.copy())
                added += 1
        with open(lang_path, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=False, indent=2)
        print(f"  {lang}: added {added} new saints -> {len(merged)} total")

    print("\nDone. Run scripts/compile_content.py to rebuild the database.")


if __name__ == "__main__":
    main()
