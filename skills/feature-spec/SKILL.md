---
name: feature-spec
description: Write a half-page spec with the user BEFORE building a new feature, then check the finished work against it. Use when they ask for a new feature, page, agent, scheduled job, integration or behaviour change ("build", "add", "make it do"). Not for bug fixes, copy edits or small tweaks. Also use when they say /feature-spec or "spec it first".
---

# Feature spec: half a page, before any code

The user may not be an engineer. The spec is how they control quality: it's where they decide *what* gets built, so the work is checked against their decision, not against Claude's own idea of "done". Keep it short. If it runs past half a page, the feature is too big, so split it.

## 1. Ask in rounds, then draft (before touching code)

**Facts are your job; decisions are theirs.** Look up anything the repo, the data or a quick check can tell you (send a subagent if it's a big search), and never ask the user for it. Ask them only about choices: what it should do, for whom, what it must never do, what counts as done.

Ask in **rounds**. A round is every decision you can ask about *now* without guessing at an answer they haven't given yet. A question that depends on another open question waits for a later round. Number each question, keep it to plain words, and give your recommendation, worded so that "yes" accepts it:

```
❓ **Q1 – <short title>**: <the question, with the options in plain words if there are several>

➡️ Recommended: <your answer, and in one line why>
```

They can answer "yes to all", "yes except Q2: ...", or one by one. Each answer can open new questions; ask those in the next round. One or two rounds is usually enough. Small details you can safely decide yourself go into the draft as stated choices they can change, not as more questions.

Then write this, in plain words:

```markdown
# <Feature name>  (<YYYY-MM-DD>)

**Goal:** one or two sentences — who it's for and what changes for them.

**Must do:**
- 3–6 bullets, each something a person could observe.

**Must not:**
- what it must not break, send, spend, publish or change (money, emails, live pages, data).

**Done means** (each one checkable, and say how):
- [ ] <observable result> — checked by <test / browser check / screenshot / live run>
- [ ] existing tests still pass

**Out of scope:** what we are deliberately not doing now.
```

Show it and **wait for their OK** before writing code. If they change it, update the file.

## 2. Save it

Save to `docs/specs/<date>-<slug>.md` in the repo and commit it with the feature. **Exception:** if everything in the repo is published (a static website deployed straight from the repo), save it outside the repo so the spec doesn't go live.

## 3. Build, then check against it

Before saying "done", go through **Done means** line by line and show the evidence for each: the test summary line, the browser check, a screenshot. A line without evidence isn't done. Say so plainly, and say what's missing.

If you run a code review, give the reviewer the spec path too, so it checks the change against what the user asked for, not just for bugs.

## 4. If the work drifts

If building shows the spec was wrong (it's impossible, it conflicts with something, or a better route exists), stop and tell the user. Don't quietly build something different from what they approved.
