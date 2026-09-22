# rules-guard

Makes `.claude/rules` actually stick, no matter which tool Claude uses to edit.

Claude Code attaches path-scoped rules (and nested `CLAUDE.md`) when it reads a matching file
with the **Read** tool. In auto and bypass permission modes it is often steered to use Bash
instead (`cat`, `sed -i`, heredocs), so those rules never load and `Read|Edit|Write` hooks
never fire. This plugin closes that gap.

## What it does

| Event | Handler | Purpose |
|---|---|---|
| `SessionStart` | `inject_rules.py` | Loads every rule into context, including `paths:`-scoped ones |
| `PreToolUse(Bash)` | `guard_bash.py` | Catches shell edits (`sed -i`, heredocs, redirects) and asks for Edit/Write |
| `PreToolUse(Bash)` | `guard_commit.py` | Blocks commits carrying Claude attribution trailers |
| `PostToolUse(Edit/Write)` | prompt (Haiku) | Fast, cheap review of the file just written |
| `Stop` | agent (Sonnet) | Validates the turn's `git diff` against the rules |

## Install

Local, for testing:

```
claude --plugin-dir /path/to/rules-guard
```

As a marketplace (own repo, with `.claude-plugin/marketplace.json` at the root):

```
/plugin marketplace add https://github.com/LipezJ/rules-guard.git
/plugin install rules-guard@rules-guard-marketplace
```

Then, inside your project:

```
/rules-guard:install
```

## What the plugin cannot do by itself

- Write your `settings.json` (`includeCoAuthoredBy`, `attribution`, `CLAUDE_CODE_THRIFTY_SONIC`).
- Install `.git/hooks/commit-msg`.

`/rules-guard:install` walks through both, or do it by hand with `settings.example.json` and
`cp git-hooks/commit-msg .git/hooks/`.

## Writing rules

Put markdown files in `.claude/rules/`. Each bullet is treated as one rule. Optional frontmatter
scopes a file to certain paths:

```markdown
---
paths:
  - "src/**/*.ts"
---
- Do not use console.log; use the logger module
- Business logic does not belong in controllers
```

Rules without `paths:` apply everywhere.

## Options

- `RG_BASH_GUARD=off` — disable the Bash guard when you really do need shell edits.
- `RG_RULES_MAX_CHARS` — cap how much rule text is injected at session start (default 20000).
- Cost-sensitive? Drop the `PostToolUse` block and keep only `Stop`.

## Requirements

`python3` on PATH, and `git` for the `Stop` check. On Windows without WSL, change `python3` to
`python` in `hooks/hooks.json`.

## Notes

- `CLAUDE_CODE_THRIFTY_SONIC=0` is an undocumented internal flag reported by the community to
  disable the Bash-first steering. It may change or disappear; the hooks here do not depend on it.
- The Bash guard is heuristic and can produce false positives on build scripts. Tune
  `SAFE_PREFIX` in `scripts/guard_bash.py` for your project.

## License

MIT
