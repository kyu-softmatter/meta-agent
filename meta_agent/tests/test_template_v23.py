"""Template v23 (the person, 2026-11-18, 'Yes, refine and derive'; the intake card's scientific_tasks[].refinement,
32684cc): a scientific task that names a refinement and has no tolerance from the person is judged by the tolerance
the standing rule derives from the run's own numerical error. The bundle makes the call as built and again with the
finer inputs its rows hand, estimates the finer result's error with discretization_error_from_two_resolutions@v1 and
derives the tolerance with tolerance_from_reference@v2, both through its runner, and judges the finer result by it.

Two unrelated kinds whose results really depend on resolution: a flow coefficient that converges at second order with
the mesh spacing, and a spectral peak that converges at second order with the sampling step. Every bundle call runs in
a fresh process.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import runner as runner_mod
from meta_agent.src.validate import gate as gate_mod
from meta_agent.tests import test_template_v17 as v17

V23 = template_mod.SOURCES["v23"]
ERROR, RULE = "discretization_error_from_two_resolutions@v1", "tolerance_from_reference@v2"
NOW = "2026-11-18T19:00:00Z"
# each kind: tool, its resolution input, the limit, the coefficient of h^2, the built and the finer spacing
KINDS = {
    "flow": ("solve_flow", "mesh_size", 2.95, -0.12, 0.2, 0.1),
    "spectrum": ("scan_spectrum", "sample_step", 502.3, 0.5, 0.4, 0.2),
}


def adapter(limit, c, inp):
    return "def run(payload):\n    h = payload['%s']\n    return {'value': %r + %r * h * h}\n" % (inp, limit, c)


def contract(tool, inp):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": tool, "description": "the step",
            "inputs": {"type": "object", "required": [inp], "properties": {inp: {"type": "number", "unit": "1", "row": inp}}},
            "outputs": {"type": "object", "properties": {"value": {"type": "number", "unit": "1"}}},
            "errors": ["invalid_input"], "side_effects": "none", "safety_gate": {"required": False, "place": "no side effects"},
            "idempotent": True, "timeout_s": None}


def task(kind, stated, tolerance=None, refinement=True, printed=None):
    tool, inp, limit, c, h, hf = KINDS[kind]
    t = {"id": "sci-a", "name": "the converged value", "call": {"tool": tool, "input": {inp: h}},
         "measure": {"stated": {"value": stated}}, "reference": {"kind": "source", "ref": "a test's reference"},
         "expected_verdict": "pass"}
    if printed is not None:
        t["measure"]["printed"] = {"value": printed}
    if refinement:
        t["refinement"] = {"skill": ERROR, "inputs": {inp: "finer_" + inp}, "ratio_row": "refinement_ratio", "order_row": "order"}
    if tolerance:
        t["tolerance"] = tolerance
    return t


def compose(tmp, name, sci, rows=None, template=V23):
    kind = name.split("-")[0]
    tool, inp, limit, c, h, hf = KINDS[kind]
    con = contract(tool, inp)
    given = {inp: (h, "1"), "finer_" + inp: (hf, "1"), "refinement_ratio": (h / hf, "1"), "order": (2.0, "1")}
    if rows is not None:
        given.update(rows)
    params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in given.items()]}
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([con]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    path = os.path.join(tmp, name)
    bundle_mod.compose(template, path, fill, [{"name": tool, "contract": con, "adapter_source": adapter(limit, c, inp), "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": params},
                       [{"id": "if-a", "call": {"tool": tool, "input": {inp: h}}, "expected_verdict": "pass"}], sci, [],
                       skills=[], simulation=False)
    return path


def validate(bundle):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "validate_tasks.py"), "--json"],
                       capture_output=True, text=True, cwd=bundle)
    return json.loads(p.stdout)["scientific"]["tasks"][0]


def finer(kind):
    tool, inp, limit, c, h, hf = KINDS[kind]
    return limit + c * hf * hf, limit + c * h * h


class TheRunsOwnErrorJudges(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v23-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_tolerance_comes_from_the_refinement_and_the_finer_result_is_judged(self):
        for kind in KINDS:
            fine, built = finer(kind)
            want = runner_mod.run(ERROR, {"fine": fine, "coarse": built, "refinement_ratio": 2.0, "order": 2.0}, now=NOW)["outputs"]["error"]
            limit = KINDS[kind][2]
            # printed to nine decimals, so that the run's own error outweighs half its last digit
            b = compose(self.tmp, kind, [task(kind, stated=limit, printed="%.9f" % limit)])
            r = validate(b)
            self.assertEqual(r["verdict"], "pass", (kind, r))          # the finer result lies within its own error of the limit
            tol = r["tolerance"]
            self.assertEqual((tol["chosen_by"], tol["from"], tol["derived_by"]), ("rule", "run_numerical_error", "computed:" + RULE), kind)
            self.assertAlmostEqual(tol["value"], want, places=12)
            self.assertEqual(r["measured"], {"value": fine}, kind)
            self.assertEqual(r["refinement"]["refines"], [KINDS[kind][1]], kind)
            self.assertEqual((r["refinement"]["as_built"], r["refinement"]["finer"]), (built, fine), kind)

    def test_a_reference_printed_with_few_digits_keeps_its_half_digit(self):
        for kind in KINDS:
            limit = KINDS[kind][2]
            r = validate(compose(self.tmp, kind + "-short", [task(kind, stated=limit, printed=repr(limit))]))
            self.assertEqual(r["tolerance"]["from"], "last_printed_digit", kind)   # the run resolves better than the digit
            self.assertNotIn("run_error_not_estimated", r["refinement"], kind)

    def test_a_reference_outside_the_run_s_error_fails(self):
        for kind in KINDS:
            limit = KINDS[kind][2]
            b = compose(self.tmp, kind + "-far", [task(kind, stated=limit + 1.0, printed=repr(limit + 1.0))])
            self.assertEqual(validate(b)["verdict"], "fail", kind)

    def test_a_person_s_tolerance_overrides_and_no_refinement_runs(self):
        for kind in KINDS:
            limit = KINDS[kind][2]
            human = {"value": 10.0, "unit": "1", "chosen_by": "human"}
            r = validate(compose(self.tmp, kind + "-person", [task(kind, stated=limit, tolerance=human)]))
            self.assertNotIn("refinement", r, kind)
            self.assertEqual(r["tolerance"], human, kind)

    def test_an_empty_row_leaves_the_half_digit_and_says_the_error_was_not_estimated(self):
        for kind in KINDS:
            limit = KINDS[kind][2]
            b = compose(self.tmp, kind + "-empty", [task(kind, stated=limit, printed=repr(limit))], rows={"order": (None, "1")})
            r = validate(b)
            self.assertEqual(r["tolerance"]["from"], "last_printed_digit", kind)
            self.assertIn("has no value", r["refinement"]["run_error_not_estimated"], kind)

    def test_the_build_refuses_a_refinement_that_cannot_run(self):
        for kind in KINDS:
            limit = KINDS[kind][2]
            for why, change in {"a row it lacks": {"ratio_row": "nothing"}, "an input the tool lacks": {"inputs": {"nothing": "order"}},
                                "a skill the library lacks": {"skill": "nothing@v1"}}.items():
                t = task(kind, stated=limit)
                t["refinement"].update(change)
                with self.assertRaises(ValueError, msg=why):
                    compose(self.tmp, kind + "-wrong", [t])
                self.assertFalse(os.path.exists(os.path.join(self.tmp, kind + "-wrong")), why)
            with self.assertRaises(ValueError):
                compose(self.tmp, kind + "-v22", [task(kind, stated=limit)], template=template_mod.SOURCES["v22"])

    def test_the_report_holds_the_run_s_error_and_passes_its_schema(self):
        c = v17.contracts()
        for kind in KINDS:
            limit = KINDS[kind][2]
            b = compose(self.tmp, kind + "-report", [task(kind, stated=limit, printed=repr(limit))])
            out = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "validate_tasks.py"), "--json"],
                                 capture_output=True, text=True, cwd=b).stdout
            vr, _, sci = gate_mod.make_validation_report({"validate": json.loads(out), "replay": {"items": [], "ok": True}},
                                                         "build-x-0001", "req-x-001", "b", "meta-macbook-20261117-2", NOW, bundle_path=b)
            self.assertEqual(sci, "pass", kind)
            n = [x for x in vr["numbers"] if x["name"] == "sci-a.value.run_numerical_error"]
            self.assertEqual(len(n), 1, (kind, vr["numbers"]))
            self.assertTrue(n[0]["source"].startswith("computed:%s@" % ERROR), kind)
            self.assertEqual([e.message for e in c.validator("validation_report").iter_errors(vr)], [], kind)


class TheVersion(unittest.TestCase):
    def test_v23_is_the_latest_and_changes_one_script(self):
        v22 = template_mod.SOURCES["v22"]
        self.assertEqual(template_mod.LATEST, "v23")
        changed = sorted(r for r in cards.tree_files(v22) if cards.sha256_file(os.path.join(v22, r)) != cards.sha256_file(os.path.join(V23, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])


if __name__ == "__main__":
    unittest.main()
