#!/usr/bin/env python3
"""Patch compile_content.py for Phase 1 bilingual support."""
path = "/home/josh/claw-code/DeFide/scripts/compile_content.py"
with open(path) as f:
    src = f.read()

# 1. Verify schema has bilingual columns
if "antiphon_1_la" not in src:
    raise SystemExit("ERROR: schema not yet updated")

# 2. Add ENGLISH_HORAS + _ENGLISH_DIR_MAP before compile_divine_office
if "ENGLISH_HORAS = os.path.join" not in src:
    marker = "def compile_divine_office(conn):"
    injection = """ENGLISH_HORAS = os.path.join(
    REPO_ROOT, "divinum-officium", "web", "www", "horas", "English"
)
_ENGLISH_DIR_MAP = {
    "tempora":  "Tempora",
    "sancti":   "Sancti",
    "commune":  "Commune",
    "extra":    "Sancti",
    "orationes": "Sancti",
    "psalmi":   "Psalterium",
    "missa":    "Tempora",
    "martyrologium": "Martyrologium",
}

"""
    src = src.replace(marker, injection + marker, 1)
    print("+ ENGLISH_HORAS + _ENGLISH_DIR_MAP")

# 3. Update the main INSERT statement
old_insert = '''                    conn.execute(
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
                                   ?, ?, ?, ?, ?, ?)"'''
