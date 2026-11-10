# -*- coding: utf-8 -*-
"""Tests of a session seating itself: check 6 at commit time and over a history, in a temporary repository
(meta_agent/tasks/009, part 3). The hook that runs is the real one.

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import datetime
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_seat_commit import TempRepo, run  # noqa: E402


class SelfRegistrationAtCommit(TempRepo):
    def seat(self, role):
        p = run(self.dir, sys.executable, "bootstrap.py", "seat", role, "--write")
        self.assertEqual(p.returncode, 0, p.stderr)
        return p.stdout.split()[1]

    def test_a_meta_session_seats_itself_then_works(self):
        name = self.seat("meta")
        self.assertEqual(name, "meta-office-%s-1" % datetime.date.today().strftime("%Y%m%d"))
        p = self.tool(name, "contracts/seats.json", message="contracts/seats: %s seats itself" % name)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.head(), ("%s@seat.invalid|person@example.invalid" % name, ["contracts/seats.json"]))
        self.write("meta_agent/work.txt", "its first work\n")
        p = self.tool(name, "meta_agent/work.txt")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        # the history is judged as a whole: the registration commit passes check 6
        first = self.git("rev-list", "--max-parents=0", "HEAD").strip()
        p = run(self.dir, sys.executable, "contracts/validate.py", "--checks", "6", "--commit-range", first + "..HEAD")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("commits=2", p.stdout)

    def test_a_wider_entry_is_refused_by_the_tool_and_by_the_hook(self):
        name = self.seat("meta")
        path = os.path.join(self.dir, "contracts", "seats.json")
        with open(path, encoding="utf-8") as f:
            table = json.load(f)
        table["seats"][-1]["paths"].append("contracts/")
        self.write("contracts/seats.json", json.dumps(table, indent=2, ensure_ascii=False) + "\n")
        n = self.count()
        p = self.tool(name, "contracts/seats.json")
        self.assertEqual(p.returncode, 1)
        self.assertIn("paths differ", p.stderr)
        # without the tool, the hook is what stands in the way
        env = dict(os.environ, GIT_COMMITTER_NAME="seat:" + name, GIT_COMMITTER_EMAIL=name + "@seat.invalid")
        self.git("add", "contracts/seats.json")
        p = run(self.dir, "git", "commit", "-m", "wider", env=env)
        self.assertNotEqual(p.returncode, 0)
        self.assertRegex(p.stdout + p.stderr, r"FAIL\s+check 6")
        self.assertEqual(self.count(), n)

    def test_a_registration_with_another_file_is_refused(self):
        name = self.seat("meta")
        self.write("meta_agent/work.txt", "too early\n")
        p = self.tool(name, "contracts/seats.json", "meta_agent/work.txt")
        self.assertEqual(p.returncode, 1)
        env = dict(os.environ, GIT_COMMITTER_NAME="seat:" + name, GIT_COMMITTER_EMAIL=name + "@seat.invalid")
        self.git("add", "contracts/seats.json", "meta_agent/work.txt")
        p = run(self.dir, "git", "commit", "-m", "both", env=env)
        self.assertNotEqual(p.returncode, 0)
        self.assertRegex(p.stdout + p.stderr, r"FAIL\s+check 6")



if __name__ == "__main__":
    unittest.main()
