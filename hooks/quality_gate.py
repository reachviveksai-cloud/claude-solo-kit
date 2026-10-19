"""Quality gate: evidence before "done", tests before commit.

Two modes, both wired by install.py into ~/.claude/settings.json:

  stop    Stop hook. If this session changed code in a project from
          kit.config.json and hasn't run that project's test_command since
          its last change (or the last run failed), Claude is sent back ONCE
          to run the tests, or to say plainly what is failing and why.
  commit  PreToolUse/Bash hook. `git commit` in a configured project is
          refused while this session has code changes with no passing test
          run since. With "review_before_commit": true it also needs a
          /code-review after the last change.

Both read THIS session's transcript, so a session is judged only on what it
did itself, never on another session's files.

Why: the bugs that reach customers are rarely hard. They're a "works" that
nothing independent checked. This makes the check mandatory instead of a habit.

Escape hatches, for when the user says so:
  - the Stop gate blocks at most once per stop (stop_hook_active), so a
    session can always finish after explaining itself. It cannot loop.
  - a commit command containing SKIP_GATE=1 passes.
FAIL-OPEN: any error inside this script allows the action. A broken gate must
never wedge every session on the machine.
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit_config import load_projects, norm, project_for, resolve  # noqa: E402

CODE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rb",
            ".rs", ".java", ".kt", ".swift", ".php", ".cs", ".sh", ".sql",
            ".yaml", ".yml", ".toml", ".json", ".css", ".scss", ".html", ".vue",
            ".svelte")
CODE_NAMES = ("dockerfile", "makefile", "requirements.txt")

_LEAD = r"(?:^|[;&|\n(){}]|&&|\|\|)\s*"
# Bash commands that rewrite files without going through Edit/Write.
BASH_EDIT = re.compile(
    _LEAD + r"(?:sed\s+-i|perl\s+-[a-z]*i|git\s+(?:apply|am|stash\s+(?:pop|apply)|"
    r"checkout\s+--|restore))"
    r"|>\s*\S+\.(?:py|tsx?|jsx?|sh|sql|ya?ml|css|html?)\b", re.I)
GIT_COMMIT = re.compile(_LEAD + r"git\s+(?:-C\s+\S+\s+)?commit\b")
GIT_C = re.compile(r"git\s+-C\s+(\"[^\"]+\"|'[^']+'|\S+)")
CD = re.compile(r"(?:^|[;&|\n]|&&)\s*cd\s+(\"[^\"]+\"|'[^']+'|\S+)")
ABS_PATH = re.compile(r"(?<![^\s\"'=])(?:/[^\s\"';&|<>()]+|[A-Za-z]:[\\/][^\s\"';&|<>()]+)")

# What a failed, or never-started, test run looks like across common runners.
FAIL_MARKS = re.compile(
    r"^FAILED |=+ FAILURES =+|=+ ERRORS =+|\b[1-9]\d* (?:failed|failing)\b"
    r"|\b[1-9]\d* errors?\b|^npm ERR!|^Tests?:\s+[1-9]\d* failed|EXIT=[1-9]"
    r"|No module named|command not found|is not recognized as|Interrupted:"
    r"|collection errors?",
    re.M | re.I)
BACKGROUND = re.compile(r"Command running in background.*?Output is being written to: (\S+)", re.S)


def is_code(path):
    base = os.path.basename(path).lower()
    return base.endswith(CODE_EXT) or base in CODE_NAMES


def test_pattern(project):
    tc = (project.get("test_command") or "").strip()
    if not tc:
        return None
    return re.compile(r"\s+".join(re.escape(w) for w in tc.split()))


def command_dirs(cmd, cwd):
    """Directories a Bash command acts in: its cwd, any `cd X`, `git -C X`, absolute paths."""
    dirs = [] if re.match(r"\s*cd\s", cmd) else [cwd]
    for m in ABS_PATH.finditer(cmd):
        p = norm(m.group(0))
        dirs.append(p if os.path.isdir(p) else os.path.dirname(p))
    for rx in (CD, GIT_C):
        for m in rx.finditer(cmd):
            dirs.append(resolve(m.group(1), cwd))
    return [d for d in dirs if d]


def result_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def scan(transcript_path, projects):
    """This session's relevant events, in order: [kind, project_name, detail]."""
    events, pending = [], {}
    with open(transcript_path, encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("isSidechain"):
                continue
            msg = d.get("message")
            if not isinstance(msg, dict):
                continue
            cwd = d.get("cwd") or ""
            content = msg.get("content")
            if d.get("type") == "user" and isinstance(content, str):
                if content.lstrip().startswith("<command-name>/code-review"):
                    events.append(["review", None, None])
                continue
            if not isinstance(content, list):
                continue
            for b in content:
                if not isinstance(b, dict):
                    continue
                t = b.get("type")
                if t == "tool_use":
                    name, inp = b.get("name"), b.get("input") or {}
                    if name in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
                        p = inp.get("file_path") or inp.get("notebook_path") or ""
                        proj = project_for(os.path.dirname(norm(p)), projects) if p else None
                        if proj and is_code(p):
                            events.append(["edit", proj["name"], p])
                    elif name == "Skill" and "code-review" in str(inp.get("skill", "")):
                        events.append(["review", None, None])
                    elif name == "Bash":
                        cmd = inp.get("command", "")
                        dirs = command_dirs(cmd, cwd)
                        for proj in projects:
                            if not any(project_for(x, [proj]) for x in dirs):
                                continue
                            rx = test_pattern(proj)
                            if rx and rx.search(cmd):
                                events.append(["test", proj["name"], None])
                                pending.setdefault(b.get("id"), []).append(len(events) - 1)
                            elif BASH_EDIT.search(cmd):
                                events.append(["edit", proj["name"], cmd[:80]])
                elif t == "tool_result" and b.get("tool_use_id") in pending:
                    res = {"text": result_text(b.get("content")),
                           "is_error": bool(b.get("is_error"))}
                    for i in pending.pop(b["tool_use_id"]):
                        events[i][2] = res
    return events


def run_status(ev):
    """'pass', 'fail' or 'running' for a test event."""
    res = ev[2]
    if res is None:
        return "running"
    text = res["text"]
    bg = BACKGROUND.search(text)
    if bg:
        try:
            with open(norm(bg.group(1)), encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            return "running"
        if not text.strip():
            return "running"
    if res["is_error"] or FAIL_MARKS.search(text):
        return "fail"
    return "pass"


def last_index(events, kind, project=None):
    for i in range(len(events) - 1, -1, -1):
        if events[i][0] == kind and (project is None or events[i][1] == project):
            return i
    return -1


def test_problem(events, proj):
    """Why this project's tests don't cover the session's last change, or None."""
    last_edit = last_index(events, "edit", proj["name"])
    if last_edit < 0:
        return None
    cmd = proj.get("test_command") or "(no test_command set in kit.config.json)"
    last_test = last_index(events, "test", proj["name"])
    if last_test < last_edit:
        return (f"You changed code in {proj['name']} and haven't run its tests since "
                f"your last change. Run `{cmd}` and read the summary line, not just "
                f"the exit code.")
    st = run_status(events[last_test])
    if st == "fail":
        return (f"Your last test run in {proj['name']} FAILED. Fix it, or name each "
                f"failing test and why in your reply.")
    if st == "running":
        return f"Your test run in {proj['name']} hasn't finished. Wait for it and report the result."
    return None


def stop_gate(hook, projects):
    if hook.get("stop_hook_active"):
        return None          # already sent back once this stop; never loop
    events = scan(hook["transcript_path"], projects)
    problems = [x for x in (test_problem(events, p) for p in projects) if x]
    if not problems:
        return None
    return {
        "decision": "block",
        "reason": "quality gate (evidence before done):\n- " + "\n- ".join(problems)
        + "\nIf you're deliberately stopping mid-task (asking the user a question, or "
        "leaving work unfinished on purpose), say that plainly in your reply instead. "
        "This gate only asks once.",
    }


def commit_gate(hook, projects):
    cmd = (hook.get("tool_input") or {}).get("command", "")
    if not GIT_COMMIT.search(cmd) or "SKIP_GATE=1" in cmd:
        return None
    dirs = command_dirs(cmd, hook.get("cwd") or "")
    targets = [p for p in projects if any(project_for(x, [p]) for x in dirs)]
    if not targets:
        return None
    events = scan(hook["transcript_path"], projects)
    for proj in targets:
        why = test_problem(events, proj)
        if not why and proj.get("review_before_commit"):
            last_edit = last_index(events, "edit", proj["name"])
            if last_edit >= 0 and last_index(events, "review") < last_edit:
                why = (f"{proj['name']} wants a code review before each commit, and "
                       f"this session changed code after its last review. Run "
                       f"/code-review, fix what it confirms, then commit.")
        if why:
            return {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "quality gate: " + why
                + " Only if the user explicitly says to skip this, add SKIP_GATE=1 "
                "to the commit command."}}
    return None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        hook = json.load(sys.stdin)
        projects = load_projects()
        if not projects:
            return 0
        out = (stop_gate(hook, projects) if mode == "stop"
               else commit_gate(hook, projects) if mode == "commit" else None)
    except Exception:
        return 0             # fail open
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
