# DeFide — Claw Code Persistent Instructions

## Context Compaction Rules

**CRITICAL: Never nest summaries during compaction.**

When Claw Code performs context compaction (summarizing older messages to free up context
window space), the summary **must be a flat, standalone document**. Do NOT prepend or
nest the old summary inside the new one.

### ❌ Wrong (causes catastrophic nesting)
```
<summary>
Conversation summary:
- Previously compacted context:
  - Previously compacted context:
    - (nested summaries grow forever, eventually crash the session)
```

### ✅ Correct (flat and self-contained)
```
<summary>
Conversation summary:
- Project: DeFide Catholic faith app (Android/Kotlin/Jetpack Compose)
- Current task: [brief description of what's happening]
- Key files: [list of relevant files]
- Last action taken: [what was just done]
- Next step: [what to do next]
</summary>
```

### Session Health Check

Before any compaction operation, verify the session file does not already contain nested
"Previously compacted context:" entries. If nested summaries are ever found, remove the
corrupted `compaction` entry entirely rather than allowing nesting to compound.

## Session / Todo Files

- `.claw/memory.md` — persistent session memory (auto-loaded by Claw Code)
- `.clawd-todos.json` — task list
- `.claw/sessions/` — session logs
- These are gitignored — do NOT commit them

## Build Commands

**IMPORTANT: Always use `dangerouslyDisableSandbox=true`** on every `bash` call, or the
shell will hit a ~180ms timeout and fail. This applies to all commands including Gradle,
adb, git, etc.

```bash
# Build debug APK
./buildApp.sh

# Direct Gradle (with sandbox disabled)
cd /home/josh/claw-code/DeFide && ANDROID_HOME="/home/josh/android-sdk" JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64" ./gradlew assembleDebug

# Compile content DB
cd /home/josh/claw-code/DeFide && python3 scripts/compile_content.py > /tmp/compile.log 2>&1
```

## Git

- Use SSH key `~/.ssh/id_ed25519_minimax`
- Upstream: `git@github.com:tristinbaker/DeFide.git`
- Work on feature branches, PR into main
- Do NOT commit binary DB files
- **Push requires**: `GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_minimax" git push`

## Divine Office Roadmap (2026-05-17)

### Phase 1 — Divine Office Language/Rite Toggle ✅ PLANNED
Toggle: Settings → "Office Rite / Language" → Modern / Semi-Traditional / Traditional
- `AppRite` enum in `UserPreferencesRepository.kt` with Modern/SemiTraditional/Traditional
- DB: add `language TEXT NOT NULL DEFAULT 'la'` to `divine_office`, `divine_office_calendar`, `divine_office_psalms`. Existing rows = `'la'`
- Compiler: read `Latin/` and `English/` source dirs; insert both as separate rows with distinct `language` values. Map rite: Latin=Traditional, English=Modern
- Kotlin model: add `language: String` to `DivineOffice`, `DivineOfficeCalendar`
- DAO: add `language` param to all queries; filter by `language` in `getOfficesByFiles`, `getAllOfficesForDay`, `getCalendarEntry`
- Repository: thread rite/language through `getAllOfficesForDate(date, rite)`
- UI: add toggle to Settings screen (Section: Divine Office Rite). Pass rite to DivineOfficeHomeScreen → DivineOfficeReaderScreen
- Later: expand to Rosary (Latin/vernacular per mystery), Bible (DRA vs WEB-C), Prayers

### Phase 2 — Fix Completorium Content
Completorium rows exist (7 rows) but antiphon/hymn/lectio/responsory/capitulum are all NULL.
- Source `.txt` files have: `[Ant Completorium]`, `[Hymnus Completorium]`, `[Hymnus Completorium_C]`, `[Lectio Completorium]`, `[Responsorium Completorium]`, `[Capitulum Completorium]`, `[Oratio Completorium]`
- Compiler Completorium branch needs to map these fields to named columns
- Oratio is already populated — verify the mapping is correct

### Phase 3 — Ferial Oratio Fallback (~600-800 missing collects)
- `FERIAL_ORATIOS` dict in `compile_content.py` is defined but never populated
- Extract weekday collects from Tempora ferial files (one-time extraction)
- Backfill: `UPDATE divine_office SET oratio=? WHERE lectio_1 IS NOT NULL AND oratio IS NULL`
- ~128 remaining sancti without oratio: manual entry or Universalis lookup (lower priority)

### Phase 4 — 7-Day Completorium Ferial Cycle
Currently only 1 ferial Completorium row exists (all 7 days share it).
- Compiler loop: generate 7 ferial Completorium rows (day 0=Sunday … day 6=Saturday)
- Sources: Latin/Psalterium/Special/Completorium.txt for ferial antiphons + hymns

### Phase 5 — Antiphon Field Mapping (27% coverage → higher)
Only 27% of rows have antiphons in `antiphon_1`. Source files use varied field names.
- Need wider field-name matching in compiler: `Antiphona1`, `Ant 1`, `Ant1`, `Antiphon`, `Antiphon 1`, etc.
- Also check `matins_antiphon` / `matinsAntiphon` mappings

### Phase 6 — Expand Rite Toggle to Rosary
Rosary already has Latin/vernacular toggle infrastructure (RosaryOrder, mystery-level toggle).
- Add `AppRite` to prayer display logic
- Latin mysteries from `Latin/Mysteriorum.txt`; vernacular from `English/Mysteriorum.txt`
