"""Template v26 (meta_agent/failures.jsonl rheotool-28; the design role's reply f071852, item a): a reference its source
gives as exact has no printed digit to be uncertain in. A scientific task marks it (measure.exact, the stated field to
true), the bundle hands the mark to tolerance_from_reference@v4, and the run's own error alone gives the tolerance; with
no run error estimated the task stays undecided. Under v25 such a reference, printed with few digits, lent the task half
of its last digit, a tolerance the run had not earned.

The two unrelated kinds of the v23 test, a flow coefficient and a spectral peak, each converging at second order with
its resolution, so that the finer result's true error equals its two-grid estimate. Every bundle call runs in a fresh
process.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import template as template_mod
from meta_agent.tests import test_template_v23 as v23
from meta_agent.tests import test_template_v24 as v24

V25, V26 = template_mod.SOURCES["v25"], template_mod.SOURCES["v26"]
RULE = "tolerance_from_reference@v4"
# a reference of each kind printed with few digits: half its last digit is wider than three times the run's error
SHORT = {"flow": "2.9", "spectrum": "502"}


def exact_task(kind, stated, printed):
    t = v23.task(kind, stated=stated, printed=printed)
    t["measure"]["exact"] = {"value": True}
    return t


class AnExactReference(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v26-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_short_exact_reference_passes_by_its_half_digit_under_v25_and_fails_marked_under_v26(self):
        for kind in v23.KINDS:
            ref = float(SHORT[kind])
            t = exact_task(kind, stated=ref, printed=SHORT[kind])
            # v25 cannot take the mark (TheBuilder below), so its task carries none: the half digit judges it
            r25 = v23.validate(v23.compose(self.tmp, kind + "-v25", [v23.task(kind, stated=ref, printed=SHORT[kind])], template=V25))
            self.assertEqual((r25["verdict"], r25["tolerance"]["from"]), ("pass", "last_printed_digit"), (kind, r25))
            r26 = v23.validate(v23.compose(self.tmp, kind + "-v26", [t], template=V26))
            self.assertEqual((r26["verdict"], r26["tolerance"]["from"]), ("fail", "run_numerical_error"), (kind, r26))

    def test_the_true_limit_marked_exact_passes_by_three_times_the_run_s_error(self):
        for kind in v23.KINDS:
            fine, e = v24.run_error(kind)
            limit = v23.KINDS[kind][2]
            r = v23.validate(v23.compose(self.tmp, kind, [exact_task(kind, stated=limit, printed=repr(limit))], template=V26))
            self.assertEqual(r["verdict"], "pass", (kind, r))
            tol = r["tolerance"]
            self.assertEqual((tol["chosen_by"], tol["from"], tol["derived_by"]), ("rule", "run_numerical_error", "computed:" + RULE), kind)
            self.assertAlmostEqual(tol["value"], 3 * e, places=12)
            run = r["refinement"]["tolerance_run"]
            self.assertEqual((run["skill"], run["outputs"]["factor"]), (RULE, 3.0), kind)

    def test_an_exact_reference_with_no_run_error_is_undecided(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            b = v23.compose(self.tmp, kind + "-empty", [exact_task(kind, stated=limit, printed=SHORT[kind])],
                            rows={"order": (None, "1")}, template=V26)
            r = v23.validate(b)
            self.assertEqual(r["verdict"], "undecided", (kind, r))
            self.assertIn("exact", r["reason"], kind)

    def test_a_reference_not_marked_is_judged_as_under_v25(self):
        for kind in v23.KINDS:
            t = v23.task(kind, stated=float(SHORT[kind]), printed=SHORT[kind])
            r25 = v23.validate(v23.compose(self.tmp, kind + "-plain25", [t], template=V25))
            r26 = v23.validate(v23.compose(self.tmp, kind + "-plain26", [t], template=V26))
            self.assertEqual((r26["verdict"], r26["tolerance"]), (r25["verdict"], dict(r25["tolerance"], derived_by="computed:" + RULE)), kind)


class TheBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v26-build-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_template_whose_rule_cannot_take_the_mark_is_refused(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            with self.assertRaises(ValueError) as cm:
                v23.compose(self.tmp, kind + "-old", [exact_task(kind, stated=limit, printed=SHORT[kind])],
                            template=template_mod.SOURCES["v24"])
            self.assertIn("exact", str(cm.exception), kind)


class TheVersion(unittest.TestCase):
    def test_v26_is_the_latest_and_changes_one_script_and_its_card(self):
        self.assertIn("v26", template_mod.SOURCES)                  # v27 is the latest since the runtime gate reads engines
        changed = sorted(r for r in cards.tree_files(V25) if cards.sha256_file(os.path.join(V25, r)) != cards.sha256_file(os.path.join(V26, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        m = cards.load_json(os.path.join(V26, "TEMPLATE.json"))
        self.assertEqual(m["tolerance_rule"]["skill"], RULE)
        self.assertIn(RULE, m["common_skills"])
        self.assertNotIn("tolerance_from_reference@v3", m["common_skills"])


if __name__ == "__main__":
    unittest.main()
