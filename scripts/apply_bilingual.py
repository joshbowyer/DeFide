#!/usr/bin/env python3
"""Apply Phase 1 bilingual patches to compile_content.py."""
import sys

PATH = "/home/josh/claw-code/DeFide/scripts/compile_content.py"
with open(PATH) as f:
    src = f.read()
errors = []
n = 0

def replace(old, new, desc):
    global src, n
    if old not in src:
        errors.append("NOT FOUND [%s]" % desc)
        return
    src = src.replace(old, new, 1)
    n += 1
    print("  [%d] OK: %s" % (n, desc))

# P1: Schema
print("P1: Schema...")
replace(
    "            antiphon_1  TEXT, antiphon_2  TEXT, antiphon_3  TEXT,\n"
    "            antiphon_4  TEXT, antiphon_5  TEXT, antiphon_6  TEXT,\n"
    "            antiphon_7  TEXT, antiphon_8  TEXT, antiphon_9  TEXT,\n"
    "            antiphon_vespera_1  TEXT, antiphon_vespera_2  TEXT, antiphon_vespera_3  TEXT,\n"
    "            antiphon_vespera_4  TEXT, antiphon_vespera_5  TEXT, antiphon_vespera_6  TEXT,\n"
    "            antiphon_vespera_7  TEXT, antiphon_vespera_8  TEXT, antiphon_vespera_9  TEXT,\n"
    "            antiphon_vespera_10 TEXT, antiphon_vespera_11 TEXT, antiphon_vespera_12 TEXT,\n"
    "            hymn        TEXT,\n"
    "            lectio_1    TEXT, lectio_2    TEXT, lectio_3    TEXT,\n"
    "            responsory_1 TEXT, responsory_2 TEXT, responsory_3 TEXT,\n"
    "            versus      TEXT,\n"
    "            preces      TEXT,\n"
    "            capitulum   TEXT,\n"
    "            oratio      TEXT,\n"
    "            conclusio   TEXT,",
    "            antiphon_1_la  TEXT, antiphon_1_en  TEXT,\n"
    "            antiphon_2_la  TEXT, antiphon_2_en  TEXT,\n"
    "            antiphon_3_la  TEXT, antiphon_3_en  TEXT,\n"
    "            antiphon_4_la  TEXT, antiphon_4_en  TEXT,\n"
    "            antiphon_5_la  TEXT, antiphon_5_en  TEXT,\n"
    "            antiphon_6_la  TEXT, antiphon_6_en  TEXT,\n"
    "            antiphon_7_la  TEXT, antiphon_7_en  TEXT,\n"
    "            antiphon_8_la  TEXT, antiphon_8_en  TEXT,\n"
    "            antiphon_9_la  TEXT, antiphon_9_en  TEXT,\n"
    "            antiphon_vespera_1_la  TEXT, antiphon_vespera_1_en  TEXT,\n"
    "            antiphon_vespera_2_la  TEXT, antiphon_vespera_2_en  TEXT,\n"
    "            antiphon_vespera_3_la  TEXT, antiphon_vespera_3_en  TEXT,\n"
    "            antiphon_vespera_4_la  TEXT, antiphon_vespera_4_en  TEXT,\n"
    "            antiphon_vespera_5_la  TEXT, antiphon_vespera_5_en  TEXT,\n"
    "            antiphon_vespera_6_la  TEXT, antiphon_vespera_6_en  TEXT,\n"
    "            antiphon_vespera_7_la  TEXT, antiphon_vespera_7_en  TEXT,\n"
    "            antiphon_vespera_8_la  TEXT, antiphon_vespera_8_en  TEXT,\n"
    "            antiphon_vespera_9_la  TEXT, antiphon_vespera_9_en  TEXT,\n"
    "            antiphon_vespera_10_la TEXT, antiphon_vespera_10_en TEXT,\n"
    "            antiphon_vespera_11_la TEXT, antiphon_vespera_11_en TEXT,\n"
    "            antiphon_vespera_12_la TEXT, antiphon_vespera_12_en TEXT,\n"
    "            hymn_la      TEXT, hymn_en      TEXT,\n"
    "            lectio_1_la  TEXT, lectio_1_en  TEXT,\n"
    "            lectio_2_la  TEXT, lectio_2_en  TEXT,\n"
    "            lectio_3_la  TEXT, lectio_3_en  TEXT,\n"
    "            responsory_1_la TEXT, responsory_1_en TEXT,\n"
    "            responsory_2_la TEXT, responsory_2_en TEXT,\n"
    "            responsory_3_la TEXT, responsory_3_en TEXT,\n"
    "            versus_la    TEXT, versus_en    TEXT,\n"
    "            preces_la    TEXT, preces_en    TEXT,\n"
    "            capitulum_la TEXT, capitulum_en TEXT,\n"
    "            oratio_la    TEXT, oratio_en   TEXT,\n"
    "            conclusio_la TEXT, conclusio_en TEXT,",
    "schema"
)

