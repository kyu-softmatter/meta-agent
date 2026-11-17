# -*- coding: utf-8 -*-
"""Tests of bundle check B6: a number in a bundle's CLAUDE.md is in its snapshot, and a unit is not a number
(tasks/016: the Tools section of a bundle prints the unit a tool contract names).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts"))
import validate  # noqa: E402


class B6(unittest.TestCase):
    def judge(self, text, numbers=()):
        d = tempfile.mkdtemp(prefix="b6-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "envelope"))
        with open(os.path.join(d, "envelope", "snapshot.json"), "w", encoding="utf-8") as f:
            json.dump({"kb_version": "kb@x", "entries": [], "numbers": [{"value": n} for n in numbers]}, f)
        with open(os.path.join(d, "CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write(text)
        report = validate.Report(quiet=True)
        validate.checkB6(d, "bundle", report)
        return [m for _, _, m in report.fails]

    def test_a_unit_a_contract_names_is_not_a_number(self):
        # two unrelated kinds of tool: an instrument's status and a simulation box
        self.assertEqual(self.judge("- output: `gap` (number, m), `temperature` (number, K), `density` (number, kg/m^3)\n"), [])
        self.assertEqual(self.judge("- output: `volume` (number, m^3), `area` (number, m^2), `g` (number, m/s^2), "
                                    "`rho` (number, g/cm^3), `fraction` (number, 1), `count` (integer, 1)\n"), [])

    def test_a_number_beside_a_unit_is_still_read(self):
        self.assertEqual(len(self.judge("The gap is 3 m^3 wide.\n")), 1)
        self.assertEqual(len(self.judge("- output: `fraction` (number, 1); it never exceeds 1\n")), 1)
        self.assertEqual(len(self.judge("A box of 2 m^2.\n", numbers=(3,))), 1)
        self.assertEqual(self.judge("A box of 2 m^2.\n", numbers=(2,)), [])


if __name__ == "__main__":
    unittest.main()
