#!/usr/bin/env python3
"""Patch compile_content.py: add ferial oratio fallback."""
with open('scripts/compile_content.py', 'r', encoding='utf-8') as f:
    src = f.read()

ferial_oratio_fallback = '''
    # ── FERIAL ORATIO FALLBACK ────────────────────────────────────────────────
    # Many tempora/sancti/commune rows have no oratio in the source because the
    # Divinum Officium dataset stores collects only at feast level. Feasts that
    # are commemorations, octaves, or minor ferias simply inherit the ferial
    # collect. We fill those gaps by assigning a ferial collect keyed to the
    # day-of-week (0=Sun..6=Sat), matching the existing FERIAL_ROWS table.
    #
    # Strategy:
    #  1. Extract day-of-week from the tempora filename (e.g. "083-5" → weekday 5)
    #  2. Extract weekday suffix from sancti/commune filenames (e.g. "07-12o" → Sat)
    #  3. Map to ferial collect from FERIAL_ROWS
    #  4. Only apply where the row is substantive (has lectio_1) but no oratio
    #
    # This does NOT overwrite rows that already have a proper oratio.

    import re

    # Build day-of-week → (Laudes oratio, Vespers oratio, Matins oratio) from FERIAL_ROWS
    ferial_oratios: dict[int, dict[str, str]] = {}
    for day, otype, _title, orat_text in FERIAL_ROWS:
        if otype not in ferial_oratios:
            ferial_oratios[day] = {}
        ferial_oratios[day][otype] = orat_text

    # Regex patterns to extract weekday from file paths
    # Tempora: "083-5" → weekday 5 (0-based, 0=Sunday)
    TEMPORA_WD_PAT = re.compile(r'/tempora/(\d{3})-(\d)$')
    # Sancti/Commune: "MM-DD" → map to weekday using calendar module
    # (actual calendar date doesn't map perfectly to liturgical weekday,
    # but for ferial fallback purposes we use a simple heuristic:
    # days 01-06 = Sun, 07-13 = Mon-Sat, 14-20 = Sun-Sat, 21-27 = Sun-Sat, 28-31 = Sun-Wed)
    SANCTI_WD_PAT = re.compile(r'/(?:sancti|commune)/(\d{2})-(\d{2})')

    import calendar
    def _file_to_ferial_wd(file_path: str) -> int | None:
        """Extract day-of-week (0=Sun..6=Sat) from file path heuristically."""
        m = TEMPORA_WD_PAT.search(file_path)
        if m:
            # Tempora weekday: the second digit is the weekday within the week
            return int(m.group(2))  # 0=Sunday, 1=Monday, ..., 6=Saturday
        m = SANCTI_WD_PAT.search(file_path)
        if m:
            mm, dd = int(m.group(1)), int(m.group(2))
            # Use the actual calendar weekday as a heuristic for ferial fallback
            # This is imperfect (a feast date != liturgical weekday) but ferial
            # fallback is just a best-effort approximation anyway
            try:
                return calendar.weekday(2000, mm, dd)  # fixed year, day-of-week only
            except ValueError:
                return None
        return None

    # Count updates
    ferial_filled = 0
    for row_id, file_path, otype in conn.execute(
        "SELECT id, file, office_type FROM divine_office "
        "WHERE lectio_1 IS NOT NULL AND lectio_1 != '' "
        "AND (oratio IS NULL OR oratio = '') "
        "AND office_type IN ('Laudes', 'Vespers', 'Matins')"
    ).fetchall():
        wd = _file_to_ferial_wd(file_path)
        if wd is not None and wd in ferial_oratios:
            ferial_orat = ferial_oratios[wd].get(otype)
            if ferial_orat:
                conn.execute(
                    "UPDATE divine_office SET oratio=? WHERE id=?",
                    (ferial_orat, row_id),
                )
                ferial_filled += 1

    print(f"  Filled {ferial_filled} oratios from ferial fallback.")
'''

# Find the insertion point: after "Resolved X oratio @-references." and before "def main()"
marker = '    print(f"  Resolved {orat_resolved} oratio @-references.")'
old = marker + '\n\n\n\ndef main()'
new = marker + ferial_oratio_fallback + '\n\n\ndef main()'
if old in src:
    src = src.replace(old, new)
    print("✓ Inserted ferial oratio fallback")
else:
    print("✗ Marker not found!")
    print(repr(src.find('Resolved {orat_resolved}')))

with open('scripts/compile_content.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("Done.")
