#!/usr/bin/env python3
"""rules-guard (SessionStart): loads every rule in .claude/rules into the session context,
including files with a paths: frontmatter. In auto/bypass modes those path-scoped rules may
never load, because they are attached when Claude reads a matching file with the Read tool —
and in those modes Claude often reads with cat or sed instead."""
import glob, json, os, sys

MAX_CHARS = int(os.environ.get("RG_RULES_MAX_CHARS", "20000"))


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    project = os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd") or ".")
    paths = sorted(glob.glob(os.path.join(project, ".claude/rules/**/*.md"), recursive=True))
    if not paths:
        return 0

    parts = []
    for p in paths:
        rel = os.path.relpath(p, project)
        try:
            parts.append(f"### {rel}\n{open(p, encoding='utf-8').read().strip()}")
        except OSError:
            continue
    if not parts:
        return 0

    body = "\n\n".join(parts)[:MAX_CHARS]
    context = ("<project-rules>\nProject rules from .claude/rules. They apply to all work in this "
               "session, including edits made through Bash:\n\n" + body + "\n</project-rules>")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