new_insert = '''                    # Load English .txt data for this file
                    en_dir = _ENGLISH_DIR_MAP.get(file_type, "Sancti")
                    en_txt_path = os.path.join(ENGLISH_HORAS, en_dir, file_stem + ".txt")
                    en_secs = _load_txt_sections(en_txt_path) if os.path.exists(en_txt_path) else {}

                    def _ek(key):
                        kl = key.lower()
                        for k, v in en_secs.items():
                            if k.lower() == kl:
                                return "\\n".join(v)
                        return None

                    en_laudes_ants = [_ek(f"Ant {i}") or _ek(f"Ant{i}") or "" for i in range(1, 10)]
                    en_v1 = _ek("Ant Vespera") or _ek("AntVespera")
                    en_vespera_ants = [en_v1] if en_v1 else []
                    for i in range(1, 13):
                        v = _ek(f"Ant Vespera {i}") or _ek(f"AntVespera{i}")
                        if v:
                            en_vespera_ants.append(v)
                    while len(en_vespera_ants) < 12:
                        en_vespera_ants.append("")
                    en_vespera_ants = en_vespera_ants[:12]
                    en_hymn = (_ek("Hymnus Vespera") or _ek("Hymnus Laudes")
                               or _ek("Hymnus Matutinum") or _ek("Hymnus Completorium_C")
                               or _ek("Hymnus Completorium"))

                    def _oratio_ek(ot):
                        return _ek(f"Oratio {ot}") or _ek(f"Oratio{ot}") \
                               or _ek("Oratio") or _ek("Oratio Completorium")

                    conn.execute(
                        """INSERT INTO divine_office
                           (file, file_type, title, office_type, invitatorium,
                            antiphon_1_la, antiphon_1_en,
                            antiphon_2_la, antiphon_2_en,
                            antiphon_3_la, antiphon_3_en,
                            antiphon_4_la, antiphon_4_en,
                            antiphon_5_la, antiphon_5_en,
                            antiphon_6_la, antiphon_6_en,
                            antiphon_7_la, antiphon_7_en,
                            antiphon_8_la, antiphon_8_en,
                            antiphon_9_la, antiphon_9_en,
                            antiphon_vespera_1_la, antiphon_vespera_1_en,
                            antiphon_vespera_2_la, antiphon_vespera_2_en,
                            antiphon_vespera_3_la, antiphon_vespera_3_en,
                            antiphon_vespera_4_la, antiphon_vespera_4_en,
                            antiphon_vespera_5_la, antiphon_vespera_5_en,
                            antiphon_vespera_6_la, antiphon_vespera_6_en,
                            antiphon_vespera_7_la, antiphon_vespera_7_en,
                            antiphon_vespera_8_la, antiphon_vespera_8_en,
                            antiphon_vespera_9_la, antiphon_vespera_9_en,
                            antiphon_vespera_10_la, antiphon_vespera_10_en,
                            antiphon_vespera_11_la, antiphon_vespera_11_en,
                            antiphon_vespera_12_la, antiphon_vespera_12_en,
                            hymn_la, hymn_en,
                            lectio_1_la, lectio_1_en,
                            lectio_2_la, lectio_2_en,
                            lectio_3_la, lectio_3_en,
                            responsory_1_la, responsory_1_en,
                            responsory_2_la, responsory_2_en,
                            responsory_3_la, responsory_3_en,
                            versus_la, versus_en,
                            preces_la, preces_en,
                            capitulum_la, capitulum_en,
                            oratio_la, oratio_en,
                            conclusio_la, conclusio_en,
                            matins_antiphon, supplemental)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                                   ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
if old_insert not in src:
    raise SystemExit("ERROR: old_insert not found in source")
src = src.replace(old_insert, new_insert)
print("+ main INSERT statement")

# 4. Update VALUES tuple
old_vals = '''                        (
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
                        ))'''
new_vals = '''                        (
                            rel.rsplit(".json", 1)[0], file_type, sec_title,
                            office_type if office_type else None,
                            merged.get("Invitatorium") or merged.get("Invit"),
                            # Latin antiphons laudes
                            laudes_ants[0] if len(laudes_ants) > 0 else None,
                            en_laudes_ants[0] if len(en_laudes_ants) > 0 else None,
                            laudes_ants[1] if len(laudes_ants) > 1 else None,
                            en_laudes_ants[1] if len(en_laudes_ants) > 1 else None,
                            laudes_ants[2] if len(laudes_ants) > 2 else None,
                            en_laudes_ants[2] if len(en_laudes_ants) > 2 else None,
                            laudes_ants[3] if len(laudes_ants) > 3 else None,
                            en_laudes_ants[3] if len(en_laudes_ants) > 3 else None,
                            laudes_ants[4] if len(laudes_ants) > 4 else None,
                            en_laudes_ants[4] if len(en_laudes_ants) > 4 else None,
                            laudes_ants[5] if len(laudes_ants) > 5 else None,
                            en_laudes_ants[5] if len(en_laudes_ants) > 5 else None,
                            laudes_ants[6] if len(laudes_ants) > 6 else None,
                            en_laudes_ants[6] if len(en_laudes_ants) > 6 else None,
                            laudes_ants[7] if len(laudes_ants) > 7 else None,
                            en_laudes_ants[7] if len(en_laudes_ants) > 7 else None,
                            laudes_ants[8] if len(laudes_ants) > 8 else None,
                            en_laudes_ants[8] if len(en_laudes_ants) > 8 else None,
                            # Latin antiphons vespera
                            vespera_ants[0] if len(vespera_ants) > 0 else None,
                            en_vespera_ants[0] if len(en_vespera_ants) > 0 else None,
                            vespera_ants[1] if len(vespera_ants) > 1 else None,
                            en_vespera_ants[1] if len(en_vespera_ants) > 1 else None,
                            vespera_ants[2] if len(vespera_ants) > 2 else None,
                            en_vespera_ants[2] if len(en_vespera_ants) > 2 else None,
                            vespera_ants[3] if len(vespera_ants) > 3 else None,
                            en_vespera_ants[3] if len(en_vespera_ants) > 3 else None,
                            vespera_ants[4] if len(vespera_ants) > 4 else None,
                            en_vespera_ants[4] if len(en_vespera_ants) > 4 else None,
                            vespera_ants[5] if len(vespera_ants) > 5 else None,
                            en_vespera_ants[5] if len(en_vespera_ants) > 5 else None,
                            vespera_ants[6] if len(vespera_ants) > 6 else None,
                            en_vespera_ants[6] if len(en_vespera_ants) > 6 else None,
                            vespera_ants[7] if len(vespera_ants) > 7 else None,
                            en_vespera_ants[7] if len(en_vespera_ants) > 7 else None,
                            vespera_ants[8] if len(vespera_ants) > 8 else None,
                            en_vespera_ants[8] if len(en_vespera_ants) > 8 else None,
                            vespera_ants[9] if len(vespera_ants) > 9 else None,
                            en_vespera_ants[9] if len(en_vespera_ants) > 9 else None,
                            vespera_ants[10] if len(vespera_ants) > 10 else None,
                            en_vespera_ants[10] if len(en_vespera_ants) > 10 else None,
                            vespera_ants[11] if len(vespera_ants) > 11 else None,
                            en_vespera_ants[11] if len(en_vespera_ants) > 11 else None,
                            # hymns
                            hymn, en_hymn,
                            # lecturas
                            lectio1, _ek("Lectio1") or _ek("Lectio 1"),
                            lectio2, _ek("Lectio2") or _ek("Lectio 2"),
                            lectio3, _ek("Lectio3") or _ek("Lectio 3"),
                            # responsories
                            resp1, _ek("Responsory1"),
                            resp2, _ek("Responsory2"),
                            resp3, _ek("Responsory3"),
                            # minor hours
                            merged.get("Versum") or merged.get("Versus"),
                            _ek("Versum") or _ek("Versus"),
                            merged.get("Preces"),
                            _ek("Preces"),
                            capitulum,
                            _ek("Capitulum Laudes") or _ek("Capitulum Vespera") or _ek("Capitulum"),
                            # oratio / conclusio
                            (merged.get(f"Oratio {office_type}")
                             or merged.get(f"Oratio{office_type}")
                             or merged.get("Oratio")
                             or merged.get("Oratio Completorium")),
                            _oratio_ek(office_type),
                            merged.get("Conclusio"),
                            _ek("Conclusio"),
                            matins_antiphon,
                            supplemental,
                        ))'''
if old_vals not in src:
    raise SystemExit("ERROR: old_vals not found in source")
src = src.replace(old_vals, new_vals)
print("+ VALUES tuple")

# 5. Ferial INSERT
old_ferial_i = '''            """INSERT INTO divine_office
               (file, file_type, title, office_type, oratio,
                antiphon_1, antiphon_2, antiphon_3, antiphon_4, antiphon_5,
                antiphon_6, antiphon_7, antiphon_8, antiphon_9,
                hymn, matins_antiphon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
new_ferial_i = '''            """INSERT INTO divine_office
               (file, file_type, title, office_type, oratio_la, oratio_en,
                antiphon_1_la, antiphon_1_en,
                antiphon_2_la, antiphon_2_en,
                antiphon_3_la, antiphon_3_en,
                antiphon_4_la, antiphon_4_en,
                antiphon_5_la, antiphon_5_en,
                antiphon_6_la, antiphon_6_en,
                antiphon_7_la, antiphon_7_en,
                antiphon_8_la, antiphon_8_en,
                antiphon_9_la, antiphon_9_en,
                hymn_la, hymn_en, matins_antiphon)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                       ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
