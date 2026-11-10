# -*- coding: utf-8 -*-
"""Tests of contracts/tools/tasks.py: the task index, claims and what check 20 refuses (tasks/009, part 4).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import seats  # noqa: E402
import tasks  # noqa: E402

SEATS = {
    "machines": {"office": "a computer"},
    "roles": {"design": {"paths": ["*"], "excludes": [], "owns": []}, "meta": {"paths": ["meta_agent/"], "excludes": [], "owns": []}},
    "seats": [seats.entry_for({"roles": {"design": {"paths": ["*"]}, "meta": {"paths": ["meta_agent/"]}}}, n, "the person")
              for n in ("design-office-20261029-1", "design-office-20261109-1", "meta-office-20261029-1", "meta-office-20261109-1")],
}
D1, D2, M1, M2 = (s["seat"] for s in SEATS["seats"])


class Tree(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="tasks-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.tdir = os.path.join(self.dir, "meta_agent", "tasks")
        os.makedirs(os.path.join(self.tdir, "claims"))
        self.rows = []
        self.task("001", "done", ["meta"], done_commit="abc1234")
        self.task("002", "open", ["design", "meta"], ["001"])
        self.task("003", "open", ["meta"], ["002"])

    def task(self, tid, status, roles, deps=(), **extra):
        name = "%s-a-task.md" % tid
        with open(os.path.join(self.tdir, name), "w", encoding="utf-8") as f:
            f.write("# %s\n\n**Status:** %s, 2026-11-09.\n" % (tid, status))
        row = dict({"id": tid, "file": name, "status": status, "roles": roles, "depends_on": list(deps), "opened": "2026-11-09"}, **extra)
        self.rows = [r for r in self.rows if r["id"] != tid] + [row]
        self.index()

    def index(self):
        with open(os.path.join(self.tdir, "index.json"), "w", encoding="utf-8") as f:
            json.dump({"tasks": self.rows}, f)

    def claim(self, tid, seat, released=False):
        name = "%s-%s%s.json" % (tid, seat, "-released" if released else "")
        data = {"task": tid, "seat": seat}
        data.update({"released_at": "t", "why": "the session ended"} if released else {"claimed_at": "t"})
        with open(os.path.join(self.tdir, "claims", name), "w", encoding="utf-8") as f:
            json.dump(data, f)

    def problems(self):
        return [m for _, m in tasks.problems(self.dir, SEATS)]

    def test_a_clean_queue(self):
        self.assertEqual(self.problems(), [])
        self.assertEqual(tasks.next_task(self.dir, SEATS, "meta"), "002")
        self.assertEqual(tasks.next_task(self.dir, SEATS, "design"), "002")

    def test_a_claim_takes_the_role_and_leaves_the_other(self):
        self.claim("002", M1)
        self.assertEqual(self.problems(), [])
        self.assertIsNone(tasks.next_task(self.dir, SEATS, "meta"))        # 003 waits for 002
        self.assertEqual(tasks.next_task(self.dir, SEATS, "design"), "002")
        self.claim("002", D1)
        self.assertEqual(self.problems(), [])
        self.assertIsNone(tasks.next_task(self.dir, SEATS, "design"))

    def test_a_second_seat_of_the_same_role_is_refused_until_a_release(self):
        self.claim("002", M1)
        self.claim("002", M2)
        self.assertTrue(any("one seat holds a task's role" in m for m in self.problems()))
        self.claim("002", M1, released=True)
        self.assertEqual(self.problems(), [])
        self.assertEqual(sorted(tasks.holders(tasks.read(self.dir))["002"]), [M2])

    def test_what_else_is_refused(self):
        self.claim("003", M1)
        self.assertTrue(any("claimed before 002 is done" in m for m in self.problems()))
        os.remove(os.path.join(self.tdir, "claims", "003-%s.json" % M1))
        self.claim("002", "meta-office-20261109-9")
        self.assertTrue(any("not an active seat" in m for m in self.problems()))
        os.remove(os.path.join(self.tdir, "claims", "002-meta-office-20261109-9.json"))
        self.task("004", "open", ["design"])
        self.claim("004", M1)
        self.assertTrue(any("is a meta seat" in m for m in self.problems()))
        os.remove(os.path.join(self.tdir, "claims", "004-%s.json" % M1))
        self.claim("002", M1, released=True)
        self.assertTrue(any("a release without its claim" in m for m in self.problems()))

    def test_index_and_files_must_agree(self):
        with open(os.path.join(self.tdir, "005-no-row.md"), "w", encoding="utf-8") as f:
            f.write("**Status:** open\n")
        self.assertTrue(any("no row in index.json" in m for m in self.problems()))
        os.remove(os.path.join(self.tdir, "005-no-row.md"))
        self.rows[1]["status"] = "done"
        self.rows[1]["done_commit"] = "abc1234"
        self.index()
        self.assertTrue(any("Status line says 'open'" in m for m in self.problems()))
        self.rows[1].pop("done_commit")
        self.index()
        self.assertTrue(any("done without done_commit" in m for m in self.problems()))

    def test_a_claim_is_committed_by_its_own_seat(self):
        path = "meta_agent/tasks/claims/002-%s.json" % M1
        self.assertIsNone(tasks.claim_committer_problem(path, "A", M1 + "@seat.invalid"))
        self.assertIn("not by", tasks.claim_committer_problem(path, "A", D1 + "@seat.invalid"))
        self.assertIsNone(tasks.claim_committer_problem("meta_agent/tasks/index.json", "M", D1 + "@seat.invalid"))


class TheRepositorysQueue(unittest.TestCase):
    def test_it_is_clean(self):
        self.assertEqual(tasks.problems(REPO, seats.load()), [])


if __name__ == "__main__":
    unittest.main()
