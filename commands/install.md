---
description: Finish the rules-guard setup (settings.json and the git commit-msg hook)
allowed-tools: Read, Edit, Write, Bash(git config:*), Bash(cp:*), Bash(chmod:*), Bash(ls:*)
---

Finish installing rules-guard in this repo. The plugin hooks are already active; what is
left is what a plugin cannot touch on its own. Do this and report back:

1. Read `.claude/settings.json` (create it if missing) and merge in, without dropping
   anything already there:
   - `"includeCoAuthoredBy": false`
   - `"attribution": { "coAuthoredBy": false }`
   - `"env": { "CLAUDE_CODE_THRIFTY_SONIC": "0" }`
   If a key already exists with a different value, do NOT overwrite it: flag it and ask.

2. Install the git hook that strips Claude attribution trailers, but check the hook path first:
   run `git config --get core.hooksPath`.
   - If it returns a path (e.g. `.githooks`), `.git/hooks/` is NOT used by this repo. Do not
     install there. Look at `<hooksPath>/commit-msg`: if it already handles Claude attribution,
     report that and change nothing. If it exists but does not, show it and ask before editing.
     If it does not exist, offer to copy the plugin's hook into `<hooksPath>/commit-msg`.
   - If it returns nothing, install into `.git/hooks/`:
     `cp "${CLAUDE_PLUGIN_ROOT}/git-hooks/commit-msg" .git/hooks/commit-msg && chmod +x .git/hooks/commit-msg`
     If `.git/hooks/commit-msg` already exists, do NOT overwrite it: show the current one and ask.

3. Check that `.claude/rules/` exists and holds at least one `.md` file. If not, say so and
   offer to create a starter rule.

4. Summarise in 3 lines: what was configured, what is still pending, and how to test it.
