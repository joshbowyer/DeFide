# Working in this workspace

## Workspace boundary note

The `read_file` and `edit_file` tools are blocked from accessing files outside `/home/josh/claw-code/test`. This workspace (`/home/josh/claw-code/DeFide`) is outside that boundary, so those tools will fail with:

```
error path ... escapes workspace boundary /home/josh/claw-code/test
```

## How to edit files

Use `bash` with Python heredocs for all file operations in this directory. Examples:

```bash
# Read a section of a file
sed -n '3100,3140p' /home/josh/claw-code/DeFide/scripts/compile_content.py

# Edit with Python
python3 - << 'PYEOF'
with open('scripts/compile_content.py', encoding='utf-8') as f:
    content = f.read()
content = content.replace('old_string', 'new_string')
with open('scripts/compile_content.py', 'w', encoding='utf-8') as f:
    f.write(content)
PYEOF

# Verify syntax after edits
python3 -c "import ast; ast.parse(open('scripts/compile_content.py').read())"
```

## Long-running scripts

`compile_content.py` takes several minutes (processes Bibles, Divine Office, catechisms, etc.). Always use `run_in_background: true` or `subprocess.Popen` so it isn't killed by short timeouts:

```bash
python3 -c "
import subprocess
proc = subprocess.Popen(
    ['python3', 'scripts/compile_content.py'],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
)
for line in proc.stdout:
    if 'ERROR' in line or 'Done' in line:
        print(line, end='')
proc.wait()
"
```

## Key gotchas for compile_content.py

- The `divine_office`, `divine_office_calendar`, and `divine_office_psalms` tables all have a `language TEXT NOT NULL` column — all INSERTs and WHERE clauses must include it.
- The main `divine_office` INSERT has 41 columns. When adding new fields, make sure the VALUES tuple has exactly 41 placeholders.
- Use `AST parsing` (`ast.parse`) to validate the file after making edits, not just syntax checks.
- Delete stale DB files before re-running: `rm -f app/src/main/assets/databases/defide_content.db*`

## Traditional Rite Content Specification (2026-05-22)

### Rosary
- **Latin mode**: Mystery titles (e.g. "Annuntiatio B. Mariae V.") and all prayers in Latin
- **Modern mode**: Mystery titles and all prayers in local language (English)
- **Traditional mode**: Mystery titles/scripture in local language (English); all prayers in Latin
  - The English mystery list is loaded separately (`englishMysteries` StateFlow in RosaryViewModel)
  - `currentRite` StateFlow exposes AppRite to the screen
  - Screen pulls English titles/scripture from `englishMysteries` when rite == TRADITIONAL

### Divine Office
- **Latin mode**: All content in Latin (DB `language='la'`)
- **Modern mode**: All content in local language (DB `language='en'`)
- **Traditional mode**: Mixed
  - English: hymn, psalms, scripture readings (lectio1/2/3)
  - Latin: invitatorium, antiphons, responsories, preces, oratio, conclusio
  - Our Father: Latin in Traditional, English in Modern
  - Examination of Conscience: Latin in Traditional, English in Modern
  - Regina Caeli: Latin only in Traditional, EN+Latin in Modern

### Implementation
- `DivineOfficeViewModel`: loads `currentRite`, `selectedOfficeLatin`, `selectedPsalmsLatin` for Traditional mode
- `DivineOfficeRepository`: new `getOfficesByFilesLatin()`, `getFerialPsalmsLatin()` methods
- `DivineOfficeReaderScreen`: all content functions accept `rite`, `officeLatin`, `psalmsLatin` params
  - `LaudesContent`, `VespersContent`, `MatinsContent`, `CompletoriumContent`, `DefaultOfficeContent` updated
  - Section composables (`OurFatherSection`, `ExaminationOfConscienceSection`, `AntiphonToMarySection`) accept `rite`
  - Latin constants added: `OUR_FATHER_LATIN`, `EXAMINATION_OF_CONSCIENCE_LATIN`
