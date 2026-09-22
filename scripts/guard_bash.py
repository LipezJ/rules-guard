#!/usr/bin/env python3
"""rules-guard (PreToolUse/Bash): detects file edits made through the shell
(sed -i, redirections, tee, heredocs, python -c writes) and asks Claude to use Edit/Write
instead, so path-scoped rules and Read/Edit/Write hooks fire again.

Denies via JSON so the reason reaches Claude AND the user (systemMessage), instead of
exit 2, whose stderr only ever reaches Claude.
Set RG_BASH_GUARD=off to disable.
"""
import json, os, re, sys

PATTERNS = [
    (r"\bsed\s+(-[a-zA-Z]*\s+)*-i\b|\bsed\s+-i", "sed -i"),
    (r"\bperl\s+-[a-zA-Z]*i", "perl -i"),
    (r"\btee\s+(?!-a?\s*/dev/null)", "tee"),
    (r">>?\s*(?!/dev/null|&\d)[^\s|;&<>]+", "redirect to file"),
    (r"<<\s*'?[A-Za-z_]+'?", "heredoc"),
    (r"\b(python3?|node)\s+-[ce]\b", "inline script that may write"),
    (r"\b(cp|mv)\s+[^|;&]*\s+[^\s|;&]+", "cp/mv over repo files"),
]
# commands where a redirect is routine and not a source edit
SAFE_PREFIX = re.compile(r"^\s*(git|grep|rg|ls|find|cat\s+[^>]*$|echo\s+[^>]*$|npm|pnpm|yarn|pytest|make|docker|curl)\b")


def main():
    if os.environ.get("RG_BASH_GUARD", "on").lower() == "off":
        return 0
    event = json.load(sys.stdin)
    cmd = (event.get("tool_input") or {}).get("command", "")
    if not cmd:
        return 0

    hits = []
    for part in re.split(r"&&|\|\||;|\n", cmd):
        if not part.strip() or SAFE_PREFIX.match(part):
            continue
        for rx, name in PATTERNS:
            if re.search(rx, part):
                hits.append(name)
                break
    if not hits:
        return 0

    what = ", ".join(sorted(set(hits)))
    reason = ("rules-guard: this command looks like it edits files from Bash (" + what + "). "
              "Use the Edit/Write/Read tools instead: shell edits bypass path-scoped .claude/rules "
              "and the project's hooks. If the command is genuinely needed (builds, generated files, "
              "tool output), tell the user why and retry with RG_BASH_GUARD=off in the environment.")
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "PreToolUse",
                               "permissionDecision": "deny",
                               "permissionDecisionReason": reason},
        "systemMessage": f"rules-guard blocked a Bash file edit ({what}). Asked Claude to use Edit/Write instead.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
