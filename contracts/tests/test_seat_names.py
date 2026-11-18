# -*- coding: utf-8 -*-
"""Tests that `bootstrap.py seat` never offers a name already used and that two --write runs at once do not
take the same name (a name is never reissued, contracts/seats.json "names"; 2026-11-17, a name used in a test
clone was offered again, and two sessions seating at once wrote the same entry twice).

Each test builds a temporary repository from this one's bootstrap.py and contracts/tools/seats.py with a small
seats table, so the real contracts/seats.json is never touched.

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import copy
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import seats  # noqa: E402

TODAY = datetime.date.today().strftime("%Y%m%d")
TABLE = {
    "machines": {"office": "a computer"},
    "roles": {
        "design": {"paths": ["*", "contracts/"], "excludes": [], "owns": ["design"]},
        "meta": {"paths": ["meta_agent/"], "excludes": ["meta_agent/CLAUDE.md"], "owns": ["meta_agent"]},
    },
    "seats": [
        {"seat": "design-office-20261029-1", "committer_email": "design-office-20261029-1@seat.invalid",
         "role": "design", "machine": "office", "seated_by": "the person", "status": "active",
         "owns": ["design"], "paths": ["*", "contracts/"], "excludes": []},
    ],
}


def name(n):
    return "meta-office-%s-%d" % (TODAY, n)


def run(cwd, *cmd, env=None):
    return subprocess.run(list(cmd), cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")


class NextName(unittest.TestCase):
    def test_a_name_used_elsewhere_is_skipped(self):
        self.assertEqual(seats.next_name(TABLE, "meta", "office", "20261109", also_used=["meta-office-20261109-1"]),
                         "meta-office-20261109-2")
        # names of another role, machine or date, and names that are not seat names, change nothing
        self.assertEqual(seats.next_name(TABLE, "meta", "office", "20261109",
                                         also_used=["meta-office-20261110-1", "design-office-20261109-1", "x"]),
                         "meta-office-20261109-1")


class FixtureRepo(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="seat-names-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        os.makedirs(os.path.join(self.dir, "contracts", "tools"))
        os.makedirs(os.path.join(self.dir, "hooks-none"))
        shutil.copy(os.path.join(REPO, "bootstrap.py"), self.dir)
        shutil.copy(os.path.join(REPO, "contracts", "tools", "seats.py"), os.path.join(self.dir, "contracts", "tools"))
        self.write("contracts/seats.json", seats.dump(TABLE))
        self.git("init", "-q")
        self.git("config", "user.name", "a person")
        self.git("config", "user.email", "person@example.invalid")
        self.git("config", "core.hooksPath", "hooks-none")
        self.git("config", "commit.gpgsign", "false")
        self.git("config", "meta-agent.machine", "office")
        self.commit("start", "bootstrap.py", "contracts")

    def git(self, *args, env=None):
        p = run(self.dir, "git", *args, env=env)
        self.assertEqual(p.returncode, 0, "git %s: %s" % (" ".join(args), p.stderr))
        return p.stdout

    def commit(self, message, *paths, committer=None):
        env = dict(os.environ)
        if committer:
            env.update(GIT_COMMITTER_NAME="seat:" + committer, GIT_COMMITTER_EMAIL=committer + "@seat.invalid")
        self.git("add", *paths)
        self.git("commit", "-q", "--allow-empty", "-m", message, env=env)

    def write(self, relpath, text):
        path = os.path.join(self.dir, relpath)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def table(self):
        return seats.load(os.path.join(self.dir, "contracts", "seats.json"))

    def seat(self, *args, env=None):
        return run(self.dir, sys.executable, "bootstrap.py", "seat", *args, env=env)

    def offered(self, p):
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        return p.stdout.split()[1]

    def lock_path(self):
        out = self.git("rev-parse", "--git-path", "seat.lock").strip()
        return os.path.join(self.dir, out)


class NamesUsedElsewhere(FixtureRepo):
    def test_a_name_only_in_a_tracked_file_is_skipped(self):
        self.write("docs/note.md", "a test clone seated %s there\n" % name(1))
        self.commit("a note", "docs/note.md")
        self.assertEqual(self.offered(self.seat("meta")), name(2))

    def test_a_name_only_in_a_committer_line_is_skipped(self):
        self.commit("work in a clone", committer=name(1))
        self.assertEqual(self.offered(self.seat("meta")), name(2))

    def test_tracked_files_and_history_together(self):
        self.write("docs/note.md", "%s\n" % name(1))
        self.commit("a note", "docs/note.md", committer=name(2))
        self.assertEqual(self.offered(self.seat("meta")), name(3))
        self.assertEqual(self.offered(self.seat("meta", "--machine", "office")), name(3))

    def test_without_git_it_says_so_and_reads_the_table_alone(self):
        self.write("docs/note.md", "%s\n" % name(1))
        self.commit("a note", "docs/note.md")
        env = dict(os.environ, PATH=os.path.join(self.dir, "no-such-dir"))
        p = self.seat("meta", "--machine", "office", env=env)
        self.assertEqual(self.offered(p), name(1))
        self.assertIn("seats.json alone", p.stdout)


class Lock(FixtureRepo):
    def test_a_held_lock_refuses_and_writes_nothing(self):
        before = seats.dump(self.table())
        with open(self.lock_path(), "w", encoding="utf-8") as f:
            f.write("held by a test\n")
        env = dict(os.environ, META_AGENT_SEAT_LOCK_WAIT="0.5")
        p = self.seat("meta", "--write", env=env)
        self.assertNotEqual(p.returncode, 0, p.stdout)
        self.assertIn("seat.lock", p.stderr)
        self.assertIn("remove", p.stderr)
        self.assertEqual(seats.dump(self.table()), before)
        self.assertTrue(os.path.exists(self.lock_path()), "a lock it did not take is not removed")

    def test_a_second_write_waits_and_takes_the_next_name(self):
        # the first session holds the lock and writes its entry while the second is already running
        with open(self.lock_path(), "w", encoding="utf-8") as f:
            f.write("held by the first session\n")
        env = dict(os.environ, META_AGENT_SEAT_LOCK_WAIT="20")
        second = subprocess.Popen([sys.executable, "bootstrap.py", "seat", "meta", "--write"], cwd=self.dir, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
        time.sleep(1.0)
        first = copy.deepcopy(TABLE)
        first["seats"].append(seats.entry_for(TABLE, name(1), "self"))
        self.write("contracts/seats.json", seats.dump(first))
        os.remove(self.lock_path())
        out, err = second.communicate(timeout=60)
        self.assertEqual(second.returncode, 0, out + err)
        self.assertEqual(out.split()[1], name(2))
        table = self.table()
        self.assertEqual(seats.table_problems(table), [])
        self.assertEqual([s["seat"] for s in table["seats"]][1:], [name(1), name(2)])
        self.assertFalse(os.path.exists(self.lock_path()), "the lock is removed after the write")

    def test_two_writes_in_a_row_take_two_names(self):
        self.assertEqual(self.offered(self.seat("meta", "--write")), name(1))
        self.assertEqual(self.offered(self.seat("meta", "--write")), name(2))
        self.assertEqual(seats.table_problems(self.table()), [])


if __name__ == "__main__":
    unittest.main()
