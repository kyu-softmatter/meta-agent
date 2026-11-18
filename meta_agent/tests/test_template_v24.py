"""Template v24 (the person, 2026-11-18, 'Yes, factor 3'; meta_agent/failures.jsonl rheotool-26): a two-grid estimate
of the run's own error enters the tolerance rule three times over, Roache's factor of safety for a comparison of two
grids. The bundle hands tolerance_from_reference@v3 how the refinement's skill estimated the error (TEMPLATE.json
run_error_from), and the record names it.

The two unrelated kinds of the v23 test, a flow coefficient and a spectral peak, each converging at second order with
its resolution: there the finer result's true error equals its two-grid estimate, so with no factor a correct run sits
on the boundary of its own tolerance. A reference twice the run's error away fails under v23 and passes under v24; one
four times away fails under both. Every bundle call runs in a fresh process.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import runner as runner_mod
from meta_agent.tests import test_template_v23 as v23

V24 = template_mod.SOURCES["v24"]
RULE = "tolerance_from_reference@v3"
NOW = "2026-11-18T21:00:00Z"


def run_error(kind):
    fine, built = v23.finer(kind)
    return fine, runner_mod.run(v23.ERROR, {"fine": fine, "coarse": built, "refinement_ratio": 2.0, "order": 2.0},
                                now=NOW)["outputs"]["error"]


def away(kind, times):
    """A reference `times` the run's own error from the finer result, on the side of the limit, printed to nine
    decimals so that the run's error outweighs half its last digit."""
    fine, e = run_error(kind)
    limit = v23.KINDS[kind][2]
    side = 1.0 if limit >= fine else -1.0
    return fine + side * times * e


class AFactorOfThree(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v24-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_tolerance_is_three_times_the_two_grid_estimate(self):
        for kind in v23.KINDS:
            fine, e = run_error(kind)
            limit = v23.KINDS[kind][2]
            r = v23.validate(v23.compose(self.tmp, kind, [v23.task(kind, stated=limit, printed="%.9f" % limit)], template=V24))
            self.assertEqual(r["verdict"], "pass", (kind, r))
            tol = r["tolerance"]
            self.assertEqual((tol["chosen_by"], tol["from"], tol["derived_by"]), ("rule", "run_numerical_error", "computed:" + RULE), kind)
            self.assertAlmostEqual(tol["value"], 3 * e, places=12)
            self.assertEqual(r["refinement"]["run_error_from"], "two_grids", kind)
            self.assertEqual(r["refinement"]["tolerance_run"]["outputs"]["factor"], 3.0, kind)

    def test_twice_the_run_s_error_fails_without_the_factor_and_passes_with_it(self):
        for kind in v23.KINDS:
            ref = away(kind, 2.0)
            t = v23.task(kind, stated=ref, printed="%.9f" % ref)
            self.assertEqual(v23.validate(v23.compose(self.tmp, kind + "-v23", [t], template=v23.V23))["verdict"], "fail", kind)
            self.assertEqual(v23.validate(v23.compose(self.tmp, kind + "-v24", [t], template=V24))["verdict"], "pass", kind)

    def test_four_times_the_run_s_error_fails_with_the_factor_too(self):
        for kind in v23.KINDS:
            ref = away(kind, 4.0)
            t = v23.task(kind, stated=ref, printed="%.9f" % ref)
            self.assertEqual(v23.validate(v23.compose(self.tmp, kind + "-far", [t], template=V24))["verdict"], "fail", kind)

    def test_an_empty_row_still_leaves_the_half_digit_and_no_factor(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            b = v23.compose(self.tmp, kind + "-empty", [v23.task(kind, stated=limit, printed=repr(limit))],
                            rows={"order": (None, "1")}, template=V24)
            r = v23.validate(b)
            self.assertEqual(r["tolerance"]["from"], "last_printed_digit", kind)
            self.assertIsNone(r["refinement"]["run_error_from"], kind)
            self.assertIsNone(r["refinement"]["tolerance_run"]["outputs"]["factor"], kind)

    def test_a_person_s_tolerance_still_overrides(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            human = {"value": 10.0, "unit": "1", "chosen_by": "human"}
            r = v23.validate(v23.compose(self.tmp, kind + "-person", [v23.task(kind, stated=limit, tolerance=human)], template=V24))
            self.assertNotIn("refinement", r, kind)
            self.assertEqual(r["tolerance"], human, kind)


class TheVersion(unittest.TestCase):
    def test_v24_is_the_latest_and_changes_one_script(self):
        v23_path = template_mod.SOURCES["v23"]
        self.assertIn("v24", template_mod.SOURCES)                  # v25 is the latest since the third run
        changed = sorted(r for r in cards.tree_files(v23_path)
                         if cards.sha256_file(os.path.join(v23_path, r)) != cards.sha256_file(os.path.join(V24, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        m = cards.load_json(os.path.join(V24, "TEMPLATE.json"))
        self.assertEqual(m["tolerance_rule"]["skill"], RULE)
        self.assertIn(RULE, m["common_skills"])
        self.assertNotIn("tolerance_from_reference@v2", m["common_skills"])


if __name__ == "__main__":
    unittest.main()
