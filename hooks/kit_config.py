"""Shared helpers for the kit's hooks: read kit.config.json, resolve paths and repos.

Config lives at ~/.claude/kit.config.json (or wherever KIT_CONFIG points):

    {
      "projects": [
        {
          "name": "my-app",
          "path": "~/code/my-app",
          "test_command": "npm test",
          "protect_main_checkout": "edit",
          "review_before_commit": false
        }
      ]
    }

protect_main_checkout: "edit" (no edits or commits in the main checkout),
"commit" (edits allowed, commits refused), or "off".
"""

import json
import os
import re

_repo_cache = {}


def config_path():
    return os.environ.get("KIT_CONFIG") or os.path.join(
        os.path.expanduser("~"), ".claude", "kit.config.json")


def _clean(p):
    p = (p or "").strip().strip("\"'")
    if os.name == "nt":
        m = re.match(r"^/([a-zA-Z])/(.*)$", p)
        if m:
            p = m.group(1).upper() + ":/" + m.group(2)
    return os.path.expanduser(p)


def norm(p):
    """A comparable absolute path. Handles ~, quotes and Git Bash /c/... on Windows."""
    p = _clean(p)
    return os.path.normcase(os.path.realpath(p)) if p else ""


def resolve(p, cwd):
    """Like norm(), but a relative path is taken relative to `cwd`, not to this process."""
    p = _clean(p)
    if p and not os.path.isabs(p) and cwd:
        p = os.path.join(_clean(cwd), p)
    return norm(p)


def repo_git(path):
    """The main .git dir of the repo `path` is in, or None.

    A linked worktree's `.git` is a FILE naming <main>/.git/worktrees/<x>, so
    every worktree resolves to the same main .git dir as its repo."""
    if not path:
        return None
    probe = norm(path)
    seen = []
    ans = None
    while True:
        if probe in _repo_cache:
            ans = _repo_cache[probe]
            break
        seen.append(probe)
        git = os.path.join(probe, ".git")
        if os.path.isdir(git):
            ans = norm(git)
            break
        if os.path.isfile(git):
            try:
                with open(git, encoding="utf-8") as fh:
                    gd = fh.read().split("gitdir:", 1)[1].strip()
                if not os.path.isabs(gd):
                    gd = os.path.join(probe, gd)
                gd = norm(gd)
                m = re.match(r"^(.*?[\\/]\.git)(?:[\\/]worktrees[\\/].*)?$", gd)
                ans = m.group(1) if m else gd
            except Exception:
                ans = None
            break
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    for s in seen:
        _repo_cache[s] = ans
    return ans


def main_checkout_root(path):
    """The repo root if `path` is inside a MAIN checkout (`.git` is a dir), else None.

    Stops at the first `.git` walking up, so a path inside a worktree
    (whose `.git` is a file) never counts as the main checkout."""
    probe = norm(path)
    while probe:
        git = os.path.join(probe, ".git")
        if os.path.exists(git):
            return probe if os.path.isdir(git) else None
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent
    return None


def load_projects():
    """Configured projects, each with its resolved `root` and `git`. [] if no config."""
    try:
        with open(config_path(), encoding="utf-8") as fh:
            cfg = json.load(fh)
    except (OSError, ValueError):
        return []
    out = []
    for p in cfg.get("projects") or []:
        if not isinstance(p, dict) or not p.get("path"):
            continue
        root = norm(p["path"])
        git = repo_git(root)
        if not git:
            continue
        q = dict(p)
        q["root"], q["git"] = root, git
        q.setdefault("name", os.path.basename(root))
        out.append(q)
    return out


def project_for(path, projects):
    """The configured project whose repo (or any of its worktrees) holds `path`."""
    g = repo_git(path)
    if not g:
        return None
    for p in projects:
        if p["git"] == g:
            return p
    return None
