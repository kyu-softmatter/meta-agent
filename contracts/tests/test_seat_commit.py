# -*- coding: utf-8 -*-
"""Tests of contracts/tools/seat_commit.py in a temporary repository (meta_agent/tasks/009, part 2). The repository is built for each test from this one's contracts/,
bootstrap.py and hook, so the hook that runs is the real one.

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESIGN = "design-office-20261029-1"
META = "meta-office-20261029-1"


def run(cwd, *cmd, env=None):
    return subprocess.run(list(cmd), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")


class TempRepo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="seat-commit-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        shutil.copytree(os.path.join(REPO, "contracts"), os.path.join(self.dir, "contracts"),
                        ignore=shutil.ignore_patterns("__pycache__", "examples", "tests"))
        shutil.copy(os.path.join(REPO, "bootstrap.py"), self.dir)
        self.write("README.md", "a temporary repository\n")
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "a person")
        self.git("config", "user.email", "person@example.invalid")
        self.git("config", "core.hooksPath", "contracts/hooks")
        self.git("config", "meta-agent.machine", "office")
        env = dict(os.environ, GIT_COMMITTER_NAME="seat:" + DESIGN, GIT_COMMITTER_EMAIL=DESIGN + "@seat.invalid")
        self.git("add", "-A")
        p = run(self.dir, "git", "commit", "-q", "-m", "start", env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def git(self, *args):
        p = run(self.dir, "git", *args)
        self.assertEqual(p.returncode, 0, "git %s: %s" % (" ".join(args), p.stderr))
        return p.stdout

    def write(self, relpath, text):
        path = os.path.join(self.dir, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def tool(self, seat, *paths, message="a commit"):
        return run(self.dir, sys.executable, os.path.join("contracts", "tools", "seat_commit.py"),
                   "--seat", seat, "-m", message, *paths)

    def head(self):
        return self.git("log", "-1", "--format=%ce|%ae").strip(), \
            sorted(l.split("\t")[-1] for l in self.git("show", "--name-status", "--format=", "HEAD").splitlines() if l.strip())

    def count(self):
        return int(self.git("rev-list", "--count", "HEAD").strip())


class SeatCommit(TempRepo):
    def test_commits_as_the_seat_and_keeps_the_author(self):
        self.write("NOTES.md", "a root file\n")
        p = self.tool(DESIGN, "NOTES.md")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        who, paths = self.head()
        self.assertEqual(who, DESIGN + "@seat.invalid|person@example.invalid")
        self.assertEqual(paths, ["NOTES.md"])
        self.assertIn("committer seat:" + DESIGN, p.stdout)

    def test_two_seats_one_folder(self):
        # the design seat has staged its own file and left another unstaged; the meta seat commits beside it
        self.write("docs/design-note.md", "staged by the design seat\n")
        self.git("add", "docs/design-note.md")
        self.write("NOTES.md", "unstaged, the design seat's\n")
        self.write("meta_agent/work.txt", "the meta seat's\n")
        p = self.tool(META, "meta_agent/work.txt")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        who, paths = self.head()
        self.assertEqual(who.split("|")[0], META + "@seat.invalid")
        self.assertEqual(paths, ["meta_agent/work.txt"])
        self.assertEqual(self.git("diff", "--cached", "--name-only").split(), ["docs/design-note.md"])
        self.assertIn("NOTES.md", self.git("status", "--porcelain"))
        # and the design seat then commits its two files, the repository's own committer untouched throughout
        p = self.tool(DESIGN, "docs/design-note.md", "NOTES.md")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        who, paths = self.head()
        self.assertEqual(who.split("|")[0], DESIGN + "@seat.invalid")
        self.assertEqual(paths, ["NOTES.md", "docs/design-note.md"])
        self.assertEqual(run(self.dir, "git", "config", "--get", "committer.name").stdout.strip(), "")

    def test_refuses_a_path_outside_the_seat(self):
        self.write("contracts/extra.txt", "not the meta seat's\n")
        n = self.count()
        p = self.tool(META, "contracts/extra.txt")
        self.assertEqual(p.returncode, 1)
        self.assertIn("outside", p.stderr)
        self.assertEqual(self.count(), n)

    def test_refuses_an_unknown_seat_and_an_empty_commit(self):
        self.write("meta_agent/work.txt", "x\n")
        p = self.tool("meta-office-20261109-7", "meta_agent/work.txt")
        self.assertEqual(p.returncode, 1)
        self.assertIn("not a seat at HEAD", p.stderr)
        p = self.tool(DESIGN, "README.md")
        self.assertEqual(p.returncode, 1)
        self.assertIn("nothing to commit", p.stderr)

    def test_the_message_may_come_from_stdin(self):
        self.write("NOTES.md", "x\n")
        p = subprocess.run([sys.executable, os.path.join("contracts", "tools", "seat_commit.py"), "--seat", DESIGN,
                            "-F", "-", "NOTES.md"], cwd=self.dir, input="a subject\n\nand a body\n",
                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.git("log", "-1", "--format=%s|%b").strip(), "a subject|and a body")

    def test_a_deletion_is_committed_too(self):
        os.remove(os.path.join(self.dir, "README.md"))
        p = self.tool(DESIGN, "README.md")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.head()[1], ["README.md"])


if __name__ == "__main__":
    unittest.main()
