# Skills

**What they're for:** A skill is a set of instructions Claude loads only when it's needed, either because you typed `/name` or because the task matches the skill's description. They're for jobs you want done the same way every time.

| Skill | When | What it does |
|---|---|---|
| `feature-spec` | "build", "add", "make it do…" | Asks you only the decisions (with a recommended answer each), writes a half-page spec, waits for your OK, then checks the finished work against every "done means" line |
| `retro` | `/retro` after a session that went badly | Reads the session log and suggests the strongest fix for each problem: a hook beats a skill, and a skill beats a line in CLAUDE.md |
| `wait-what` | `/wait-what` when you didn't follow | Explains the last message again: where we are, what it means for you, what's needed from you |
| `morning-brief` | `/morning-brief`, or on a schedule | One screen of what's waiting on you, what's stuck, and what's in flight, from memory and git. Read only. See `routines/morning-brief/` |

**Installed:** `install.py` copies each one to `~/.claude/skills/<name>/`, skipping any you already have.
