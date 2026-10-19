# House rules

I build my products through Claude Code, and I am not a software engineer. Quality comes from evidence, not claims. These rules apply in every project.

## Spec before you build

For a new feature (a page, an agent, a scheduled job, an integration, a change in behaviour), use the `feature-spec` skill first: agree a half-page spec with me (goal, must do, must not, "done means", out of scope), get my OK, then build. Not for bug fixes or small tweaks. When you finish, check every "done means" line and show the evidence for each.

## One session per copy of the code

Several Claude sessions may be working in the same repo at once. Work in your own git worktree, not the main checkout. A hook (`worktree_guard.py`) refuses edits or commits in the main checkouts listed in `~/.claude/kit.config.json`, and its message says how to make a worktree. Remove your worktree when you're done.

## Evidence before "done"

A hook (`quality_gate.py`) holds every session to this: after changing code in a project listed in `kit.config.json`, run that project's tests before you say "done" or commit. If a test fails, fix it or say plainly which test and why.

If you stop mid-task, say so plainly. Never report a check as passed without its summary line.

## Memory

My memory lives in `~/.claude/memory/`. The index below is loaded into every session.

- One fact per file, with a short frontmatter (`name`, `description`, `type`: user, feedback, project or reference).
- Add one line to `MEMORY.md` for each file: `- [Title](file.md) — hook`. Never put the fact itself in the index.
- Before writing, check for a file that already covers it and update that instead. Delete notes that turn out to be wrong.
- Use absolute dates ("2026-10-19", not "yesterday"). For project notes, say where things stand: built, pushed, live, or waiting on me.
- Don't save what the repo already records (code, git history). Save what a fresh session couldn't work out on its own: decisions, why, and what's still open.

@~/.claude/memory/MEMORY.md

## Plain language

Explain outcomes in plain words: what changed for visitors or for me, and what I need to do. Keep the jargon in commit messages. If I say `/wait-what`, explain it again from the start.
