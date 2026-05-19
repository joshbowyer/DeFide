#!/usr/bin/env python3
"""
compile_content.py — Builds defide_content.db from source JSON files.

Usage:
    python scripts/compile_content.py

Output:
    app/src/main/assets/databases/defide_content.db

Expected source layout:
    content/bible/dra/metadata.json
    content/bible/dra/books/<BookName>.json   (one per book, DR naming)
    content/bible/web-c/books/<BookName>.json (one per book, DR naming)
    content/prayers/prayers.json
    content/novenas/novenas.json
    content/catechism/ccc_paragraphs.json
"""

import json
import os
import re
import sqlite3
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")
OUT_DB = os.path.join(REPO_ROOT, "app", "src", "main", "assets", "databases", "defide_content.db")

# ---------------------------------------------------------------------------
# Canonical Catholic book manifest
# Keys are the DR file names (without .json).
# Values: (book_number, testament, short_name, full_name)
# ---------------------------------------------------------------------------
BOOK_MANIFEST = {
    "Genesis":          (1,  "OT", "Gen",    "Genesis"),
    "Exodus":           (2,  "OT", "Ex",     "Exodus"),
    "Leviticus":        (3,  "OT", "Lev",    "Leviticus"),
    "Numbers":          (4,  "OT", "Num",    "Numbers"),
    "Deuteronomy":      (5,  "OT", "Deut",   "Deuteronomy"),
    "Josue":            (6,  "OT", "Josh",   "Joshua"),
    "Judges":           (7,  "OT", "Judg",   "Judges"),
    "Ruth":             (8,  "OT", "Ruth",   "Ruth"),
    "1 Kings":          (9,  "OT", "1 Sam",  "1 Samuel"),
    "2 Kings":          (10, "OT", "2 Sam",  "2 Samuel"),
    "3 Kings":          (11, "OT", "1 Kgs",  "1 Kings"),
    "4 Kings":          (12, "OT", "2 Kgs",  "2 Kings"),
    "1 Paralipomenon":  (13, "OT", "1 Chr",  "1 Chronicles"),
    "2 Paralipomenon":  (14, "OT", "2 Chr",  "2 Chronicles"),
    "1 Esdras":         (15, "OT", "Ezra",   "Ezra"),
    "2 Esdras":         (16, "OT", "Neh",    "Nehemiah"),
    "Tobias":           (17, "DC", "Tob",    "Tobit"),
    "Judith":           (18, "DC", "Jdt",    "Judith"),
    "Esther":           (19, "OT", "Esth",   "Esther"),
    "1 Machabees":      (20, "DC", "1 Mac",  "1 Maccabees"),
    "2 Machabees":      (21, "DC", "2 Mac",  "2 Maccabees"),
    "Job":              (22, "OT", "Job",    "Job"),
    "Psalms":           (23, "OT", "Ps",     "Psalms"),
    "Proverbs":         (24, "OT", "Prov",   "Proverbs"),
    "Ecclesiastes":     (25, "OT", "Eccl",   "Ecclesiastes"),
    "Canticles":        (26, "OT", "Song",   "Song of Songs"),
    "Wisdom":           (27, "DC", "Wis",    "Wisdom"),
    "Ecclesiasticus":   (28, "DC", "Sir",    "Sirach"),
    "Isaias":           (29, "OT", "Isa",    "Isaiah"),
    "Jeremias":         (30, "OT", "Jer",    "Jeremiah"),
    "Lamentations":     (31, "OT", "Lam",    "Lamentations"),
    "Baruch":           (32, "DC", "Bar",    "Baruch"),
    "Ezechiel":         (33, "OT", "Ezek",   "Ezekiel"),
    "Daniel":           (34, "OT", "Dan",    "Daniel"),
    "Osee":             (35, "OT", "Hos",    "Hosea"),
    "Joel":             (36, "OT", "Joel",   "Joel"),
    "Amos":             (37, "OT", "Amos",   "Amos"),
    "Abdias":           (38, "OT", "Obad",   "Obadiah"),
    "Jonas":            (39, "OT", "Jon",    "Jonah"),
    "Micheas":          (40, "OT", "Mic",    "Micah"),
    "Nahum":            (41, "OT", "Nah",    "Nahum"),
    "Habacuc":          (42, "OT", "Hab",    "Habakkuk"),
    "Sophonias":        (43, "OT", "Zeph",   "Zephaniah"),
    "Aggeus":           (44, "OT", "Hag",    "Haggai"),
    "Zacharias":        (45, "OT", "Zech",   "Zechariah"),
    "Malachias":        (46, "OT", "Mal",    "Malachi"),
    "Matthew":          (47, "NT", "Matt",   "Matthew"),
    "Mark":             (48, "NT", "Mark",   "Mark"),
    "Luke":             (49, "NT", "Luke",   "Luke"),
    "John":             (50, "NT", "John",   "John"),
    "Acts":             (51, "NT", "Acts",   "Acts"),
    "Romans":           (52, "NT", "Rom",    "Romans"),
    "1 Corinthians":    (53, "NT", "1 Cor",  "1 Corinthians"),
    "2 Corinthians":    (54, "NT", "2 Cor",  "2 Corinthians"),
    "Galatians":        (55, "NT", "Gal",    "Galatians"),
    "Ephesians":        (56, "NT", "Eph",    "Ephesians"),
    "Philippians":      (57, "NT", "Phil",   "Philippians"),
    "Colossians":       (58, "NT", "Col",    "Colossians"),
    "1 Thessalonians":  (59, "NT", "1 Thess","1 Thessalonians"),
    "2 Thessalonians":  (60, "NT", "2 Thess","2 Thessalonians"),
    "1 Timothy":        (61, "NT", "1 Tim",  "1 Timothy"),
    "2 Timothy":        (62, "NT", "2 Tim",  "2 Timothy"),
    "Titus":            (63, "NT", "Titus",  "Titus"),
    "Philemon":         (64, "NT", "Phlm",   "Philemon"),
    "Hebrews":          (65, "NT", "Heb",    "Hebrews"),
    "James":            (66, "NT", "Jas",    "James"),
    "1 Peter":          (67, "NT", "1 Pet",  "1 Peter"),
    "2 Peter":          (68, "NT", "2 Pet",  "2 Peter"),
    "1 John":           (69, "NT", "1 Jn",   "1 John"),
    "2 John":           (70, "NT", "2 Jn",   "2 John"),
    "3 John":           (71, "NT", "3 Jn",   "3 John"),
    "Jude":             (72, "NT", "Jude",   "Jude"),
    "Apocalypse":       (73, "NT", "Rev",    "Revelation"),
}


# ---------------------------------------------------------------------------
# NRSVCE book manifest
# Keys are the book names as they appear in nrsvce.json.
# Values: (book_number, testament, short_name, full_name, dr_name)
# book_numbers mirror the DRA manifest; extra DC-only books get 74-77.
# ---------------------------------------------------------------------------
NRSVCE_BOOK_MANIFEST = {
    # Old Testament
    "Genesis":           (1,  "OT", "Gen",       "Genesis",              "Genesis"),
    "Exodus":            (2,  "OT", "Ex",         "Exodus",               "Exodus"),
    "Leviticus":         (3,  "OT", "Lev",        "Leviticus",            "Leviticus"),
    "Numbers":           (4,  "OT", "Num",        "Numbers",              "Numbers"),
    "Deuteronomy":       (5,  "OT", "Deut",       "Deuteronomy",          "Deuteronomy"),
    "Joshua":            (6,  "OT", "Josh",       "Joshua",               "Joshua"),
    "Judges":            (7,  "OT", "Judg",       "Judges",               "Judges"),
    "Ruth":              (8,  "OT", "Ruth",       "Ruth",                 "Ruth"),
    "1 Samuel":          (9,  "OT", "1 Sam",      "1 Samuel",             "1 Samuel"),
    "2 Samuel":          (10, "OT", "2 Sam",      "2 Samuel",             "2 Samuel"),
    "1 Kings":           (11, "OT", "1 Kgs",      "1 Kings",              "1 Kings"),
    "2 Kings":           (12, "OT", "2 Kgs",      "2 Kings",              "2 Kings"),
    "1 Chronicles":      (13, "OT", "1 Chr",      "1 Chronicles",         "1 Chronicles"),
    "2 Chronicles":      (14, "OT", "2 Chr",      "2 Chronicles",         "2 Chronicles"),
    "Ezra":              (15, "OT", "Ezra",       "Ezra",                 "Ezra"),
    "Nehemiah":          (16, "OT", "Neh",        "Nehemiah",             "Nehemiah"),
    "Esther":            (19, "OT", "Esth",       "Esther",               "Esther"),
    "Job":               (22, "OT", "Job",        "Job",                  "Job"),
    "Psalms":            (23, "OT", "Ps",         "Psalms",               "Psalms"),
    "Proverbs":          (24, "OT", "Prov",       "Proverbs",             "Proverbs"),
    "Ecclesiastes":      (25, "OT", "Eccl",       "Ecclesiastes",         "Ecclesiastes"),
    "Song of Solomon":   (26, "OT", "Song",       "Song of Songs",        "Song of Solomon"),
    "Isaiah":            (29, "OT", "Isa",        "Isaiah",               "Isaiah"),
    "Jeremiah":          (30, "OT", "Jer",        "Jeremiah",             "Jeremiah"),
    "Lamentations":      (31, "OT", "Lam",        "Lamentations",         "Lamentations"),
    "Ezekiel":           (33, "OT", "Ezek",       "Ezekiel",              "Ezekiel"),
    "Daniel":            (34, "OT", "Dan",        "Daniel",               "Daniel"),
    "Hosea":             (35, "OT", "Hos",        "Hosea",                "Hosea"),
    "Joel":              (36, "OT", "Joel",       "Joel",                 "Joel"),
    "Amos":              (37, "OT", "Amos",       "Amos",                 "Amos"),
    "Obadiah":           (38, "OT", "Obad",       "Obadiah",              "Obadiah"),
    "Jonah":             (39, "OT", "Jon",        "Jonah",                "Jonah"),
    "Micah":             (40, "OT", "Mic",        "Micah",                "Micah"),
    "Nahum":             (41, "OT", "Nah",        "Nahum",                "Nahum"),
    "Habakkuk":          (42, "OT", "Hab",        "Habakkuk",             "Habakkuk"),
    "Zephaniah":         (43, "OT", "Zeph",       "Zephaniah",            "Zephaniah"),
    "Haggai":            (44, "OT", "Hag",        "Haggai",               "Haggai"),
    "Zechariah":         (45, "OT", "Zech",       "Zechariah",            "Zechariah"),
    "Malachi":           (46, "OT", "Mal",        "Malachi",              "Malachi"),
    # Deuterocanonical
    "Tobit":             (17, "DC", "Tob",        "Tobit",                "Tobit"),
    "Judith":            (18, "DC", "Jdt",        "Judith",               "Judith"),
    "Greek Esther":      (74, "DC", "Grk Esth",   "Greek Esther",         "Greek Esther"),
    "1 Maccabees":       (20, "DC", "1 Mac",      "1 Maccabees",          "1 Maccabees"),
    "2 Maccabees":       (21, "DC", "2 Mac",      "2 Maccabees",          "2 Maccabees"),
    "Wisdom":            (27, "DC", "Wis",        "Wisdom",               "Wisdom"),
    "Sirach":            (28, "DC", "Sir",        "Sirach",               "Sirach"),
    "Baruch":            (32, "DC", "Bar",        "Baruch",               "Baruch"),
    "Prayer Of Azariah": (75, "DC", "Pr Azar",    "Prayer of Azariah",    "Prayer Of Azariah"),
    "Susanna":           (76, "DC", "Sus",        "Susanna",              "Susanna"),
    "Bel And The Dragon":(77, "DC", "Bel",        "Bel and the Dragon",   "Bel And The Dragon"),
    # New Testament
    "Matthew":           (47, "NT", "Matt",       "Matthew",              "Matthew"),
    "Mark":              (48, "NT", "Mark",       "Mark",                 "Mark"),
    "Luke":              (49, "NT", "Luke",       "Luke",                 "Luke"),
    "John":              (50, "NT", "John",       "John",                 "John"),
    "Acts":              (51, "NT", "Acts",       "Acts",                 "Acts"),
    "Romans":            (52, "NT", "Rom",        "Romans",               "Romans"),
    "1 Corinthians":     (53, "NT", "1 Cor",      "1 Corinthians",        "1 Corinthians"),
    "2 Corinthians":     (54, "NT", "2 Cor",      "2 Corinthians",        "2 Corinthians"),
    "Galatians":         (55, "NT", "Gal",        "Galatians",            "Galatians"),
    "Ephesians":         (56, "NT", "Eph",        "Ephesians",            "Ephesians"),
    "Philippians":       (57, "NT", "Phil",       "Philippians",          "Philippians"),
    "Colossians":        (58, "NT", "Col",        "Colossians",           "Colossians"),
    "1 Thessalonians":   (59, "NT", "1 Thess",    "1 Thessalonians",      "1 Thessalonians"),
    "2 Thessalonians":   (60, "NT", "2 Thess",    "2 Thessalonians",      "2 Thessalonians"),
    "1 Timothy":         (61, "NT", "1 Tim",      "1 Timothy",            "1 Timothy"),
    "2 Timothy":         (62, "NT", "2 Tim",      "2 Timothy",            "2 Timothy"),
    "Titus":             (63, "NT", "Titus",      "Titus",                "Titus"),
    "Philemon":          (64, "NT", "Phlm",       "Philemon",             "Philemon"),
    "Hebrews":           (65, "NT", "Heb",        "Hebrews",              "Hebrews"),
    "James":             (66, "NT", "Jas",        "James",                "James"),
    "1 Peter":           (67, "NT", "1 Pet",      "1 Peter",              "1 Peter"),
    "2 Peter":           (68, "NT", "2 Pet",      "2 Peter",              "2 Peter"),
    "1 John":            (69, "NT", "1 Jn",       "1 John",               "1 John"),
    "2 John":            (70, "NT", "2 Jn",       "2 John",               "2 John"),
    "3 John":            (71, "NT", "3 Jn",       "3 John",               "3 John"),
    "Jude":              (72, "NT", "Jude",       "Jude",                 "Jude"),
    "Revelation":        (73, "NT", "Rev",        "Revelation",           "Revelation"),
}

# Superscript digits Unicode → strip from start of verse text
_SUPERSCRIPT_RE = re.compile(r'^[⁰¹²³⁴⁵⁶⁷⁸⁹]+\s*')


