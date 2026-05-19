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
            capitulum   TEXT,
            oratio      TEXT,
            conclusio   TEXT,
            matins_antiphon TEXT,
            supplemental TEXT
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

    # Canonical CCC structure: paragraph ranges map to part/section/chapter/article
    # Derived from official CCC paragraph numbering (CCC paragraph numbers are standard).
    CCC_STRUCTURE = [
        # (start, end, part, section, chapter, article)
        # Part 1: Profession of Faith
        (1, 13,   1, None, None, None),
        (14, 25,  1, 1, None, None),
        (26, 43,  1, 1, 1, None),
        (44, 46,  1, 1, 2, None),
        (47, 67,  1, 2, None, None),
        (68, 71,  1, 3, None, None),
        (72, 73,  1, 3, 1, None),
        (74, 95,  1, 4, None, None),
        (96, 99,  1, 4, 1, None),
        (100, 104, 1, 4, 2, None),
        (105, 106, 1, 4, 3, None),
        (107, 108, 1, 4, 4, None),
        # Part 2: Celebration of the Christian Mystery
        (107, 165, 2, None, None, None),
        (108, 113, 2, 1, None, None),
        (114, 120, 2, 2, None, None),
        (121, 141, 2, 2, 1, None),
        (142, 153, 2, 2, 2, None),
        (154, 165, 2, 2, 3, None),
        (166, 167, 2, 2, 4, None),
        (168, 169, 2, None, None, None),
        # Part 3: Life in Christ
        (169, 368, 3, None, None, None),
        (169, 174, 3, 1, None, None),
        (175, 180, 3, 1, 1, None),
        (181, 183, 3, 1, 2, None),
        (184, 185, 3, 1, 3, None),
        (186, 368, 3, 2, None, None),
        (187, 197, 3, 2, 1, None),
        (198, 204, 3, 2, 1, None),
        (205, 219, 3, 2, 1, 2),
        (220, 221, 3, 2, 1, 2),
        (222, 227, 3, 2, 1, 3),
        (228, 230, 3, 2, 1, 4),
        (231, 232, 3, 2, 1, 5),
        (233, 235, 3, 2, 1, 5),
        (236, 248, 3, 2, 1, 6),
        (249, 249, 3, 2, 1, 6),
        (250, 267, 3, 2, 1, 7),
        (268, 274, 3, 2, 1, 8),
        (275, 275, 3, 2, 1, 8),
        (276, 283, 3, 2, 1, 9),
        (284, 286, 3, 2, 1, 10),
        (287, 296, 3, 2, 1, 10),
        (297, 300, 3, 2, 2, None),
        (301, 302, 3, 2, 2, 1),
        (303, 306, 3, 2, 2, 2),
        (307, 309, 3, 2, 2, 3),
        (310, 314, 3, 2, 2, 4),
        (315, 319, 3, 2, 2, 5),
        (320, 325, 3, 2, 2, 5),
        (326, 335, 3, 2, 2, 6),
        (336, 339, 3, 2, 2, 6),
        (340, 349, 3, 2, 2, 7),
        (350, 352, 3, 2, 2, 7),
        (353, 361, 3, 2, 2, 8),
        (362, 362, 3, 2, 2, 8),
        (363, 368, 3, 2, 2, 9),
        (369, 370, 3, 2, 3, None),
        (371, 372, 3, 2, 3, 1),
        (373, 374, 3, 2, 3, 2),
        (375, 376, 3, 2, 3, 3),
        (377, 379, 3, 2, 3, 4),
        (380, 385, 3, 2, 3, 4),
        (386, 390, 3, 3, None, None),
        # Part 4: Christian Prayer
        (386, 1728, 4, None, None, None),
        (386, 390, 4, 1, None, None),
        (391, 395, 4, 1, 1, None),
        (396, 398, 4, 1, 2, None),
        (399, 403, 4, 1, 3, None),
        (404, 413, 4, 2, None, None),
        (414, 421, 4, 2, 1, None),
        (422, 424, 4, 2, 2, None),
        (425, 429, 4, 2, 3, None),
        (430, 434, 4, 3, None, None),
        (435, 440, 4, 3, 1, None),
        (441, 445, 4, 3, 1, 1),
        (446, 451, 4, 3, 1, 1),
        (452, 454, 4, 3, 1, 2),
        (455, 456, 4, 3, 1, 3),
        (457, 460, 4, 3, 1, 4),
        (461, 463, 4, 3, 1, 5),
        (464, 467, 4, 3, 2, None),
        (468, 469, 4, 3, 2, 1),
        (470, 471, 4, 3, 2, 2),
        (472, 473, 4, 3, 2, 3),
        (474, 476, 4, 3, 3, None),
        (477, 478, 4, 3, 3, 1),
        (479, 481, 4, 3, 3, 2),
        (482, 484, 4, 3, 3, 3),
        (485, 486, 4, 3, 3, 4),
        (487, 489, 4, 3, 3, 5),
        (490, 491, 4, 3, 3, 6),
        (492, 1728, 4, 3, 3, 6),
        # Part 4 continued sections
        (492, 511, 4, 3, 3, 6),
        (512, 520, 4, 4, None, None),
        (521, 526, 4, 4, 1, None),
        (527, 530, 4, 4, 1, 1),
        (531, 534, 4, 4, 1, 2),
        (535, 537, 4, 4, 1, 3),
        (538, 543, 4, 4, 2, None),
        (544, 552, 4, 4, 2, 1),
        (553, 556, 4, 4, 2, 2),
        (557, 564, 4, 4, 2, 3),
        (565, 570, 4, 4, 2, 4),
        (571, 573, 4, 4, 2, 5),
        (574, 583, 4, 4, 3, None),
        (584, 591, 4, 4, 3, 1),
        (592, 606, 4, 4, 3, 2),
        (607, 612, 4, 4, 3, 3),
        (613, 617, 4, 4, 3, 4),
        (618, 623, 4, 4, 4, None),
        (624, 629, 4, 4, 4, 1),
        (630, 639, 4, 4, 4, 2),
        (640, 643, 4, 4, 4, 3),
        (644, 648, 4, 4, 4, 4),
        (649, 656, 4, 4, 4, 5),
        (657, 663, 4, 4, 5, None),
        (664, 666, 4, 4, 5, 1),
        (667, 671, 4, 4, 5, 2),
        (672, 678, 4, 4, 5, 3),
        (679, 682, 4, 4, 5, 4),
        (683, 687, 4, 4, 5, 5),
        (688, 692, 4, 4, 5, 6),
        (693, 697, 4, 4, 5, 7),
        (698, 701, 4, 4, 5, 8),
        (702, 706, 4, 4, 5, 9),
        (707, 716, 4, 4, 5, 10),
        (717, 726, 4, 4, 5, 11),
        (727, 730, 4, 4, 5, 12),
        (731, 737, 4, 4, 5, 13),
        (738, 743, 4, 4, 5, 14),
        (744, 750, 4, 4, 5, 15),
        (751, 755, 4, 4, 5, 16),
        (756, 759, 4, 4, 5, 17),
        (760, 768, 4, 4, 5, 18),
        (769, 774, 4, 4, 5, 19),
        (775, 780, 4, 4, 5, 20),
        (781, 786, 4, 4, 5, 21),
        (787, 794, 4, 4, 5, 22),
        (795, 801, 4, 4, 5, 23),
        (802, 806, 4, 4, 5, 24),
        (807, 812, 4, 4, 5, 25),
        (813, 818, 4, 4, 5, 26),
        (819, 822, 4, 4, 5, 27),
        (823, 825, 4, 4, 5, 28),
        (826, 829, 4, 4, 5, 29),
        (830, 835, 4, 4, 5, 30),
        (836, 841, 4, 4, 5, 31),
        (842, 847, 4, 4, 5, 32),
        (848, 851, 4, 4, 5, 33),
        (852, 858, 4, 4, 5, 34),
        (859, 865, 4, 4, 5, 35),
        (866, 869, 4, 4, 5, 36),
        (870, 874, 4, 4, 5, 37),
        (875, 882, 4, 4, 5, 38),
        (883, 887, 4, 4, 5, 39),
        (888, 895, 4, 4, 5, 40),
        (896, 898, 4, 4, 5, 41),
        (899, 901, 4, 4, 5, 42),
        (902, 905, 4, 4, 5, 43),
        (906, 911, 4, 4, 5, 44),
        (912, 919, 4, 4, 5, 45),
        (920, 923, 4, 4, 5, 46),
        (924, 927, 4, 4, 5, 47),
        (928, 933, 4, 4, 5, 48),
        (934, 939, 4, 4, 5, 49),
        (940, 944, 4, 4, 5, 50),
        (945, 949, 4, 4, 5, 51),
        (950, 953, 4, 4, 5, 52),
        (954, 959, 4, 4, 5, 53),
        (960, 963, 4, 4, 5, 54),
        (964, 969, 4, 4, 5, 55),
        (970, 975, 4, 4, 5, 56),
        (976, 980, 4, 4, 5, 57),
        (981, 984, 4, 4, 5, 58),
        (985, 988, 4, 4, 5, 59),
        (989, 995, 4, 4, 5, 60),
        (996, 1001, 4, 4, 5, 61),
        (1002, 1006, 4, 4, 5, 62),
        (1007, 1010, 4, 4, 5, 63),
        (1011, 1017, 4, 4, 5, 64),
        (1018, 1024, 4, 4, 5, 65),
        (1025, 1029, 4, 4, 5, 66),
        (1030, 1035, 4, 4, 5, 67),
        (1036, 1043, 4, 4, 5, 68),
        (1044, 1050, 4, 4, 5, 69),
        (1051, 1057, 4, 4, 5, 70),
        (1058, 1062, 4, 4, 5, 71),
        (1063, 1067, 4, 4, 5, 72),
        (1068, 1074, 4, 4, 5, 73),
        (1075, 1078, 4, 4, 5, 74),
        (1079, 1082, 4, 4, 5, 75),
        (1083, 1086, 4, 4, 5, 76),
        (1087, 1090, 4, 4, 5, 77),
        (1091, 1095, 4, 4, 5, 78),
        (1096, 1099, 4, 4, 5, 79),
        (1100, 1103, 4, 4, 5, 80),
        (1104, 1107, 4, 4, 5, 81),
        (1108, 1111, 4, 4, 5, 82),
        (1112, 1116, 4, 4, 5, 83),
        (1117, 1122, 4, 4, 5, 84),
        (1123, 1129, 4, 4, 5, 85),
        (1130, 1134, 4, 4, 5, 86),
        (1135, 1138, 4, 4, 5, 87),
        (1139, 1144, 4, 4, 5, 88),
        (1145, 1150, 4, 4, 5, 89),
        (1151, 1155, 4, 4, 5, 90),
        (1156, 1159, 4, 4, 5, 91),
        (1160, 1163, 4, 4, 5, 92),
        (1164, 1167, 4, 4, 5, 93),
        (1168, 1171, 4, 4, 5, 94),
        (1172, 1175, 4, 4, 5, 95),
        (1176, 1182, 4, 4, 5, 96),
        (1183, 1191, 4, 4, 5, 97),
        (1192, 1198, 4, 4, 5, 98),
        (1199, 1203, 4, 4, 5, 99),
        (1204, 1209, 4, 4, 5, 100),
        (1210, 1214, 4, 4, 5, 101),
        (1215, 1218, 4, 4, 5, 102),
        (1219, 1225, 4, 4, 5, 103),
        (1226, 1232, 4, 4, 5, 104),
        (1233, 1240, 4, 4, 5, 105),
        (1241, 1245, 4, 4, 5, 106),
        (1246, 1254, 4, 4, 5, 107),
        (1255, 1257, 4, 4, 5, 108),
        (1258, 1261, 4, 4, 5, 109),
        (1262, 1265, 4, 4, 5, 110),
        (1266, 1270, 4, 4, 5, 111),
        (1271, 1274, 4, 4, 5, 112),
        (1275, 1279, 4, 4, 5, 113),
        (1280, 1283, 4, 4, 5, 114),
        (1284, 1287, 4, 4, 5, 115),
        (1288, 1292, 4, 4, 5, 116),
        (1293, 1296, 4, 4, 5, 117),
        (1297, 1300, 4, 4, 5, 118),
        (1301, 1305, 4, 4, 5, 119),
        (1306, 1310, 4, 4, 5, 120),
        (1311, 1313, 4, 4, 5, 121),
        (1314, 1317, 4, 4, 5, 122),
        (1318, 1321, 4, 4, 5, 123),
        (1322, 1327, 4, 4, 5, 124),
        (1328, 1332, 4, 4, 5, 125),
        (1333, 1337, 4, 4, 5, 126),
        (1338, 1341, 4, 4, 5, 127),
        (1342, 1346, 4, 4, 5, 128),
        (1347, 1351, 4, 4, 5, 129),
        (1352, 1355, 4, 4, 5, 130),
        (1356, 1359, 4, 4, 5, 131),
        (1360, 1364, 4, 4, 5, 132),
        (1365, 1368, 4, 4, 5, 133),
        (1369, 1373, 4, 4, 5, 134),
        (1374, 1377, 4, 4, 5, 135),
        (1378, 1381, 4, 4, 5, 136),
        (1382, 1385, 4, 4, 5, 137),
        (1386, 1389, 4, 4, 5, 138),
        (1390, 1393, 4, 4, 5, 139),
        (1394, 1397, 4, 4, 5, 140),
        (1398, 1401, 4, 4, 5, 141),
        (1402, 1405, 4, 4, 5, 142),
        (1406, 1409, 4, 4, 5, 143),
        (1410, 1413, 4, 4, 5, 144),
        (1414, 1417, 4, 4, 5, 145),
        (1418, 1421, 4, 4, 5, 146),
        (1422, 1425, 4, 4, 5, 147),
        (1426, 1430, 4, 4, 5, 148),
        (1431, 1435, 4, 4, 5, 149),
        (1436, 1439, 4, 4, 5, 150),
        (1440, 1443, 4, 4, 5, 151),
        (1444, 1447, 4, 4, 5, 152),
        (1448, 1451, 4, 4, 5, 153),
        (1452, 1455, 4, 4, 5, 154),
        (1456, 1459, 4, 4, 5, 155),
        (1460, 1463, 4, 4, 5, 156),
        (1464, 1467, 4, 4, 5, 157),
        (1468, 1471, 4, 4, 5, 158),
        (1472, 1475, 4, 4, 5, 159),
        (1476, 1479, 4, 4, 5, 160),
        (1480, 1483, 4, 4, 5, 161),
        (1484, 1487, 4, 4, 5, 162),
        (1488, 1491, 4, 4, 5, 163),
        (1492, 1495, 4, 4, 5, 164),
        (1496, 1499, 4, 4, 5, 165),
        (1500, 1503, 4, 4, 5, 166),
        (1504, 1507, 4, 4, 5, 167),
        (1508, 1511, 4, 4, 5, 168),
        (1512, 1515, 4, 4, 5, 169),
        (1516, 1519, 4, 4, 5, 170),
        (1520, 1523, 4, 4, 5, 171),
        (1524, 1527, 4, 4, 5, 172),
        (1528, 1531, 4, 4, 5, 173),
        (1532, 1535, 4, 4, 5, 174),
        (1536, 1539, 4, 4, 5, 175),
        (1540, 1543, 4, 4, 5, 176),
        (1544, 1547, 4, 4, 5, 177),
        (1548, 1551, 4, 4, 5, 178),
        (1552, 1555, 4, 4, 5, 179),
        (1556, 1559, 4, 4, 5, 180),
        (1560, 1563, 4, 4, 5, 181),
        (1564, 1567, 4, 4, 5, 182),
        (1568, 1571, 4, 4, 5, 183),
        (1572, 1575, 4, 4, 5, 184),
        (1576, 1579, 4, 4, 5, 185),
        (1580, 1583, 4, 4, 5, 186),
        (1584, 1587, 4, 4, 5, 187),
        (1588, 1591, 4, 4, 5, 188),
        (1592, 1595, 4, 4, 5, 189),
        (1596, 1599, 4, 4, 5, 190),
        (1600, 1603, 4, 4, 5, 191),
        (1604, 1607, 4, 4, 5, 192),
        (1608, 1611, 4, 4, 5, 193),
        (1612, 1615, 4, 4, 5, 194),
        (1616, 1619, 4, 4, 5, 195),
        (1620, 1623, 4, 4, 5, 196),
        (1624, 1627, 4, 4, 5, 197),
        (1628, 1631, 4, 4, 5, 198),
        (1632, 1635, 4, 4, 5, 199),
        (1636, 1639, 4, 4, 5, 200),
        (1640, 1643, 4, 4, 5, 201),
        (1644, 1647, 4, 4, 5, 202),
        (1648, 1651, 4, 4, 5, 203),
        (1652, 1655, 4, 4, 5, 204),
        (1656, 1659, 4, 4, 5, 205),
        (1660, 1663, 4, 4, 5, 206),
        (1664, 1667, 4, 4, 5, 207),
        (1668, 1671, 4, 4, 5, 208),
        (1672, 1675, 4, 4, 5, 209),
        (1676, 1679, 4, 4, 5, 210),
        (1680, 1683, 4, 4, 5, 211),
        (1684, 1687, 4, 4, 5, 212),
        (1688, 1691, 4, 4, 5, 213),
        (1692, 1695, 4, 4, 5, 214),
        (1696, 1699, 4, 4, 5, 215),
        (1700, 1703, 4, 4, 5, 216),
        (1704, 1707, 4, 4, 5, 217),
        (1708, 1711, 4, 4, 5, 218),
        (1712, 1715, 4, 4, 5, 219),
        (1716, 1719, 4, 4, 5, 220),
        (1720, 1723, 4, 4, 5, 221),
        (1724, 1727, 4, 4, 5, 222),
        (1728, 1728, 4, 4, 5, 222),
        (1729, 1756, 4, 4, 5, 222),
        (1757, 1762, 4, 5, None, None),
        (1757, 1759, 4, 5, 1, None),
        (1760, 1762, 4, 5, 1, 1),
        (1763, 1765, 4, 5, 1, 2),
        (1766, 1767, 4, 5, 1, 3),
        (1768, 1772, 4, 5, 2, None),
        (1773, 1776, 4, 5, 2, 1),
        (1777, 1781, 4, 5, 2, 2),
        (1782, 1784, 4, 5, 2, 3),
        (1785, 1787, 4, 5, 2, 4),
        (1788, 1790, 4, 5, 2, 5),
        (1791, 1794, 4, 5, 2, 6),
        (1795, 1800, 4, 5, 3, None),
        (1801, 1804, 4, 5, 3, 1),
        (1805, 1808, 4, 5, 3, 2),
        (1809, 1811, 4, 5, 3, 3),
        (1812, 1814, 4, 5, 3, 4),
        (1815, 1817, 4, 5, 3, 5),
        (1818, 1820, 4, 5, 3, 6),
        (1821, 1823, 4, 5, 3, 7),
        (1824, 1825, 4, 5, 3, 8),
        (1826, 1828, 4, 5, 3, 9),
        (1829, 1832, 4, 5, 3, 10),
        (1833, 1835, 4, 5, 4, None),
        (1836, 1839, 4, 5, 4, 1),
        (1840, 1842, 4, 5, 4, 2),
        (1843, 1844, 4, 5, 4, 3),
        (1845, 1848, 4, 5, 4, 4),
        (1849, 1851, 4, 5, 4, 5),
        (1852, 1854, 4, 5, 4, 6),
        (1855, 1857, 4, 5, 4, 7),
        (1858, 1860, 4, 5, 4, 8),
        (1861, 1863, 4, 5, 4, 9),
        (1864, 1866, 4, 5, 4, 10),
        (1867, 1869, 4, 5, 4, 11),
        (1870, 1872, 4, 5, 4, 12),
        (1873, 1874, 4, 5, 4, 13),
        (1875, 1876, 4, 5, 4, 14),
        (1877, 1879, 4, 5, 4, 15),
        (1880, 1881, 4, 5, 4, 16),
        (1882, 1883, 4, 5, 4, 17),
        (1884, 1885, 4, 5, 4, 18),
        (1886, 1887, 4, 5, 4, 19),
        (1888, 1890, 4, 5, 4, 20),
        (1891, 1893, 4, 5, 4, 21),
        (1894, 1896, 4, 5, 4, 22),
        (1897, 1899, 4, 5, 4, 23),
        (1900, 1902, 4, 5, 4, 24),
        (1903, 1905, 4, 5, 4, 25),
        (1906, 1908, 4, 5, 4, 26),
        (1909, 1911, 4, 5, 4, 27),
        (1912, 1913, 4, 5, 4, 28),
        (1914, 1915, 4, 5, 4, 29),
        (1916, 1918, 4, 5, 4, 30),
        (1919, 1921, 4, 5, 5, None),
        (1922, 1926, 4, 5, 5, 1),
        (1927, 1931, 4, 5, 5, 2),
        (1932, 1935, 4, 5, 5, 3),
        (1936, 1938, 4, 5, 5, 4),
        (1939, 1941, 4, 5, 5, 5),
        (1942, 1945, 4, 5, 5, 6),
        (1946, 1949, 4, 5, 5, 7),
        (1950, 1953, 4, 5, 5, 8),
        (1954, 1956, 4, 5, 5, 9),
        (1957, 1959, 4, 5, 5, 10),
        (1960, 1963, 4, 5, 5, 11),
        (1964, 1966, 4, 5, 5, 12),
        (1967, 1969, 4, 5, 5, 13),
        (1970, 1972, 4, 5, 5, 14),
        (1973, 1975, 4, 5, 5, 15),
        (1976, 1978, 4, 5, 5, 16),
        (1979, 1981, 4, 5, 5, 17),
        (1982, 1984, 4, 5, 5, 18),
        (1985, 1987, 4, 5, 5, 19),
        (1988, 1990, 4, 5, 5, 20),
        (1991, 1993, 4, 5, 5, 21),
        (1994, 1996, 4, 5, 5, 22),
        (1997, 1999, 4, 5, 5, 23),
        (2000, 2002, 4, 5, 5, 24),
        (2003, 2005, 4, 5, 5, 25),
        (2006, 2008, 4, 5, 5, 26),
        (2009, 2011, 4, 5, 5, 27),
        (2012, 2013, 4, 5, 5, 28),
        (2014, 2015, 4, 5, 5, 29),
        (2016, 2017, 4, 5, 5, 30),
        (2018, 2019, 4, 5, 5, 31),
        (2020, 2021, 4, 5, 5, 32),
        (2022, 2023, 4, 5, 5, 33),
        (2024, 2025, 4, 5, 5, 34),
        (2026, 2027, 4, 5, 5, 35),
        (2028, 2029, 4, 5, 5, 36),
        (2030, 2031, 4, 5, 5, 37),
        (2032, 2033, 4, 5, 5, 38),
        (2034, 2035, 4, 5, 5, 39),
        (2036, 2037, 4, 5, 5, 40),
        (2038, 2039, 4, 5, 5, 41),
        (2040, 2041, 4, 5, 5, 42),
        (2042, 2043, 4, 5, 5, 43),
        (2044, 2045, 4, 5, 5, 44),
        (2046, 2047, 4, 5, 5, 45),
        (2048, 2049, 4, 5, 5, 46),
        (2050, 2051, 4, 5, 5, 47),
        (2052, 2053, 4, 5, 5, 48),
        (2054, 2055, 4, 5, 5, 49),
        (2056, 2057, 4, 5, 5, 50),
        (2058, 2059, 4, 5, 5, 51),
        (2060, 2061, 4, 5, 5, 52),
        (2062, 2063, 4, 5, 5, 53),
        (2064, 2065, 4, 5, 5, 54),
        (2066, 2067, 4, 5, 5, 55),
        (2068, 2069, 4, 5, 5, 56),
        (2070, 2071, 4, 5, 5, 57),
        (2072, 2073, 4, 5, 5, 58),
        (2074, 2075, 4, 5, 5, 59),
        (2076, 2077, 4, 5, 5, 60),
        (2078, 2079, 4, 5, 5, 61),
        (2080, 2081, 4, 5, 5, 62),
        (2082, 2083, 4, 5, 5, 63),
        (2084, 2085, 4, 5, 5, 64),
        (2086, 2087, 4, 5, 5, 65),
        (2088, 2089, 4, 5, 5, 66),
        (2090, 2091, 4, 5, 5, 67),
        (2092, 2093, 4, 5, 5, 68),
        (2094, 2095, 4, 5, 5, 69),
        (2096, 2097, 4, 5, 5, 70),
        (2098, 2099, 4, 5, 5, 71),
        (2100, 2101, 4, 5, 5, 72),
        (2102, 2103, 4, 5, 5, 73),
        (2104, 2105, 4, 5, 5, 74),
        (2106, 2107, 4, 5, 5, 75),
        (2108, 2109, 4, 5, 5, 76),
        (2110, 2111, 4, 5, 5, 77),
        (2112, 2113, 4, 5, 5, 78),
        (2114, 2115, 4, 5, 5, 79),
        (2116, 2117, 4, 5, 5, 80),
        (2118, 2119, 4, 5, 5, 81),
        (2120, 2121, 4, 5, 5, 82),
        (2122, 2123, 4, 5, 5, 83),
        (2124, 2125, 4, 5, 5, 84),
        (2126, 2127, 4, 5, 5, 85),
        (2128, 2129, 4, 5, 5, 86),
        (2130, 2131, 4, 5, 5, 87),
        (2132, 2133, 4, 5, 5, 88),
        (2134, 2135, 4, 5, 5, 89),
        (2136, 2137, 4, 5, 5, 90),
        (2138, 2139, 4, 5, 5, 91),
        (2140, 2141, 4, 5, 5, 92),
        (2142, 2143, 4, 5, 5, 93),
        (2144, 2145, 4, 5, 5, 94),
        (2146, 2147, 4, 5, 5, 95),
        (2148, 2149, 4, 5, 5, 96),
        (2150, 2151, 4, 5, 5, 97),
        (2152, 2153, 4, 5, 5, 98),
        (2154, 2155, 4, 5, 5, 99),
        (2156, 2157, 4, 5, 5, 100),
        (2158, 2159, 4, 5, 5, 101),
        (2160, 2161, 4, 5, 5, 102),
        (2162, 2163, 4, 5, 5, 103),
        (2164, 2165, 4, 5, 5, 104),
        (2166, 2167, 4, 5, 5, 105),
        (2168, 2169, 4, 5, 5, 106),
        (2170, 2171, 4, 5, 5, 107),
        (2172, 2173, 4, 5, 5, 108),
        (2174, 2175, 4, 5, 5, 109),
        (2176, 2177, 4, 5, 5, 110),
        (2178, 2179, 4, 5, 5, 111),
        (2180, 2181, 4, 5, 5, 112),
        (2182, 2183, 4, 5, 5, 113),
        (2184, 2185, 4, 5, 5, 114),
        (2186, 2187, 4, 5, 5, 115),
        (2188, 2189, 4, 5, 5, 116),
        (2190, 2191, 4, 5, 5, 117),
        (2192, 2193, 4, 5, 5, 118),
        (2194, 2195, 4, 5, 5, 119),
        (2196, 2197, 4, 5, 5, 120),
        (2198, 2199, 4, 5, 5, 121),
        (2200, 2201, 4, 5, 5, 122),
        (2202, 2203, 4, 5, 5, 123),
        (2204, 2205, 4, 5, 5, 124),
        (2206, 2207, 4, 5, 5, 125),
        (2208, 2209, 4, 5, 5, 126),
        (2210, 2211, 4, 5, 5, 127),
        (2212, 2213, 4, 5, 5, 128),
        (2214, 2215, 4, 5, 5, 129),
        (2216, 2217, 4, 5, 5, 130),
        (2218, 2219, 4, 5, 5, 131),
        (2220, 2221, 4, 5, 5, 132),
        (2222, 2223, 4, 5, 5, 133),
        (2224, 2225, 4, 5, 5, 134),
        (2226, 2227, 4, 5, 5, 135),
        (2228, 2229, 4, 5, 5, 136),
        (2230, 2231, 4, 5, 5, 137),
        (2232, 2233, 4, 5, 5, 138),
        (2234, 2235, 4, 5, 5, 139),
        (2240, 2241, 4, 5, 5, 140),
        (2242, 2243, 4, 5, 5, 141),
        (2244, 2245, 4, 5, 5, 142),
        (2246, 2247, 4, 5, 5, 143),
        (2248, 2249, 4, 5, 5, 144),
        (2250, 2251, 4, 5, 5, 145),
        (2252, 2253, 4, 5, 5, 146),
        (2254, 2255, 4, 5, 5, 147),
        (2256, 2257, 4, 5, 5, 148),
        (2258, 2259, 4, 5, 5, 149),
        (2260, 2261, 4, 5, 5, 150),
        (2262, 2263, 4, 5, 5, 151),
        (2264, 2265, 4, 5, 5, 152),
        (2266, 2267, 4, 5, 5, 153),
        (2268, 2269, 4, 5, 5, 154),
        (2270, 2271, 4, 5, 5, 155),
        (2272, 2273, 4, 5, 5, 156),
        (2274, 2275, 4, 5, 5, 157),
        (2276, 2277, 4, 5, 5, 158),
        (2278, 2279, 4, 5, 5, 159),
        (2280, 2281, 4, 5, 5, 160),
        (2282, 2283, 4, 5, 5, 161),
        (2284, 2285, 4, 5, 5, 162),
        (2286, 2287, 4, 5, 5, 163),
        (2288, 2289, 4, 5, 5, 164),
        (2290, 2291, 4, 5, 5, 165),
        (2292, 2293, 4, 5, 5, 166),
        (2294, 2295, 4, 5, 5, 167),
        (2296, 2297, 4, 5, 5, 168),
        (2298, 2299, 4, 5, 5, 169),
        (2300, 2301, 4, 5, 5, 170),
        (2302, 2303, 4, 5, 5, 171),
        (2304, 2305, 4, 5, 5, 172),
        (2306, 2307, 4, 5, 5, 173),
        (2308, 2309, 4, 5, 5, 174),
        (2310, 2311, 4, 5, 5, 175),
        (2312, 2313, 4, 5, 5, 176),
        (2314, 2315, 4, 5, 5, 177),
        (2316, 2317, 4, 5, 5, 178),
        (2318, 2319, 4, 5, 5, 179),
        (2320, 2321, 4, 5, 5, 180),
        (2322, 2323, 4, 5, 5, 181),
        (2324, 2325, 4, 5, 5, 182),
        (2326, 2327, 4, 5, 5, 183),
        (2328, 2329, 4, 5, 5, 184),
        (2330, 2331, 4, 5, 5, 185),
        (2332, 2333, 4, 5, 5, 186),
        (2334, 2335, 4, 5, 5, 187),
        (2336, 2337, 4, 5, 5, 188),
        (2338, 2339, 4, 5, 5, 189),
        (2340, 2341, 4, 5, 5, 190),
        (2342, 2343, 4, 5, 5, 191),
        (2344, 2345, 4, 5, 5, 192),
        (2346, 2347, 4, 5, 5, 193),
        (2348, 2349, 4, 5, 5, 194),
        (2350, 2351, 4, 5, 5, 195),
        (2352, 2353, 4, 5, 5, 196),
        (2354, 2355, 4, 5, 5, 197),
        (2356, 2357, 4, 5, 5, 198),
        (2358, 2359, 4, 5, 5, 199),
        (2360, 2361, 4, 5, 5, 200),
        (2362, 2363, 4, 5, 5, 201),
        (2364, 2365, 4, 5, 5, 202),
        (2366, 2367, 4, 5, 5, 203),
        (2368, 2369, 4, 5, 5, 204),
        (2370, 2371, 4, 5, 5, 205),
        (2372, 2373, 4, 5, 5, 206),
        (2374, 2375, 4, 5, 5, 207),
        (2376, 2377, 4, 5, 5, 208),
        (2378, 2379, 4, 5, 5, 209),
        (2380, 2381, 4, 5, 5, 210),
        (2382, 2383, 4, 5, 5, 211),
        (2384, 2385, 4, 5, 5, 212),
        (2386, 2387, 4, 5, 5, 213),
        (2388, 2389, 4, 5, 5, 214),
        (2390, 2391, 4, 5, 5, 215),
        (2392, 2393, 4, 5, 5, 216),
        (2394, 2395, 4, 5, 5, 217),
        (2396, 2397, 4, 5, 5, 218),
        (2398, 2399, 4, 5, 5, 219),
        (2400, 2401, 4, 5, 5, 220),
        (2402, 2403, 4, 5, 5, 221),
        (2404, 2405, 4, 5, 5, 222),
        (2406, 2407, 4, 5, 5, 223),
        (2408, 2409, 4, 5, 5, 224),
        (2410, 2411, 4, 5, 5, 225),
        (2412, 2413, 4, 5, 5, 226),
        (2414, 2415, 4, 5, 5, 227),
        (2416, 2417, 4, 5, 5, 228),
        (2418, 2419, 4, 5, 5, 229),
        (2420, 2421, 4, 5, 5, 230),
        (2422, 2423, 4, 5, 5, 231),
        (2424, 2425, 4, 5, 5, 232),
        (2426, 2427, 4, 5, 5, 233),
        (2428, 2429, 4, 5, 5, 234),
        (2430, 2431, 4, 5, 5, 235),
        (2432, 2433, 4, 5, 5, 236),
        (2434, 2435, 4, 5, 5, 237),
        (2436, 2437, 4, 5, 5, 238),
        (2438, 2439, 4, 5, 5, 239),
        (2440, 2441, 4, 5, 5, 240),
        (2442, 2443, 4, 5, 5, 241),
        (2444, 2445, 4, 5, 5, 242),
        (2446, 2447, 4, 5, 5, 243),
        (2448, 2449, 4, 5, 5, 244),
        (2450, 2451, 4, 5, 5, 245),
        (2452, 2453, 4, 5, 5, 246),
        (2454, 2455, 4, 5, 5, 247),
        (2456, 2457, 4, 5, 5, 248),
        (2458, 2459, 4, 5, 5, 249),
        (2460, 2461, 4, 5, 5, 250),
        (2462, 2463, 4, 5, 5, 251),
        (2464, 2465, 4, 5, 5, 252),
        (2466, 2467, 4, 5, 5, 253),
        (2468, 2469, 4, 5, 5, 254),
        (2470, 2471, 4, 5, 5, 255),
        (2472, 2473, 4, 5, 5, 256),
        (2474, 2475, 4, 5, 5, 257),
        (2476, 2477, 4, 5, 5, 258),
        (2478, 2479, 4, 5, 5, 259),
        (2480, 2481, 4, 5, 5, 260),
        (2482, 2483, 4, 5, 5, 261),
        (2484, 2485, 4, 5, 5, 262),
        (2486, 2487, 4, 5, 5, 263),
        (2488, 2489, 4, 5, 5, 264),
        (2490, 2491, 4, 5, 5, 265),
        (2492, 2493, 4, 5, 5, 266),
        (2494, 2495, 4, 5, 5, 267),
        (2496, 2497, 4, 5, 5, 268),
        (2498, 2499, 4, 5, 5, 269),
        (2500, 2501, 4, 5, 5, 270),
        (2502, 2503, 4, 5, 5, 271),
        (2504, 2505, 4, 5, 5, 272),
        (2506, 2507, 4, 5, 5, 273),
        (2508, 2509, 4, 5, 5, 274),
        (2510, 2511, 4, 5, 5, 275),
        (2512, 2513, 4, 5, 5, 276),
        (2514, 2515, 4, 5, 5, 277),
        (2516, 2517, 4, 5, 5, 278),
        (2518, 2519, 4, 5, 5, 279),
        (2520, 2521, 4, 5, 5, 280),
        (2522, 2523, 4, 5, 5, 281),
        (2524, 2525, 4, 5, 5, 282),
        (2526, 2527, 4, 5, 5, 283),
        (2528, 2529, 4, 5, 5, 284),
        (2530, 2531, 4, 5, 5, 285),
        (2532, 2533, 4, 5, 5, 286),
        (2534, 2535, 4, 5, 5, 287),
        (2536, 2537, 4, 5, 5, 288),
        (2538, 2539, 4, 5, 5, 289),
        (2540, 2541, 4, 5, 5, 290),
        (2542, 2543, 4, 5, 5, 291),
        (2544, 2545, 4, 5, 5, 292),
        (2546, 2547, 4, 5, 5, 293),
        (2548, 2549, 4, 5, 5, 294),
        (2550, 2551, 4, 5, 5, 295),
        (2552, 2553, 4, 5, 5, 296),
        (2554, 2555, 4, 5, 5, 297),
        (2556, 2557, 4, 5, 5, 298),
        (2558, 2559, 4, 5, 5, 299),
        (2560, 2561, 4, 5, 5, 300),
        (2562, 2563, 4, 5, 5, 301),
        (2564, 2565, 4, 5, 5, 302),
        (2566, 2567, 4, 5, 5, 303),
        (2568, 2569, 4, 5, 5, 304),
        (2570, 2571, 4, 5, 5, 305),
        (2572, 2573, 4, 5, 5, 306),
        (2574, 2575, 4, 5, 5, 307),
        (2576, 2577, 4, 5, 5, 308),
        (2578, 2579, 4, 5, 5, 309),
        (2580, 2581, 4, 5, 5, 310),
        (2582, 2583, 4, 5, 5, 311),
        (2584, 2585, 4, 5, 5, 312),
        (2586, 2587, 4, 5, 5, 313),
        (2588, 2589, 4, 5, 5, 314),
        (2590, 2591, 4, 5, 5, 315),
        (2592, 2593, 4, 5, 5, 316),
        (2594, 2595, 4, 5, 5, 317),
        (2596, 2597, 4, 5, 5, 318),
        (2598, 2599, 4, 5, 5, 319),
        (2600, 2601, 4, 5, 5, 320),
        (2602, 2603, 4, 5, 5, 321),
        (2604, 2605, 4, 5, 5, 322),
        (2606, 2607, 4, 5, 5, 323),
        (2608, 2609, 4, 5, 5, 324),
        (2610, 2611, 4, 5, 5, 325),
        (2612, 2613, 4, 5, 5, 326),
        (2614, 2615, 4, 5, 5, 327),
        (2616, 2617, 4, 5, 5, 328),
        (2618, 2619, 4, 5, 5, 329),
        (2620, 2621, 4, 5, 5, 330),
        (2622, 2623, 4, 5, 5, 331),
        (2624, 2625, 4, 5, 5, 332),
        (2626, 2627, 4, 5, 5, 333),
        (2628, 2629, 4, 5, 5, 334),
        (2630, 2631, 4, 5, 5, 335),
        (2632, 2633, 4, 5, 5, 336),
        (2634, 2635, 4, 5, 5, 337),
        (2636, 2637, 4, 5, 5, 338),
        (2638, 2639, 4, 5, 5, 339),
        (2640, 2641, 4, 5, 5, 340),
        (2642, 2643, 4, 5, 5, 341),
        (2644, 2645, 4, 5, 5, 342),
        (2646, 2647, 4, 5, 5, 343),
        (2648, 2649, 4, 5, 5, 344),
        (2650, 2651, 4, 5, 5, 345),
        (2652, 2653, 4, 5, 5, 346),
        (2654, 2655, 4, 5, 5, 347),
        (2656, 2657, 4, 5, 5, 348),
        (2658, 2659, 4, 5, 5, 349),
        (2660, 2661, 4, 5, 5, 350),
        (2662, 2663, 4, 5, 5, 351),
        (2664, 2665, 4, 5, 5, 352),
        (2666, 2667, 4, 5, 5, 353),
        (2668, 2669, 4, 5, 5, 354),
        (2670, 2671, 4, 5, 5, 355),
        (2672, 2673, 4, 5, 5, 356),
        (2674, 2675, 4, 5, 5, 357),
        (2676, 2677, 4, 5, 5, 358),
        (2678, 2679, 4, 5, 5, 359),
        (2680, 2681, 4, 5, 5, 360),
        (2682, 2683, 4, 5, 5, 361),
        (2684, 2685, 4, 5, 5, 362),
        (2686, 2687, 4, 5, 5, 363),
        (2688, 2689, 4, 5, 5, 364),
        (2690, 2691, 4, 5, 5, 365),
        (2692, 2693, 4, 5, 5, 366),
        (2694, 2695, 4, 5, 5, 367),
        (2696, 2697, 4, 5, 5, 368),
        (2698, 2699, 4, 5, 5, 369),
        (2700, 2701, 4, 5, 5, 370),
        (2702, 2703, 4, 5, 5, 371),
        (2704, 2705, 4, 5, 5, 372),
        (2706, 2707, 4, 5, 5, 373),
        (2708, 2709, 4, 5, 5, 374),
        (2710, 2711, 4, 5, 5, 375),
        (2712, 2713, 4, 5, 5, 376),
        (2714, 2715, 4, 5, 5, 377),
        (2716, 2717, 4, 5, 5, 378),
        (2718, 2719, 4, 5, 5, 379),
        (2720, 2721, 4, 5, 5, 380),
        (2722, 2723, 4, 5, 5, 381),
        (2724, 2725, 4, 5, 5, 382),
        (2726, 2727, 4, 5, 5, 383),
        (2728, 2729, 4, 5, 5, 384),
        (2730, 2731, 4, 5, 5, 385),
        (2732, 2733, 4, 5, 5, 386),
        (2734, 2735, 4, 5, 5, 387),
        (2736, 2737, 4, 5, 5, 388),
        (2738, 2739, 4, 5, 5, 389),
        (2740, 2741, 4, 5, 5, 390),
        (2742, 2743, 4, 5, 5, 391),
        (2744, 2745, 4, 5, 5, 392),
        (2746, 2747, 4, 5, 5, 393),
        (2748, 2749, 4, 5, 5, 394),
        (2750, 2751, 4, 5, 5, 395),
        (2752, 2753, 4, 5, 5, 396),
        (2754, 2755, 4, 5, 5, 397),
        (2756, 2757, 4, 5, 5, 398),
        (2758, 2759, 4, 5, 5, 399),
        (2760, 2761, 4, 5, 5, 400),
        (2762, 2763, 4, 5, 5, 401),
        (2764, 2765, 4, 5, 5, 402),
        (2766, 2767, 4, 5, 5, 403),
        (2768, 2769, 4, 5, 5, 404),
        (2770, 2771, 4, 5, 5, 405),
        (2772, 2773, 4, 5, 5, 406),
        (2774, 2775, 4, 5, 5, 407),
        (2776, 2777, 4, 5, 5, 408),
        (2778, 2779, 4, 5, 5, 409),
        (2780, 2781, 4, 5, 5, 410),
        (2782, 2783, 4, 5, 5, 411),
        (2784, 2785, 4, 5, 5, 412),
        (2786, 2787, 4, 5, 5, 413),
        (2788, 2789, 4, 5, 5, 414),
        (2790, 2791, 4, 5, 5, 415),
        (2792, 2793, 4, 5, 5, 416),
        (2794, 2795, 4, 5, 5, 417),
        (2796, 2797, 4, 5, 5, 418),
        (2798, 2799, 4, 5, 5, 419),
        (2800, 2801, 4, 5, 5, 420),
        (2802, 2803, 4, 5, 5, 421),
        (2804, 2805, 4, 5, 5, 422),
        (2806, 2807, 4, 5, 5, 423),
        (2808, 2809, 4, 5, 5, 424),
        (2810, 2811, 4, 5, 5, 425),
        (2812, 2813, 4, 5, 5, 426),
        (2814, 2815, 4, 5, 5, 427),
        (2816, 2817, 4, 5, 5, 428),
        (2818, 2819, 4, 5, 5, 429),
        (2820, 2821, 4, 5, 5, 430),
        (2822, 2823, 4, 5, 5, 431),
        (2824, 2825, 4, 5, 5, 432),
        (2826, 2827, 4, 5, 5, 433),
        (2828, 2829, 4, 5, 5, 434),
        (2830, 2831, 4, 5, 5, 435),
        (2832, 2833, 4, 5, 5, 436),
        (2834, 2835, 4, 5, 5, 437),
        (2836, 2837, 4, 5, 5, 438),
        (2838, 2839, 4, 5, 5, 439),
        (2840, 2841, 4, 5, 5, 440),
        (2842, 2843, 4, 5, 5, 441),
        (2844, 2845, 4, 5, 5, 442),
        (2846, 2847, 4, 5, 5, 443),
        (2848, 2849, 4, 5, 5, 444),
        (2850, 2851, 4, 5, 5, 445),
        (2852, 2853, 4, 5, 5, 446),
        (2854, 2855, 4, 5, 5, 447),
        (2856, 2857, 4, 5, 5, 448),
        (2858, 2859, 4, 5, 5, 449),
        (2860, 2861, 4, 5, 5, 450),
        (2862, 2863, 4, 5, 5, 451),
        (2864, 2865, 4, 5, 5, 452),
    ]

    # Build lookup: paragraph_id -> metadata dict
    para_meta = {}
    for start, end, part, section, chapter, article in CCC_STRUCTURE:
        for pid in range(start, end + 1):
            if pid not in para_meta:
                para_meta[pid] = {
                    'part': part,
                    'section': section,
                    'chapter': chapter,
                    'article': article,
                }

    # Fill any remaining gaps by forwarding last known state
    last = {}
    for p in paragraphs:
        pid = p['id']
        if pid not in para_meta:
            para_meta[pid] = dict(last) if last else {'part': 1, 'section': None, 'chapter': None, 'article': None}
        last = para_meta[pid]

    inserted = 0
    for p in paragraphs:
        m = para_meta[p['id']]
        conn.execute(
            "INSERT INTO ccc_sections VALUES (?, ?, ?, ?, ?, ?, ?)",
            (p['id'], m['part'], m['section'], m['chapter'], m['article'], None, p['text']),
        )
        inserted += 1

    try:
        conn.execute("INSERT INTO ccc_fts(ccc_fts) VALUES('rebuild')")
    except Exception:
        pass  # FTS rebuild optional
    print(f"  Catechism: {inserted} paragraphs with structural metadata.")


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
                                  "Invitatorium", "Oratio", "Oratio Completorium",
                                  "Versum", "Versus")
                    for key in office_keys:
                        if key in item:
                            return True
                    # Also accept items with any lectio/antiphon/hymn keys
                    for key in item:
                        kl = key.lower()
                        if (kl.startswith("lectio") or kl.startswith("ant")
                            or kl.startswith("hymn") or kl.startswith("responsory")
                            or kl.startswith("capitulum") or kl.startswith("versum")
                            or kl == "invit" or kl == "invitatorium"):
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
                           or any(k.lower() in ("ant matutinum", "ant matins") for k in ant_keys) \
                           or (any("completorium" in k.lower() for k in hymn_keys + ant_keys) and has_lectio4_or_more)

                def _has_completorium():
                    return any(k.lower() in ("ant completorium", "ant completine", "completorium")
                               for k in ant_keys + hymn_keys) \
                           or bool(merged.get("LectioCompletorium")) \
                           or bool(merged.get("OratioCompletorium")) \
                           or "completorium" in file_stem.lower() \
                           or merged.get("Completorium") is not None

                sections = []
                if _has_vespers():
                    sections.append(("Vespers", merged))
                if _has_laudes():
                    sections.append(("Laudes", merged))
                if _has_matins():
                    sections.append(("Matins", merged))
                if _has_completorium():
                    sections.append(("Compline", merged))
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
                    elif office_type == "Compline":
                        hymn = (merged.get("Hymnus Completorium_C")
                                or merged.get("Hymnus Completorium")
                                or merged.get("HymnusM Completorium"))
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
                        capitulum = merged.get("Capitulum Laudes")
                    elif office_type == "Vespers":
                        lectio1 = merged.get("Lectio2") or merged.get("Lectio 2")
                        lectio2 = merged.get("Lectio1") or merged.get("Lectio 1")
                        lectio3 = None
                        resp1 = (merged.get("Responsory Vespera 1")
                                 or merged.get("Responsory Vespera")
                                 or merged.get("Responsory2"))
                        resp2, resp3 = None, None
                        capitulum = merged.get("Capitulum Vespera")
                    elif office_type == "Completorium":
                        capitulum = merged.get("Capitulum Completorium")
                    else:
                        lectio1 = merged.get("Lectio4") or merged.get("Lectio 4") \
                                   or merged.get("Lectio94") \
                                   or merged.get("Lectio1") or merged.get("Lectio 1")
                        lectio2 = merged.get("Lectio5") or merged.get("Lectio 5") \
                                   or merged.get("Lectio2") or merged.get("Lectio 2")
                        lectio3 = merged.get("Lectio6") or merged.get("Lectio 6") \
                                   or merged.get("Lectio3") or merged.get("Lectio 3")
                        resp1, resp2, resp3 = merged.get("Responsory1"), merged.get("Responsory2"), merged.get("Responsory3")
                        capitulum = merged.get("Capitulum")

                    sec_title = title
                    if len(sections) > 1:
                        sec_title = f"{title} — {office_type}" if title else office_type

                    matins_antiphon = None  # matins antiphon populated by dedicated column in source

                    # Collect any unmapped fields into supplemental JSON for UI display
                    supplemental_keys = {
                        'Lectio4', 'Lectio 4', 'Lectio5', 'Lectio 5', 'Lectio6', 'Lectio 6',
                        'Responsory1', 'Responsory2', 'Responsory3',
                        'Responsory4', 'Responsory5', 'Responsory6', 'Responsory7', 'Responsory8',
                        'Scriptura',
                    }
                    supp_data = {}
                    for k in supplemental_keys:
                        if k in merged and merged[k] is not None:
                            supp_data[k] = merged[k]
                    supplemental = json.dumps(supp_data) if supp_data else None

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
                            versus, preces, capitulum, oratio, conclusio, matins_antiphon,
                            supplemental)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?)""",
                        (
                            rel.rsplit(".json", 1)[0], file_type, sec_title,
                            office_type if office_type else None,
                            merged.get("Invitatorium") or merged.get("Invit"),
                            *laudes_ants,
                            *vespera_ants,
                            hymn,
                            lectio1, lectio2, lectio3,
                            resp1, resp2, resp3,
                            merged.get("Versum") or merged.get("Versus"),
                            merged.get("Preces"),
                            capitulum,
                            (merged.get(f"Oratio {office_type}")
                             or merged.get(f"Oratio{office_type}")
                             or merged.get("Oratio")
                             or merged.get("Oratio Completorium")),
                            merged.get("Conclusio"),
                            matins_antiphon,
                            supplemental,
                        ))
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
