---
description: Finish the rules-guard setup (settings, git commit-msg hook) and re-check it later
allowed-tools: Read, Edit, Write, Bash(git config:*), Bash(cp:*), Bash(chmod:*), Bash(ls:*), Bash(rm:*)
---

Finish installing rules-guard in this repo, or re-check an existing install. Everything below is
idempotent: run it again any time. Report what you found and what you changed.

1. Settings. These three keys are what rules-guard expects:
   - `"includeCoAuthoredBy": false`
   - `"attribution": { "coAuthoredBy": false }`
   - `"env": { "CLAUDE_CODE_THRIFTY_SONIC": "0" }`

   Read BOTH `.claude/settings.json` (shared, committed) and `.claude/settings.local.json`
   (personal, usually gitignored) before writing anything. A key already present in EITHER file
   at the expected value is done: leave it where it is and do not copy it to the other file.
   Only add what is missing, and merge without dropping existing keys. If a key exists with a
   different value, do not overwrite it: flag it and ask.

   Where to add a missing key: `includeCoAuthoredBy` and `attribution` are repo policy, so they
   belong in `.claude/settings.json`. `CLAUDE_CODE_THRIFTY_SONIC` is an undocumented internal
   flag and a personal choice, so prefer `.claude/settings.local.json`; if that file is not
   gitignored, say so and ask first.

2. Git commit-msg hook. Check the hook path first: `git config --get core.hooksPath`.
   - If it returns a path (e.g. `.githooks`), `.git/hooks/` is NOT used by this repo. Do not
     install there. Look at `<hooksPath>/commit-msg`: if it already handles Claude attribution,
     report that and change nothing. If it exists but does not, show it and ask before editing.
     If it does not exist, offer to copy the plugin's hook into `<hooksPath>/commit-msg`.
     Then check for a stale `.git/hooks/commit-msg` left by an earlier run or another tool: it
     is inert today, but it would activate silently if anyone unsets `core.hooksPath`. Report it
     and offer to delete it.
   - If it returns nothing, install into `.git/hooks/`:
     `cp "${CLAUDE_PLUGIN_ROOT}/git-hooks/commit-msg" .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg`
     If `.git/hooks/commit-msg` already exists, do NOT overwrite it: show the current one and ask.

3. Rules. Check that at least one rule file exists in `.claude/rules/`, `~/.claude/rules/` or a
   nested `<subdir>/.claude/rules/`. If none, say so and offer to create a starter rule.

4. Summarise in 3 lines: what was already correct, what you changed, and what needs your call.
