# Hooks

**What they're for:** A rule in CLAUDE.md is a request, and a hook is a guarantee. Claude Code runs these scripts before or after its own actions, and a hook can refuse the action and tell Claude why. These two cover the mistakes that cost the most when you run many sessions at once.

Both read `~/.claude/kit.config.json`, which lists your projects (copy `kit.config.example.json` and edit the paths). A project that isn't listed is never touched. With no config at all, both hooks do nothing.

## `worktree_guard.py`: one session per copy of the code

Two sessions in one folder will sweep each other's half-finished work into commits. The guard refuses work in a project's **main checkout** and says how to make a [git worktree](https://git-scm.com/docs/git-worktree), a second copy of the repo on its own branch:

| `protect_main_checkout` | Edits in main checkout | `git commit` in main checkout |
|---|---|---|
| `"edit"` | refused | refused |
| `"commit"` | allowed | refused |
| `"off"` | allowed | allowed |

Worktrees are never blocked. Escape hatch, only when you explicitly say so: `SHARED_CHECKOUT_OK=1` in the command.

## `quality_gate.py`: evidence before "done"

It reads the current session's own log, so it judges only what this session did:

- **When Claude tries to finish** (`stop`): if it changed code in a listed project and hasn't run that project's `test_command` since, or the last run failed, it's sent back once to run the tests or explain the failure. It only asks once, so it can never trap a session.
- **Before `git commit`** (`commit`): the commit is refused until a passing test run follows the last code change. With `"review_before_commit": true`, a `/code-review` is required too.

Escape hatch: `SKIP_GATE=1` in the commit command.

## Safety

Both hooks **fail open**: if anything inside them breaks, the action is allowed. A broken hook must never lock you out of your own machine.

`kit_config.py` is shared by both. `install.py` wires all of this into `~/.claude/settings.json`.
