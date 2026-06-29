#!/usr/bin/env python3
"""Apply Phase 1 bilingual patches to compile_content.py via line-based editing."""
import sys

PATH = "/home/josh/claw-code/DeFide/scripts/compile_content.py"
with open(PATH) as f:
    lines = f.readlines()

# ── P1: Add ENGLISH_HORAS + _ENGLISH_DIR_MAP before _load_txt_sections ──────────
insert1 = None
for i, line in enumerate(lines):
    if line.startswith("def _load_txt_sections"):
        insert1 = i
        break

if insert1 is None:
    print("ERROR: _load_txt_sections not found")
    sys.exit(1)

en_block = (
    '\n'
    'ENGLISH_HORAS = os.path.join(\n'
    '    REPO_ROOT, "divinum-officium", "web", "www", "horas", "English"\n'
    ')\n'
    '_ENGLISH_DIR_MAP = {\n'
    '    "tempora":  "Tempora",\n'
    '    "sancti":   "Sancti",\n'
    '    "commune":  "Commune",\n'
    '    "extra":    "Sancti",\n'
    '    "orationes": "Sancti",\n'
    '    "psalmi":   "Psalterium",\n'
    '    "missa":    "Tempora",\n'
    '    "martyrologium": "Martyrologium",\n'
    '}\n'
    '\n'
    '\n'
)

lines.insert(insert1, en_block)
print(f"  [P1] Added ENGLISH_HORAS at line {insert1+1}")

# ── P2: Add _populate_english_offices after _post_resolve_hymns ───────────────
# Find the blank line just before compile_baltimore_catechism
insert2 = None
for i, line in enumerate(lines):
    if line.startswith("def compile_baltimore_catechism"):
        insert2 = i
        break

if insert2 is None:
    print("ERROR: compile_baltimore_catechism not found")
    sys.exit(1)

populate_block = (
    '\n'
    'def _populate_english_offices(conn):\n'
    '    QUOTE = "Populating English bilingual columns..."\n'
    '    print(QUOTE)\n'
    '    updated = 0\n'
    '    skipped = 0\n'
    '\n'
    '    rows = conn.execute(\n'
    '        "SELECT id, file, file_type FROM divine_office"\n'
    '    ).fetchall()\n'
    '\n'
    '    for row_id, file_path, file_type in rows:\n'
    '        if not file_path:\n'
    '            skipped += 1\n'
    '            continue\n'
    '        en_dir = _ENGLISH_DIR_MAP.get(file_type, "Sancti")\n'
    '        en_path = os.path.join(ENGLISH_HORAS, en_dir, file_path + ".txt")\n'
    '        if not os.path.exists(en_path):\n'
    '            skipped += 1\n'
    '            continue\n'
    '        en_secs = _load_txt_sections(en_path)\n'
    '\n'
    '        def ek(key):\n'
    '            kl = key.lower()\n'
    '            for k, v in en_secs.items():\n'
    '                if k.lower() == kl:\n'
    '                    return "\\n".join(v)\n'
    '            return None\n'
    '\n'
    '        sets = []\n'
    '        vals = []\n'
    '\n'
    '        hymn_en = ek("Hymnus Vespera") or ek("Hymnus Laudes") \\\n'
    '                   or ek("Hymnus Matutinum") or ek("Hymnus Completorium_C") \\\n'
    '                   or ek("Hymnus Completorium")\n'
    '        if hymn_en:\n'
    '            sets.append("hymn_en=?"); vals.append(hymn_en)\n'
    '\n'
    '        for col, key in [\n'
    '            ("lectio_1_en", "Lectio1"), ("lectio_1_en", "Lectio 1"),\n'
    '            ("lectio_2_en", "Lectio2"), ("lectio_2_en", "Lectio 2"),\n'
    '            ("lectio_3_en", "Lectio3"), ("lectio_3_en", "Lectio 3"),\n'
    '            ("responsory_1_en", "Responsory1"),\n'
    '            ("responsory_2_en", "Responsory2"),\n'
    '            ("responsory_3_en", "Responsory3"),\n'
    '            ("oratio_en", "Oratio"), ("oratio_en", "Oratio Completorium"),\n'
    '            ("conclusio_en", "Conclusio"),\n'
    '            ("capitulum_en", "Capitulum"),\n'
    '            ("versus_en", "Versum"), ("versus_en", "Versus"),\n'
    '            ("preces_en", "Preces"),\n'
    '        ]:\n'
    '            val = ek(key)\n'
    '            if val and col not in [s.split("=")[0] for s in sets]:\n'
    '                sets.append(f"{col}=?"); vals.append(val)\n'
    '\n'
    '        # Antiphons laudes\n'
    '        for i in range(1, 10):\n'
    '            en_val = ek(f"Ant {i}") or ek(f"Ant{i}")\n'
    '            if en_val:\n'
    '                sets.append(f"antiphon_{i}_en=?"); vals.append(en_val)\n'
    '\n'
    '        # Antiphons vespera\n'
    '        en_v1 = ek("Ant Vespera") or ek("AntVespera")\n'
    '        if en_v1:\n'
    '            sets.append("antiphon_vespera_1_en=?"); vals.append(en_v1)\n'
    '        for i in range(1, 13):\n'
    '            en_val = ek(f"Ant Vespera {i}") or ek(f"AntVespera{i}")\n'
    '            if en_val:\n'
    '                idx = i + 1\n'
    '                sets.append(f"antiphon_vespera_{idx}_en=?"); vals.append(en_val)\n'
    '\n'
    '        if sets:\n'
    '            vals.append(row_id)\n'
    '            conn.execute(\n'
    '                f"UPDATE divine_office SET {chr(39).join(sets).replace(chr(39)+chr(61)+chr(63), chr(61)+chr(63))} WHERE id=?".replace(chr(39)+chr(44)+chr(32), chr(44)+chr(32)),\n'
    '                vals\n'
    '            )\n'
    '            updated += 1\n'
    '\n'
    '    print(f"  English columns: {updated} rows updated, {skipped} skipped")\n'
    '    return updated\n'
    '\n'
    '\n'
)

