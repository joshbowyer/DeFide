#!/usr/bin/env python3
"""Comprehensive patch: add re/calendar imports, FERIAL_ORATIOS module dict, oratio fallback."""
import re, sys

with open('scripts/compile_content.py', 'r', encoding='utf-8') as f:
    src = f.read()

# ── 1. Add import re and import calendar at module level ──────────────────────
if 'import re\n' not in src and 'import re;' not in src:
    src = src.replace(
        'import sys\n',
        'import sys\nimport re\nimport calendar\n'
    )
    print("✓ Added import re and import calendar")
else:
    print("✓ re/calendar already imported")

# ── 2. Add FERIAL_ORATIOS module-level dict ────────────────────────────────
if 'FERIAL_ORATIOS: dict[int, dict[str, str]] = {}' not in src:
    src = src.replace(
        'REPO_ROOT = ',
        '# Ferial oratios: day → office_type → oratio text (populated at runtime)\n'
        'FERIAL_ORATIOS: dict[int, dict[str, str]] = {}\n\n'
        'REPO_ROOT = '
    )
    print("✓ Added FERIAL_ORATIOS declaration")
else:
    print("✓ FERIAL_ORATIOS already declared")

# ── 3. Populate FERIAL_ORATIOS inside _do_divine_office_backfill ──────────
# Insert after "FERIAL_ROWS = [" block closes (inside the function)
ferial_rows_end_marker = 'FERIAL_ROWS = [\n        (0, "Laudes",'
# Find the end of FERIAL_ROWS (the closing "    ]")
fr_start = src.find(ferial_rows_end_marker)
if fr_start < 0:
    print("✗ FERIAL_ROWS start not found!")
    sys.exit(1)

# Find the closing "]"
fr_end = src.find('\n    ]', fr_start)
if fr_end < 0:
    print("✗ FERIAL_ROWS closing ] not found!")
    sys.exit(1)
fr_end += len('\n    ]')

init_code = '''
    # Populate FERIAL_ORATIOS from FERIAL_ROWS for the oratio fallback step
    for _d, _o, _t, _orat in FERIAL_ROWS:
        FERIAL_ORATIOS.setdefault(_d, {})[_o] = _orat
'''
src = src[:fr_end] + init_code + src[fr_end:]
print("✓ Added FERIAL_ORATIOS initialization after FERIAL_ROWS")

# ── 4. Add post-processing fallback after oratio @-resolution ─────────────────
fallback_code = '''
    # ── FERIAL ORATIO FALLBACK ───────────────────────────────────────────
    # Some feast rows (octaves, commemorations, ferial tempora) have no oratio in the
    # source dataset — the feast itself doesn't define one. We fall back to the
    # appropriate ferial (weekday) collect keyed to the day-of-week.
    #
    # Tempora files encode weekday in filename: "083-5" → weekday 5 (Sat).
    # Sancti/commune files: use actual calendar weekday as heuristic.

    def _file_to_ferial_wd(file_path: str) -> int | None:
        m = re.search(r'/tempora/(\d{3})-(\d)$', file_path)
        if m:
            return int(m.group(2))  # 0=Sun, 6=Sat
        m = re.search(r'/(?:sancti|commune)/(\d{2})-(\d{2})', file_path)
        if m:
            try:
                return calendar.weekday(2000, int(m.group(1)), int(m.group(2)))
            except ValueError:
                return None
        return None

    filled = 0
    for row_id, file_path, otype in conn.execute(
        "SELECT id, file, office_type FROM divine_office "
        "WHERE lectio_1 IS NOT NULL AND lectio_1 != '' "
        "AND (oratio IS NULL OR oratio = '') "
        "AND office_type IN ('Laudes', 'Vespers', 'Matins')"
    ):
        wd = _file_to_ferial_wd(file_path)
        if wd is not None and wd in FERIAL_ORATIOS:
            fallback_orat = FERIAL_ORATIOS[wd].get(otype)
            if fallback_orat:
                conn.execute(
                    "UPDATE divine_office SET oratio=? WHERE id=?",
                    (fallback_orat, row_id)
                )
                filled += 1
    print(f"  Filled {filled} oratios from ferial fallback.")
'''

# Find "print(f"  Resolved {orat_resolved} oratio @-references.")" and insert after
insert_after = '    print(f"  Resolved {orat_resolved} oratio @-references.")'
if insert_after in src:
    src = src.replace(insert_after, insert_after + fallback_code)
    print("✓ Added ferial oratio fallback after oratio resolution")
else:
    print("✗ Could not find insertion point!")
    sys.exit(1)

with open('scripts/compile_content.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("\nAll patches applied to compile_content.py")
