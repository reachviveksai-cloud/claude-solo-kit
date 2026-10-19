---
name: retro
description: Look back at a Claude session and suggest changes to the setup (checks, hooks, skills, CLAUDE.md, tools) so the same problems don't happen again. Use when the user says /retro, "what went wrong", or "how do we stop this happening again".
disable-model-invocation: true
---

# Retro: fix the setup, not just the code

When the user builds through Claude, quality comes from the setup around Claude, not from Claude remembering to be careful. A retro looks at one session and asks: **what would have stopped each problem automatically next time?**

In this skill you only suggest. Change nothing until the user says which suggestions to do.

## 1. Read what actually happened

Default to the current session. If they name another one, find its log under `~/.claude/projects/<project folder>/*.jsonl` (newest first) and read it, rather than relying on memory or a summary.

Note every moment that cost time, quality or trust:
- something reported as working that wasn't, or a check claimed without its result
- a mistake the user had to catch, or a correction they had to repeat
- a long search for a file, a fact or a command
- a step that needed the user (a login, a dashboard, a secret) and stalled
- information Claude needed but couldn't see (logs, live data, a dashboard)
- an expensive or repeated action that got nowhere

## 2. For each problem, pick the strongest fix

Go down this list and stop at the first fix that would really work. The higher up, the more reliable:

1. **An automatic check.** A test, a lint rule, a browser check, or a hook in `~/.claude/kit/hooks/` (like `quality_gate.py` and `worktree_guard.py`). Use this whenever a script could spot the mistake's pattern. First check whether a check already exists but isn't wired up or is broken. Fixing that is the finding.
2. **A skill change.** If the problem came from how a recurring job was done (spec, review, deploy), change that skill, e.g. `feature-spec`.
3. **A project doc a skill or review reads**, for judgement calls no script can check.
4. **A line in CLAUDE.md**, as a last resort. CLAUDE.md is loaded into every session, so each line costs something every time. Also look for lines there that changed nothing, or that belong in a check instead, and suggest removing them.
5. **Better access to information**, e.g. a server log saved to a file, read-only access to a dashboard, or a script that answers a question in one command.

## 3. Report, worst first

In plain words. For each suggestion:

```
**1. <what went wrong, in one line>**
What happened: <one or two sentences, with the moment from the session>
Fix: <the change, and which kind from the list above>
Effect: <what will be different next time>
Size: small / medium / large
```

End with one question: which ones to do. Then make only those, and show evidence that each one works (e.g. the hook refusing a test case, the check failing then passing).