# P2: ENGLISH_HORAS
print("P2: ENGLISH_HORAS...")
replace(
    "def compile_divine_office(conn):",
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
    'def compile_divine_office(conn):',
    "ENGLISH_HORAS"
)

# P3: VALUES tuple
print("P3: VALUES tuple...")
V_OLD = (
    "                        (\n"
    "                            rel.rsplit(\".json\", 1)[0], file_type, sec_title,\n"
    "                            office_type if office_type else None,\n"
    "                            merged.get(\"Invitatorium\") or merged.get(\"Invit\"),\n"
    "                            *laudes_ants,\n"
    "                            *vespera_ants,\n"
    "                            hymn,\n"
    "                            lectio1, lectio2, lectio3,\n"
    "                            resp1, resp2, resp3,\n"
    "                            merged.get(\"Versum\") or merged.get(\"Versus\"),\n"
    "                            merged.get(\"Preces\"),\n"
    "                            capitulum,\n"
    "                            (merged.get(f\"Oratio {office_type}\")\n"
    "                             or merged.get(f\"Oratio{office_type}\")\n"
    "                             or merged.get(\"Oratio\")\n"
    "                             or merged.get(\"Oratio Completorium\")),\n"
    "                            merged.get(\"Conclusio\"),\n"
    "                            matins_antiphon,\n"
    "                            supplemental,\n"
    "                        ))"
)
parts = [
    "                        (",
    "                            rel.rsplit(\".json\", 1)[0], file_type, sec_title,",
    "                            office_type if office_type else None,",
    "                            merged.get(\"Invitatorium\") or merged.get(\"Invit\"),",
    "                            # Latin antiphons laudes",
]
for i in range(9):
    parts.append("                            laudes_ants[%d] if len(laudes_ants) > %d else None," % (i, i))
    parts.append("                            en_laudes_ants[%d] if len(en_laudes_ants) > %d else None," % (i, i))
parts.append("                            # Latin antiphons vespera")
for i in range(12):
    parts.append("                            vespera_ants[%d] if len(vespera_ants) > %d else None," % (i, i))
    parts.append("                            en_vespera_ants[%d] if len(en_vespera_ants) > %d else None," % (i, i))
parts += [
    "                            # hymns",
    "                            hymn, en_hymn,",
    "                            # lecturas",
    '                            lectio1, _ek("Lectio1") or _ek("Lectio 1"),',
    '                            lectio2, _ek("Lectio2") or _ek("Lectio 2"),',
    '                            lectio3, _ek("Lectio3") or _ek("Lectio 3"),',
    "                            # responsories",
    '                            resp1, _ek("Responsory1"),',
    '                            resp2, _ek("Responsory2"),',
    '                            resp3, _ek("Responsory3"),',
    "                            # minor hours",
    "                            merged.get(\"Versum\") or merged.get(\"Versus\"),",
    '                            _ek("Versum") or _ek("Versus"),',
    "                            merged.get(\"Preces\"),",
    '                            _ek("Preces"),',
    "                            capitulum,",
    '                            _ek("Capitulum Laudes") or _ek("Capitulum Vespera") or _ek("Capitulum"),',
    "                            # oratio / conclusio",
    '                            (merged.get(f"Oratio {office_type}")',
    "                             or merged.get(f\"Oratio{office_type}\")",
    "                             or merged.get(\"Oratio\")",
    "                             or merged.get(\"Oratio Completorium\")),",
    "                            _oratio_ek(office_type),",
    "                            merged.get(\"Conclusio\"),",
    '                            _ek("Conclusio"),',
    "                            matins_antiphon,",
    "                            supplemental,",
    "                        ))",
]
replace(V_OLD, "\n".join(parts), "VALUES tuple")

