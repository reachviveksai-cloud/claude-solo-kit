# House rules (CLAUDE.md)

**What it's for:** Claude Code reads `~/.claude/CLAUDE.md` at the start of every session, in every project. This file holds the few rules that matter most when you're not an engineer: agree a spec first, one session per copy of the code, no "done" without evidence, and plain language.

**How it's installed:** `install.py` copies `CLAUDE.kit.md` to `~/.claude/kit/CLAUDE.kit.md`.

- If you have no `~/.claude/CLAUDE.md`, the installer creates one that contains just `@kit/CLAUDE.kit.md`, which pulls these rules in.
- If you already have one, it is left alone. Add this line to it yourself:

  ```
  @kit/CLAUDE.kit.md
  ```

**Make it yours:** Keep it short. Every line is loaded into every session, so a rule that never changes anything is a cost. When a rule keeps getting broken, turn it into a hook (see `hooks/`) instead of writing it louder. The `retro` skill helps you decide which.
