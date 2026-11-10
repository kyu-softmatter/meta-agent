# -*- coding: utf-8 -*-
"""Tests of what the pre-commit gate judges: the tree the commit would make, with that tree's own
contracts (the person, 2026-11-09, docs/ideas/20261109.md; meta_agent/tasks/009 part 7). In a temporary
repository with the real hook.

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_seat_commit import DESIGN, META, TempRepo, run  # noqa: E402

UNFINISHED = '{\n  "card": "agent_goal",\n  "id": "req-halfway"\n'


class CommitGate(TempRepo):
    def test_another_seats_unfinished_card_does_not_stop_a_commit(self):
        self.write("meta_agent/requests/req-halfway/agent_goal.json", UNFINISHED)      # the meta seat, mid-write
        p = run(self.dir, sys.executable, "contracts/validate.py", "--quiet")
        self.assertEqual(p.returncode, 1, "the working tree as a whole is still refused")
        self.write("NOTES.md", "the design seat's own work\n")
        p = self.tool(DESIGN, "NOTES.md")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.head()[1], ["NOTES.md"])
        self.assertIn("@index", p.stdout + p.stderr)

    def test_a_seats_own_unfinished_card_still_stops_its_commit(self):
        self.write("meta_agent/requests/req-halfway/agent_goal.json", UNFINISHED)
        n = self.count()
        p = self.tool(META, "meta_agent/requests/req-halfway/agent_goal.json")
        self.assertEqual(p.returncode, 1)
        self.assertRegex(p.stdout + p.stderr, r"FAIL\s+check 1")
        self.assertEqual(self.count(), n)

    def test_another_seats_half_edited_contracts_do_not_bend_a_commit(self):
        # the design seat is in the middle of editing a schema and the validator; neither is staged
        self.write("contracts/schemas/agent_goal.schema.json", '{ "half": ')
        for half_edited in ("contracts/tools/notes.py", "contracts/validate.py"):
            with open(os.path.join(self.dir, *half_edited.split("/")), "a", encoding="utf-8") as f:
                f.write("\ndef broken(:\n")
        self.write("meta_agent/work.txt", "the meta seat's own work\n")
        p = self.tool(META, "meta_agent/work.txt")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.head()[1], ["meta_agent/work.txt"])

    def test_the_boundary_is_still_judged(self):
        self.write("contracts/extra.txt", "x\n")
        self.git("add", "contracts/extra.txt")
        env = dict(os.environ, GIT_COMMITTER_NAME="seat:" + META, GIT_COMMITTER_EMAIL=META + "@seat.invalid")
        p = run(self.dir, "git", "commit", "-m", "outside", env=env)
        self.assertNotEqual(p.returncode, 0)
        self.assertRegex(p.stdout + p.stderr, r"FAIL\s+check 6")


if __name__ == "__main__":
    unittest.main()
