# Memory

**What it's for:** Every Claude session starts with a blank head. Memory is how session 40 knows what session 3 decided, without you explaining it again.

It is just a folder of small Markdown files plus one index:

```
~/.claude/memory/
  MEMORY.md                      <- the index: one line per note, loaded into every session
  pricing-decision.md            <- one fact per file
  feedback-plain-language.md
  launch-checklist-status.md
```

The house rules (`claude-md/`) tell Claude how to write notes, and `@~/.claude/memory/MEMORY.md` pulls the index into every session. Claude opens a note only when its index line looks relevant, so 50 notes cost about as much as 50 lines.

**Why one fact per file:** a note can be updated or deleted without touching the others, and a stale note is easy to spot and remove. One big notes file turns into a diary nobody trusts.

**The four kinds of note** (the `type` in each file's frontmatter):

| type | holds | example |
|---|---|---|
| `user` | who you are, how you like to work | "Not an engineer; explain outcomes, not code" |
| `feedback` | a correction or a confirmed approach, and why | "Never post to social without my OK, after the 2026-09 mix-up" |
| `project` | where a piece of work stands | "Pricing page: live since 2026-10-02; annual plan waiting on me" |
| `reference` | where to find things | "Analytics dashboard is at …" |

**Installed:** `install.py` copies `MEMORY.md` to `~/.claude/memory/` only if you don't have one yet. The three files in `examples/` are made up. Read them to see the shape, and don't install them.

> Recent Claude Code versions also have a built-in "auto memory" that works the same way (a folder per project plus an index). If you use that, keep these writing rules and skip this folder.
