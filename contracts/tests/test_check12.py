# -*- coding: utf-8 -*-
"""Tests of check 12 on a reference printed in another unit than the measured quantity: the comparison is made in
the reference's printed unit, the measured value converted into it by the registry's factor, and a tolerance the
rule derived is in it (the person, 2026-11-20, "Compare in its printed unit (Recommended)"; tasks/032, dftmd-10).

Run from the repository root:  python -m unittest discover -s contracts/tests

Of two unrelated kinds: a DFT rest length in bohr against a bond length printed in angstrom, and a simulated
viscosity in Pa.s against a measured one printed in mPa.s. Every value is a test value.
"""
import copy
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts"))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import validate  # noqa: E402
import units as U  # noqa: E402

C = validate.Contracts()
RULE = {"chosen_by": "rule", "rule": "docs/ideas/20261118.md", "derived_by": "computed:tolerance_from_reference@v5",
        "from": "last_printed_digit"}


def task(run_value, run_unit, printed_unit, tolerance):
    f, why = U.factor(C.units, run_unit, printed_unit)
    assert why is None, why
    return {"id": "sci-1", "name": "a test comparison", "verdict": "fail",
            "reference": {"kind": "source", "ref": "a test reference", "unit": printed_unit},
            "measured": {"value": run_value * f, "unit": printed_unit,
                         "converted_from": {"value": run_value, "unit": run_unit},
                         "converted_by": "computed:unit_convert@v1"},
            "tolerance": dict(RULE, value=tolerance, unit=printed_unit),
            "agreement": {"value": 0.0, "unit": printed_unit}}


KINDS = [task(1.4235809566, "bohr", "Angstrom", 5e-06), task(1.2, "Pa.s", "mPa.s", 0.05)]


def judge(t):
    report = validate.Report(quiet=True)
    validate.check12([("x/validation_report.json", {"card": "validation_report", "scientific": {"tasks": [t]}})],
                     C, report, REPO)
    return [m for _, _, m in report.fails]


class ComparedInThePrintedUnit(unittest.TestCase):
    def test_a_comparison_in_the_printed_unit_passes(self):
        for t in KINDS:
            self.assertEqual(judge(t), [], t["reference"]["unit"])

    def test_a_value_not_converted_by_the_registry_fails(self):
        for t in KINDS:
            t = copy.deepcopy(t)
            t["measured"]["value"] *= 1.01
            self.assertTrue(any("registry's factor" in m for m in judge(t)))

    def test_a_conversion_across_dimensions_fails(self):
        t = copy.deepcopy(KINDS[1])
        t["measured"]["converted_from"]["unit"] = "m^2/s"
        self.assertTrue(any("no factor of the registry" in m for m in judge(t)))

    def test_the_measured_value_the_tolerance_and_the_agreement_are_in_the_printed_unit(self):
        for t, run_unit in zip(KINDS, ("bohr", "Pa.s")):
            for field in ("measured", "tolerance", "agreement"):
                bad = copy.deepcopy(t)
                bad[field]["unit"] = run_unit
                if field == "measured":
                    bad["measured"].pop("converted_from")
                    bad["measured"].pop("converted_by")
                self.assertTrue(any("printed" in m for m in judge(bad)), (field, run_unit))

    def test_a_tolerance_the_person_gave_keeps_its_own_unit(self):
        t = copy.deepcopy(KINDS[0])
        t["tolerance"] = {"value": 0.01, "unit": "bohr", "chosen_by": "human"}
        self.assertEqual(judge(t), [])

    def test_no_printed_unit_no_comparison_unit_is_asked(self):
        t = copy.deepcopy(KINDS[0])
        del t["reference"]["unit"]
        t["tolerance"]["unit"] = "bohr"
        self.assertEqual(judge(t), [])


if __name__ == "__main__":
    unittest.main()