def _clean_nrsvce_verse(text: str) -> str:
    """Strip leading superscript verse number and normalize whitespace."""
    return _SUPERSCRIPT_RE.sub('', text).strip()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        PRAGMA journal_mode=WAL;

        -- Bible
        CREATE TABLE IF NOT EXISTS translations (
            id      TEXT PRIMARY KEY,
            name    TEXT NOT NULL,
            language TEXT NOT NULL,
            license TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS books (
            id              INTEGER PRIMARY KEY,
            translation_id  TEXT NOT NULL,
            book_number     INTEGER NOT NULL,
            testament       TEXT NOT NULL,
            short_name      TEXT NOT NULL,
            full_name       TEXT NOT NULL,
            dr_name         TEXT NOT NULL,
            FOREIGN KEY (translation_id) REFERENCES translations(id)
        );

        CREATE TABLE IF NOT EXISTS verses (
            id      INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL,
            chapter INTEGER NOT NULL,
            verse   INTEGER NOT NULL,
            text    TEXT NOT NULL,
            FOREIGN KEY (book_id) REFERENCES books(id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS verses_fts USING fts4(
            content="verses",
            text
        );

        -- Catechism
        CREATE TABLE IF NOT EXISTS ccc_sections (
            id      INTEGER PRIMARY KEY,
            part    INTEGER,
            section INTEGER,
            chapter INTEGER,
            article INTEGER,
            heading TEXT,
            body    TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS ccc_fts USING fts4(
            content="ccc_sections",
            heading, body
        );

        -- Baltimore Catechism
        CREATE TABLE IF NOT EXISTS baltimore_catechism (
            id       INTEGER PRIMARY KEY,
            number   INTEGER NOT NULL,
            lesson   INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer   TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_bc_lesson ON baltimore_catechism(lesson, number);

        -- Prayers
        CREATE TABLE IF NOT EXISTS prayers (
            id       TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'en',
            title    TEXT NOT NULL,
            body     TEXT NOT NULL,
            source   TEXT,
            category TEXT NOT NULL,
            PRIMARY KEY (id, language)
        );

        CREATE TABLE IF NOT EXISTS prayer_tags (
            prayer_id TEXT NOT NULL,
            language  TEXT NOT NULL DEFAULT 'en',
            tag       TEXT NOT NULL,
            PRIMARY KEY (prayer_id, language, tag)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS prayers_fts USING fts4(
            content="prayers",
            title, body
        );

        -- Novenas
        CREATE TABLE IF NOT EXISTS novenas (
            id          TEXT NOT NULL,
            language    TEXT NOT NULL DEFAULT 'en',
            title       TEXT NOT NULL,
            description TEXT,
            total_days  INTEGER NOT NULL DEFAULT 9,
            feast_day   TEXT,
            PRIMARY KEY (id, language)
        );

        CREATE TABLE IF NOT EXISTS novena_days (
            id         INTEGER PRIMARY KEY,
            novena_id  TEXT NOT NULL,
            language   TEXT NOT NULL DEFAULT 'en',
            day_number INTEGER NOT NULL,
            title      TEXT,
            body       TEXT NOT NULL
        );

        -- Rosary
        CREATE TABLE IF NOT EXISTS mysteries (
            id               TEXT NOT NULL,
            language         TEXT NOT NULL DEFAULT 'en',
            name             TEXT NOT NULL,
            traditional_days TEXT,
            PRIMARY KEY (id, language)
        );

        CREATE TABLE IF NOT EXISTS mystery_beads (
            id                 INTEGER PRIMARY KEY,
            mystery_id         TEXT NOT NULL,
            language           TEXT NOT NULL DEFAULT 'en',
            variant            TEXT NOT NULL DEFAULT 'dominican',
            position           INTEGER NOT NULL,
            prayer_id          TEXT,
            mystery_number     INTEGER,
            mystery_title      TEXT,
            mystery_scripture  TEXT,
            mystery_meditation TEXT
        );

        -- Saints
        CREATE TABLE IF NOT EXISTS saints (
            id         TEXT NOT NULL,
            language   TEXT NOT NULL DEFAULT 'en',
            name       TEXT NOT NULL,
            feast_date TEXT,
            short_bio  TEXT NOT NULL,
            full_bio   TEXT NOT NULL,
            patronage  TEXT,
            category   TEXT NOT NULL,
            PRIMARY KEY (id, language)
        );

        CREATE INDEX IF NOT EXISTS idx_saints_language ON saints(language, name);
-- Divine Office
        CREATE TABLE IF NOT EXISTS divine_office_calendar (
            key           TEXT PRIMARY KEY,
            title         TEXT NOT NULL,
            rank          TEXT,
            grade         INTEGER NOT NULL DEFAULT 0,
            tempora_file  TEXT,
            sancti_file   TEXT,
            commune_file  TEXT
        );

        CREATE TABLE IF NOT EXISTS divine_office (
            id          INTEGER PRIMARY KEY,
            file        TEXT NOT NULL,
            file_type   TEXT NOT NULL,
            title       TEXT NOT NULL,
            office_type TEXT,
            invitatorium TEXT,
            antiphon_1  TEXT, antiphon_2  TEXT, antiphon_3  TEXT,
            antiphon_4  TEXT, antiphon_5  TEXT, antiphon_6  TEXT,
            antiphon_7  TEXT, antiphon_8  TEXT, antiphon_9  TEXT,
            antiphon_vespera_1  TEXT, antiphon_vespera_2  TEXT, antiphon_vespera_3  TEXT,
            antiphon_vespera_4  TEXT, antiphon_vespera_5  TEXT, antiphon_vespera_6  TEXT,
            antiphon_vespera_7  TEXT, antiphon_vespera_8  TEXT, antiphon_vespera_9  TEXT,
            antiphon_vespera_10 TEXT, antiphon_vespera_11 TEXT, antiphon_vespera_12 TEXT,
            hymn        TEXT,
            lectio_1    TEXT, lectio_2    TEXT, lectio_3    TEXT,
            responsory_1 TEXT, responsory_2 TEXT, responsory_3 TEXT,
            versus      TEXT,
            preces      TEXT,
            oratio      TEXT,
            conclusio   TEXT,
            matins_antiphon TEXT
        );

        CREATE TABLE IF NOT EXISTS divine_office_psalms (
            id          INTEGER PRIMARY KEY,
            day         INTEGER NOT NULL,
            office_type TEXT NOT NULL,
            antiphon    TEXT,
            psalms      TEXT NOT NULL,
            psalm_text  TEXT
        );

        -- Indexes for fast chapter / book lookups
        CREATE INDEX IF NOT EXISTS idx_verses_book_chapter ON verses(book_id, chapter);
        CREATE INDEX IF NOT EXISTS idx_books_translation ON books(translation_id, book_number);
        CREATE INDEX IF NOT EXISTS idx_mystery_beads_mystery ON mystery_beads(mystery_id, language, variant, position);
        CREATE INDEX IF NOT EXISTS idx_novena_days_novena ON novena_days(novena_id, day_number);
    """)


# Starting book_id offsets per translation so IDs never collide across translations.
# DRA: 1–999, NRSVCE: 1001–1999, Vulgate: 2001–2999, Vulgate-ET: 3001–3999, WEB-C: 4001–4999
# Ave-Maria (PT): 5001–5999
_TRANSLATION_BOOK_ID_OFFSET = {
    "dra":        1,
    "vulgate":    2001,
    "vulgate-et": 3001,
    "web-c":      4001,
    "ave-maria":  5001,
    "porcap":     6001,
    "crampon":    7001,
    "rk1998":     8001,
    "platense":   9001,
    "sg":         10001,
}

# Portuguese display names for Ave-Maria, keyed by DR filename (no extension).
_PT_BOOK_NAMES = {
    "Genesis":          "Gênesis",
    "Exodus":           "Êxodo",
    "Leviticus":        "Levítico",
    "Numbers":          "Números",
    "Deuteronomy":      "Deuteronômio",
    "Josue":            "Josué",
    "Judges":           "Juízes",
    "Ruth":             "Rute",
    "1 Kings":          "I Samuel",
    "2 Kings":          "II Samuel",
    "3 Kings":          "I Reis",
    "4 Kings":          "II Reis",
    "1 Paralipomenon":  "I Crônicas",
    "2 Paralipomenon":  "II Crônicas",
    "1 Esdras":         "Esdras",
    "2 Esdras":         "Neemias",
    "Tobias":           "Tobias",
    "Judith":           "Judite",
    "Esther":           "Ester",
    "Job":              "Jó",
    "Psalms":           "Salmos",
    "1 Machabees":      "I Macabeus",
    "2 Machabees":      "II Macabeus",
    "Proverbs":         "Provérbios",
    "Ecclesiastes":     "Eclesiastes",
    "Canticles":        "Cântico dos Cânticos",
    "Wisdom":           "Sabedoria",
    "Ecclesiasticus":   "Eclesiástico",
    "Isaias":           "Isaías",
    "Jeremias":         "Jeremias",
    "Lamentations":     "Lamentações",
    "Baruch":           "Baruc",
    "Ezechiel":         "Ezequiel",
    "Daniel":           "Daniel",
    "Osee":             "Oséias",
    "Joel":             "Joel",
    "Amos":             "Amós",
    "Abdias":           "Abdias",
    "Jonas":            "Jonas",
    "Micheas":          "Miquéias",
    "Nahum":            "Naum",
    "Habacuc":          "Habacuc",
    "Sophonias":        "Sofonias",
    "Aggeus":           "Ageu",
    "Zacharias":        "Zacarias",
    "Malachias":        "Malaquias",
    "Matthew":          "São Mateus",
    "Mark":             "São Marcos",
    "Luke":             "São Lucas",
    "John":             "São João",
    "Acts":             "Atos dos Apóstolos",
    "Romans":           "Romanos",
    "1 Corinthians":    "I Coríntios",
    "2 Corinthians":    "II Coríntios",
    "Galatians":        "Gálatas",
    "Ephesians":        "Efésios",
    "Philippians":      "Filipenses",
    "Colossians":       "Colossenses",
    "1 Thessalonians":  "I Tessalonicenses",
    "2 Thessalonians":  "II Tessalonicenses",
    "1 Timothy":        "I Timóteo",
    "2 Timothy":        "II Timóteo",
    "Titus":            "Tito",
    "Philemon":         "Filêmon",
    "Hebrews":          "Hebreus",
    "James":            "São Tiago",
    "1 Peter":          "I São Pedro",
    "2 Peter":          "II São Pedro",
    "1 John":           "I São João",
    "2 John":           "II São João",
    "3 John":           "III São João",
    "Jude":             "São Judas",
    "Apocalypse":       "Apocalipse",
}


# European Portuguese display names for PorCap (Bíblia dos Capuchinhos).
# Key differences from pt-BR: Génesis, Deuteronómio, Crónicas, Filémon, etc.
_PORCAP_BOOK_NAMES = {
    "Genesis":          "Génesis",
    "Exodus":           "Êxodo",
    "Leviticus":        "Levítico",
    "Numbers":          "Números",
    "Deuteronomy":      "Deuteronómio",
    "Josue":            "Josué",
    "Judges":           "Juízes",
    "Ruth":             "Rute",
    "1 Kings":          "1 Samuel",
    "2 Kings":          "2 Samuel",
    "3 Kings":          "1 Reis",
    "4 Kings":          "2 Reis",
    "1 Paralipomenon":  "1 Crónicas",
    "2 Paralipomenon":  "2 Crónicas",
    "1 Esdras":         "Esdras",
    "2 Esdras":         "Neemias",
    "Tobias":           "Tobite",
    "Judith":           "Judite",
    "Esther":           "Ester",
    "Job":              "Job",
    "Psalms":           "Salmos",
    "1 Machabees":      "1 Macabeus",
    "2 Machabees":      "2 Macabeus",
    "Proverbs":         "Provérbios",
    "Ecclesiastes":     "Eclesiastes",
    "Canticles":        "Cântico dos Cânticos",
    "Wisdom":           "Sabedoria",
    "Ecclesiasticus":   "Eclesiástico",
    "Isaias":           "Isaías",
    "Jeremias":         "Jeremias",
    "Lamentations":     "Lamentações",
    "Baruch":           "Baruc",
    "Ezechiel":         "Ezequiel",
    "Daniel":           "Daniel",
    "Osee":             "Oseias",
    "Joel":             "Joel",
    "Amos":             "Amós",
    "Abdias":           "Abdias",
    "Jonas":            "Jonas",
    "Micheas":          "Miqueias",
    "Nahum":            "Naum",
    "Habacuc":          "Habacuc",
    "Sophonias":        "Sofonias",
    "Aggeus":           "Ageu",
    "Zacharias":        "Zacarias",
    "Malachias":        "Malaquias",
    "Matthew":          "Mateus",
    "Mark":             "Marcos",
    "Luke":             "Lucas",
    "John":             "João",
    "Acts":             "Atos dos Apóstolos",
    "Romans":           "Romanos",
    "1 Corinthians":    "1 Coríntios",
    "2 Corinthians":    "2 Coríntios",
    "Galatians":        "Gálatas",
    "Ephesians":        "Efésios",
    "Philippians":      "Filipenses",
    "Colossians":       "Colossenses",
    "1 Thessalonians":  "1 Tessalonicenses",
    "2 Thessalonians":  "2 Tessalonicenses",
    "1 Timothy":        "1 Timóteo",
    "2 Timothy":        "2 Timóteo",
    "Titus":            "Tito",
    "Philemon":         "Filémon",
    "Hebrews":          "Hebreus",
    "James":            "Tiago",
    "1 Peter":          "1 Pedro",
    "2 Peter":          "2 Pedro",
    "1 John":           "1 João",
    "2 John":           "2 João",
    "3 John":           "3 João",
    "Jude":             "Judas",
    "Apocalypse":       "Apocalipse",
}


# Spanish display names for Platense (Straubinger), keyed by DR filename (no extension).
_ES_BOOK_NAMES = {
    "Genesis":          "Génesis",
    "Exodus":           "Éxodo",
    "Leviticus":        "Levítico",
    "Numbers":          "Números",
    "Deuteronomy":      "Deuteronomio",
    "Josue":            "Josué",
    "Judges":           "Jueces",
    "Ruth":             "Rut",
    "1 Kings":          "1 Samuel",
    "2 Kings":          "2 Samuel",
    "3 Kings":          "1 Reyes",
    "4 Kings":          "2 Reyes",
    "1 Paralipomenon":  "1 Crónicas",
    "2 Paralipomenon":  "2 Crónicas",
    "1 Esdras":         "Esdras",
    "2 Esdras":         "Nehemías",
    "Tobias":           "Tobías",
    "Judith":           "Judit",
    "Esther":           "Ester",
    "1 Machabees":      "1 Macabeos",
    "2 Machabees":      "2 Macabeos",
    "Job":              "Job",
    "Psalms":           "Salmos",
    "Proverbs":         "Proverbios",
    "Ecclesiastes":     "Eclesiastés",
    "Canticles":        "Cantar de los Cantares",
    "Wisdom":           "Sabiduría",
    "Ecclesiasticus":   "Eclesiástico",
    "Isaias":           "Isaías",
    "Jeremias":         "Jeremías",
    "Lamentations":     "Lamentaciones",
    "Baruch":           "Baruc",
    "Ezechiel":         "Ezequiel",
    "Daniel":           "Daniel",
    "Osee":             "Oseas",
    "Joel":             "Joel",
    "Amos":             "Amós",
    "Abdias":           "Abdías",
    "Jonas":            "Jonás",
    "Micheas":          "Miqueas",
    "Nahum":            "Nahúm",
    "Habacuc":          "Habacuc",
    "Sophonias":        "Sofonías",
    "Aggeus":           "Ageo",
    "Zacharias":        "Zacarías",
    "Malachias":        "Malaquías",
    "Matthew":          "San Mateo",
    "Mark":             "San Marcos",
    "Luke":             "San Lucas",
    "John":             "San Juan",
    "Acts":             "Hechos de los Apóstoles",
    "Romans":           "Romanos",
    "1 Corinthians":    "1 Corintios",
    "2 Corinthians":    "2 Corintios",
    "Galatians":        "Gálatas",
    "Ephesians":        "Efesios",
    "Philippians":      "Filipenses",
    "Colossians":       "Colosenses",
    "1 Thessalonians":  "1 Tesalonicenses",
    "2 Thessalonians":  "2 Tesalonicenses",
    "1 Timothy":        "1 Timoteo",
    "2 Timothy":        "2 Timoteo",
    "Titus":            "Tito",
    "Philemon":         "Filemón",
    "Hebrews":          "Hebreos",
    "James":            "Santiago",
    "1 Peter":          "1 Pedro",
    "2 Peter":          "2 Pedro",
    "1 John":           "1 Juan",
    "2 John":           "2 Juan",
    "3 John":           "3 Juan",
    "Jude":             "Judas",
    "Apocalypse":       "Apocalipsis",
}


# French display names for Crampon, keyed by DR filename (no extension).
_FR_BOOK_NAMES = {
    "Genesis":          "Genèse",
    "Exodus":           "Exode",
    "Leviticus":        "Lévitique",
    "Numbers":          "Nombres",
    "Deuteronomy":      "Deutéronome",
    "Josue":            "Josué",
    "Judges":           "Juges",
    "Ruth":             "Ruth",
    "1 Kings":          "1 Samuel",
    "2 Kings":          "2 Samuel",
    "3 Kings":          "1 Rois",
    "4 Kings":          "2 Rois",
    "1 Paralipomenon":  "1 Chroniques",
    "2 Paralipomenon":  "2 Chroniques",
    "1 Esdras":         "Esdras",
    "2 Esdras":         "Néhémie",
    "Tobias":           "Tobie",
    "Judith":           "Judith",
    "Esther":           "Esther",
    "1 Machabees":      "1 Maccabées",
    "2 Machabees":      "2 Maccabées",
    "Job":              "Job",
    "Psalms":           "Psaumes",
    "Proverbs":         "Proverbes",
    "Ecclesiastes":     "Ecclésiaste",
    "Canticles":        "Cantique des Cantiques",
    "Wisdom":           "Sagesse",
    "Ecclesiasticus":   "Siracide",
    "Isaias":           "Isaïe",
    "Jeremias":         "Jérémie",
    "Lamentations":     "Lamentations",
    "Baruch":           "Baruch",
    "Ezechiel":         "Ézéchiel",
    "Daniel":           "Daniel",
    "Osee":             "Osée",
    "Joel":             "Joël",
    "Amos":             "Amos",
    "Abdias":           "Abdias",
    "Jonas":            "Jonas",
    "Micheas":          "Michée",
    "Nahum":            "Nahoum",
    "Habacuc":          "Habacuc",
    "Sophonias":        "Sophonie",
    "Aggeus":           "Aggée",
    "Zacharias":        "Zacharie",
    "Malachias":        "Malachie",
    "Matthew":          "Matthieu",
    "Mark":             "Marc",
    "Luke":             "Luc",
    "John":             "Jean",
    "Acts":             "Actes des Apôtres",
    "Romans":           "Romains",
    "1 Corinthians":    "1 Corinthiens",
    "2 Corinthians":    "2 Corinthiens",
    "Galatians":        "Galates",
    "Ephesians":        "Éphésiens",
    "Philippians":      "Philippiens",
    "Colossians":       "Colossiens",
    "1 Thessalonians":  "1 Thessaloniciens",
    "2 Thessalonians":  "2 Thessaloniciens",
    "1 Timothy":        "1 Timothée",
    "2 Timothy":        "2 Timothée",
    "Titus":            "Tite",
    "Philemon":         "Philémon",
    "Hebrews":          "Hébreux",
    "James":            "Jacques",
    "1 Peter":          "1 Pierre",
    "2 Peter":          "2 Pierre",
    "1 John":           "1 Jean",
    "2 John":           "2 Jean",
    "3 John":           "3 Jean",
    "Jude":             "Jude",
    "Apocalypse":       "Apocalypse",
}


# Classical Latin names for the Clementine Vulgate, keyed by DR filename.
_LA_BOOK_NAMES = {
    "Genesis":          "Genesis",
    "Exodus":           "Exodus",
    "Leviticus":        "Leviticus",
    "Numbers":          "Numeri",
    "Deuteronomy":      "Deuteronomium",
    "Josue":            "Iosue",
    "Judges":           "Iudicum",
    "Ruth":             "Ruth",
    "1 Kings":          "I Regum",
    "2 Kings":          "II Regum",
    "3 Kings":          "III Regum",
    "4 Kings":          "IV Regum",
    "1 Paralipomenon":  "I Paralipomenon",
    "2 Paralipomenon":  "II Paralipomenon",
    "1 Esdras":         "I Esdrae",
    "2 Esdras":         "II Esdrae",
    "Tobias":           "Tobias",
    "Judith":           "Iudith",
    "Esther":           "Esther",
    "1 Machabees":      "I Machabaeorum",
    "2 Machabees":      "II Machabaeorum",
    "Job":              "Iob",
    "Psalms":           "Psalmi",
    "Proverbs":         "Proverbia",
    "Ecclesiastes":     "Ecclesiastes",
    "Canticles":        "Canticum Canticorum",
    "Wisdom":           "Sapientia",
    "Ecclesiasticus":   "Ecclesiasticus",
    "Isaias":           "Isaias",
    "Jeremias":         "Ieremias",
    "Lamentations":     "Threni",
    "Baruch":           "Baruch",
    "Ezechiel":         "Ezechiel",
    "Daniel":           "Daniel",
    "Osee":             "Osee",
    "Joel":             "Ioel",
    "Amos":             "Amos",
    "Abdias":           "Abdias",
    "Jonas":            "Ionas",
    "Micheas":          "Micheas",
    "Nahum":            "Nahum",
    "Habacuc":          "Habacuc",
    "Sophonias":        "Sophonias",
    "Aggeus":           "Aggaeus",
    "Zacharias":        "Zacharias",
    "Malachias":        "Malachias",
    "Matthew":          "Matthaeus",
    "Mark":             "Marcus",
    "Luke":             "Lucas",
    "John":             "Ioannes",
    "Acts":             "Actus Apostolorum",
    "Romans":           "Ad Romanos",
    "1 Corinthians":    "Ad Corinthios I",
    "2 Corinthians":    "Ad Corinthios II",
    "Galatians":        "Ad Galatas",
    "Ephesians":        "Ad Ephesios",
    "Philippians":      "Ad Philippenses",
    "Colossians":       "Ad Colossenses",
    "1 Thessalonians":  "Ad Thessalonicenses I",
    "2 Thessalonians":  "Ad Thessalonicenses II",
    "1 Timothy":        "Ad Timotheum I",
    "2 Timothy":        "Ad Timotheum II",
    "Titus":            "Ad Titum",
    "Philemon":         "Ad Philemonem",
    "Hebrews":          "Ad Hebraeos",
    "James":            "Epistola Iacobi",
    "1 Peter":          "Epistola Petri I",
    "2 Peter":          "Epistola Petri II",
    "1 John":           "Epistola Ioannis I",
    "2 John":           "Epistola Ioannis II",
    "3 John":           "Epistola Ioannis III",
    "Jude":             "Epistola Iudae",
    "Apocalypse":       "Apocalypsis",
}


_LT_BOOK_NAMES = {
    "Genesis":          "Pradžios knyga",
    "Exodus":           "Išėjimo knyga",
    "Leviticus":        "Kunigų knyga",
    "Numbers":          "Skaičių knyga",
    "Deuteronomy":      "Pakartoto Įstatymo knyga",
    "Josue":            "Jozuės knyga",
    "Judges":           "Teisėjų knyga",
    "Ruth":             "Rutos knyga",
    "1 Kings":          "1 Samuelio knyga",
    "2 Kings":          "2 Samuelio knyga",
    "3 Kings":          "1 Karalių knyga",
    "4 Kings":          "2 Karalių knyga",
    "1 Paralipomenon":  "1 Kronikų knyga",
    "2 Paralipomenon":  "2 Kronikų knyga",
    "1 Esdras":         "Ezdro knyga",
    "2 Esdras":         "Nehemijo knyga",
    "Tobias":           "Tobito knyga",
    "Judith":           "Juditos knyga",
    "Esther":           "Esteros knyga",
    "1 Machabees":      "1 Makabiejų knyga",
    "2 Machabees":      "2 Makabiejų knyga",
    "Job":              "Jobo knyga",
    "Psalms":           "Psalmių knyga",
    "Proverbs":         "Patarlių knyga",
    "Ecclesiastes":     "Koheleto knyga",
    "Canticles":        "Giesmių Giesmė",
    "Wisdom":           "Išminties knyga",
    "Ecclesiasticus":   "Siracido knyga",
    "Isaias":           "Izaijo knyga",
    "Jeremias":         "Jeremijo knyga",
    "Lamentations":     "Raudų knyga",
    "Baruch":           "Barucho knyga",
    "Ezechiel":         "Ezekielio knyga",
    "Daniel":           "Danieliaus knyga",
    "Osee":             "Ozėjo knyga",
    "Joel":             "Joelio knyga",
    "Amos":             "Amoso knyga",
    "Abdias":           "Abdijo knyga",
    "Jonas":            "Jonos knyga",
    "Micheas":          "Michėjo knyga",
    "Nahum":            "Nahumo knyga",
    "Habacuc":          "Habakuko knyga",
    "Sophonias":        "Sofonijo knyga",
    "Aggeus":           "Agėjo knyga",
    "Zacharias":        "Zacharijo knyga",
    "Malachias":        "Malachijo knyga",
    "Matthew":          "Evangelija pagal Matą",
    "Mark":             "Evangelija pagal Morkų",
    "Luke":             "Evangelija pagal Luką",
    "John":             "Evangelija pagal Joną",
    "Acts":             "Apaštalų darbai",
    "Romans":           "Laiškas romiečiams",
    "1 Corinthians":    "Pirmasis laiškas korintiečiams",
    "2 Corinthians":    "Antrasis laiškas korintiečiams",
    "Galatians":        "Laiškas galatams",
    "Ephesians":        "Laiškas efeziečiams",
    "Philippians":      "Laiškas filipiečiams",
    "Colossians":       "Laiškas kolosiečiams",
    "1 Thessalonians":  "Pirmasis laiškas tesalonikiečiams",
    "2 Thessalonians":  "Antrasis laiškas tesalonikiečiams",
    "1 Timothy":        "Pirmasis laiškas Timotiejui",
    "2 Timothy":        "Antrasis laiškas Timotiejui",
    "Titus":            "Laiškas Titui",
    "Philemon":         "Laiškas Filemonui",
    "Hebrews":          "Laiškas žydams",
    "James":            "Jokūbo laiškas",
    "1 Peter":          "Pirmasis Petro laiškas",
    "2 Peter":          "Antrasis Petro laiškas",
    "1 John":           "Pirmasis Jono laiškas",
    "2 John":           "Antrasis Jono laiškas",
    "3 John":           "Trečiasis Jono laiškas",
    "Jude":             "Judo laiškas",
    "Apocalypse":       "Apreiškimas Jonui",
}


# Studium Biblicum (思高圣经) filename -> DR key mapping (only entries that differ).
_SG_FILENAME_TO_DR = {
    "Joshua":           "Josue",
    "1_Samuel":         "1 Kings",
    "2_Samuel":         "2 Kings",
    "1_Kings":          "3 Kings",
    "2_Kings":          "4 Kings",
    "1_Chronicles":     "1 Paralipomenon",
    "2_Chronicles":     "2 Paralipomenon",
    "Ezra":             "1 Esdras",
    "Nehemiah":         "2 Esdras",
    "Tobit":            "Tobias",
    "1_Maccabees":      "1 Machabees",
    "2_Maccabees":      "2 Machabees",
    "Song_of_Songs":    "Canticles",
    "Isaiah":           "Isaias",
    "Jeremiah":         "Jeremias",
    "Ezekiel":          "Ezechiel",
    "Hosea":            "Osee",
    "Obadiah":          "Abdias",
    "Jonah":            "Jonas",
    "Micah":            "Micheas",
    "Habakkuk":         "Habacuc",
    "Zephaniah":        "Sophonias",
    "Haggai":           "Aggeus",
    "Zechariah":        "Zacharias",
    "Malachi":          "Malachias",
    "1_Corinthians":    "1 Corinthians",
    "2_Corinthians":    "2 Corinthians",
    "1_Thessalonians":  "1 Thessalonians",
    "2_Thessalonians":  "2 Thessalonians",
    "1_Timothy":        "1 Timothy",
    "2_Timothy":        "2 Timothy",
    "1_Peter":          "1 Peter",
    "2_Peter":          "2 Peter",
    "1_John":           "1 John",
    "2_John":           "2 John",
    "3_John":           "3 John",
    "Revelation":       "Apocalypse",
}

_ZH_BOOK_NAMES = {
    "Genesis":          "创世纪",
    "Exodus":           "出谷纪",
    "Leviticus":        "肋未纪",
    "Numbers":          "民数纪",
    "Deuteronomy":      "申命纪",
    "Josue":            "若苏厄书",
    "Judges":           "民长纪",
    "Ruth":             "卢德传",
    "1 Kings":          "撒慕尔纪上",
    "2 Kings":          "撒慕尔纪下",
    "3 Kings":          "列王纪上",
    "4 Kings":          "列王纪下",
    "1 Paralipomenon":  "编年纪上",
    "2 Paralipomenon":  "编年纪下",
    "1 Esdras":         "厄斯德拉上",
    "2 Esdras":         "厄斯德拉下",
    "Tobias":           "多俾亚传",
    "Judith":           "友弟德传",
    "Esther":           "艾斯德尔传",
    "1 Machabees":      "玛加伯上",
    "2 Machabees":      "玛加伯下",
    "Job":              "约伯传",
    "Psalms":           "圣咏集",
    "Proverbs":         "箴言",
    "Ecclesiastes":     "训道篇",
    "Canticles":        "雅歌",
    "Wisdom":           "智慧篇",
    "Ecclesiasticus":   "德训篇",
    "Isaias":           "依撒意亚",
    "Jeremias":         "耶肋米亚",
    "Lamentations":     "哀歌",
    "Baruch":           "巴路克",
    "Ezechiel":         "厄则克耳",
    "Daniel":           "达尼尔",
    "Osee":             "欧瑟亚",
    "Joel":             "岳厄尔",
    "Amos":             "亚毛斯",
    "Abdias":           "亚北底亚",
    "Jonas":            "约纳",
    "Micheas":          "米该亚",
    "Nahum":            "纳鸿",
    "Habacuc":          "哈巴谷",
    "Sophonias":        "索福尼亚",
    "Aggeus":           "哈盖",
    "Zacharias":        "匝加利亚",
    "Malachias":        "玛拉基亚",
    "Matthew":          "玛窦福音",
    "Mark":             "马尔谷福音",
    "Luke":             "路加福音",
    "John":             "若望福音",
    "Acts":             "宗徒大事录",
    "Romans":           "罗马书",
    "1 Corinthians":    "格林多前书",
    "2 Corinthians":    "格林多后书",
    "Galatians":        "加拉达书",
    "Ephesians":        "厄弗所书",
    "Philippians":      "斐理伯书",
    "Colossians":       "哥罗森书",
    "1 Thessalonians":  "得撒洛尼前书",
    "2 Thessalonians":  "得撒洛尼后书",
    "1 Timothy":        "弟茂德前书",
    "2 Timothy":        "弟茂德后书",
    "Titus":            "弟铎书",
    "Philemon":         "费肋孟书",
    "Hebrews":          "希伯来书",
    "James":            "雅各伯书",
    "1 Peter":          "伯多禄前书",
    "2 Peter":          "伯多禄后书",
    "1 John":           "若望一书",
    "2 John":           "若望二书",
    "3 John":           "若望三书",
    "Jude":             "犹大书",
    "Apocalypse":       "默示录",
}


def compile_sg(conn: sqlite3.Connection) -> None:
    """Compiles the Studium Biblicum (思高圣经) Chinese Catholic Bible."""
    translation_dir = os.path.join(CONTENT_DIR, "bible", "zh", "sg")
    books_dir = os.path.join(translation_dir, "books")
    meta_path = os.path.join(translation_dir, "metadata.json")

    if not os.path.isdir(books_dir):
        print("  SKIP: content/bible/zh/sg/books not found.")
        return

    with open(meta_path) as f:
        meta = json.load(f)

    conn.execute(
        "INSERT OR REPLACE INTO translations VALUES (?, ?, ?, ?)",
        (meta["id"], meta["name"], meta["language"], meta["license"]),
    )

    book_files = sorted(os.listdir(books_dir))
    verse_rows = []
    book_id_counter = _TRANSLATION_BOOK_ID_OFFSET["sg"]

    for filename in book_files:
        if not filename.endswith(".json"):
            continue
        sg_name = filename[:-5]
        dr_name = _SG_FILENAME_TO_DR.get(sg_name, sg_name)
        if dr_name not in BOOK_MANIFEST:
            print(f"  WARN: unknown book '{sg_name}' -> '{dr_name}', skipping")
            continue

        book_number, testament, short_name, _ = BOOK_MANIFEST[dr_name]
        full_name = _ZH_BOOK_NAMES.get(dr_name, dr_name)
        book_id = book_id_counter
        book_id_counter += 1

        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)",
            (book_id, meta["id"], book_number, testament, short_name, full_name, dr_name),
        )

        with open(os.path.join(books_dir, filename)) as f:
            data = json.load(f)

        for chapter_str, verses in sorted(data.items(), key=lambda x: int(x[0])):
            for verse_str, text in sorted(verses.items(), key=lambda x: int(x[0])):
                verse_rows.append((book_id, int(chapter_str), int(verse_str), text))

    conn.executemany(
        "INSERT INTO verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
        verse_rows,
    )
    conn.execute("INSERT INTO verses_fts(verses_fts) VALUES('rebuild')")
    print(f"  {meta['name']}: {len(verse_rows)} total verses indexed.")


def compile_dr_format(
    conn: sqlite3.Connection,
    translation_id: str,
    lang: str = "en",
    book_full_names: dict | None = None,
) -> None:
    """
    Ingests any translation stored in the DRA per-book folder format:
        content/bible/<lang>/<translation_id>/metadata.json
        content/bible/<lang>/<translation_id>/books/<DR-name>.json
    Book files must be named using BOOK_MANIFEST keys.

    book_full_names: optional dict mapping DR filename (no extension) → display name override.
                     Use this for non-English translations so the full_name column is localized.
    """
    translation_dir = os.path.join(CONTENT_DIR, "bible", lang, translation_id)
    books_dir = os.path.join(translation_dir, "books")
    meta_path = os.path.join(translation_dir, "metadata.json")

    if not os.path.isdir(books_dir):
        print(f"  SKIP: {books_dir} not found.")
        return

    with open(meta_path) as f:
        meta = json.load(f)

    conn.execute(
        "INSERT OR REPLACE INTO translations VALUES (?, ?, ?, ?)",
        (meta["id"], meta["name"], meta["language"], meta["license"]),
    )

    book_files = sorted(
        [fn for fn in os.listdir(books_dir) if fn.endswith(".json")],
        key=lambda fn: BOOK_MANIFEST.get(fn[:-5], (999,))[0],
    )

    verse_rows = []
    book_id_counter = _TRANSLATION_BOOK_ID_OFFSET.get(translation_id, 1)

    for filename in book_files:
        dr_name = filename[:-5]
        if dr_name not in BOOK_MANIFEST:
            print(f"  WARN: unknown book file '{filename}' — skipping")
            continue

        book_number, testament, short_name, full_name = BOOK_MANIFEST[dr_name]
        if book_full_names and dr_name in book_full_names:
            full_name = book_full_names[dr_name]
        book_id = book_id_counter
        book_id_counter += 1

        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)",
            (book_id, meta["id"], book_number, testament, short_name, full_name, dr_name),
        )

        with open(os.path.join(books_dir, filename)) as f:
            data = json.load(f)

        for chapter_str, verses in sorted(data.items(), key=lambda x: int(x[0])):
            for verse_str, text in sorted(verses.items(), key=lambda x: int(x[0])):
                verse_rows.append((book_id, int(chapter_str), int(verse_str), text))

        print(f"  {book_number:>2}. {full_name} ({len(verse_rows)} verses so far)")

    conn.executemany(
        "INSERT INTO verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
        verse_rows,
    )
    conn.execute("INSERT INTO verses_fts(verses_fts) VALUES('rebuild')")
    print(f"  {meta['name']}: {len(verse_rows)} total verses indexed.")


def compile_nrsvce(conn: sqlite3.Connection) -> None:
    nrsvce_path = os.path.join(CONTENT_DIR, "bible", "nrsvce", "nrsvce.json")
    if not os.path.exists(nrsvce_path):
        print(f"  SKIP: {nrsvce_path} not found.")
        return

    conn.execute(
        "INSERT OR REPLACE INTO translations VALUES (?, ?, ?, ?)",
        ("nrsvce", "New Revised Standard Version Catholic Edition", "en", "© 1989, 1993 NCC; Catholic edition © 1993, 2021 USCCB"),
    )

    with open(nrsvce_path) as f:
        data = json.load(f)

    # testament key order in the JSON: Old Testament, Deuterocanonical, New Testament
    testament_map = {
        "Old Testament": "OT",
        "Deuterocanonical": "DC",
        "New Testament": "NT",
    }

    verse_rows = []
    # NRSVCE book IDs start at 1001 to avoid collisions with DRA (1–73)
    book_id_counter = 1001

    # Sort all books by their book_number from the manifest
    all_books = []
    for testament_label, books in data.items():
        for book_name, chapters in books.items():
            if book_name not in NRSVCE_BOOK_MANIFEST:
                print(f"  WARN: unknown NRSVCE book '{book_name}' — skipping")
                continue
            all_books.append((NRSVCE_BOOK_MANIFEST[book_name][0], book_name, chapters))
    all_books.sort(key=lambda x: x[0])

    for book_number, book_name, chapters in all_books:
        entry = NRSVCE_BOOK_MANIFEST[book_name]
        _, testament, short_name, full_name, dr_name = entry
        book_id = book_id_counter
        book_id_counter += 1

        conn.execute(
            "INSERT INTO books VALUES (?, ?, ?, ?, ?, ?, ?)",
            (book_id, "nrsvce", book_number, testament, short_name, full_name, dr_name),
        )

        for chapter_str, verses in sorted(chapters.items(), key=lambda x: int(x[0])):
            for verse_str, text in sorted(verses.items(), key=lambda x: int(x[0])):
                verse_rows.append((book_id, int(chapter_str), int(verse_str), _clean_nrsvce_verse(text)))

        print(f"  {book_number:>2}. {full_name} ({len(verse_rows)} verses so far)")

    conn.executemany(
        "INSERT INTO verses (book_id, chapter, verse, text) VALUES (?, ?, ?, ?)",
        verse_rows,
    )
    conn.execute("INSERT INTO verses_fts(verses_fts) VALUES('rebuild')")
    print(f"  NRSVCE: {len(verse_rows)} total verses indexed.")


def compile_catechism(conn: sqlite3.Connection) -> None:
    path = os.path.join(CONTENT_DIR, "catechism", "ccc_paragraphs.json")
    with open(path) as f:
        paragraphs = json.load(f)

    if not paragraphs:
        print("  SKIP: ccc_paragraphs.json is empty.")
        return

    for p in paragraphs:
        conn.execute(
            "INSERT INTO ccc_sections VALUES (?, ?, ?, ?, ?, ?, ?)",
            (p["id"], p.get("part"), p.get("section"), p.get("chapter"),
             p.get("article"), p.get("heading"), p["body"]),
        )
    conn.execute("INSERT INTO ccc_fts(ccc_fts) VALUES('rebuild')")
    print(f"  Catechism: {len(paragraphs)} paragraphs indexed.")


def compile_prayers(conn: sqlite3.Connection, lang: str) -> None:
    path = os.path.join(CONTENT_DIR, "prayers", lang, "prayers.json")
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found.")
        return
    with open(path) as f:
        prayers = json.load(f)

    if not prayers:
        print(f"  SKIP: prayers.json ({lang}) is empty.")
        return

    for p in prayers:
        conn.execute(
            "INSERT INTO prayers (id, language, title, body, source, category) VALUES (?, ?, ?, ?, ?, ?)",
            (p["id"], lang, p["title"], p["body"], p.get("source"), p["category"]),
        )
        for tag in p.get("tags", []):
            conn.execute(
                "INSERT INTO prayer_tags (prayer_id, language, tag) VALUES (?, ?, ?)",
                (p["id"], lang, tag),
            )

    conn.execute("INSERT INTO prayers_fts(prayers_fts) VALUES('rebuild')")
    print(f"  Prayers ({lang}): {len(prayers)} entries indexed.")


def compile_novenas(conn: sqlite3.Connection, lang: str) -> None:
    path = os.path.join(CONTENT_DIR, "novenas", lang, "novenas.json")
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found.")
        return
    with open(path) as f:
        novenas = json.load(f)

    if not novenas:
        print(f"  SKIP: novenas.json ({lang}) is empty.")
        return

    for n in novenas:
        conn.execute(
            "INSERT INTO novenas (id, language, title, description, total_days, feast_day) VALUES (?, ?, ?, ?, ?, ?)",
            (n["id"], lang, n["title"], n.get("description"),
             n.get("total_days", 9), n.get("feast_day")),
        )
        for day in n["days"]:
            conn.execute(
                "INSERT INTO novena_days (novena_id, language, day_number, title, body) VALUES (?, ?, ?, ?, ?)",
                (n["id"], lang, day["day"], day.get("title"), day["body"]),
            )
    print(f"  Novenas ({lang}): {len(novenas)} entries loaded.")


def compile_rosary(conn: sqlite3.Connection, lang: str, variant: str = "dominican") -> None:
    path = os.path.join(CONTENT_DIR, "rosary", lang, "mysteries.json")
    if not os.path.exists(path):
        print(f"  SKIP: content/rosary/{lang}/mysteries.json not found.")
        return

    with open(path) as f:
        mystery_sets = json.load(f)

    # ── Sequence definitions ──────────────────────────────────────────────────
    INTRO_EN = [
        ("apostles-creed", None),
        ("our-father",     None),
        ("hail-mary",      "For an increase in Faith"),
        ("hail-mary",      "For an increase in Hope"),
        ("hail-mary",      "For an increase in Charity"),
        ("glory-be",       None),
    ]
    INTRO_PT = [
        ("apostles-creed", None),
        ("our-father",     None),
        ("hail-mary",      "Por um aumento em Fé"),
        ("hail-mary",      "Por um aumento em Esperança"),
        ("hail-mary",      "Por um aumento em Caridade"),
        ("glory-be",       None),
    ]
    # Fátima opening: Deus in adjutorium + Glory Be (no Our Father or Hail Marys)
    INTRO_FATIMA_PT = [
        ("deus-in-adjutorium", None),
        ("glory-be",           None),
    ]
    # Fátima closing: 3 Hail Marys (faith/hope/charity) then Hail Holy Queen
    CLOSING_FATIMA_PT = [
        ("hail-mary",       "Por um aumento em Fé"),
        ("hail-mary",       "Por um aumento em Esperança"),
        ("hail-mary",       "Por um aumento em Caridade"),
        ("hail-holy-queen", None),
    ]

    if variant == "fatima":
        INTRO = INTRO_FATIMA_PT
        CLOSING = CLOSING_FATIMA_PT
        EXTRA_DECADE = ["oh-maria-concebida", "fatima-prayer"]
    else:
        INTRO = INTRO_PT if lang in ("pt-BR", "pt-PT") else INTRO_EN
        CLOSING = [("hail-holy-queen", None)]
        EXTRA_DECADE = ["fatima-prayer"]

    # ── Insert beads ──────────────────────────────────────────────────────────
    def insert_bead(ms_id, pos, prayer_id, mystery_title=None, mystery_number=None,
                    mystery_scripture=None, mystery_meditation=None):
        conn.execute(
            """INSERT INTO mystery_beads
               (mystery_id, language, variant, position, prayer_id, mystery_title,
                mystery_number, mystery_scripture, mystery_meditation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ms_id, lang, variant, pos, prayer_id, mystery_title,
             mystery_number, mystery_scripture, mystery_meditation),
        )

    total_beads = 0
    for ms in mystery_sets:
        # mysteries rows are shared across variants; only insert once per (id, language)
        conn.execute(
            "INSERT OR IGNORE INTO mysteries (id, language, name, traditional_days) VALUES (?, ?, ?, ?)",
            (ms["id"], lang, ms["name"], ms.get("traditional_days")),
        )

        position = 1

        for prayer_id, intention in INTRO:
            insert_bead(ms["id"], position, prayer_id, mystery_title=intention)
            position += 1

        for m in ms["mysteries"]:
            # Mystery announcement — dedicated page, no prayer_id
            insert_bead(ms["id"], position, None,
                        mystery_number=m["number"], mystery_title=m["title"],
                        mystery_scripture=m.get("scripture"), mystery_meditation=m.get("meditation"))
            position += 1

            insert_bead(ms["id"], position, "our-father", mystery_number=m["number"])
            position += 1

            for _ in range(10):
                insert_bead(ms["id"], position, "hail-mary", mystery_number=m["number"])
                position += 1

            insert_bead(ms["id"], position, "glory-be", mystery_number=m["number"])
            position += 1

            for prayer_id in EXTRA_DECADE:
                insert_bead(ms["id"], position, prayer_id, mystery_number=m["number"])
                position += 1

        for prayer_id, intention in CLOSING:
            insert_bead(ms["id"], position, prayer_id, mystery_title=intention)
            position += 1

        total_beads += position - 1
        print(f"  {ms['name']} ({variant}): {position - 1} beads")

    print(f"  Rosary ({lang}, {variant}): {len(mystery_sets)} mystery sets, {total_beads} total beads.")


def compile_saints(conn: sqlite3.Connection, lang: str) -> None:
    path = os.path.join(CONTENT_DIR, "saints", lang, "saints.json")
    if not os.path.exists(path):
        print(f"  SKIP: {path} not found.")
        return
    with open(path) as f:
        saints = json.load(f)

    if not saints:
        print(f"  SKIP: saints.json ({lang}) is empty.")
        return

    for s in saints:
        conn.execute(
            "INSERT OR REPLACE INTO saints (id, language, name, feast_date, short_bio, full_bio, patronage, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (s["id"], lang, s["name"], s.get("feast_date"), s["short_bio"], s["full_bio"],
             s.get("patronage"), s["category"]),
        )
    print(f"  Saints ({lang}): {len(saints)} entries loaded.")


# This file contains the compile_divine_office function and helpers.
# Append this to compile_content.py.

import os, re, json, sqlite3

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(REPO_ROOT, "content")

_txt_cache = {}


def _parse_rank(rank):
    if not rank:
        return ""
    if rank.startswith(";;"):
        parts = rank.split(";;")
        if len(parts) >= 2:
            style = parts[1].strip()
            if style in ("Duplex", "Semiduplex", "Simplex", "Duplex optional",
                         "Triumph", "Ferial", "Feria"):
                return style
            return style
    cleaned = re.sub(r"\s*\(sed [^)]+\)", "", rank).strip()
    parts = cleaned.split()
    best_end = len(parts)
    for size in range(len(parts) - 1, 3, -1):
        first = " ".join(parts[:size])
        rest = " ".join(parts[size:])
        if first in rest:
            best_end = size
            break
    cleaned = " ".join(parts[:best_end]).strip()
    if not cleaned or len(cleaned) > 80:
        return ""
    return cleaned


def _clean_title(title):
    if not title:
        return ""
    cleaned = re.sub(r"\s*\(sed [^)]+\)", "", title).strip()
    parts = cleaned.split()
    best_end = len(parts)
    for size in range(len(parts) - 1, 3, -1):
        first = " ".join(parts[:size])
        rest = " ".join(parts[size:])
        if first in rest:
            best_end = size
            break
    return " ".join(parts[:best_end]).strip()


def _normalize_office_type(office_type):
    if not office_type:
        return ""
    t = office_type.lower().strip()
    if t in ("laudes", "laudes/", "laudes 1", "laudes 2", "laudes 3"):
        return "Laudes"
    if t in ("vespera", "vespers", "vesper", "vesp", "vespera/", "vespers/"):
        return "Vespers"
    if t in ("matutinum", "matins", "matutine", "mat"):
        return "Matins"
    if t in ("completorium", "compline"):
        return "Compline"
    if t in ("prima", "prime", "pr"):
        return "Prime"
    if t in ("tertia", "terce", "ter"):
        return "Terce"
    if t in ("sexta", "sext", "sex"):
        return "Sext"
    if t in ("nona", "none", "non"):
        return "None"
    return office_type


def _load_txt_file(filename):
    psalterium = os.path.join(
        REPO_ROOT, "divinum-officium", "web", "www", "horas", "Latin", "Psalterium", "Psalmi"
    )
    path = os.path.join(psalterium, filename)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    sections = {}
    current = None
    pending_refs = []
    pending_ant_idx = None

    def _flush():
        nonlocal pending_refs, pending_ant_idx
        if pending_refs and pending_ant_idx is not None and sections.get(current):
            sections[current][pending_ant_idx]["refs"].extend(pending_refs)
        pending_refs.clear()
        pending_ant_idx = None

    for raw in lines:
        line = raw.strip()
        if not line:
            pending_refs.clear()
            pending_ant_idx = None
            continue
        if line.startswith("[") and line.endswith("]"):
            _flush()
            current = line[1:-1]
            sections.setdefault(current, [])
        elif current is None:
            continue
        elif line.startswith("("):
            _flush()
            sections[current].append({"type": "rubric", "antiphon": None, "text": line, "refs": []})
        elif line.startswith("V. ") or line.startswith("R. "):
            _flush()
            sections[current].append({"type": "versicle", "antiphon": None, "text": line, "refs": []})
        elif "=" in line:
            _flush()
            ant_text = line.split("=", 1)[1].strip()
            idx = len(sections[current])
            sections[current].append({
                "type": "ant" if ant_text else "bare",
                "antiphon": ant_text or None,
                "text": line,
                "refs": [],
            })
            pending_ant_idx = idx
        elif ";;" in line:
            _flush()
            ant_text, ref_part = line.split(";;", 1)
            refs = [r.strip() for r in ref_part.replace(",", ";").split(";") if r.strip()]
            sections[current].append({
                "type": "ant" if ant_text.strip() else "bare",
                "antiphon": ant_text.strip() or None,
                "text": line,
                "refs": refs,
            })
        else:
            refs = [r.strip() for r in line.replace(",", ";").split(";") if r.strip()]
            if refs:
                if pending_ant_idx is not None and sections.get(current):
                    sections[current][pending_ant_idx]["refs"].extend(refs)
                else:
                    sections[current].append({"type": "bare", "antiphon": None, "text": line, "refs": list(refs)})

    _flush()
    return sections


_VERSE_CACHE = {}
_VULGATE_PSALMS_BOOK_ID = 2022


def _expand_psalm_ref(conn, ref):
    if not ref:
        return []
    ref = ref.strip()
    if not ref:
        return []
    m = re.match(r"^(\d+)(.*)$", ref)
    if not m:
        return []
    ps_id = int(m.group(1))
    suffix = m.group(2)

    if _VULGATE_PSALMS_BOOK_ID not in _VERSE_CACHE:
        cu = conn.execute(
            "SELECT chapter, verse, text FROM verses WHERE book_id=? ORDER BY chapter, verse",
            (_VULGATE_PSALMS_BOOK_ID,),
        )
        rows = cu.fetchall()
        verses_by_ch = {}
        for ch, vn, txt in rows:
            verses_by_ch.setdefault(ch, []).append((vn, txt))
        _VERSE_CACHE[_VULGATE_PSALMS_BOOK_ID] = verses_by_ch
    verses_by_ch = _VERSE_CACHE[_VULGATE_PSALMS_BOOK_ID]

    if ps_id not in verses_by_ch:
        return []
    all_verses = verses_by_ch[ps_id]

    if not suffix:
        return [f"{ps_id}:{vn}:{txt}" for vn, txt in all_verses]

    rm = re.match(r"^\((\d+)(?:[-']([\d]+))?(?:[-']([\d]+))?\)$", suffix)
    if rm:
        v_start = int(rm.group(1))
        v_end = int(rm.group(3)) if rm.group(3) else v_start
        return [f"{ps_id}:{vn}:{txt}" for vn, txt in all_verses if v_start <= vn <= v_end]

    return [f"{ps_id}:{vn}:{txt}" for vn, txt in all_verses]


def _build_blocks_from_txt_rows(sec_rows, conn):
    """
    Convert parsed txt section rows into antiphon+verses blocks.

    Key invariant: antiphon rows (with inline or trailing refs) always start a new block.
    Bare ref rows accumulate into their own block(s) WITHOUT being paired with an
    antiphon from a previous section (antiphon rows are strictly per-section).

    Returns a list of dicts:
      {antiphon: str|null, verses: ["ps:vs:text", ...]}
    """
    blocks = []
    current_ant = None
    current_verses = []
    pending_bare = False  # True once we've seen a bare ref row; signals section changed

    for srow in sec_rows:
        s_type = srow.get("type", "bare")
        s_ant  = srow.get("antiphon")
        s_refs = srow.get("refs", [])

        # Versicles: close current block and store separately (skipped for display)
        if s_type == "versicle":
            if current_ant is not None:
                blocks.append({"antiphon": current_ant, "verses": current_verses})
                current_ant, current_verses = None, []
            continue

        if s_type == "ant" and s_ant:
            # Always start a new antiphon block (refs may follow on same or next line)
            if current_ant is not None:
                blocks.append({"antiphon": current_ant, "verses": current_verses})
            elif pending_bare and current_verses:
                # Closing a bare-verse section — no antiphon, just verses
                blocks.append({"antiphon": None, "verses": current_verses})
            current_ant = s_ant
            current_verses = []
            pending_bare = False
            for ref in s_refs:
                current_verses.extend(_expand_psalm_ref(conn, ref))

        elif s_type == "bare":
            # First bare ref after an antiphon row: close the antiphon block first
            if current_ant is not None:
                blocks.append({"antiphon": current_ant, "verses": current_verses})
                current_ant, current_verses = None, []
            pending_bare = True
            for ref in s_refs:
                current_verses.extend(_expand_psalm_ref(conn, ref))

    # Flush any remaining open block
    if current_ant is not None:
        blocks.append({"antiphon": current_ant, "verses": current_verses})
    elif current_verses:
        blocks.append({"antiphon": None, "verses": current_verses})

    return blocks


# ---------------------------------------------------------------------------
# Hymn lookup — builds a {section_key -> full_hymn_text} map from source files.
# Section keys mirror the `[Hymnus DayN Laudes]` / `[Hymnus DayN Vespera]` / etc.
# format used in Major Special.txt and Minor Special.txt.
# ---------------------------------------------------------------------------

_HYMN_TAG_PAT = re.compile(r"^\{:H-([^:}]+):\}")
_HYMN_SUBS_PAT = re.compile(r":s/([^/]*)/([^/]*)/")


def _strip_tag_from_line(line: str) -> str:
    """Remove a {:H-TagName:} prefix from a hymn text line."""
    return _HYMN_TAG_PAT.sub("", line)


def _apply_subs(text: str, subs: str) -> str:
    """Apply sed-style s/SEARCH/REPLACE/ substitutions to text."""
    for sub in subs.split("/;"):
        sub = sub.strip()
        if sub.startswith("s/"):
            parts = sub[2:].split("/", 2)
            if len(parts) == 3:
                text = text.replace(parts[1], parts[2])
    return text


def _build_hymn_lookup() -> dict[str, str]:
    """
    Scan Major Special.txt and Minor Special.txt and return a flat
    {section_key -> full_hymn_text} map for all hymn sections.
    """
    latin_dir = os.path.join(REPO_ROOT, "divinum-officium", "web", "www", "horas", "Latin")
    special_dir = os.path.join(latin_dir, "Psalterium", "Special")
    lookup: dict[str, str] = {}

    for fname in ("Major Special.txt", "Minor Special.txt"):
        path = os.path.join(special_dir, fname)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            current_key: str | None = None
            pending_tag: str | None = None
            pending_subs: str | None = None
            lines: list[str] = []

        with open(path, encoding="utf-8") as fh:
            current_key = None
            pending_tag = None
            pending_subs = None
            lines = []
            for raw in fh:
                line = raw.rstrip("\n")
                if line.startswith("[") and line.endswith("]"):
                    # Flush previous section
                    if current_key is not None and lines:
                        body = "\n".join(lines)
                        lookup[current_key] = body
                        # Also register under the bare tag key if present
                        if pending_tag:
                            lookup[f"@:Hymnus{pending_tag}"] = body
                    current_key = line[1:-1]  # e.g. "Hymnus Day1 Laudes"
                    lines = []
                    pending_tag = None
                    pending_subs = None
                    continue

                if current_key is None:
                    continue

                # Lines in hymn sections start with {:H-TagName:} (the tag marker)
                # or are continuation lines.
                if line.startswith("{:H-"):
                    m = _HYMN_TAG_PAT.match(line)
                    if m:
                        pending_tag = m.group(1)  # e.g. "LaudsFeria"
                    # Strip the tag and keep the rest as first text line
                    lines.append(_strip_tag_from_line(line))
                elif line.startswith("@:") or line.startswith("@Tempora"):
                    # Substitution reference: apply subs directly to accumulated lines
                    if ":" in line:
                        after_colon = line.split(":", 1)[1]
                        if "::" in after_colon:
                            ref_part, subs_part = after_colon.split("::", 1)
                        else:
                            ref_part = after_colon
                            subs_part = ""
                        # Check if the ref resolves to another section in the same file
                        ref_key = ref_part.strip()  # e.g. "Hymnus Day1 Laudes"
                        if ref_key in lookup:
                            resolved = lookup[ref_key]
                            if subs_part:
                                resolved = _apply_subs(resolved, subs_part)
                            lookup[current_key] = resolved
                            current_key = None
                            lines = []
                            pending_tag = None
                            pending_subs = None
                            continue
                    # Can't resolve inline — skip
                elif line.startswith("(") or line.startswith("  (") or line.strip() == "":
                    # Rubric / blank — skip
                    pass
                else:
                    lines.append(line)

            # Flush last section
            if current_key is not None and lines:
                lookup[current_key] = "\n".join(lines)

    return lookup


def _do_divine_office_backfill(conn, ferial_map, matins_map, hymn_lookup: dict[str, str]):
    print("  Loading Matins antiphons from matutinum.txt...")
    mat_secs = _load_txt_file("Psalmi matutinum.txt")
    matins_ant_by_day = {}
    for sec_key, sec_rows in mat_secs.items():
        if not sec_key.startswith("Day"):
            continue
        day_str = sec_key[len("Day"):].lstrip("mM")
        try:
            day = int(day_str)
        except ValueError:
            continue
        if day in matins_ant_by_day:
            continue
        for srow in sec_rows:
            if srow["type"] == "ant" and srow.get("antiphon"):
                matins_ant_by_day[day] = srow["antiphon"]
                break

    major_secs = _load_txt_file("Psalmi major.txt")
    laudes_ant_by_day = {}
    vespers_ant_by_day = {}
    for sec_key, sec_rows in major_secs.items():
        m = re.match(r"^Day(\d+)\s+(.*)$", sec_key)
        if not m:
            continue
        day = int(m.group(1))
        ot_raw = m.group(2).strip()
        if ot_raw.lower().startswith("laudes") and day not in laudes_ant_by_day:
            for srow in sec_rows:
                if srow["type"] == "ant" and srow.get("antiphon"):
                    laudes_ant_by_day[day] = srow["antiphon"]
                    break
        elif ot_raw.lower().startswith("vesper") and day not in vespers_ant_by_day:
            for srow in sec_rows:
                if srow["type"] == "ant" and srow.get("antiphon"):
                    vespers_ant_by_day[day] = srow["antiphon"]
                    break

    print("  Loading Completorium antiphons from Psalmi minor.txt...")
    minor_txt_path = os.path.join(
        REPO_ROOT, "divinum-officium", "web", "www", "horas", "Latin",
        "Psalterium", "Psalmi", "Psalmi minor.txt"
    )
    day_map = {"Dominica": 0, "Feria II": 1, "Feria III": 2, "Feria IV": 3,
               "Feria V": 4, "Feria VI": 5, "Sabbato": 6}
    completorium_ant_by_day = {}
    in_completorium = False
    with open(minor_txt_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("[") and line.endswith("]"):
                in_completorium = (line[1:-1] == "Completorium")
                continue
            if not in_completorium:
                continue
            if "=" not in line:
                continue
            label, rest = line.split("=", 1)
            label = label.strip()
            if label not in day_map:
                continue
            day = day_map[label]
            ant = rest.strip()
            # Antiphon text on first line, psalm refs on next line — split at \n
            if "\n" in ant:
                ant = ant.split("\n", 1)[0]
            ant = ant.rstrip(".")
            if ant and day not in completorium_ant_by_day:
                completorium_ant_by_day[day] = ant

    print(f"  Completorium antiphons loaded for {len(completorium_ant_by_day)} days.")

    matins_updated = 0
    for day, ant in matins_ant_by_day.items():
        n = conn.execute(
            "UPDATE divine_office SET matins_antiphon=? "
            "WHERE office_type='Matins' AND matins_antiphon IS NULL",
            (ant,),
        ).rowcount
        matins_updated += n
    print(f"  Updated matins_antiphon for {matins_updated} Matins rows.")

    FERIAL_ROWS = [
        (0, "Laudes",  "Dominica — Laudes",
         "Concéde nos, quǽsumus, omnípotens Deus: ut qui fragilitátis nostræ recognóscimus, "
         "dignitátis quoque nostræ memóres, cuncta tibi devotióne reddámus. $Per Dóminum"),
        (0, "Vespers", "Dominica — Vespera",
         "Largíre quǽsumus, Dómine, fámulis et famulábus tuis certam spem et solidam caritátem: "
         "ut in omni loco et témpore tibi grátias ágere habéant méritis efficiéntibus. $Per Dóminum"),
        (0, "Matins",  "Dominica — Matutinum",
         "Créa in me, Deus, spíritum rectum, et novum intra viscera mea confírma. $Deus, a quo孤儿órum."),
        (1, "Laudes",  "Feria II — Laudes",
         "Dirigátur, Dómine, orátio mea sicut incénsum in conspéctu tuo: et exáudi nos in tua miseratióne confidéntes. $Per Dóminum"),
        (1, "Vespers", "Feria II — Vespera",
         "Illúmina, Dómine, fáciem tuam super servos tuos, et abscónde eos in protectione alárum tuárum. $Per Dóminum"),
        (1, "Matins",  "Feria II — Matutinum",
         "In manúibus tuis, Dómine, fortitúdo mea: quia confirmásti super me misericórdiam tuam. $Deus, a quo孤儿órum."),
        (2, "Laudes",  "Feria III — Laudes",
         "Benedíctus es, Dómine, doce me justificatiónes tuas: et vivificábis me in eis. $Per Dóminum"),
        (2, "Vespers", "Feria III — Vespera",
         "Sit, Dómine, misericórdia tua super nos, quemádmodum sperávimus in te: et in médio templi tui láudabimur. $Per Dóminum"),
        (2, "Matins",  "Feria III — Matutinum",
         "In matutínis, Dómine, meditábor in te: quia fuísti adjútor meus. $Deus, a quo孤儿órum."),
        (3, "Laudes",  "Feria IV — Laudes",
         "Eréxit a Dómino cor meum, ut audírem et annotárem ómnia cármina ejus. $Per Dóminum"),
        (3, "Vespers", "Feria IV — Vespera",
         "Meménto nóminis tui, Dómine, et líbera nos in veritáte tua: quia magna est in nós misericórdia tua. $Per Dóminum"),
        (3, "Matins",  "Feria IV — Matutinum",
         "Expúngere, Dómine, scélera nostra: et mundémur ab ómnibus peccátis nostris. $Deus, a quo孤儿órum."),
        (4, "Laudes",  "Feria V — Laudes",
         "Deus, in adjutórium meum inténde: ut festínanter liberéntur qui cómminantur ánimam meam. $Per Dóminum"),
        (4, "Vespers", "Feria V — Vespera",
         "Tunc invocábis me, et ego exáudiam te: et revocábis et congregábis me. $Per Dóminum"),
        (4, "Matins",  "Feria V — Matutinum",
         "Audívi, Dómine, quod ánimam meam audíres: quóniam in te sperávi. $Deus, a quo孤儿órum."),
        (5, "Laudes",  "Feria VI — Laudes",
         "Lætátus sum in his, quæ dicta sunt mihi: in domum Dómini íbimus. $Per Dóminum"),
        (5, "Vespers", "Feria VI — Vespera",
         "Pósuit in cælo meo lumen non apparens: et nómini tuo Dómine, laus et grátias. $Per Dóminum"),
        (5, "Matins",  "Feria VI — Matutinum",
         "Pérfice gressus meos in viam tuam, Dómine: ut non moveántur vestígia mea. $Deus, a quo孤儿órum."),
        (6, "Laudes",  "Sabbato — Laudes",
         "Sperét Israel in Dómino: quóniam in eo misericórdia et abúndans détestptio in eo. $Per Dóminum"),
        (6, "Vespers", "Sabbato — Vespera",
         "Sint lumbi vestri præcíncti, et lucérnæ ardéntes: quia Dóminus nobis in occúrsum. $Qui tecum"),
        (6, "Matins",  "Sabbato — Matutinum",
         "Laudáte Dóminum, ómnes géntes: et collaudáte eum, ómnes pópuli. $Quóniam confirmáta est."),
    ]

    inserted = 0
    for day, ot, title, oratio in FERIAL_ROWS:
        exists = conn.execute(
            "SELECT COUNT(*) FROM divine_office WHERE file=? AND office_type=?",
            (f"ferial/{day}", ot),
        ).fetchone()[0]
        if exists:
            continue
        antiphon = matins_ant_by_day.get(day) if ot == "Matins" else (
            laudes_ant_by_day.get(day) if ot == "Laudes" else vespers_ant_by_day.get(day)
        )
        ant_list = []
        if ot != "Matins":
            blocks = ferial_map.get((day, ot))
            if blocks:
                for blk in blocks:
                    a = blk.get("antiphon")
                    if a:
                        ant_list.append(a)
        while len(ant_list) < 9:
            ant_list.append("")
        ant_list = ant_list[:9]

        conn.execute(
            """INSERT INTO divine_office
               (file, file_type, title, office_type, oratio,
                antiphon_1, antiphon_2, antiphon_3, antiphon_4, antiphon_5,
                antiphon_6, antiphon_7, antiphon_8, antiphon_9,
                hymn, matins_antiphon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                f"ferial/{day}", "ferial", title, ot, oratio,
                *ant_list[:9],
                None,
                antiphon,
            ),
        )
        inserted += 1

        ps_exists = conn.execute(
            "SELECT COUNT(*) FROM divine_office_psalms WHERE day=? AND office_type=?",
            (day, ot),
        ).fetchone()[0]
        if ps_exists:
            continue
        blocks = matins_map.get(day) if ot == "Matins" else ferial_map.get((day, ot))
        if blocks:
            conn.execute(
                "INSERT INTO divine_office_psalms (day, office_type, antiphon, psalms, psalm_text) VALUES (?, ?, ?, ?, ?)",
                (day, ot, antiphon, "[]", json.dumps(blocks, ensure_ascii=False)),
            )
        else:
            conn.execute(
                "INSERT INTO divine_office_psalms (day, office_type, antiphon, psalms) VALUES (?, ?, ?, ?)",
                (day, ot, antiphon, "[]"),
            )

    print(f"  Inserted {inserted} ferial fallback rows into divine_office.")

    # -----------------------------------------------------------------------
    # Completorium ferial rows — not covered by JSON files, built from txt
    # -----------------------------------------------------------------------
    _LATIN_HORAS = os.path.join(REPO_ROOT, "divinum-officium", "web", "www", "horas", "Latin")

    def _load_txt_sections_local(path):
        sections = {}
        current = None
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.rstrip("\n")
                if line.startswith("[") and line.endswith("]"):
                    current = line[1:-1]
                    sections[current] = []
                elif current is not None:
                    sections[current].append(line)
        return sections

    minor_special = os.path.join(_LATIN_HORAS, "Psalterium", "Special", "Minor Special.txt")
    ms = _load_txt_sections_local(minor_special) if os.path.exists(minor_special) else {}

    hymn_text = "\n".join(ms.get("Hymnus Completorium", []))
    # Standard Completorium oratio
    oratio_text = (
        "Vísita, quǽsumus, Dómine, habitátionem istam, et ómnes insídias inimíci ab ea repélle: "
        "ángeli sancti tui custódiam præstent, et nos in pace custodíre dignéris. Per Dóminum"
    )

    COMPLEMENTUM_ROWS = [
        (0, "Dominica"),
        (1, "Feria II"),
        (2, "Feria III"),
        (3, "Feria IV"),
        (4, "Feria V"),
        (5, "Feria VI"),
        (6, "Sabbato"),
    ]

    comp_inserted = 0
    for day, day_label in COMPLEMENTUM_ROWS:
        exists = conn.execute(
            "SELECT COUNT(*) FROM divine_office WHERE file=? AND office_type=?",
            (f"ferial/{day}", "Completorium"),
        ).fetchone()[0]
        if exists:
            # Update matins_antiphon with Completorium antiphon from txt
            ant = completorium_ant_by_day.get(day, "")
            if ant:
                conn.execute(
                    "UPDATE divine_office SET matins_antiphon=? WHERE file=? AND office_type=?",
                    (ant, f"ferial/{day}", "Completorium"),
                )
            continue
        # Insert new Completorium row
        ant = completorium_ant_by_day.get(day, "")
        conn.execute(
            """INSERT INTO divine_office
               (file, file_type, title, office_type, hymn, matins_antiphon, oratio)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"ferial/{day}",
                "ferial",
                f"{day_label} — Completorium",
                "Completorium",
                hymn_text,
                ant,
                oratio_text,
            ),
        )
        comp_inserted += 1

    print(f"  Completorium ferial rows: {comp_inserted} inserted, {7-comp_inserted-len(completorium_ant_by_day)} updated.")


# ---------------------------------------------------------------------------
# Hymn reference resolver
# ---------------------------------------------------------------------------
# Resolves @-style hymn references that appear in the Latin .txt source files
# and in the JSON data. E.g.:
#   @:Hymnus Vespera         → inline section named [Hymnus Vespera]
#   @Sancti/03-19:Hymnus Vespera  → section in Latin/Sancti/03-19.txt
#   @Commune/C1:Hymnus Vespera
#   @Psalterium/Special/Major Special:Hymnus Quad5 Laudes
# Substitutions are also supported: "s/SEARCH/REPLACE/" strips the match,
# "s/SEARCH/REPLACE/;s/SEARCH2/REPLACE2/" chains them.
# ---------------------------------------------------------------------------

_LATIN_HORAS = os.path.join(
    REPO_ROOT, "divinum-officium", "web", "www", "horas", "Latin"
)
_HYMN_TAG_RE = re.compile(r"^(\d+:)?\{:H-([^:}]+):\}(?:v\.)?(.*)$")


def _load_txt_sections(filepath: str) -> dict[str, list[str]]:
    """Parse a Latin horas .txt file into sections keyed by [Section Name]."""
    if not os.path.exists(filepath):
        return {}
    sections: dict[str, list[str]] = {}
    current: str | None = None
    with open(filepath, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if line.startswith("[") and line.endswith("]"):
                current = line[1:-1]
                sections.setdefault(current, [])
            elif current is not None:
                sections[current].append(line)
    return sections


def _get_hymn_tag_body(tag: str) -> str:
    """
    Load all Latin hymn tag files and extract the body of the named hymn.
    Hymn tags like H-Exsultetorbisgaudiis resolve to a file like
    H-Exsultetorbisgaudiis.txt in the Psalterium directory.
    """
    hymn_dir = os.path.join(_LATIN_HORAS, "Psalterium")
    tag_file = os.path.join(hymn_dir, f"{tag}.txt")
    if not os.path.exists(tag_file):
        return ""
    # The hymn file contains a [Hymnus Xxxx] section with the text lines
    secs = _load_txt_sections(tag_file)
    # Find the section whose name (lowercased no-space) matches the tag
    tag_lower = tag.lower()
    for sec_name, lines in secs.items():
        if sec_name.lower().replace(" ", "").replace("-", "") == tag_lower:
            return "\n".join(lines)
    # Fallback: return all sections concatenated
    return "\n".join(
        line for lines in secs.values() for line in lines
        if line.strip() and not line.startswith("[")
    )


def _apply_subs(text: str, subs: str) -> str:
    """Apply sed-style s/SEARCH/REPLACE/ substitutions to text."""
    for sub in subs.split("/;"):
        sub = sub.strip()
        if sub.startswith("s/"):
            parts = sub[2:].split("/", 2)
            if len(parts) == 3:
                text = text.replace(parts[1], parts[2])
    return text


def _resolve_hymn_ref(ref: str, json_dir: str = "") -> str:
    """
    Resolve a hymn @-reference string to its full Latin text.

    Formats:
      @:Hymnus Vespera                        → inline section in current file
      @Sancti/03-19:Hymnus Vespera            → file in Latin/Sancti/03-19.txt
      @Tempora/Pasc2-3:Hymnus Vespera         → file in Latin/Tempora/Pasc2-3.txt
      @Commune/C1:Hymnus Vespera              → file in Latin/Commune/C1.txt
      @Psalterium/Special/Major Special:Hymnus Quad5 Laudes
      @Sancti/03-19:Hymnus Vespera:s/Scándere/Vúlnera/   → substitution
      @Sancti/03-19:Hymnus Vespera::s/SEARCH/REPLACE/    → same (empty sub-prefix OK)

    json_dir is the path prefix used to resolve inline (@:) references — if
    provided and no explicit file_part is given, Minor Special.txt is checked.
    """
    if not ref or not ref.startswith("@"):
        return ref

    # Split off any trailing substitutions "::s/.../"
    text_part, _, subst_part = ref.partition("::")
    # text_part looks like: ":Hymnus Vespera" or "Sancti/03-19:Hymnus Vespera"
    core = text_part.lstrip("@")
    subs = subst_part.strip()

    # Parse the reference
    if ":" in core:
        file_part, sec_name = core.split(":", 1)
    else:
        file_part = ""
        sec_name = core

    file_path: str
    if file_part:
        # e.g. "Sancti/03-19", "Tempora/Pasc2-3", "Psalterium/Special/Major Special"
        file_path = os.path.join(_LATIN_HORAS, file_part + ".txt")
    else:
        # Inline reference: try Minor Special.txt for Completorium hymn refs
        minor_special = os.path.join(_LATIN_HORAS, "Psalterium", "Special", "Minor Special.txt")
        if os.path.exists(minor_special):
            sections = _load_txt_sections(minor_special)
            for k, v in sections.items():
                if k.lower() == sec_name.lower():
                    text = "\n".join(v)
                    return _apply_subs(text, subs) if subs else text
            # Partial match fallback
            sec_lower = sec_name.lower()
            for k, v in sections.items():
                if sec_lower in k.lower() or k.lower() in sec_lower:
                    text = "\n".join(v)
                    return _apply_subs(text, subs) if subs else text
        file_path = ""

    # Try to find the section in the target file
    sections: dict[str, list[str]] = {}
    if file_path and os.path.exists(file_path):
        sections = _load_txt_sections(file_path)

    # Also check if the section name refers to a hymn tag file
    tag_match = _HYMN_TAG_RE.match(sec_name)
    if tag_match:
        tag = tag_match.group(2)
        tag_body = _get_hymn_tag_body(tag)
        if tag_body:
            # If there's a specific section name we also want, prefer that
            tag_specific_key = sec_name.split(":")[0] if ":" in sec_name else sec_name
            for k, v in sections.items():
                if k.lower() == tag_specific_key.lower():
                    text = "\n".join(v)
                    return _apply_subs(text, subs) if subs else text
            # Fall back to tag body
            return _apply_subs(tag_body, subs) if subs else tag_body

    # Look up the named section
    for k, v in sections.items():
        if k.lower() == sec_name.lower():
            text = "\n".join(v)
            return _apply_subs(text, subs) if subs else text

    # Try case-insensitive partial match
    sec_lower = sec_name.lower()
    for k, v in sections.items():
        if sec_lower in k.lower() or k.lower() in sec_lower:
            text = "\n".join(v)
            return _apply_subs(text, subs) if subs else text

    return ref  # unresolved


def _post_resolve_hymns(conn):
    """After all divine_office rows are inserted, resolve any remaining @ hymn refs."""
    cu = conn.execute(
        "SELECT id, hymn FROM divine_office WHERE hymn LIKE '@%'"
    )
    rows = cu.fetchall()
    if not rows:
        return 0
    resolved = 0
    for row_id, hymn_ref in rows:
        resolved_text = _resolve_hymn_ref(hymn_ref)
        if resolved_text != hymn_ref:
            conn.execute(
                "UPDATE divine_office SET hymn=? WHERE id=?",
                (resolved_text, row_id),
            )
            resolved += 1
    return resolved



def compile_baltimore_catechism(conn: sqlite3.Connection) -> None:
    path = os.path.join(CONTENT_DIR, "catechism", "baltimore.json")
    if not os.path.exists(path):
        print("  SKIP: catechism/baltimore.json not found.")
        return
    with open(path) as f:
        entries = json.load(f)
    if not entries:
        print("  SKIP: baltimore.json is empty.")
        return
    for e in entries:
        conn.execute(
            "INSERT INTO baltimore_catechism (id, number, lesson, question, answer) VALUES (?, ?, ?, ?, ?)",
            (e["id"], e["number"], e["lesson"], e["question"], e["answer"]),
        )
    print(f"  Baltimore Catechism: {len(entries)} entries indexed.")


def compile_divine_office(conn):
    do_dir = os.path.join(CONTENT_DIR, "divine_office", "data")
    print(f"  DEBUG: CONTENT_DIR={CONTENT_DIR}")
    print(f"  DEBUG: do_dir={do_dir} isdir={os.path.isdir(do_dir)}")
    if not os.path.isdir(do_dir):
        print("  SKIP: content/divine_office/data not found.")
        return

    CALENDAR_FILE_TYPES = {"tempora", "sancti", "commune", "extra",
                           "orationes", "psalmi", "missa", "martyrologium"}

    office_rows = 0
    calendar_rows = 0
    psalm_rows = 0

    for root, _dirs, files in os.walk(do_dir):
        for fn in sorted(files):
            if not fn.endswith(".json"):
                continue
            path = os.path.join(root, fn)
            rel = os.path.relpath(path, do_dir)
            parts = rel.split(os.sep)
            file_type = parts[0] if len(parts) > 1 else fn
            file_stem = fn.rsplit(".json", 1)[0]

            with open(path) as f:
                data = json.load(f)

            if isinstance(data, list):
                merged = {}
                for item in data:
                    if isinstance(item, dict):
                        merged.update(item)

                # Filter: only process list items that have real office content
                # (skip pure-metadata items like {"Rank":...}, {"Rule":...}, {"Comment":...}, etc.)
                def _has_office_content(item: dict) -> bool:
                    if not isinstance(item, dict):
                        return False
                    # Presence of these keys = real office content
                    office_keys = ("Officium", "Scriptura", "title",
                                  "Lectio1", "Lectio 1", "Lectio2", "Lectio 2",
                                  "Hymnus", "Hymnus Laudes", "Hymnus Vespera", "HymnusM Laudes", "HymnusM Vespera",
                                  "Ant 1", "Ant 2", "Ant Laudes", "Ant Vespera", "AntVespera",
                                  "Invitatorium", "Oratio", "Versum", "Versus")
                    for key in office_keys:
                        if key in item:
                            return True
                    # Also accept items with any lectio/antiphon/hymn keys
                    for key in item:
                        kl = key.lower()
                        if kl.startswith("lectio") or kl.startswith("ant") or kl.startswith("hymn"):
                            return True
                    return False

                content_items = [it for it in data if isinstance(it, dict) and _has_office_content(it)]
                if not content_items:
                    continue  # no real office content in this file

                # Build merged from content items only (skip metadata-only items)
                merged = {}
                for item in content_items:
                    merged.update(item)

                raw_title = (
                    merged.get("Officium") or merged.get("Scriptura")
                    or merged.get("title") or _parse_rank(merged.get("Rank"))
                )
                title = _clean_title(raw_title) if raw_title else ""
                rank = _parse_rank(merged.get("Rank"))

                has_lectio1 = bool(merged.get("Lectio1") or merged.get("Lectio 1"))
                has_lectio2 = bool(merged.get("Lectio2") or merged.get("Lectio 2"))
                has_lectio4_or_more = any(
                    merged.get(f"Lectio{i}") for i in list(range(4, 13)) + list(range(90, 100))
                )
                hymn_keys = [k for k in merged if k.lower().startswith("hymnus")]
                ant_keys = [k for k in merged if k.lower().startswith("ant")]

                def _has_vespers():
                    return has_lectio2 or any("vesper" in k.lower() for k in hymn_keys) \
                           or any("vesper" in k.lower() for k in ant_keys)

                def _has_laudes():
                    return has_lectio1 or any("laudes" in k.lower() for k in hymn_keys) \
                           or any(k.lower() in ("ant laudes",) for k in ant_keys) \
                           or any(k.lower() in (f"ant {i}", f"ant{i}") for i in range(1, 10) for k in ant_keys)

                def _has_matins():
                    return has_lectio4_or_more or any("matutin" in k.lower() for k in hymn_keys) \
                           or any(k.lower() in ("ant matutinum", "ant matins") for k in ant_keys)

                sections = []
                if _has_vespers():
                    sections.append(("Vespers", merged))
                if _has_laudes():
                    sections.append(("Laudes", merged))
                if _has_matins():
                    sections.append(("Matins", merged))
                if not sections:
                    sections.append(("", merged))

                if file_type in CALENDAR_FILE_TYPES:
                    conn.execute(
                        """INSERT OR REPLACE INTO divine_office_calendar
                           (key, title, rank, grade, tempora_file, sancti_file, commune_file)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            file_stem, title, rank, merged.get("Grade", 0),
                            f"{file_type}/{file_stem}" if file_type == "tempora" else None,
                            f"{file_type}/{file_stem}" if file_type == "sancti" else None,
                            f"{file_type}/{file_stem}" if file_type == "commune" else None,
                        ),
                    )
                    calendar_rows += 1

                def _inline_hymn_resolve(ref: str) -> str:
                    """
                    Resolve @:SectionName refs against the merged JSON dict (same file).
                    E.g. @:Hymnus Vespera  →  merged.get("Hymnus Vespera")
                    Strips trailing ::s/SEARCH/REPLACE/ substitutions.
                    """
                    if not ref or not ref.startswith("@:"):
                        return ref
                    ref = ref[1:]  # drop leading @, leaving ":Hymnus Vespera"
                    ref = ref.lstrip(":")  # strip the remaining leading colon
                    subs = ""
                    if "::" in ref:
                        ref, subs = ref.split("::", 1)
                    key = ref.strip()  # e.g. "Hymnus Vespera"
                    # Case-insensitive lookup in merged dict
                    key_lower = key.lower()
                    for k, v in merged.items():
                        if k.lower() == key_lower:
                            text = str(v)
                            for s in subs.split("/;"):
                                s = s.strip()
                                if s.startswith("s/") and s.count("/") >= 4:
                                    parts = s[2:].split("/", 2)
                                    if len(parts) == 3:
                                        text = text.replace(parts[1], parts[2])
                            return text
                    return "@" + ref  # unresolved

                for office_type, sec in sections:
                    hymn = None
                    if office_type == "Vespers":
                        hymn = merged.get("Hymnus Vespera") or merged.get("HymnusM Vespera")
                    elif office_type == "Laudes":
                        hymn = merged.get("Hymnus Laudes") or merged.get("HymnusM Laudes")
                    elif office_type == "Matins":
                        hymn = merged.get("Hymnus Matutinum") or merged.get("HymnusM Matutinum")
                    # Resolve inline @:SectionName refs against merged JSON
                    if hymn and str(hymn).startswith("@:"):
                        hymn = _inline_hymn_resolve(str(hymn))

                    laudes_ants = [
                        merged.get(f"Ant {i}") or merged.get(f"Ant{i}") or ""
                        for i in range(1, 10)
                    ]
                    vespera_ants = []
                    v1 = merged.get("Ant Vespera") or merged.get("AntVespera")
                    if v1:
                        vespera_ants.append(v1)
                    for i in range(1, 13):
                        v = merged.get(f"Ant Vespera {i}") or merged.get(f"AntVespera{i}")
                        if v:
                            vespera_ants.append(v)
                    while len(vespera_ants) < 12:
                        vespera_ants.append("")
                    vespera_ants = vespera_ants[:12]  # CAP at 12 columns

                    if office_type == "Laudes":
                        lectio1 = merged.get("Lectio1") or merged.get("Lectio 1")
                        lectio2, lectio3 = None, None
                        resp1 = merged.get("Responsory1")
                        resp2, resp3 = None, None
                    elif office_type == "Vespers":
                        lectio1, lectio3 = None, None
                        lectio2 = merged.get("Lectio2") or merged.get("Lectio 2")
                        resp1, resp3 = None, None
                        resp2 = merged.get("Responsory2")
                    else:
                        lectio1 = merged.get("Lectio4") or merged.get("Lectio 4") \
                                   or merged.get("Lectio94") \
                                   or merged.get("Lectio1") or merged.get("Lectio 1")
                        lectio2 = merged.get("Lectio5") or merged.get("Lectio 5") \
                                   or merged.get("Lectio2") or merged.get("Lectio 2")
                        lectio3 = merged.get("Lectio6") or merged.get("Lectio 6") \
                                   or merged.get("Lectio3") or merged.get("Lectio 3")
                        resp1, resp2, resp3 = merged.get("Responsory1"), merged.get("Responsory2"), merged.get("Responsory3")

                    sec_title = title
                    if len(sections) > 1:
                        sec_title = f"{title} — {office_type}" if title else office_type

                    conn.execute(
                        """INSERT INTO divine_office
                           (file, file_type, title, office_type, invitatorium,
                            antiphon_1, antiphon_2, antiphon_3, antiphon_4, antiphon_5,
                            antiphon_6, antiphon_7, antiphon_8, antiphon_9,
                            antiphon_vespera_1, antiphon_vespera_2, antiphon_vespera_3,
                            antiphon_vespera_4, antiphon_vespera_5, antiphon_vespera_6,
                            antiphon_vespera_7, antiphon_vespera_8, antiphon_vespera_9,
                            antiphon_vespera_10, antiphon_vespera_11, antiphon_vespera_12,
                            hymn, lectio_1, lectio_2, lectio_3,
                            responsory_1, responsory_2, responsory_3,
                            versus, preces, oratio, conclusio, matins_antiphon)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?)""",
                        (
                            rel.rsplit(".json", 1)[0], file_type, sec_title,
                            office_type if office_type else None,
                            merged.get("Invitatorium"),
                            *laudes_ants,
                            *vespera_ants,
                            hymn,
                            lectio1, lectio2, lectio3,
                            resp1, resp2, resp3,
                            merged.get("Versum") or merged.get("Versus"),
                            merged.get("Preces"),
                            merged.get("Oratio"),
                            merged.get("Conclusio"),
                            None,
                        ),
                    )
                    office_rows += 1

            elif isinstance(data, dict):
                for key, val in data.items():
                    key_str = str(key)
                    if key_str.startswith("("):
                        inner = key_str[1:-1]
                        p = [pt.strip().strip("'\"") for pt in inner.split(",")]
                        day_str = p[0]
                        ot = _normalize_office_type(p[1]) if len(p) > 1 else ""
                        try:
                            day = int(day_str)
                        except ValueError:
                            day = 0
                    elif key_str.startswith("Day"):
                        day_rest = key_str[len("Day"):]
                        m = re.match(r"^([a-z]?)(\d+)", day_rest)
                        day = int(m.group(2)) if m else 0
                        ot = day_rest.split("_", 1)[1] if "_" in day_rest else ""
                    else:
                        try:
                            day = int(key_str)
                        except ValueError:
                            day = 0
                        ot = key_str

                    norm_ot = _normalize_office_type(ot)
                    if not norm_ot:
                        continue  # Skip rows without a usable office type
                    conn.execute(
                        """INSERT OR IGNORE INTO divine_office_psalms
                           (day, office_type, antiphon, psalms)
                           VALUES (?, ?, ?, ?)""",
                        (
                            day,
                            norm_ot,
                            val.get("antiphon") if isinstance(val, dict) else None,
                            json.dumps(val.get("psalms", []) if isinstance(val, dict) else []),
                        ),
                    )
                    psalm_rows += 1

    print(f"  Divine Office: {office_rows} offices, {calendar_rows} calendar entries, {psalm_rows} psalm rows.")

    print("  Pre-expanding psalm texts from Latin Psalmi txt files...")
    major_secs = _load_txt_file("Psalmi major.txt")
    mat_secs = _load_txt_file("Psalmi matutinum.txt")

    ferial_map = {}
    for sec_key, sec_rows in major_secs.items():
        m = re.match(r"^Day(\d+)\s+(.*)$", sec_key)
        if not m:
            continue
        day = int(m.group(1))
        ot_raw = m.group(2).strip()
        ot = "Vespers" if ot_raw.lower().startswith("vesper") else "Laudes" if ot_raw.lower().startswith("laudes") else ot_raw
        blocks = _build_blocks_from_txt_rows(sec_rows, conn)
        if blocks:
            ferial_map[(day, ot)] = blocks

    matins_map = {}
    for sec_key, sec_rows in mat_secs.items():
        if not sec_key.startswith("Day"):
            continue
        day_str = sec_key[len("Day"):].lstrip("mM")
        try:
            day = int(day_str)
        except ValueError:
            continue
        blocks = _build_blocks_from_txt_rows(sec_rows, conn)
        if blocks:
            matins_map[day] = blocks

    expanded = 0
    cu = conn.execute("SELECT id, day, office_type FROM divine_office_psalms")
    for row_id, day, office_type in cu.fetchall():
        ot = office_type or "Laudes"
        blocks = None
        if ot == "Matins":
            blocks = matins_map.get(day)
        else:
            blocks = ferial_map.get((day, ot))
            if not blocks:
                other = "Vespers" if ot == "Laudes" else "Laudes"
                blocks = ferial_map.get((day, other))
            if not blocks:
                weekday = (day - 1) % 7
                blocks = ferial_map.get((weekday, ot))
        if blocks:
            conn.execute(
                "UPDATE divine_office_psalms SET psalm_text=? WHERE id=?",
                (json.dumps(blocks, ensure_ascii=False), row_id),
            )
            expanded += 1

    print(f"  Expanded {expanded} psalm rows with antiphon text and verse text.")

    print("  Building hymn lookup from Major/Minor Special.txt...")
    hymn_lookup = _build_hymn_lookup()
    hymn_keys_found = len(hymn_lookup)
    _do_divine_office_backfill(conn, ferial_map, matins_map, hymn_lookup)

    print("  Resolving hymn @-references...")
    hymn_resolved = _post_resolve_hymns(conn)
    print(f"  Resolved {hymn_resolved} hymn @-references.")

    print("  Post-processing hymns (tag expansion, @-ref resolution, ferial hymns)...")
    _HYMN_TAG_PAT = re.compile(r"^\{:H-([^:}]+):\}")
    LATIN_HORAS = os.path.join(REPO_ROOT, "divinum-officium", "web", "www", "horas", "Latin")

    def _strip_tag(line: str) -> str:
        return _HYMN_TAG_PAT.sub("", line)

    # Build comprehensive tag -> text lookup from ALL Latin horas .txt files
    tag_to_text: dict[str, str] = {}
    for root, _dirs, files in os.walk(LATIN_HORAS):
        for fn in sorted(files):
            if not fn.endswith(".txt"):
                continue
            fp = os.path.join(root, fn)
            with open(fp, encoding="utf-8", errors="ignore") as fh:
                current_key: str | None = None
                lines: list[str] = []
                pending_tag: str | None = None
                for raw in fh:
                    line = raw.rstrip("\n")
                    if line.startswith("[") and line.endswith("]"):
                        if current_key is not None and lines and pending_tag:
                            tag_to_text[pending_tag] = "\n".join(lines)
                        current_key = line[1:-1]
                        lines = []
                        pending_tag = None
                        continue
                    if current_key is None:
                        continue
                    m = _HYMN_TAG_PAT.match(line)
                    if m:
                        pending_tag = m.group(1)
                    if line.startswith("(") or line.startswith("  (") or line.strip() == "":
                        pass
                    else:
                        lines.append(_strip_tag(line))
                if current_key is not None and lines and pending_tag:
                    tag_to_text[pending_tag] = "\n".join(lines)
    print(f"    Loaded {len(tag_to_text)} hymn tag definitions.")

    def _resolve_hymn_ref(ref: str) -> str:
        """Resolve a hymn @-reference string to its full text."""
        if not ref or not ref.startswith("@"):
            return ref
        text_part, _, subst_part = ref.partition("::")
        subs = subst_part.strip()
        core = text_part.lstrip("@")
        if ":" in core:
            file_part, sec_name = core.split(":", 1)
            fp = os.path.join(LATIN_HORAS, file_part + ".txt")
        else:
            fp = ""
            sec_name = core
        sections: dict[str, list[str]] = {}
        if fp and os.path.exists(fp):
            with open(fp, encoding="utf-8", errors="ignore") as fh:
                current: str | None = None
                for raw in fh:
                    line = raw.rstrip("\n")
                    if line.startswith("[") and line.endswith("]"):
                        current = line[1:-1]
                        sections.setdefault(current, [])
                    elif current is not None:
                        sections[current].append(line)
        for k, v in sections.items():
            if k.lower() == sec_name.lower():
                text = "\n".join(v)
                if subs:
                    for s in subs.split("/;"):
                        s = s.strip()
                        if s.startswith("s/"):
                            parts = s[2:].split("/", 2)
                            if len(parts) == 3:
                                text = text.replace(parts[1], parts[2])
                return text
        return ref

    # Build ferial hymn lookup: day+office_type -> hymn text
    ferial_hymns: dict[tuple[int, str], str] = {}
    for tag, text in tag_to_text.items():
        # Match patterns like "LaudsFeria", "VespFeria", "LaudsAdv", etc.
        m = re.match(r"^(Lauds|Vesp|Mat)([A-Z][a-z]*)$", tag)
        if m:
            ot = "Laudes" if m.group(1) == "Lauds" else "Vespers" if m.group(1) == "Vesp" else "Matins"
            ferial_hymns[(0, ot)] = text  # Default to Sunday (day 0)
    # More specific ferial lookup
    for tag, text in tag_to_text.items():
        if tag in ("LaudsFeria", "VespFeria"):
            ot = "Laudes" if "Lauds" in tag else "Vespers"
            ferial_hymns[(0, ot)] = text

    hymn_updated = 0
    cu = conn.execute("SELECT id, hymn FROM divine_office WHERE hymn IS NOT NULL")
    for row_id, hymn in cu.fetchall():
        if not hymn:
            continue
        # Step 1: expand {:H-TagName:} tag markup
        tag_m = re.match(r"^\{:H-([^:}]+):\}(.*)$", hymn, re.DOTALL)
        if tag_m:
            tag, rest = tag_m.group(1), tag_m.group(2)
            expanded = tag_to_text.get(tag, "")
            if rest.strip():
                expanded = expanded.rstrip() + "\n" + rest.strip()
            conn.execute("UPDATE divine_office SET hymn=? WHERE id=?", (expanded, row_id))
            hymn_updated += 1
            hymn = expanded  # for step 2

        # Step 2: resolve @-references
        if hymn.startswith("@"):
            resolved = _resolve_hymn_ref(hymn)
            if resolved != hymn:
                conn.execute("UPDATE divine_office SET hymn=? WHERE id=?", (resolved, row_id))
                hymn_updated += 1

    # Step 3: backfill ferial hymns
    ferial_hymn_tags = {
        "Laudes": "LaudsFeria",
        "Vespers": "VespFeria",
        "Matins": "Audibenigne",
    }
    ferial_updated = 0
    for ot, tag in ferial_hymn_tags.items():
        hymn_text = tag_to_text.get(tag)
        if not hymn_text:
            continue
        n = conn.execute(
            "UPDATE divine_office SET hymn=? WHERE office_type=? AND (hymn IS NULL OR hymn = '')",
            (hymn_text, ot),
        ).rowcount
        ferial_updated += n

    # Step 3b: backfill ferial hymns for NULL-office-type entries
    # that have antiphon data indicating which office they belong to
    ferial_null_updated = 0
    for ot, tag in ferial_hymn_tags.items():
        hymn_text = tag_to_text.get(tag)
        if not hymn_text:
            continue
        if ot == "Laudes":
            # Has any laudes antiphon column filled
            n = conn.execute(
                "UPDATE divine_office SET hymn=? WHERE office_type IS NULL "
                "AND (hymn IS NULL OR hymn = '') "
                "AND (antiphon_1 IS NOT NULL AND antiphon_1 != '')",
                (hymn_text,),
            ).rowcount
        elif ot == "Vespers":
            # Has any vespera antiphon column filled
            n = conn.execute(
                "UPDATE divine_office SET hymn=? WHERE office_type IS NULL "
                "AND (hymn IS NULL OR hymn = '') "
                "AND (antiphon_vespera_1 IS NOT NULL AND antiphon_vespera_1 != '')",
                (hymn_text,),
            ).rowcount
        else:
            continue  # Matins not inferred from antiphons
        ferial_null_updated += n
    ferial_updated += ferial_null_updated
    print(f"    Updated {hymn_updated} hymn rows (tag expand + @-resolve), backfilled {ferial_updated} ferial hymn rows (incl. {ferial_null_updated} NULL-ot).")

    # Step 4: resolve remaining cross-file @ refs
    # Scan ALL Latin horas directories (Sancti, Commune, Tempora) to build a
    # complete file index keyed by filename -> {section_name: [lines]}.
    hymn_file_index: dict[str, dict[str, list[str]]] = {}
    for subdir in ("Sancti", "Commune", "Tempora"):
        subdir_path = os.path.join(LATIN_HORAS, subdir)
        if not os.path.isdir(subdir_path):
            continue
        for fn in os.listdir(subdir_path):
            if not fn.endswith(".txt"):
                continue
            fp = os.path.join(subdir_path, fn)
            sections: dict[str, list[str]] = {}
            current: str | None = None
            with open(fp, encoding="utf-8", errors="ignore") as fh:
                for raw in fh:
                    line = raw.rstrip("\n")
                    if line.startswith("[") and line.endswith("]"):
                        current = line[1:-1]
                        sections.setdefault(current, [])
                    elif current is not None:
                        sections[current].append(line)
            if sections:
                hymn_file_index[fn] = sections

    def _resolve_hymn_chain(ref: str, _seen: set | None = None) -> str:
        """
        Resolve a hymn reference string to its full text.
        Handles:
          @:Hymnus Vespera        -> inline section in source file
          @Sancti/02-22          -> default hymn in target file
          @Sancti/02-22:Hymnus Vespera
          @Commune/C11           -> default hymn
          @Tempora/Pasc2-3:Hymnus Laudes
          @Commune/C6::16-25     -> trailing :: marker, no actual sub
          ::s/PATTERN/REPLACEMENT/;::s/PATTERN/REPLACEMENT/  (subs)
        Returns the resolved hymn text or the original ref if unresolved.
        """
        if _seen is None:
            _seen = set()
        if not ref or not ref.startswith("@"):
            return ref

        # Detect and strip trailing date range slugs (::16-25, ::Pasc2-3, etc.)
        cleaned = ref.lstrip("@")
        slug = ""
        m = re.match(r"^(.+?)(::[a-zA-Z0-9_-]+)$", cleaned)
        if m:
            slug = m.group(2)  # e.g. "::16-25"
            cleaned = m.group(1)

        # Extract ::substitutions if present
        subs = ""
        if "::" in cleaned:
            cleaned, subs = cleaned.split("::", 1)
        elif slug:
            subs = slug.lstrip(":")

        # Resolve file_part and sec_hint
        if ":" in cleaned:
            file_part, sec_hint = cleaned.split(":", 1)
        else:
            file_part, sec_hint = cleaned, ""

        file_part = file_part.strip()
        fn = file_part.split("/")[-1] + ".txt"

        sections = hymn_file_index.get(fn, {})

        # Helper: find section by (partial) name match
        def find_section(hint: str) -> str | None:
            hint_lower = hint.lower()
            for sec_name, lines in sections.items():
                sn_lower = sec_name.lower()
                # Exact-ish match: hint appears in section name
                if hint_lower in sn_lower or sn_lower in hint_lower:
                    return "\n".join(lines)
            return None

        # Primary section lookup
        raw_text: str | None = None
        if sec_hint:
            raw_text = find_section(sec_hint)
        else:
            # Default: prefer vespers > laudes > matins > first hymn
            for pref in ("vesper", "laudes", "matutin"):
                for sec_name, lines in sections.items():
                    if "hymnus" in sec_name.lower() and pref in sec_name.lower():
                        raw_text = "\n".join(lines)
                        break
                if raw_text:
                    break

        if raw_text is None:
            return ref  # file not found or section not found

        # If the resolved text is itself a @ reference, follow the chain
        stripped = raw_text.strip()
        if stripped.startswith("@") and stripped not in _seen:
            _seen2 = set(_seen) | {stripped}
            return _resolve_hymn_chain(stripped, _seen2)

        return raw_text

    def _apply_subs(text: str, subs: str) -> str:
        """Apply sed-style s/SEARCH/REPLACE/ substitutions."""
        for s in subs.split("/;"):
            s = s.strip()
            if s.startswith("s/") and s.count("/") >= 4:
                parts = s[2:].split("/", 2)
                if len(parts) == 3:
                    text = text.replace(parts[1], parts[2])
        return text

    cross_resolved = 0
    cu = conn.execute("SELECT id, hymn FROM divine_office WHERE hymn LIKE '@%'")
    for row_id, hymn_ref in cu.fetchall():
        resolved = _resolve_hymn_chain(hymn_ref)
        if resolved != hymn_ref:
            conn.execute(
                "UPDATE divine_office SET hymn=? WHERE id=?",
                (resolved, row_id),
            )
            cross_resolved += 1
    print(f"    Cross-file @ ref resolution: {cross_resolved} rows resolved.")


def main() -> None:
    os.makedirs(os.path.dirname(OUT_DB), exist_ok=True)

    if os.path.exists(OUT_DB):
        os.remove(OUT_DB)

    print(f"Building {OUT_DB} ...")
    conn = sqlite3.connect(OUT_DB)

    try:
        create_schema(conn)
        print("Schema created.")

        print("Compiling Bible (DRA)...")
        compile_dr_format(conn, "dra", lang="en")

        print("Compiling Bible (Latin Vulgate)...")
        compile_dr_format(conn, "vulgate", lang="la", book_full_names=_LA_BOOK_NAMES)

        print("Compiling Bible (Latin Vulgate — English Translation)...")
        compile_dr_format(conn, "vulgate-et", lang="en")

        print("Compiling Bible (World English Bible — Catholic Edition)...")
        compile_dr_format(conn, "web-c", lang="en")

        print("Compiling Bible (Bíblia Ave-Maria — Portuguese)...")
        compile_dr_format(conn, "ave-maria", lang="pt-BR", book_full_names=_PT_BOOK_NAMES)

        print("Compiling Bible (Bíblia dos Capuchinhos — European Portuguese)...")
        compile_dr_format(conn, "porcap", lang="pt-PT", book_full_names=_PORCAP_BOOK_NAMES)

        print("Compiling Bible (Crampon 1923 — French)...")
        compile_dr_format(conn, "crampon", lang="fr", book_full_names=_FR_BOOK_NAMES)

        print("Compiling Bible (Biblija RK K1998 — Lithuanian)...")
        compile_dr_format(conn, "rk1998", lang="lt", book_full_names=_LT_BOOK_NAMES)

        print("Compiling Bible (Biblia Platense — Spanish)...")
        compile_dr_format(conn, "platense", lang="es", book_full_names=_ES_BOOK_NAMES)

        print("Compiling Bible (思高圣经 — Chinese)...")
        compile_sg(conn)

        print("Compiling Catechism...")
        compile_catechism(conn)

        print("Compiling Prayers...")
        compile_prayers(conn, "en")
        compile_prayers(conn, "pt-BR")
        compile_prayers(conn, "pt-PT")
        compile_prayers(conn, "fr")
        compile_prayers(conn, "lt")
        compile_prayers(conn, "es")

        print("Compiling Novenas...")
        compile_novenas(conn, "en")
        compile_novenas(conn, "pt-BR")
        compile_novenas(conn, "pt-PT")
        compile_novenas(conn, "fr")
        compile_novenas(conn, "es")

        print("Compiling Rosary...")
        compile_rosary(conn, "en")
        compile_rosary(conn, "pt-BR")
        compile_rosary(conn, "pt-PT")
        compile_rosary(conn, "pt-PT", variant="fatima")
        compile_rosary(conn, "fr")
        compile_rosary(conn, "lt")
        compile_rosary(conn, "es")

        print("Compiling Saints...")
        compile_saints(conn, "en")
        compile_saints(conn, "es")
        compile_saints(conn, "fr")
        compile_saints(conn, "lt")
        compile_saints(conn, "pt-BR")
        compile_saints(conn, "pt-PT")
        compile_saints(conn, "zh-CN")

        compile_baltimore_catechism(conn)
        compile_divine_office(conn)
        conn.commit()

        print("Optimizing FTS indexes...")
        conn.isolation_level = None
        conn.execute("INSERT INTO verses_fts(verses_fts) VALUES('optimize')")
        conn.execute("INSERT INTO prayers_fts(prayers_fts) VALUES('optimize')")
        conn.execute("VACUUM")

        size_kb = os.path.getsize(OUT_DB) // 1024
        print(f"\nDone. Output: {OUT_DB} ({size_kb} KB)")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}", file=sys.stderr)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
