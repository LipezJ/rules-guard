#!/usr/bin/env python3
"""rules-guard (PreToolUse/Bash): detects file edits made through the shell
(sed -i, redirections, tee, heredocs, python -c writes) and asks Claude to use Edit/Write
instead, so path-scoped rules and Read/Edit/Write hooks fire again.

Denies via JSON so the reason reaches Claude AND the user (systemMessage), instead of
exit 2, whose stderr only ever reaches Claude.
Set RG_BASH_GUARD=off to disable.
"""
import json, os, re, sys

# Source-ish files: only edits to these are worth intercepting.
SOURCE_EXT = (r"(?:[A-Za-z0-9_.\-/]+\.(?:java|kt|kts|ts|tsx|js|jsx|py|rb|go|rs|c|h|cpp|cs|php|swift|"
              r"sql|sh|bash|zsh|yml|yaml|json|toml|xml|gradle|md|txt|env|conf|cfg|ini|properties))")

PATTERNS = [
    (r"\bsed\s+(-[a-zA-Z]*\s+)*-i\b|\bsed\s+-i", "sed -i"),
    (r"\bperl\s+-[a-zA-Z]*i", "perl -i"),
    (r"\btee\s+(?:-a\s+)?" + SOURCE_EXT, "tee into a file"),
    # a real file redirect; NOT `> /dev/null`, `>&2`, `> -` or a pipe into a command's stdin
    (r">>?\s*" + SOURCE_EXT, "redirect into a file"),
    # inline scripts only when they actually look like they write
    (r"\b(?:python3?|node)\s+-[ce]\b(?=[^|;&]*(?:open\s*\([^)]*['\"][wa]|writeFileSync|"
     r"write_text|>\s*[A-Za-z0-9_.\-/]+))", "inline script that writes files"),
    (r"\b(?:cp|mv)\s+[^|;&]*\s+" + SOURCE_EXT + r"\s*(?:$|[|;&])", "cp/mv onto a source file"),
]
# A heredoc on its own feeds a command's stdin (gh pr create --body-file -, git commit -F -):
# that is not a file edit. `cat > file <<EOF` is still caught by the redirect pattern above.

# commands where a redirect is routine and not a source edit
SAFE_PREFIX = re.compile(r"^\s*(git|gh|glab|grep|rg|ls|find|cat\s+[^>]*$|echo\s+[^>]*$|npm|pnpm|yarn|"
                         r"pytest|make|gradle|\./gradlew|mvn|docker|kubectl|curl|jq|awk|sort|uniq|head|tail)\b")


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
