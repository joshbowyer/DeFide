#!/usr/bin/env python3
"""Patch compile_content.py: add oratio reference resolver."""
import re, sys

with open('scripts/compile_content.py', 'r', encoding='utf-8') as f:
    src = f.read()

oratio_resolver_code = r'''
    # ── Oratio (collect) reference resolver ─────────────────────────────────────
    # Resolves @Tempora/, @Sancti/, @Commune/ refs in the Oratio field
    # against the already-built hymn_file_index (which indexes all Latin .txt files).
    #
    # Reference format examples:
    #   @Tempora/Nat1-0           → file Latin/Tempora/Nat1-0.txt, section [Oratio]
    #   @Sancti/02-22:Oratio      → file Latin/Sancti/02-22.txt, section [Oratio]
    #   @Commune/C4-1             → file Latin/Commune/C4-1.txt, section [Oratio]
    #
    # Some refs carry "s/SEARCH/REPLACE/" substitution syntax (for antiphons);
    # the collect itself is stored plain so we just strip the substitution part.

    def _resolve_oratio_ref(ref: str, _seen: set | None = None) -> str:
        """Resolve an @Tempora/ or @Sancti/ or @Commune/ oratio reference."""
        if _seen is None:
            _seen = set()
        if not ref or not ref.startswith("@"):
            return ref
        if ref in _seen:
            return ref
        _seen.add(ref)

        # Strip any trailing ::s/ substitution (collects don't use them)
        core = ref.lstrip("@")
        if "::" in core:
            core = core.split("::")[0]

        # Parse file_part and optional section hint
        if ":" in core:
            file_part, _sec_hint = core.split(":", 1)
        else:
            file_part, _sec_hint = core, "Oratio"

        file_part = file_part.strip()
        # e.g. "Tempora/Nat1-0" → "Nat1-0.txt"
        fn = file_part.split("/")[-1] + ".txt"

        sections = hymn_file_index.get(fn, {})
        if not sections:
            return ref  # file not found

        # Find [Oratio] section — exact match first, then case-insensitive scan
        if "Oratio" in sections:
            text = "\n".join(sections["Oratio"])
            if text:
                return text

        for sec_name, lines in sections.items():
            if "oratio" in sec_name.lower() and lines:
                return "\n".join(lines)

        return ref  # no [Oratio] section found

    def _post_resolve_oratio(conn):
        """Scan rows with @-prefixed oratio and resolve them in-place."""
        cu = conn.execute(
            "SELECT id, oratio FROM divine_office WHERE oratio LIKE '@%'"
        )
        rows = cu.fetchall()
        if not rows:
            return 0
        resolved = 0
        for row_id, oratio_ref in rows:
            resolved_text = _resolve_oratio_ref(oratio_ref)
            if resolved_text != oratio_ref:
                conn.execute(
                    "UPDATE divine_office SET oratio=? WHERE id=?",
                    (resolved_text, row_id),
                )
                resolved += 1
        return resolved

    print("  Resolving oratio @-references...")
    orat_resolved = _post_resolve_oratio(conn)
    print(f"  Resolved {orat_resolved} oratio @-references.")
'''

# Find the exact insertion point
insert_before = '\ndef main()'
# Go back to just after the cross-file resolution print
marker = '    print(f"    Cross-file @ ref resolution: {cross_resolved} rows resolved.")'

# Count occurrences
count = src.count(marker)
print(f"Found {count} occurrence(s) of marker")

if count == 1:
    # Replace the marker + the next \n\ndef main() with marker + oratio_resolver + \ndef main()
    old = marker + '\n\n\ndef main()'
    new = marker + oratio_resolver_code + '\n\n\ndef main()'
    if old in src:
        src = src.replace(old, new)
        print("✓ Inserted oratio resolver (3-newline form)")
    else:
        # Try with 2 newlines
        old2 = marker + '\n\ndef main()'
        new2 = marker + oratio_resolver_code + '\n\ndef main()'
        if old2 in src:
            src = src.replace(old2, new2)
            print("✓ Inserted oratio resolver (2-newline form)")
        else:
            print("✗ Standard marker not found — searching...")
            idx = src.find('cross_resolved} rows resolved.')
            print(f"Context: {repr(src[idx:idx+150])}")
else:
    print(f"Warning: {count} occurrences — finding right one")
    # Find the one inside _do_divine_office_backfill (before def main)
    idx_main = src.find('\ndef main()')
    idx_marker = src.rfind(marker, 0, idx_main)
    print(f"Inserting at index {idx_marker}")
    old = src[idx_marker:idx_main]
    # Build new: keep marker + oratio resolver + \ndef main()
    src = src[:idx_marker] + marker + oratio_resolver_code + '\n' + src[idx_marker:idx_marker+len(marker)] + src[idx_marker+len(marker):]
    # That approach is messy — just find and replace the block
    # Actually let's find the exact context
    idx = src.find('\ndef main()')
    before = src[idx-300:idx]
    print(f"300 chars before def main(): {repr(before)}")

with open('scripts/compile_content.py', 'w', encoding='utf-8') as f:
    f.write(src)
print("Done.")
