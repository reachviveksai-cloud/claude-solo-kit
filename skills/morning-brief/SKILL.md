---
name: morning-brief
description: A short start-of-day brief — what's open, what's stuck, and what to follow up on today — built from the memory index and the git state of the projects in kit.config.json. Use when the user says /morning-brief or "what's on today", or when a scheduled routine runs it.
---

# Morning brief

Give the user one screen telling them where everything stands, so they don't have to remember. **Read only:** change no files, run no deploys, send nothing.

## 1. Gather (facts only)

1. **Memory.** Read `~/.claude/memory/MEMORY.md`, then open the `project` and `feedback` notes whose lines mention something open, waiting, pending, not released, or a date.
2. **Projects.** Read `~/.claude/kit.config.json`. For each project path that exists, run read-only git commands:
   - `git -C <path> status --short --branch`: uncommitted work, and commits not yet pushed
   - `git -C <path> log --oneline --since="2 days ago"`: what moved recently
   - `git -C <path> worktree list`: worktrees still lying around (each one is unfinished or forgotten work)
   - `git -C <path> stash list`
3. **Dates.** Note today's date. Compare it with dates in the notes: anything promised for today or earlier that isn't marked done is overdue.

If a source is missing (no config, no memory, a path that doesn't exist), say so in one line and carry on.

## 2. Write the brief

Plain words, under 25 lines, in this order:

```
# Morning brief — <date>

**Waiting on you** (decisions or steps only you can take)
- ...

**Stuck or overdue**
- <thing> — <since when> — <what would unstick it>

**Follow up today**
- ...

**In flight** (built but not finished: unpushed commits, open worktrees, uncommitted changes)
- <project>: ...

**Moved since yesterday**
- ...
```

Leave out empty sections. Each line names the note or repo it came from, so it can be checked. Don't invent tasks: if memory and git say nothing is open, say "Nothing open" and stop.

## 3. If run on a schedule

Also write the brief to `~/.claude/briefs/<YYYY-MM-DD>.md` (create the folder if needed; this is the only file you may write).
