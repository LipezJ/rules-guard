#!/usr/bin/env python3
"""rules-guard (PreToolUse/Bash): blocks commits carrying Claude attribution trailers.
Complements includeCoAuthoredBy/attribution, which several issues report is not always honored
when the commit message is hand-built from Bash. Exit 2 => blocked, and Claude reads why."""
import json, re, sys

MARKERS = [
    (r"Co-?Authored-?By:\s*Claude", "Co-Authored-By: Claude"),
    (r"Generated with \[?Claude Code", "Generated with Claude Code"),
    (r"noreply@anthropic\.com", "noreply@anthropic.com"),
    (r"\U0001F916\s*Generated", "attribution emoji"),
]


def main():
    event = json.load(sys.stdin)
    cmd = (event.get("tool_input") or {}).get("command", "")
    if not cmd or not re.search(r"\bgit\b[^|;&]*\bcommit\b", cmd):
        return 0
    hits = [name for rx, name in MARKERS if re.search(rx, cmd, re.IGNORECASE)]
    if not hits:
        return 0
    print("rules-guard: this commit carries Claude attribution (" + ", ".join(hits) + ").\n"
          "This repo does not use it. Redo the commit with a clean message: no Co-Authored-By "
          "trailer and no 'Generated with Claude Code' line.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
