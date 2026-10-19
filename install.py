#!/usr/bin/env python3
"""Install the kit into ~/.claude without overwriting anything you already have.

    python3 install.py                 # install into ~/.claude
    python3 install.py --home /tmp/x   # install into /tmp/x/.claude (to try it out)

Every file is copied only if it doesn't exist yet. settings.json is backed up
first, then the kit's hooks are ADDED to it (existing hooks are kept, and
running the installer twice doesn't add them twice).
"""

import argparse
import json
import os
import shutil
import sys
import time

KIT = os.path.dirname(os.path.abspath(__file__))
SKILLS = ("feature-spec", "retro", "wait-what", "morning-brief")
HOOK_FILES = ("kit_config.py", "worktree_guard.py", "quality_gate.py")
EDIT_TOOLS = "Edit|Write|MultiEdit|NotebookEdit"

done, skipped = [], []


def fwd(p):
    return p.replace("\\", "/")


def copy(src, dst):
    if os.path.exists(dst):
        skipped.append(dst)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    done.append(dst)


def write_new(dst, text):
    if os.path.exists(dst):
        skipped.append(dst)
        return
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    done.append(dst)


def hook_key(command):
    """(script file name, trailing mode) — the same hook even if paths changed."""
    parts = command.split('"')
    if len(parts) < 3:
        return (command, "")
    return (os.path.basename(parts[-2]), parts[-1].strip())


def add_hook(settings, event, matcher, command, status):
    """Add one hook unless the same script and mode is already wired for this event and matcher."""
    key = hook_key(command)
    groups = settings.setdefault("hooks", {}).setdefault(event, [])
    for g in groups:
        if g.get("matcher") != matcher:
            continue
        for h in g.get("hooks", []):
            if hook_key(h.get("command", "")) == key:
                return False
    entry = {"type": "command", "command": command, "timeout": 15}
    if status:
        entry["statusMessage"] = status
    group = {"hooks": [entry]}
    if matcher:
        group["matcher"] = matcher
    groups.append(group)
    return True


def wire_settings(claude, hooks_dir):
    path = os.path.join(claude, "settings.json")
    settings = {}
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                settings = json.load(fh)
        except ValueError:
            print(f"!! {path} isn't valid JSON, so the hooks were NOT added. "
                  f"Fix it and run the installer again.")
            return
        backup = f"{path}.kit-backup-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(path, backup)
        done.append(backup)
    py = fwd(sys.executable)
    guard = f'"{py}" "{fwd(hooks_dir)}/worktree_guard.py"'
    gate = f'"{py}" "{fwd(hooks_dir)}/quality_gate.py"'
    added = [
        add_hook(settings, "PreToolUse", EDIT_TOOLS, guard, "Checking for a shared checkout..."),
        add_hook(settings, "PreToolUse", "Bash", guard, "Checking for a shared checkout..."),
        add_hook(settings, "PreToolUse", "Bash", gate + " commit", "Checking the quality gate..."),
        add_hook(settings, "Stop", None, gate + " stop", None),
    ]
    if not any(added):
        skipped.append(path + " (hooks already wired)")
        return
    os.makedirs(claude, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(settings, fh, indent=2)
        fh.write("\n")
    done.append(f"{path} ({sum(added)} hooks added)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--home", default=os.path.expanduser("~"),
                    help="folder that holds .claude (default: your home folder)")
    args = ap.parse_args()
    claude = os.path.join(os.path.abspath(os.path.expanduser(args.home)), ".claude")
    kit_dir = os.path.join(claude, "kit")
    hooks_dir = os.path.join(kit_dir, "hooks")

    for f in HOOK_FILES:
        copy(os.path.join(KIT, "hooks", f), os.path.join(hooks_dir, f))
    copy(os.path.join(KIT, "claude-md", "CLAUDE.kit.md"), os.path.join(kit_dir, "CLAUDE.kit.md"))
    for s in SKILLS:
        copy(os.path.join(KIT, "skills", s, "SKILL.md"), os.path.join(claude, "skills", s, "SKILL.md"))
    copy(os.path.join(KIT, "memory", "MEMORY.md"), os.path.join(claude, "memory", "MEMORY.md"))
    copy(os.path.join(KIT, "kit.config.example.json"), os.path.join(claude, "kit.config.json"))

    claude_md = os.path.join(claude, "CLAUDE.md")
    had_claude_md = os.path.exists(claude_md)
    write_new(claude_md, "@kit/CLAUDE.kit.md\n")

    wire_settings(claude, hooks_dir)

    print("Installed:")
    for d in done:
        print("  +", d)
    if skipped:
        print("Left alone (already there):")
        for s in skipped:
            print("  =", s)
    steps = [f"Edit {os.path.join(claude, 'kit.config.json')}: list your real project folders and test commands."]
    if had_claude_md:
        steps.append("You already had a CLAUDE.md. Add this line to it: @kit/CLAUDE.kit.md")
    steps.append("Restart Claude Code, then try /morning-brief.")
    print("\nNext:")
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
