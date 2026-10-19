# Claude solo-founder kit

The setup I use to run three products through [Claude Code](https://claude.com/claude-code) without being a software engineer. It's not a framework. It's a few small files that fix the problems you hit once Claude does real work every day:

| Problem | Piece | Folder |
|---|---|---|
| Every session starts with a blank head | **Memory**: one fact per file, plus an index loaded into every session | [`memory/`](memory/) |
| Rules get forgotten | **House rules** in CLAUDE.md, kept short | [`claude-md/`](claude-md/) |
| Claude builds the wrong thing | **`feature-spec`**: you make the decisions, Claude writes a half-page spec, then checks the finished work against it | [`skills/`](skills/) |
| Two sessions overwrite each other | **Worktree guard**: one session per copy of the code | [`hooks/`](hooks/) |
| "Done!" when it isn't | **Quality gate**: no "done" and no commit until the tests have run | [`hooks/`](hooks/) |
| The same mistake twice | **`retro`**: turns a bad session into a check, so it can't happen again | [`skills/`](skills/) |
| You didn't follow what Claude said | **`wait-what`**: explain it again, plainly | [`skills/`](skills/) |
| Losing track of what's open | **Morning brief**: a scheduled, read-only summary from memory and git | [`routines/`](routines/morning-brief/) |

## Setup (5 minutes)

You need [Claude Code](https://claude.com/claude-code), Python 3.8+ and git, on Mac, Linux or Windows.

```bash
git clone https://github.com/reachviveksai-cloud/claude-solo-founder-kit
cd claude-solo-founder-kit
python3 install.py
```

On Windows, use `python` instead of `python3`.

The installer **never overwrites** anything: each file is copied only if you don't have it yet, and `settings.json` is backed up before the hooks are added. To see exactly what it does first, try it on an empty folder: `python3 install.py --home /tmp/try-kit`.

Then:

1. **List your projects** in `~/.claude/kit.config.json`: the folder, the test command, and how strictly to guard the main checkout. The hooks ignore any repo that isn't listed.
2. **Restart Claude Code.**
3. Try it: type `/morning-brief`, or ask for a new feature and watch `feature-spec` ask you the decisions first.

If you already had a `~/.claude/CLAUDE.md`, add one line to it: `@kit/CLAUDE.kit.md`.

## Check it works

```bash
python3 -m unittest discover -s tests -v
```

22 checks: the guard blocking and allowing, the gate blocking and allowing, and the installer keeping your existing files. They use throwaway repos and never touch your real `~/.claude`.

## The ideas behind it

- **A hook beats a rule.** CLAUDE.md is a request; a hook is a guarantee. When a rule keeps getting broken, turn it into a hook (that's what `retro` is for).
- **Facts are Claude's job; decisions are yours.** Claude should never ask you something it can look up.
- **Evidence, not claims.** "Done" means a test summary line, a screenshot or a live check, never "should work".
- **Fail open.** A broken hook allows the action. It must never lock you out of your own machine.

---

Built by Vivek, who runs [zeroed.ca](https://zeroed.ca) this way. Questions and improvements welcome: open an issue. MIT licensed.
