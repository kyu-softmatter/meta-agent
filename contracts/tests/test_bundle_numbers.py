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


    def test_the_unit_one_is_passed_whatever_follows_it_in_the_brackets(self):
        self.assertEqual(self.judge("- input: `fraction` (number, 1, required; the volume fraction), `n` (integer, 1; a count)\n"), [])
        self.assertEqual(len(self.judge("- input: `fraction` (number, 12, required)\n")), 1)


class Check3(unittest.TestCase):
    """A page shows where a claim was read; a numeral of a locus is the card's."""

    def judge(self, card, text):
        d = tempfile.mkdtemp(prefix="c3-")
        self.addCleanup(shutil.rmtree, d, True)
        with open(os.path.join(d, "page.md"), "w", encoding="utf-8") as f:
            f.write(text)
        report = validate.Report(quiet=True)
        validate.check3([(os.path.join(d, "card.json"), card)], {d: [os.path.join(d, "page.md")]}, report, d)
        return [m for _, _, m in report.fails]

    def test_a_numeral_of_a_locus_may_stand_on_the_page_and_no_other_text_of_a_card(self):
        # two unrelated kinds of source: a notebook's cells and a manual's page
        card = {"claims": [{"claim": "the stage ends after 13000 moves", "loci": ["section 5, cells [4] to [8]"]},
                           {"claim": "the cone is truncated", "locus": "manual, page 212"}], "numbers": [{"value": 7.5}]}
        self.assertEqual(self.judge(card, "Read in section 5, cells [4] to [8], and on page 212; the value is 7.5.\n"), [])
        self.assertEqual(len(self.judge(card, "The stage ends after 13000 moves.\n")), 1)      # a claim's text gives the page no number


if __name__ == "__main__":
    unittest.main()
