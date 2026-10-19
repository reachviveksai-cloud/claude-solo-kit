"""Checks for the kit: the two hooks and the installer.

    python3 -m unittest discover -s tests -v

Uses throwaway git repos and fake session logs in a temp folder. Touches
nothing in your real ~/.claude.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(KIT, "hooks", "worktree_guard.py")
GATE = os.path.join(KIT, "hooks", "quality_gate.py")
INSTALL = os.path.join(KIT, "install.py")


def git(*args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
                        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.app = os.path.join(self.tmp, "app")
        self.wt = os.path.join(self.tmp, "app-wt")
        self.api = os.path.join(self.tmp, "api")
        self.other = os.path.join(self.tmp, "other")
        for repo in (self.app, self.api, self.other):
            os.makedirs(repo)
            git("init", "-q", cwd=repo)
            with open(os.path.join(repo, "main.py"), "w") as fh:
                fh.write("x = 1\n")
            git("add", ".", cwd=repo)
            git("commit", "-q", "-m", "init", cwd=repo)
        git("worktree", "add", "-q", self.wt, "-b", "task", cwd=self.app)
        self.config = os.path.join(self.tmp, "kit.config.json")
        self.write_config()
        self.log = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_config(self, **app_extra):
        cfg = {"projects": [
            {"name": "app", "path": self.app, "test_command": "python -m pytest",
             "protect_main_checkout": "edit", **app_extra},
            {"name": "api", "path": self.api, "test_command": "npm test",
             "protect_main_checkout": "commit"},
        ]}
        with open(self.config, "w") as fh:
            json.dump(cfg, fh)

    def run_hook(self, script, payload, *args):
        r = subprocess.run([sys.executable, script, *args], input=json.dumps(payload),
                           capture_output=True, text=True,
                           env={**os.environ, "KIT_CONFIG": self.config})
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(r.stdout) if r.stdout.strip() else None

    # ---- fake session log -------------------------------------------------
    def tool(self, name, inp, cwd, result=None, is_error=False):
        tid = f"t{len(self.log)}"
        self.log.append({"type": "assistant", "cwd": cwd, "message": {"content": [
            {"type": "tool_use", "id": tid, "name": name, "input": inp}]}})
        if result is not None:
            self.log.append({"type": "user", "cwd": cwd, "message": {"content": [
                {"type": "tool_result", "tool_use_id": tid, "content": result,
                 "is_error": is_error}]}})

    def edit(self, path):
        self.tool("Edit", {"file_path": path}, self.wt, "ok")

    def bash(self, cmd, result="", is_error=False, cwd=None):
        self.tool("Bash", {"command": cmd}, cwd or self.wt, result, is_error)

    def transcript(self):
        p = os.path.join(self.tmp, "session.jsonl")
        with open(p, "w") as fh:
            for line in self.log:
                fh.write(json.dumps(line) + "\n")
        return p

    def stop(self, active=False):
        return self.run_hook(GATE, {"transcript_path": self.transcript(),
                                    "stop_hook_active": active}, "stop")

    def commit(self, cwd=None, cmd='git commit -m "x"'):
        return self.run_hook(GATE, {"transcript_path": self.transcript(),
                                    "tool_input": {"command": cmd},
                                    "cwd": cwd or self.wt}, "commit")


def denied(out):
    return bool(out) and out["hookSpecificOutput"]["permissionDecision"] == "deny"


class WorktreeGuard(Base):
    def edit_payload(self, path):
        return {"tool_name": "Write", "tool_input": {"file_path": path}}

    def commit_payload(self, cwd, cmd='git commit -m "x"'):
        return {"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": cwd}

    def test_blocks_edit_in_main_checkout(self):
        out = self.run_hook(GUARD, self.edit_payload(os.path.join(self.app, "main.py")))
        self.assertTrue(denied(out))
        self.assertIn("worktree add", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_allows_edit_in_worktree(self):
        self.assertIsNone(self.run_hook(GUARD, self.edit_payload(os.path.join(self.wt, "main.py"))))

    def test_blocks_commit_in_main_checkout(self):
        self.assertTrue(denied(self.run_hook(GUARD, self.commit_payload(self.app))))

    def test_blocks_commit_after_cd_into_main_checkout(self):
        out = self.run_hook(GUARD, self.commit_payload(self.tmp, 'cd app && git commit -m "x"'))
        self.assertTrue(denied(out))

    def test_allows_commit_in_worktree(self):
        self.assertIsNone(self.run_hook(GUARD, self.commit_payload(self.wt)))

    def test_commit_mode_allows_edit_but_blocks_commit(self):
        self.assertIsNone(self.run_hook(GUARD, self.edit_payload(os.path.join(self.api, "main.py"))))
        self.assertTrue(denied(self.run_hook(GUARD, self.commit_payload(self.api))))

    def test_unlisted_repo_is_never_touched(self):
        self.assertIsNone(self.run_hook(GUARD, self.edit_payload(os.path.join(self.other, "main.py"))))
        self.assertIsNone(self.run_hook(GUARD, self.commit_payload(self.other)))

    def test_escape_hatch(self):
        cmd = 'SHARED_CHECKOUT_OK=1 git commit -m "x"'
        self.assertIsNone(self.run_hook(GUARD, self.commit_payload(self.app, cmd)))

    def test_no_config_does_nothing(self):
        os.remove(self.config)
        self.assertIsNone(self.run_hook(GUARD, self.edit_payload(os.path.join(self.app, "main.py"))))


class QualityGate(Base):
    def test_blocks_done_and_commit_when_tests_not_run(self):
        self.edit(os.path.join(self.wt, "main.py"))
        out = self.stop()
        self.assertEqual(out["decision"], "block")
        self.assertIn("python -m pytest", out["reason"])
        self.assertTrue(denied(self.commit()))

    def test_allows_after_passing_tests(self):
        self.edit(os.path.join(self.wt, "main.py"))
        self.bash("python -m pytest", "12 passed in 0.4s")
        self.assertIsNone(self.stop())
        self.assertIsNone(self.commit())

    def test_failed_run_still_blocks(self):
        self.edit(os.path.join(self.wt, "main.py"))
        self.bash("python -m pytest", "FAILED tests/test_x.py::test_y\n1 failed, 11 passed", True)
        self.assertIn("FAILED", self.stop()["reason"])
        self.assertTrue(denied(self.commit()))

    def test_edit_after_tests_needs_a_new_run(self):
        self.edit(os.path.join(self.wt, "main.py"))
        self.bash("python -m pytest", "12 passed")
        self.edit(os.path.join(self.wt, "main.py"))
        self.assertEqual(self.stop()["decision"], "block")

    def test_asks_only_once(self):
        self.edit(os.path.join(self.wt, "main.py"))
        self.assertIsNone(self.stop(active=True))

    def test_docs_and_unlisted_repos_are_ignored(self):
        self.edit(os.path.join(self.wt, "README.md"))
        self.edit(os.path.join(self.other, "main.py"))
        self.assertIsNone(self.stop())

    def test_bash_edit_counts_as_a_change(self):
        self.bash("sed -i 's/1/2/' main.py", "")
        self.assertEqual(self.stop()["decision"], "block")

    def test_review_before_commit(self):
        self.write_config(review_before_commit=True)
        self.edit(os.path.join(self.wt, "main.py"))
        self.bash("python -m pytest", "12 passed")
        self.assertTrue(denied(self.commit()))
        self.tool("Skill", {"skill": "code-review"}, self.wt, "ok")
        self.assertIsNone(self.commit())

    def test_skip_gate(self):
        self.edit(os.path.join(self.wt, "main.py"))
        self.assertIsNone(self.commit(cmd='SKIP_GATE=1 git commit -m "x"'))


class Installer(unittest.TestCase):
    def setUp(self):
        self.home = os.path.realpath(tempfile.mkdtemp())
        self.claude = os.path.join(self.home, ".claude")

    def tearDown(self):
        shutil.rmtree(self.home, ignore_errors=True)

    def install(self):
        r = subprocess.run([sys.executable, INSTALL, "--home", self.home],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r.stdout

    def settings(self):
        with open(os.path.join(self.claude, "settings.json")) as fh:
            return json.load(fh)

    def hook_commands(self):
        return [h["command"] for groups in self.settings()["hooks"].values()
                for g in groups for h in g["hooks"]]

    def test_fresh_install(self):
        self.install()
        for rel in ("kit/hooks/worktree_guard.py", "kit/hooks/quality_gate.py",
                    "kit/hooks/kit_config.py", "kit/CLAUDE.kit.md", "memory/MEMORY.md",
                    "kit.config.json", "skills/feature-spec/SKILL.md", "skills/retro/SKILL.md",
                    "skills/wait-what/SKILL.md", "skills/morning-brief/SKILL.md"):
            self.assertTrue(os.path.isfile(os.path.join(self.claude, rel)), rel)
        with open(os.path.join(self.claude, "CLAUDE.md")) as fh:
            self.assertEqual(fh.read().strip(), "@kit/CLAUDE.kit.md")
        self.assertEqual(len(self.hook_commands()), 4)

    def test_second_run_adds_nothing(self):
        self.install()
        out = self.install()
        self.assertEqual(len(self.hook_commands()), 4)
        self.assertIn("hooks already wired", out)

    def test_keeps_what_you_already_have(self):
        os.makedirs(os.path.join(self.claude, "skills", "retro"))
        mine = {"CLAUDE.md": "# my rules\n", "skills/retro/SKILL.md": "my retro\n"}
        for rel, text in mine.items():
            with open(os.path.join(self.claude, rel), "w") as fh:
                fh.write(text)
        with open(os.path.join(self.claude, "settings.json"), "w") as fh:
            json.dump({"theme": "dark", "hooks": {"Stop": [{"hooks": [
                {"type": "command", "command": "echo mine"}]}]}}, fh)
        out = self.install()
        for rel, text in mine.items():
            with open(os.path.join(self.claude, rel)) as fh:
                self.assertEqual(fh.read(), text, rel)
        s = self.settings()
        self.assertEqual(s["theme"], "dark")
        self.assertIn("echo mine", self.hook_commands())
        self.assertEqual(len(self.hook_commands()), 5)
        self.assertTrue(any(f.startswith("settings.json.kit-backup-") for f in os.listdir(self.claude)))
        self.assertIn("@kit/CLAUDE.kit.md", out)

    def test_wired_hook_command_runs(self):
        """The command written into settings.json actually starts the hook."""
        self.install()
        guard = next(c for c in self.hook_commands() if c.endswith('worktree_guard.py"'))
        r = subprocess.run(guard, shell=True, input=json.dumps(
            {"tool_name": "Write", "tool_input": {"file_path": "/nowhere/x.py"}}),
            capture_output=True, text=True, env={**os.environ, "HOME": self.home,
                                                 "USERPROFILE": self.home})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
