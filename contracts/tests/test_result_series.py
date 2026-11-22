# -*- coding: utf-8 -*-
"""A result card that quotes a series (tasks/034, rheo-4; at the ask 20261122-meta-macbook-20261122-1-1).

Run from the repository root:  python -m unittest discover -s contracts/tests

Of two unrelated kinds on purpose (the person, 2026-11-11): the members' results of the accepted hub fixtures
under contracts/examples/hub/, an MD agent under a DFT→MD hub and a heat-conduction agent under a photonic hub.
Check 1 takes series[] on a result; check 2 judges each series as it judges a number: every part's unit is in
contracts/units.json, every point holds one number per part, and the grade is the one derived from its source
and value_kind.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
RESULTS = [os.path.join("dft-md", "hoomd-h2-bond", "outbox", "result-hoomd-h2-bond-r2.json"),
           os.path.join("photonic-heating", "fenics-waveguide-heat", "outbox", "result-fenics-waveguide-heat-r2.json")]


def a_series(card, **change):
    """A series read off the same record as the card's first number, with that number's source and grade."""
    n = card["numbers"][0]
    s = {"name": "a_series", "parts": [{"name": "t", "unit": "s", "description": "time"},
                                       {"name": "x", "unit": n["unit"], "description": "the quantity at that time"}],
         "points": [[0.0, 0.0], [0.5, 1.0], [1.0, 1.5]],
         "source": n["source"], "grade": n["grade"], "value_kind": n["value_kind"],
         "conditions": n.get("conditions") or {}}
    s.update(change)
    return s


class ResultSeries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="result-series-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def judge(self, rel, series):
        with open(os.path.join(REPO, "contracts", "examples", "hub", rel), encoding="utf-8") as f:
            card = json.load(f)
        card["series"] = [series(card)]
        member = os.path.basename(os.path.dirname(os.path.dirname(rel)))
        dest = os.path.join(self.tmp, member, "outbox")
        shutil.rmtree(os.path.join(self.tmp, member), ignore_errors=True)
        os.makedirs(dest)
        with open(os.path.join(dest, os.path.basename(rel)), "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2, ensure_ascii=False)
        run = subprocess.run([sys.executable, VALIDATE, self.tmp, "--checks", "1,2"], cwd=REPO,
                             capture_output=True, text=True)
        return run.returncode, run.stdout + run.stderr

    def test_a_series_is_taken(self):
        for rel in RESULTS:
            code, out = self.judge(rel, lambda card: a_series(card))
            self.assertEqual(code, 0, rel + "\n" + out)

    def test_a_point_short_of_its_parts_is_refused(self):
        for rel in RESULTS:
            code, out = self.judge(rel, lambda card: a_series(card, points=[[0.0, 0.0], [0.5]]))
            self.assertNotEqual(code, 0, rel)
            self.assertIn("check 2", out)

    def test_a_part_in_no_registered_unit_is_refused(self):
        for rel in RESULTS:
            code, out = self.judge(rel, lambda card: a_series(card, parts=[
                {"name": "t", "unit": "fortnight", "description": "time"},
                {"name": "x", "unit": card["numbers"][0]["unit"], "description": "the quantity"}]))
            self.assertNotEqual(code, 0, rel)
            self.assertIn("check 2", out)

    def test_a_grade_stated_by_hand_is_refused(self):
        for rel in RESULTS:
            code, out = self.judge(rel, lambda card: a_series(card, grade="E1"))
            self.assertNotEqual(code, 0, rel)
            self.assertIn("check 2", out)

    def test_a_series_without_points_is_refused(self):
        for rel in RESULTS:
            code, _ = self.judge(rel, lambda card: a_series(card, points=[]))
            self.assertNotEqual(code, 0, rel)


if __name__ == "__main__":
    unittest.main()
