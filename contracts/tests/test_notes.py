# -*- coding: utf-8 -*-
"""Tests of contracts/tools/notes.py: notes between seats and what check 21 says (tasks/009, part 5).

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
import notes  # noqa: E402
import seats  # noqa: E402

ROLES = {"design": {"paths": ["*"]}, "meta": {"paths": ["meta_agent/"]}}
D, M, M2 = "design-office-20261029-1", "meta-office-20261029-1", "meta-office-20261109-1"
SEATS = {"machines": {"office": "a computer"}, "roles": ROLES,
         "seats": [seats.entry_for({"roles": ROLES}, n, "the person") for n in (D, M, M2)]}


class Notes(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="notes-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.ndir = os.path.join(self.dir, "meta_agent", "inbox", "seats")
        os.makedirs(self.ndir)

    def note(self, seat, n, **data):
        nid = "20261109-%s-%d" % (seat, n)
        with open(os.path.join(self.ndir, nid + ".json"), "w", encoding="utf-8") as f:
            json.dump(dict({"from": seat, "written_at": "t"}, **data), f)
        return nid

    def judge(self):
        fails, pending = notes.judge(self.dir, SEATS)
        return [m for _, m in fails], [m for _, m in pending]

    def test_an_ask_waits_for_its_role_until_a_reply(self):
        ask = self.note(M, 1, kind="ask", to_role="design", task="010", answers=None, text="A field for the tools a skill calls, please.")
        fails, pending = self.judge()
        self.assertEqual(fails, [])
        self.assertEqual(len(pending), 1)
        self.assertTrue(pending[0].startswith("for the design role, from %s on tasks/010:" % M))
        self.note(D, 1, kind="reply", answers=ask, text="Added in the manifest schema.")
        self.assertEqual(self.judge(), ([], []))

    def test_the_asker_may_withdraw(self):
        ask = self.note(M, 1, kind="ask", to_role="design", answers=None, text="Is the layout final?")
        self.note(M, 2, kind="withdrawn", answers=ask, text="Found it in plan.md 14-31.")
        self.assertEqual(self.judge(), ([], []))

    def test_what_is_refused(self):
        ask = self.note(M, 1, kind="ask", to_role="design", answers=None, text="x")
        self.note(M2, 1, kind="reply", answers=ask, text="a meta seat answers an ask to design")
        self.note(D, 1, kind="withdrawn", answers=ask, text="the design seat withdraws someone else's ask")
        self.note(D, 2, kind="reply", answers="20261109-%s-9" % M, text="a reply to nothing")
        self.note(M, 2, kind="ask", to_role="operator", answers=None, text="an unknown role")
        self.note(M, 3, kind="ask", to_role="design", answers=None, text="  ")
        self.note("meta-office-20261109-9", 1, kind="ask", to_role="design", answers=None, text="an unregistered seat")
        fails, pending = self.judge()
        for part in ("is a meta seat", "withdraws", "is not an ask in this folder", "to_role 'operator'", "no text", "is not a seat"):
            self.assertTrue(any(part in m for m in fails), part)
        self.assertEqual(len(pending), 3)   # the first ask (its reply and withdrawal were refused), the empty one, the unregistered seat's

    def test_a_note_is_committed_by_its_own_seat(self):
        path = "meta_agent/inbox/seats/20261109-%s-1.json" % M
        self.assertIsNone(notes.note_committer_problem(path, "A", M + "@seat.invalid"))
        self.assertIn("not by", notes.note_committer_problem(path, "A", D + "@seat.invalid"))

    def test_the_repository_has_nothing_refused(self):
        self.assertEqual(notes.judge(REPO, seats.load())[0], [])


if __name__ == "__main__":
    unittest.main()