# P4: Ferial INSERT
print("P4: Ferial...")
replace(
    "            \"\"\"INSERT INTO divine_office\n"
    "               (file, file_type, title, office_type, oratio,\n"
    "                antiphon_1, antiphon_2, antiphon_3, antiphon_4, antiphon_5,\n"
    "                antiphon_6, antiphon_7, antiphon_8, antiphon_9,\n"
    "                hymn, matins_antiphon)\n"
    "               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\"",
    "            \"\"\"INSERT INTO divine_office\n"
    "               (file, file_type, title, office_type, oratio_la, oratio_en,\n"
    "                antiphon_1_la, antiphon_1_en,\n"
    "                antiphon_2_la, antiphon_2_en,\n"
    "                antiphon_3_la, antiphon_3_en,\n"
    "                antiphon_4_la, antiphon_4_en,\n"
    "                antiphon_5_la, antiphon_5_en,\n"
    "                antiphon_6_la, antiphon_6_en,\n"
    "                antiphon_7_la, antiphon_7_en,\n"
    "                antiphon_8_la, antiphon_8_en,\n"
    "                antiphon_9_la, antiphon_9_en,\n"
    "                hymn_la, hymn_en, matins_antiphon)\n"
    "               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n"
    "                       ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\"",
    "ferial INSERT"
)
replace(
    "            (\n"
    "                f\"ferial/{day}\", \"ferial\", title, ot, oratio,\n"
    "                *ant_list[:9],\n"
    "                None,\n"
    "                antiphon,\n"
    "            ),",
    "            (\n"
    "                f\"ferial/{day}\", \"ferial\", title, ot, oratio, None,\n"
    "                ant_list[0] if len(ant_list) > 0 else None, None,\n"
    "                ant_list[1] if len(ant_list) > 1 else None, None,\n"
    "                ant_list[2] if len(ant_list) > 2 else None, None,\n"
    "                ant_list[3] if len(ant_list) > 3 else None, None,\n"
    "                ant_list[4] if len(ant_list) > 4 else None, None,\n"
    "                ant_list[5] if len(ant_list) > 5 else None, None,\n"
    "                ant_list[6] if len(ant_list) > 6 else None, None,\n"
    "                ant_list[7] if len(ant_list) > 7 else None, None,\n"
    "                ant_list[8] if len(ant_list) > 8 else None, None,\n"
    "                None, None,\n"
    "                antiphon,\n"
    "            ),",
    "ferial VALUES"
)

# P5: Completorium INSERT
print("P5: Completorium...")
replace(
    "        conn.execute(\n"
    "            \"\"\"INSERT INTO divine_office\n"
    "               (file, file_type, title, office_type, hymn, matins_antiphon, oratio)\n"
    "               VALUES (?, ?, ?, ?, ?, ?, ?)\"",
    "        conn.execute(\n"
    "            \"\"\"INSERT INTO divine_office\n"
    "               (file, file_type, title, office_type,\n"
    "                hymn_la, hymn_en, matins_antiphon, oratio_la, oratio_en)\n"
    "               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\"",
    "Completorium INSERT"
)
replace(
    "                f\"ferial/{day}\",\n"
    "                \"ferial\",\n"
    "                f\"{day_label} — Completorium\",\n"
    "                \"Completorium\",\n"
    "                hymn_text,\n"
    "                ant,\n"
    "                oratio_text,\n"
    "            ),",
    "                f\"ferial/{day}\",\n"
    "                \"ferial\",\n"
    "                f\"{day_label} — Completorium\",\n"
    "                \"Completorium\",\n"
    "                hymn_text, None,\n"
    "                ant,\n"
    "                oratio_text, None,\n"
    "            ),",
    "Completorium VALUES"
)

# P6: Main INSERT
print("P6: Main INSERT...")
idx = src.find('conn.execute(\n                        """INSERT INTO divine_office')
if idx < 0:
    errors.append("NOT FOUND [main INSERT start]")
