#!/usr/bin/env python3
import re
import json
import os
import urllib.request
import sys

# Conversion from the Martini bible text, copyright free, available at https://archive.org/stream/bibbia-martini/Bibbia%20Martini_djvu.txt

# Mapping from Italian abbreviations to English names (DRA format, enriched with the proprietary text formulae for compatibility)
BOOK_MAP = {
    "Gen": "Genesis",
    "Eso": "Exodus",
    "Le": "Leviticus",
    "Nu": "Numbers",
    "De": "Deuteronomy",
    "Gios": "Josue",
    "Giudic": "Judges",
    "Ru": "Ruth",
    "1Sam": "1 Kings",
    "2Sam": "2 Kings",
    "1Re": "3 Kings",
    "2Re": "4 Kings",
    "1Cr": "1 Paralipomenon",
    "2Cr": "2 Paralipomenon",
    "Esd": "1 Esdras",
    "Ne": "2 Esdras",
    "Tob": "Tobias",
    "Giudit": "Judith",
    "Est": "Esther",
    "1Macc": "1 Machabees",
    "2Macc": "2 Machabees",
    "Giob": "Job",
    "Sal": "Psalms",
    "Prov": "Proverbs",
    "Ec": "Ecclesiastes",
    "Cant": "Canticles",
    "CC": "Canticles",
    "Sap": "Wisdom",
    "Sir": "Ecclesiasticus",
    "Is": "Isaias",
    "Ger": "Jeremias",
    "Lam": "Lamentations",
    "Bar": "Baruch",
    "Ez": "Ezechiel",
    "Da": "Daniel",
    "Os": "Osee",
    "Gioe": "Joel",
    "Am": "Amos",
    "Abac": "Habacuc",
    "So": "Sophonias",
    "Ag": "Aggeus",
    "Zac": "Zacharias",
    "Mal": "Malachias",
    "Na": "Nahum",
    "Abd": "Abdias",
    "Mi": "Micheas",
    "Gion": "Jonas",
    "Mt": "Matthew",
    "Mc": "Mark",
    "Lc": "Luke",
    "Gv": "John",
    "At": "Acts",
    "Rm": "Romans",
    "1Cor": "1 Corinthians",
    "2Cor": "2 Corinthians",
    "Gal": "Galatians",
    "Ef": "Ephesians",
    "Fili": "Philippians",
    "Col": "Colossians",
    "1Ts": "1 Thessalonians",
    "2Ts": "2 Thessalonians",
    "1Tm": "1 Timothy",
    "ITm": "1 Timothy",
    "1ITm": "1 Timothy",
    "2Tm": "2 Timothy",
    "Tt": "Titus",
    "Filem": "Philemon",
    "Fm": "Philemon",
    "Eb": "Hebrews",
    "Giac": "James",
    "1Pt": "1 Peter",
    "1P": "1 Peter",
    "2Pt": "2 Peter",
    "2P": "2 Peter",
    "1Gv": "1 John",
    "1G": "1 John",
    "2Gv": "2 John",
    "2G": "2 John",
    "3Gv": "3 John",
    "3G": "3 John",
    "Gd": "Jude",
    "Giuda": "Jude",
    "Ap": "Apocalypse",
}

def convert_bibbia_to_json(input_file, output_dir):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match book markers: optional digit prefix + letters + chapter + optional :verse
    book_pattern = r'^(\d?[A-Za-z]+) (\d+)(?::(\d+))?'
    book_starts = list(re.finditer(book_pattern, content, re.MULTILINE))

    # Group by book abbreviation
    books = {}
    for match in book_starts:
        abbr = match.group(1)
        if abbr not in books:
            books[abbr] = []
        books[abbr].append(match)

    for abbr, matches in books.items():
        if abbr not in BOOK_MAP:
            print(f"WARNING: no mapping for {abbr}")
            continue

        book_name = BOOK_MAP[abbr]
        print(f"Processing {abbr} -> {book_name}...")

        chapters = {}
        for i, match in enumerate(matches):
            chapter_num = match.group(2)
            verse_start_num = match.group(3) or "1"
            start_pos = match.start()

            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                next_book_start = len(content)
                for other_abbr, other_matches in books.items():
                    for other_match in other_matches:
                        if other_match.start() > start_pos:
                            next_book_start = min(next_book_start, other_match.start())
                            break
                end_pos = next_book_start

            chapter_text = content[start_pos:end_pos].strip()
            chapter_text = re.sub(r'\d?[A-Za-z]+ \d+(?::\d+)?\s*', '', chapter_text, count=1)
            chapter_text = re.sub(r'\n', ' ', chapter_text)
            chapter_text = re.sub(r'\s+', ' ', chapter_text).strip()

            verse_splits = re.split(r'[.?!:,;]\s+(\d+)\s+', chapter_text)

            verses = {}
            if verse_splits:
                first_verse_text = verse_splits[0].strip()
                if first_verse_text:
                    verses[verse_start_num] = first_verse_text

                for j in range(1, len(verse_splits), 2):
                    if j + 1 < len(verse_splits):
                        verse_num = verse_splits[j]
                        verse_text = verse_splits[j + 1].strip()
                        if verse_text:
                            verses[verse_num] = verse_text

            if verses:
                chapters[chapter_num] = verses

        if chapters:
            output_file = os.path.join(output_dir, f"{book_name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chapters, f, ensure_ascii=False, indent=1)
            print(f"  Created {output_file} with {len(chapters)} chapters")

def download_bibbia(url):
    print(f"Downloading from {url}...")
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    return content

def main():
    url = 'https://archive.org/stream/bibbia-martini/Bibbia%20Martini_djvu.txt'
    output_dir = 'books'
    os.makedirs(output_dir, exist_ok=True)

    cache_file = os.path.join(output_dir, 'bibbia-martini.txt')

    if os.path.exists(cache_file):
        print(f"Using cached {cache_file}")
    else:
        content = download_bibbia(url)
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cached to {cache_file}")

    convert_bibbia_to_json(cache_file, output_dir)

if __name__ == '__main__':
    main()
