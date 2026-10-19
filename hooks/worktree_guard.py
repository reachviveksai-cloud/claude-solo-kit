"""PreToolUse hook: one Claude session per copy of the code.

When several sessions share one checkout, they sweep each other's
half-finished work into commits, reset branches under each other, and a
single `git add -A` can ship someone else's draft. So for each project in
kit.config.json with protect_main_checkout set:

  "edit"    Edit/Write in the main checkout is refused, and so is `git commit`.
  "commit"  editing is allowed, but `git commit` in the main checkout is refused.

A git worktree (whose `.git` is a file) is never blocked: that's the point.
The refusal message says how to make one.

Escape hatch, only when the user explicitly says so: put SHARED_CHECKOUT_OK=1
in the Bash command. FAIL-OPEN: any error inside this script allows the action.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit_config import load_projects, main_checkout_root, norm, resolve  # noqa: E402

_LEAD = r"(?:^|[;&|\n(){}]|&&|\|\|)\s*"
GIT_COMMIT = re.compile(_LEAD + r"git\s+(?:-C\s+(\"[^\"]+\"|'[^']+'|\S+)\s+)?commit\b")
CD = re.compile(r"(?:^|[;&|\n]|&&)\s*cd\s+(\"[^\"]+\"|'[^']+'|\S+)")


def guarded(path, projects, modes):
    """The project whose MAIN checkout holds `path`, if its mode is in `modes`."""
    root = main_checkout_root(path)
    if not root:
        return None
    for p in projects:
        if p["root"] == root and p.get("protect_main_checkout", "off") in modes:
            return p
    return None


def how_to(p):
    root = p["root"]
    sibling = os.path.join(os.path.dirname(root), os.path.basename(root) + "-<task>")
    return (f'git -C "{root}" worktree add "{sibling}" -b <branch>\n'
            f"Work and commit there, then remove it: "
            f'git -C "{root}" worktree remove "{sibling}"')


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason}}))


def main():
    try:
        hook = json.load(sys.stdin)
        projects = load_projects()
        if not projects:
            return 0
        tool = hook.get("tool_name", "")
        inp = hook.get("tool_input") or {}
        if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
            path = inp.get("file_path") or inp.get("notebook_path") or ""
            p = guarded(os.path.dirname(norm(path)), projects, ("edit",)) if path else None
            if p:
                deny(f"one session per copy: this is the SHARED main checkout of "
                     f"{p['name']}, where other sessions may be working. Make your "
                     f"own worktree and edit there instead:\n  {how_to(p)}")
            return 0
        if tool == "Bash":
            cmd = inp.get("command", "")
            m = GIT_COMMIT.search(cmd)
            if not m or "SHARED_CHECKOUT_OK=1" in cmd:
                return 0
            cwd = hook.get("cwd") or ""
            if m.group(1):
                where = m.group(1)
            else:
                cds = CD.findall(cmd[:m.start()])
                where = cds[-1] if cds else cwd
            p = guarded(resolve(where, cwd), projects, ("edit", "commit"))
            if p:
                deny(f"one session per copy: `git commit` in the SHARED main "
                     f"checkout of {p['name']} can sweep other sessions' work into "
                     f"your commit. Commit from your own worktree:\n  {how_to(p)}\n"
                     f"Only if the user explicitly says so, add SHARED_CHECKOUT_OK=1.")
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
