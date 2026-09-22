#!/usr/bin/env python3
"""rules-guard (SessionStart): loads every rule Claude Code might otherwise miss into the
session context: user-level rules (~/.claude/rules), project rules (.claude/rules) and nested
rules in subdirectories (**/.claude/rules).

Path-scoped rules are normally attached when Claude reads a matching file with the Read tool.
In auto/bypass modes Claude is often steered to read with cat or sed instead, so they never
load at all. Injecting them up front removes that dependency."""
import glob, json, os, sys

MAX_CHARS = int(os.environ.get("RG_RULES_MAX_CHARS", "20000"))
MAX_DEPTH = int(os.environ.get("RG_NESTED_DEPTH", "4"))  # how deep to look for nested .claude/rules
SKIP_DIRS = {"node_modules", ".git", "build", "dist", "target", "vendor", ".venv", "venv"}


def rule_files(project):
    """(scope, absolute path) for every rule file, user-level first, then project, then nested."""
    found, seen = [], set()

    user_dir = os.path.join(os.path.expanduser("~"), ".claude", "rules")
    for p in sorted(glob.glob(os.path.join(user_dir, "**", "*.md"), recursive=True)):
        if p not in seen:
            seen.add(p)
            found.append(("user", p))

    root_dir = os.path.join(project, ".claude", "rules")
    for p in sorted(glob.glob(os.path.join(root_dir, "**", "*.md"), recursive=True)):
        if p not in seen:
            seen.add(p)
            found.append(("project", p))

    for depth in range(1, MAX_DEPTH + 1):
        pattern = os.path.join(project, *(["*"] * depth), ".claude", "rules", "**", "*.md")
        for p in sorted(glob.glob(pattern, recursive=True)):
            rel = os.path.relpath(p, project)
            if p in seen or any(part in SKIP_DIRS for part in rel.split(os.sep)):
                continue
            seen.add(p)
            found.append(("nested", p))

    return found


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        event = {}
    project = os.environ.get("CLAUDE_PROJECT_DIR", event.get("cwd") or ".")

    parts = []
    for scope, path in rule_files(project):
        if scope == "user":
            label = f"~/{os.path.relpath(path, os.path.expanduser('~'))} (user-level)"
        else:
            label = os.path.relpath(path, project)
        try:
            parts.append(f"### {label}\n{open(path, encoding='utf-8').read().strip()}")
        except OSError:
            continue
    if not parts:
        return 0

    body = "\n\n".join(parts)[:MAX_CHARS]
    context = ("<project-rules>\nRules from .claude/rules (user-level, project and nested). They apply "
               "to all work in this session, including edits made through Bash. A rule with a paths: "
               "frontmatter applies only to files matching those globs; a nested rule applies only "
               "within its own directory:\n\n" + body + "\n</project-rules>")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart",
                                             "additionalContext": context}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
