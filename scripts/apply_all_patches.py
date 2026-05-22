#!/usr/bin/env python3
"""Apply all divine office compiler patches to compile_content.py."""
import re, sys

with open('scripts/compile_content.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

changes = []

def find_line(predicate, start=0):
    for i in range(start, len(lines)):
        if predicate(lines[i]):
            return i + 1   # 1-indexed
    return None

def replace_lines(start, end, new_lines, desc):
    global lines
    new_src = lines[:start-1] + new_lines + lines[end-1:]
    lines = new_src
    changes.append(desc)
    return True

# ── PATCH 1: Add imports ───────────────────────────────────────────
import_sys = find_line(lambda l: l.strip() == 'import sys')
print(f"P1: import sys at line {import_sys}")
replace_lines(import_sys+1, import_sys+1, ['import re\n', 'import calendar\n'], "P1: add import re/calendar")

# ── PATCH 2: Add FERIL_ORATIOS module dict ─────────────────────────
repo_root = find_line(lambda l: l.strip().startswith('REPO_ROOT = '))
print(f"P2: REPO_ROOT at line {repo_root}")
replace_lines(repo_root, repo_root, [
    '# Ferial oratios: day -> office_type -> oratio text (populated at runtime)\n',
    'FERIAL_ORATIOS: dict[int, dict[str, str]] = {}\n',
    '\n',
], "P2: add FERIL_ORATIOS")

# ── PATCH 3: Populate FERIL_ORATIOS inside the backfill function ───
# Find FERIAL_ROWS = [ and its closing ]
fr_start = find_line(lambda l: l.strip() == 'FERIAL_ROWS = [')
# closing ]: find a line that is ']' preceded only by spaces
for i in range(fr_start, len(lines)):
    stripped = lines[i].rstrip('\n')
    if stripped == ']' and lines[i][0] == ' ':
        fr_end = i + 1
        break
print(f"P3: FERIAL_ROWS {fr_start}→{fr_end}")
replace_lines(fr_end+1, fr_end+1, [
    '\n',
    '    # Populate FERIL_ORATIOS from FERIAL_ROWS for the oratio fallback step\n',
    '    for _d, _o, _t, _orat in FERIAL_ROWS:\n',
    '        FERIAL_ORATIOS.setdefault(_d, {})[_o] = _orat\n',
    '\n',
], "P3: populate FERIL_ORATIOS")

# ── PATCH 4: Fix capitulum/lectio fallback chains ───────────────────
laudes_if = find_line(lambda l: '                    if office_type == "Laudes":' in l)
print(f"P4: office_type branches start at line {laudes_if}")

# Find where the Completorium branch ends → 'else:' line
comp_if = find_line(
    lambda l: '                    elif office_type == "Completorium":' in l,
    start=laudes_if
)
# find 'else:' at same indentation as Completorium branch
for i in range(comp_if, min(comp_if+10, len(lines))):
    if lines[i].strip() == 'else:' and lines[i].startswith('                    '):
        else_line = i + 1
        break

laudes_end = else_line - 1
print(f"  Completorium elif at {comp_if}, else: at {else_line}, will replace lines {laudes_if}–{laudes_end}")

laudes_new = [
    '                    if office_type == "Laudes":\n',
    '                        lectio1 = merged.get("Lectio1") or merged.get("Lectio 1")\n',
    '                        lectio2 = merged.get("Lectio Prima") or merged.get("Lectio1 in 2 loco")\n',
    '                        lectio3 = None\n',
    '                        resp1 = merged.get("Responsory1")\n',
    '                        resp2, resp3 = None, None\n',
    '                        capitulum = (merged.get("Capitulum Laudes")\n',
    '                                     or merged.get("Capitulum Prima")\n',
    '                                     or merged.get("Capitulum Tertia")\n',
    '                                     or merged.get("Capitulum Sexta")\n',
    '                                     or merged.get("Capitulum Nona")\n',
    '                                     or merged.get("Capitulum Completorium")\n',
    '                                     or merged.get("Capitulum"))\n',
    '                    elif office_type == "Vespers":\n',
    '                        lectio1 = merged.get("Lectio2") or merged.get("Lectio 2")\n',
    '                        lectio2 = merged.get("Lectio1") or merged.get("Lectio 1")\n',
    '                        lectio3 = merged.get("Lectio Prima") or merged.get("Lectio1 in 2 loco")\n',
    '                        resp1 = (merged.get("Responsory Vespera 1")\n',
    '                                 or merged.get("Responsory Vespera")\n',
    '                                 or merged.get("Responsory2"))\n',
    '                        resp2, resp3 = None, None\n',
    '                        capitulum = (merged.get("Capitulum Vespera")\n',
    '                                     or merged.get("Capitulum Sexta")\n',
    '                                     or merged.get("Capitulum Nona")\n',
    '                                     or merged.get("Capitulum Prima")\n',
    '                                     or merged.get("Capitulum Tertia")\n',
    '                                     or merged.get("Capitulum Completorium")\n',
    '                                     or merged.get("Capitulum"))\n',
    '                    elif office_type == "Completorium":\n',
    '                        capitulum = (merged.get("Capitulum Completorium")\n',
    '                                     or merged.get("Capitulum Nona")\n',
    '                                     or merged.get("Capitulum Sexta")\n',
    '                                     or merged.get("Capitulum Tertia")\n',
    '                                     or merged.get("Capitulum Prima")\n',
    '                                     or merged.get("Capitulum Laudes")\n',
    '                                     or merged.get("Capitulum Vespera")\n',
    '                                     or merged.get("Capitulum"))\n',
]
replace_lines(laudes_if, laudes_end, laudes_new, "P4: capitulum/lectio fallback chains")

# ── PATCH 5: Fix Versum key lookup ─────────────────────────────────
versus_line = find_line(lambda l: 'merged.get("Versum") or merged.get("Versus")' in l)
print(f"P5: versus at line {versus_line}")
replace_lines(versus_line, versus_line, [
    '                            (merged.get("Versum 0") or merged.get("Versum 1") or merged.get("Versum 2") or merged.get("Versum 3") or merged.get("Versum Nona") or merged.get("Versum Tertia") or merged.get("Versum Sexta") or merged.get("Versum") or merged.get("Versus")),'
    + '\n',
], "P5: fix versus keys")

# ── PATCH 6: Expand supplemental_keys ───────────────────────────────
supp_start = find_line(lambda l: "supplemental_keys = {" in l and "'Scriptura'" in l)
for i in range(supp_start, min(supp_start+20, len(lines))):
    if lines[i].strip() == '}':
        supp_end = i + 1
        break
print(f"P6: supplemental_keys {supp_start}→{supp_end}")
replace_lines(supp_start, supp_end, [
    '                    supplemental_keys = {\n',
    '                        # Readings\n',
    "                        'Lectio4', 'Lectio 4', 'Lectio5', 'Lectio 5', 'Lectio6', 'Lectio 6',\n",
    "                        'Lectio7', 'Lectio8', 'Lectio9',\n",
    "                        'Lectio1 in 2 loco', 'Lectio2 in 2 loco', 'Lectio3 in 2 loco',\n",
    "                        'Lectio4 in 2 loco', 'Lectio5 in 2 loco', 'Lectio6 in 2 loco',\n",
    "                        'Lectio7 in 2 loco', 'Lectio8 in 2 loco', 'Lectio9 in 2 loco',\n",
    "                        'Lectio4 in 3 loco', 'Lectio5 in 3 loco', 'Lectio6 in 3 loco',\n",
    "                        'Lectio7 in 3 loco', 'Lectio8 in 3 loco', 'Lectio9 in 3 loco',\n",
    "                        'Lectio in 2 loco', 'Lectio in 3 loco',\n",
    "                        'Lectio Prima', 'Lectio M01', 'Lectio M02', 'Lectio M03',\n",
    "                        'Lectio M04', 'Lectio M05', 'Lectio M06', 'Lectio M07',\n",
    "                        'Lectio M08', 'Lectio M09', 'Lectio M10', 'Lectio M11', 'Lectio M12',\n",
    '                        # Responsories\n',
    "                        'Responsory1', 'Responsory2', 'Responsory3',\n",
    "                        'Responsory4', 'Responsory5', 'Responsory6', 'Responsory7', 'Responsory8',\n",
    "                        'Responsory9', 'Responsory91',\n",
    "                        'Responsory Breve Tertia', 'Responsory Breve Sexta', 'Responsory Breve Nona',\n",
    "                        'Responsory7c',\n",
    "                        'Nocturn 1 Versum', 'Nocturn 2 Versum', 'Nocturn 3 Versum',\n",
    "                        'Scriptura',\n",
    '                    }\n',
], "P6: expand supplemental_keys")

# ── PATCH 7: Oratio resolver + ferial fallback ───────────────────────
main_line = find_line(lambda l: l.strip() == 'def main():')
print(f"P7: def main() at line {main_line}")

fallback_code = [
    '\n',
    '    # ── ORATIO RESOLVER + FERIAL FALLBACK ──────────────────────────────\n',
    '\n',
    '    def _resolve_oratio_ref(ref: str, _seen: set | None = None) -> str:\n',
    '        if _seen is None:\n',
    '            _seen = set()\n',
    '        if not ref or not ref.startswith("@"):\n',
    '            return ref\n',
    '        ref = ref.strip()\n',
    '        if ref in _seen:\n',
    '            return ref\n',
    '        _seen.add(ref)\n',
    '        core = ref.lstrip("@")\n',
    '        if "::" in core:\n',
    '            core = core.split("::")[0]\n',
    '        if ":" in core:\n',
    '            file_part = core.split(":", 1)[0]\n',
    '        else:\n',
    '            file_part = core\n',
    '        file_part = file_part.strip()\n',
    '        fn = file_part.split("/")[-1] + ".txt"\n',
    '        sections = hymn_file_index.get(fn, {})\n',
    '        if not sections:\n',
    '            return ref\n',
    '        if "Oratio" in sections:\n',
    '            text = "\\n".join(sections["Oratio"])\n',
    '            if text:\n',
    '                return text\n',
    '        for sec_name, sec_lines in sections.items():\n',
    '            if "oratio" in sec_name.lower() and sec_lines:\n',
    '                return "\\n".join(sec_lines)\n',
    '        return ref\n',
    '\n',
    '    def _post_resolve_oratio():\n',
    '        rows = conn.execute(\n',
    '            "SELECT id, oratio FROM divine_office WHERE oratio LIKE \'@%\'"\n',
    '        ).fetchall()\n',
    '        resolved = 0\n',
    '        for row_id, orat_ref in rows:\n',
    '            result = _resolve_oratio_ref(orat_ref)\n',
    '            if result != orat_ref:\n',
    '                conn.execute(\n',
    '                    "UPDATE divine_office SET oratio=? WHERE id=?",\n',
    '                    (result, row_id)\n',
    '                )\n',
    '                resolved += 1\n',
    '        return resolved\n',
    '\n',
    '    orat_resolved = _post_resolve_oratio()\n',
    '    print(f"  Resolved {orat_resolved} oratio @-references.")\n',
    '\n',
    '    # FERIAL ORATIO FALLBACK\n',
    '    # Some feast rows have no oratio; fill from the weekday table by parsing the source file date.\n',
    '\n',
    '    def _file_to_ferial_wd(file_path: str):\n',
    '        m = re.search(r"/tempora/(\d{3})-(\d)$", file_path)\n',
    '        if m:\n',
    '            return int(m.group(2))\n',
    '        m = re.search(r"/(?:sancti|commune)/(\d{2})-(\d{2})", file_path)\n',
    '        if m:\n',
    '            try:\n',
    '                return calendar.weekday(2000, int(m.group(1)), int(m.group(2)))\n',
    '            except ValueError:\n',
    '                return None\n',
    '        return None\n',
    '\n',
    '    filled = 0\n',
    '    rows = conn.execute(\n',
    '        "SELECT id, file, office_type FROM divine_office "\n',
    '        "WHERE lectio_1 IS NOT NULL AND lectio_1 != \'\' "\n',
    '        "AND (oratio IS NULL OR oratio = \'\' ) "\n',
    '        "AND office_type IN (\'Laudes\', \'Vespers\', \'Matins\')"\n',
    '    ).fetchall()\n',
    '    for row_id, file_path, otype in rows:\n',
    '        wd = _file_to_ferial_wd(file_path)\n',
    '        if wd is not None and wd in FERIAL_ORATIOS:\n',
    '            fb_orat = FERIAL_ORATIOS[wd].get(otype)\n',
    '            if fb_orat:\n',
    '                conn.execute(\n',
    '                    "UPDATE divine_office SET oratio=? WHERE id=?",\n',
    '                    (fb_orat, row_id)\n',
    '                )\n',
    '                filled += 1\n',
    '    print(f"  Filled {filled} oratios from ferial fallback.")\n',
    '\n',
]
replace_lines(main_line, main_line, fallback_code, "P7: oratio resolver + ferial fallback")

# ── WRITE ────────────────────────────────────────────────────────────
with open('scripts/compile_content.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"\n✓ All {len(changes)} patches applied:")
for c in changes:
    print(f"  ✓ {c}")

# Syntax check
import ast
try:
    ast.parse(''.join(lines))
    print("\n✓ Syntax check passed!")
except SyntaxError as e:
    print(f"\n✗ SyntaxError at line {e.lineno}: {e.msg}")
    for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
        print(f"  {i+1}: {lines[i].rstrip()[:120]}")
    sys.exit(1)