# The above has issues with f-string quoting. Let me use a simpler approach.
# Actually let's write the UPDATE as a regular string join:
update_block = (
    '\n'
    'def _populate_english_offices(conn):\n'
    '    print("Populating English bilingual columns...")\n'
    '    updated = 0\n'
    '    skipped = 0\n'
    '\n'
    '    rows = conn.execute(\n'
    '        "SELECT id, file, file_type FROM divine_office"\n'
    '    ).fetchall()\n'
    '\n'
    '    for row_id, file_path, file_type in rows:\n'
    '        if not file_path:\n'
    '            skipped += 1\n'
    '            continue\n'
    '        en_dir = _ENGLISH_DIR_MAP.get(file_type, "Sancti")\n'
    '        en_path = os.path.join(ENGLISH_HORAS, en_dir, file_path + ".txt")\n'
    '        if not os.path.exists(en_path):\n'
    '            skipped += 1\n'
    '            continue\n'
    '        en_secs = _load_txt_sections(en_path)\n'
    '\n'
    '        def ek(key):\n'
    '            kl = key.lower()\n'
    '            for k, v in en_secs.items():\n'
    '                if k.lower() == kl:\n'
    '                    return "\\n".join(v)\n'
    '            return None\n'
    '\n'
    '        sets = []\n'
    '        vals = []\n'
    '\n'
    '        hymn_en = ek("Hymnus Vespera") or ek("Hymnus Laudes") \\\n'
    '                   or ek("Hymnus Matutinum") or ek("Hymnus Completorium_C") \\\n'
    '                   or ek("Hymnus Completorium")\n'
    '        if hymn_en:\n'
    '            sets.append("hymn_en=?"); vals.append(hymn_en)\n'
    '\n'
    '        for col, key in [\n'
    '            ("lectio_1_en", "Lectio1"), ("lectio_1_en", "Lectio 1"),\n'
    '            ("lectio_2_en", "Lectio2"), ("lectio_2_en", "Lectio 2"),\n'
    '            ("lectio_3_en", "Lectio3"), ("lectio_3_en", "Lectio 3"),\n'
    '            ("responsory_1_en", "Responsory1"),\n'
    '            ("responsory_2_en", "Responsory2"),\n'
    '            ("responsory_3_en", "Responsory3"),\n'
    '            ("oratio_en", "Oratio"), ("oratio_en", "Oratio Completorium"),\n'
    '            ("conclusio_en", "Conclusio"),\n'
    '            ("capitulum_en", "Capitulum"),\n'
    '            ("versus_en", "Versum"), ("versus_en", "Versus"),\n'
    '            ("preces_en", "Preces"),\n'
    '        ]:\n'
    '            val = ek(key)\n'
    '            if val and col not in [s.split("=")[0] for s in sets]:\n'
    '                sets.append(col + "=?"); vals.append(val)\n'
    '\n'
    '        for i in range(1, 10):\n'
    '            en_val = ek("Ant " + str(i)) or ek("Ant" + str(i))\n'
    '            if en_val:\n'
    '                sets.append("antiphon_" + str(i) + "_en=?"); vals.append(en_val)\n'
    '\n'
    '        en_v1 = ek("Ant Vespera") or ek("AntVespera")\n'
    '        if en_v1:\n'
    '            sets.append("antiphon_vespera_1_en=?"); vals.append(en_v1)\n'
    '        for i in range(1, 13):\n'
    '            en_val = ek("Ant Vespera " + str(i)) or ek("AntVespera" + str(i))\n'
    '            if en_val:\n'
    '                sets.append("antiphon_vespera_" + str(i+1) + "_en=?"); vals.append(en_val)\n'
    '\n'
    '        if sets:\n'
    '            vals.append(row_id)\n'
    '            set_clause = ", ".join(sets)\n'
    '            conn.execute(\n'
    '                "UPDATE divine_office SET " + set_clause + " WHERE id=?",\n'
    '                vals\n'
    '            )\n'
    '            updated += 1\n'
    '\n'
    '    print("  English columns: " + str(updated) + " rows updated, " + str(skipped) + " skipped")\n'
    '    return updated\n'
    '\n'
    '\n'
)

lines.insert(insert2, update_block)
print(f"  [P2] Added _populate_english_offices at line {insert2+1}")

# ── P3: Call in main() after compile_divine_office ────────────────────────────
insert3 = None
for i, line in enumerate(lines):
    if "compile_divine_office(conn)" in line and "def " not in line:
        insert3 = i + 1
        break

if insert3 is None:
    print("ERROR: compile_divine_office call not found in main")
    sys.exit(1)

lines.insert(insert3, "\n        print(\"Populating English office columns...\")\n        _populate_english_offices(conn)\n")
print(f"  [P3] Added call in main() at line {insert3+1}")

# ── Write ─────────────────────────────────────────────────────────────────────
with open(PATH, "w") as f:
    f.writelines(lines)

print("\nAll patches applied OK")
