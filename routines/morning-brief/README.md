# Morning brief routine

**What it's for:** Staying on track without having to remember. Every weekday morning, Claude reads your memory notes and the git state of your projects, then tells you what's waiting on you, what's stuck, and what's half-finished. It's **read only**: it never edits, pushes, posts or sends anything.

The routine is the `morning-brief` skill (`skills/morning-brief/SKILL.md`) run on a timer. Pick one way to schedule it.

## Option A: Claude desktop app (easiest)

In the Claude desktop app, ask in a Code session:

> Every weekday at 8:00, run /morning-brief

Claude sets up a scheduled task. It runs on your computer while the app is open.

## Option B: cron (Mac / Linux)

`crontab -e`, then add:

```
0 8 * * 1-5  cd ~ && claude -p "/morning-brief" --allowedTools "Read,Glob,Grep,Bash(git:*),Write" >> ~/.claude/briefs/cron.log 2>&1
```

## Option C: Windows Task Scheduler

Create a basic task (weekdays, 8:00) whose action is:

```
Program:   claude
Arguments: -p "/morning-brief" --allowedTools "Read,Glob,Grep,Bash(git:*),Write"
Start in:  %USERPROFILE%
```

Each run also saves the brief to `~/.claude/briefs/<date>.md`, so you can read it later.

## What a brief looks like

This is a real run on a sample project (`my-app`, with the three example notes from `memory/examples/`), saved exactly as written. Look at "Stuck or overdue": it caught a commit that went against a decision recorded in memory. That's the point of reading memory and git together.

```
# Morning brief — 2026-10-19

**Waiting on you**
- Pricing page: choose the annual plan, 2 months free or 20% off. Nothing gets built until you do. (memory: project-pricing-page)

**Stuck or overdue**
- my-app has an unpushed commit "Add annual toggle", but your note says not to build the annual plan until you choose. Check it before it's pushed. (memory: project-pricing-page; git log)

**In flight**
- my-app: 2 commits not pushed to origin/main: "Add annual toggle", "Fix footer link" (git status: ahead 2)
- my-app: 1 new file not committed: src/pricing.js (git status)
- my-app: worktree my-app-onboarding (branch onboarding-emails) is open but has no commits of its own yet (git worktree list)

**Moved since yesterday**
- my-app: pushed "Add plan comparison table" and "Pricing page copy pass"; committed locally "Add annual toggle" and "Fix footer link" (git log)
```
