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