else:
    chunk = src[idx:idx+3000]
    ei = chunk.find(')"""')
    if ei < 0:
        errors.append("NOT FOUND [main INSERT end]")
    else:
        old_insert = src[idx:idx+ei+4]
        new_insert = (
            '                    # Load English .txt data for this file\n'
            '                    en_dir = _ENGLISH_DIR_MAP.get(file_type, "Sancti")\n'
            '                    en_txt_path = os.path.join(ENGLISH_HORAS, en_dir, file_stem + ".txt")\n'
            '                    en_secs = _load_txt_sections(en_txt_path) if os.path.exists(en_txt_path) else {}\n'
            '\n'
            '                    def _ek(key):\n'
            '                        kl = key.lower()\n'
            '                        for k, v in en_secs.items():\n'
            '                            if k.lower() == kl:\n'
            '                                return "\\n".join(v)\n'
            '                        return None\n'
            '\n'
            '                    en_laudes_ants = [_ek(f"Ant {i}") or _ek(f"Ant{i}") or "" for i in range(1, 10)]\n'
            '                    en_v1 = _ek("Ant Vespera") or _ek("AntVespera")\n'
            '                    en_vespera_ants = [en_v1] if en_v1 else []\n'
            '                    for i in range(1, 13):\n'
            '                        v = _ek(f"Ant Vespera {i}") or _ek(f"AntVespera{i}")\n'
            '                        if v:\n'
            '                            en_vespera_ants.append(v)\n'
            '                    while len(en_vespera_ants) < 12:\n'
            '                        en_vespera_ants.append("")\n'
            '                    en_vespera_ants = en_vespera_ants[:12]\n'
            '                    en_hymn = (_ek("Hymnus Vespera") or _ek("Hymnus Laudes")\n'
            '                               or _ek("Hymnus Matutinum") or _ek("Hymnus Completorium_C")\n'
            '                               or _ek("Hymnus Completorium"))\n'
            '\n'
            '                    def _oratio_ek(ot):\n'
            '                        return _ek(f"Oratio {ot}") or _ek(f"Oratio{ot}") \\\n'
            '                               or _ek("Oratio") or _ek("Oratio Completorium")\n'
            '\n'
            '                    conn.execute(\n'
            '                        """INSERT INTO divine_office\n'
            '                           (file, file_type, title, office_type, invitatorium,\n'
            '                            antiphon_1_la, antiphon_1_en,\n'
            '                            antiphon_2_la, antiphon_2_en,\n'
            '                            antiphon_3_la, antiphon_3_en,\n'
            '                            antiphon_4_la, antiphon_4_en,\n'
            '                            antiphon_5_la, antiphon_5_en,\n'
            '                            antiphon_6_la, antiphon_6_en,\n'
            '                            antiphon_7_la, antiphon_7_en,\n'
            '                            antiphon_8_la, antiphon_8_en,\n'
            '                            antiphon_9_la, antiphon_9_en,\n'
            '                            antiphon_vespera_1_la, antiphon_vespera_1_en,\n'
            '                            antiphon_vespera_2_la, antiphon_vespera_2_en,\n'
            '                            antiphon_vespera_3_la, antiphon_vespera_3_en,\n'
            '                            antiphon_vespera_4_la, antiphon_vespera_4_en,\n'
            '                            antiphon_vespera_5_la, antiphon_vespera_5_en,\n'
            '                            antiphon_vespera_6_la, antiphon_vespera_6_en,\n'
            '                            antiphon_vespera_7_la, antiphon_vespera_7_en,\n'
            '                            antiphon_vespera_8_la, antiphon_vespera_8_en,\n'
            '                            antiphon_vespera_9_la, antiphon_vespera_9_en,\n'
            '                            antiphon_vespera_10_la, antiphon_vespera_10_en,\n'
            '                            antiphon_vespera_11_la, antiphon_vespera_11_en,\n'
            '                            antiphon_vespera_12_la, antiphon_vespera_12_en,\n'
            '                            hymn_la, hymn_en,\n'
            '                            lectio_1_la, lectio_1_en,\n'
            '                            lectio_2_la, lectio_2_en,\n'
            '                            lectio_3_la, lectio_3_en,\n'
            '                            responsory_1_la, responsory_1_en,\n'
            '                            responsory_2_la, responsory_2_en,\n'
            '                            responsory_3_la, responsory_3_en,\n'
            '                            versus_la, versus_en,\n'
            '                            preces_la, preces_en,\n'
            '                            capitulum_la, capitulum_en,\n'
            '                            oratio_la, oratio_en,\n'
            '                            conclusio_la, conclusio_en,\n'
            '                            matins_antiphon, supplemental)\n'
            '                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n'
            '                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n'
            '                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n'
            '                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,\n'
            '                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""'
        )
        if old_insert in src:
            src = src.replace(old_insert, new_insert, 1)
            n += 1
            print("  [%d] OK: main INSERT" % n)
        else:
            errors.append("NOT FOUND [main INSERT replacement]")

if errors:
    print("ERRORS:", errors)
    sys.exit(1)
with open(PATH, "w") as f:
    f.write(src)
print("All %d patches applied OK" % n)