if old_ferial_i not in src:
    raise SystemExit("ERROR: old_ferial_i not found")
src = src.replace(old_ferial_i, new_ferial_i)
print("+ ferial INSERT")

old_ferial_v = '''            (
                f"ferial/{day}", "ferial", title, ot, oratio,
                *ant_list[:9],
                None,
                antiphon,
            ),'''
new_ferial_v = '''            (
                f"ferial/{day}", "ferial", title, ot, oratio, None,
                ant_list[0] if len(ant_list) > 0 else None, None,
                ant_list[1] if len(ant_list) > 1 else None, None,
                ant_list[2] if len(ant_list) > 2 else None, None,
                ant_list[3] if len(ant_list) > 3 else None, None,
                ant_list[4] if len(ant_list) > 4 else None, None,
                ant_list[5] if len(ant_list) > 5 else None, None,
                ant_list[6] if len(ant_list) > 6 else None, None,
                ant_list[7] if len(ant_list) > 7 else None, None,
                ant_list[8] if len(ant_list) > 8 else None, None,
                None, None,
                antiphon,
            ),'''
if old_ferial_v not in src:
    raise SystemExit("ERROR: old_ferial_v not found")
src = src.replace(old_ferial_v, new_ferial_v)
print("+ ferial VALUES")

# 6. Completorium INSERT
old_comp_i = '''        conn.execute(
            """INSERT INTO divine_office
               (file, file_type, title, office_type, hymn, matins_antiphon, oratio)
               VALUES (?, ?, ?, ?, ?, ?, ?)'''
new_comp_i = '''        conn.execute(
            """INSERT INTO divine_office
               (file, file_type, title, office_type,
                hymn_la, hymn_en, matins_antiphon, oratio_la, oratio_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'''
if old_comp_i not in src:
    raise SystemExit("ERROR: old_comp_i not found")
src = src.replace(old_comp_i, new_comp_i)
print("+ Completorium INSERT")

old_comp_v = '''                f"ferial/{day}",
                "ferial",
                f"{day_label} — Completorium",
                "Completorium",
                hymn_text,
                ant,
                oratio_text,
            ),'''
new_comp_v = '''                f"ferial/{day}",
                "ferial",
                f"{day_label} — Completorium",
                "Completorium",
                hymn_text, None,
                ant,
                oratio_text, None,
            ),'''
if old_comp_v not in src:
    raise SystemExit("ERROR: old_comp_v not found")
src = src.replace(old_comp_v, new_comp_v)
print("+ Completorium VALUES")

with open(path, "w") as f:
    f.write(src)
print("\nAll patches applied OK")
