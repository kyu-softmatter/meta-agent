"""Template v25 (failures.jsonl cfd-25; the intake card's third_inputs, 6c7a488): a refinement that names a third,
finer run observes the order of convergence from the three results through observed_order_of_convergence@v1, so the
run's own error needs no order from a source; the finest result is judged, and the rule is told three_or_more_grids,
so that no factor enters (the person, 2026-11-18). Where no order can be read, the half-digit branch applies.

Two unrelated kinds of the v23 test, a flow coefficient and a spectral peak, each converging at second order.

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

V25 = template_mod.SOURCES["v25"]
ORDER = "observed_order_of_convergence@v1"
NOW = "2026-11-18T21:30:00Z"


def task(kind, stated, printed):
    t = v23.task(kind, stated=stated, printed=printed)
    inp = v23.KINDS[kind][1]
    t["refinement"] = {"skill": v23.ERROR, "inputs": {inp: "finer_" + inp}, "ratio_row": "refinement_ratio",
                       "third_inputs": {inp: "finest_" + inp}}
    return t


def compose(tmp, name, sci, rows=None, template=V25):
    kind = name.split("-")[0]
    h, hf = v23.KINDS[kind][4], v23.KINDS[kind][5]
    given = {"finest_" + v23.KINDS[kind][1]: (hf / 2, "1")}
    given.update(rows or {})
    return v23.compose(tmp, name, sci, rows=given, template=template)


def values(kind):
    tool, inp, limit, c, h, hf = v23.KINDS[kind]
    return [limit + c * x * x for x in (h, hf, hf / 2)]


class AThirdRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v25-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_order_is_observed_and_the_finest_result_is_judged_with_no_factor(self):
        for kind in v23.KINDS:
            coarse, medium, fine = values(kind)
            # the reference a third of the way from the limit to the finest result: inside the run's error, not on its edge,
            # since the estimate is exact for a pure second-order model
            ref = v23.KINDS[kind][2] + (fine - v23.KINDS[kind][2]) / 3
            b = compose(self.tmp, kind, [task(kind, stated=ref, printed="%.9f" % ref)])
            self.assertIn(ORDER, os.listdir(os.path.join(b, "skills")), kind)
            r = v23.validate(b)
            self.assertEqual(r["verdict"], "pass", (kind, r))
            ref = r["refinement"]
            self.assertTrue(ref["order_run"]["outputs"]["observed"], kind)
            self.assertAlmostEqual(ref["order_run"]["outputs"]["order"], 2.0, places=9)
            self.assertEqual(ref["run_error_from"], "three_or_more_grids", kind)
            self.assertEqual(r["measured"], {"value": fine}, kind)
            want = runner_mod.run(v23.ERROR, {"fine": fine, "coarse": medium, "refinement_ratio": 2.0, "order": ref["order_run"]["outputs"]["order"]}, now=NOW)["outputs"]["error"]
            self.assertAlmostEqual(r["tolerance"]["value"], want, places=12)   # no factor on a three-grid estimate
            self.assertEqual(r["tolerance"]["from"], "run_numerical_error", kind)

    def test_an_empty_third_row_leaves_the_half_digit_and_says_why(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            b = compose(self.tmp, kind + "-empty", [task(kind, stated=limit, printed=repr(limit))],
                        rows={"finest_" + v23.KINDS[kind][1]: (None, "1")})
            r = v23.validate(b)
            self.assertEqual(r["tolerance"]["from"], "last_printed_digit", kind)
            self.assertIn("third run", r["refinement"]["run_error_not_estimated"], kind)

    def test_the_build_refuses_a_third_run_on_v24_or_with_a_row_it_lacks(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            with self.assertRaises(ValueError):
                compose(self.tmp, kind + "-v24", [task(kind, stated=limit, printed=repr(limit))], template=template_mod.SOURCES["v24"])
            t = task(kind, stated=limit, printed=repr(limit))
            t["refinement"]["third_inputs"] = {v23.KINDS[kind][1]: "nothing"}
            with self.assertRaises(ValueError):
                compose(self.tmp, kind + "-norow", [t])


class TheVersion(unittest.TestCase):
    def test_v25_is_the_latest_and_changes_one_script_and_its_card(self):
        v24 = template_mod.SOURCES["v24"]
        self.assertIn("v25", template_mod.SOURCES)                  # v26 is the latest since the exact reference
        changed = sorted(r for r in cards.tree_files(v24) if cards.sha256_file(os.path.join(v24, r)) != cards.sha256_file(os.path.join(V25, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        meta = cards.load_json(os.path.join(V25, "TEMPLATE.json"))
        self.assertEqual(meta["order_skill"], ORDER)
        self.assertIn(ORDER, meta["common_skills"])


if __name__ == "__main__":
    unittest.main()
