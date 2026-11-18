"""Template v19 and the builder, on the person's standing rule of 2026-11-18 for tolerances (docs/ideas/20261118.md;
the design role's ask 20261118-design-macbook-20261117-1-5): a scientific task with no tolerance from the person gets
one from tolerance_from_reference@v1, run through the runner on the reference as the task prints it, recorded as
chosen_by rule with the rule, the skill and which way it came; the bundle's src/validate_tasks.py judges by it as by a
person's; a person's tolerance overrides it; a bundle of v18 does not judge by it.

Two unrelated kinds, the engine and the spectrometer of the v13 test; every bundle call runs in a fresh process.

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
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import runner as runner_mod
from meta_agent.src.validate import gate as gate_mod
from meta_agent.tests import test_template_v13 as v13
from meta_agent.tests import test_template_v17 as v17

V19 = template_mod.SOURCES["v19"]
RULE = "tolerance_from_reference@v1"
SEAT = "meta-macbook-20261117-2"
NOW = "2026-11-18T16:00:00Z"


def task(kind, printed=None, stated=None, tolerance=None):
    t = v13.task(kind, stated=stated, tolerance=tolerance)
    t["reference"] = {"kind": "source", "ref": "the skill's worked value"}
    if printed is not None:
        t["measure"]["printed"] = {next(iter(t["measure"]["stated"])): printed}
    return t


def item(bundle):
    return cards.load_json(os.path.join(bundle, "validation", "scientific", "sci-a.json"))


class TheBuilderDerivesByTheRule(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v19-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_task_with_no_tolerance_gets_the_rule_s_from_its_stored_number(self):
        for kind in v13.KINDS:
            b = v17.compose(self.tmp, kind, [task(kind)], template=V19)
            tol = item(b)["tolerance"]
            want = runner_mod.run(RULE, {"printed": repr(v13.expected(kind)), "stated_uncertainty": None})["outputs"]
            self.assertEqual((tol["chosen_by"], tol["rule"], tol["derived_by"], tol["from"]),
                             ("rule", "docs/ideas/20261118.md", "computed:" + RULE, "last_printed_digit"), kind)
            self.assertEqual(tol["value"], want["tolerance"], kind)
            self.assertEqual(item(b)["tolerance_derivation"]["printed_from"], "the stored number", kind)
            r = v13.validate(b)
            self.assertEqual(r["verdict"], "pass", (kind, r))         # measured equals the reference: within it

    def test_the_printed_form_is_read_before_the_stored_number(self):
        for kind in v13.KINDS:
            b = v17.compose(self.tmp, kind + "-printed", [task(kind, printed="%.2f" % v13.expected(kind))], template=V19)
            self.assertEqual(item(b)["tolerance"]["value"], 0.005, kind)
            self.assertEqual(item(b)["tolerance_derivation"]["printed_from"], "measure.printed", kind)

    def test_a_value_outside_the_rule_s_tolerance_fails(self):
        for kind in v13.KINDS:
            off = v13.expected(kind) + 0.5
            b = v17.compose(self.tmp, kind + "-off", [task(kind, stated=off, printed="%.1f" % off)], template=V19)
            self.assertEqual(item(b)["tolerance"]["value"], 0.05, kind)
            self.assertEqual(v13.validate(b)["verdict"], "fail", kind)

    def test_a_person_s_tolerance_overrides_the_rule(self):
        for kind in v13.KINDS:
            b = v17.compose(self.tmp, kind + "-person", [task(kind, tolerance=v13.HUMAN)], template=V19)
            self.assertEqual(item(b)["tolerance"], v13.HUMAN, kind)
            self.assertNotIn("tolerance_derivation", item(b), kind)

    def test_a_v18_bundle_derives_none_and_does_not_judge_by_a_rule_tolerance(self):
        rule_tol = {"value": 1.0, "unit": "1", "chosen_by": "rule", "rule": "docs/ideas/20261118.md",
                    "derived_by": "computed:" + RULE, "from": "last_printed_digit"}
        for kind in v13.KINDS:
            b = v17.compose(self.tmp, kind + "-v18", [task(kind)], template=template_mod.SOURCES["v18"])
            self.assertNotIn("tolerance", item(b), kind)
            b = v17.compose(self.tmp, kind + "-v18r", [task(kind, tolerance=rule_tol)], template=template_mod.SOURCES["v18"])
            self.assertEqual(v13.validate(b)["verdict"], "undecided", kind)
            b = v17.compose(self.tmp, kind + "-v19r", [task(kind, tolerance=rule_tol)], template=V19)
            self.assertEqual(v13.validate(b)["verdict"], "pass", kind)

    def test_a_rule_tolerance_without_its_derivation_is_not_judged_by(self):
        for kind in v13.KINDS:
            bare = {"value": 1.0, "unit": "1", "chosen_by": "rule"}
            b = v17.compose(self.tmp, kind + "-bare", [task(kind, tolerance=bare)], template=V19)
            self.assertEqual(v13.validate(b)["verdict"], "undecided", kind)

    def test_the_report_passes_its_schema_and_the_bundle_its_checks(self):
        c = v17.contracts()
        for kind in v13.KINDS:
            b = v17.compose(self.tmp, kind + "-report", [task(kind)], template=V19)
            out = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "validate_tasks.py"), "--json"],
                                 capture_output=True, text=True, cwd=b).stdout
            vr, _, sci = gate_mod.make_validation_report({"validate": json.loads(out), "replay": {"items": [], "ok": True}},
                                                         "build-%s-0001" % kind, "req-%s-001" % kind, "b", SEAT, NOW, bundle_path=b)
            self.assertEqual(sci, "pass", kind)
            self.assertEqual(vr["scientific"]["tasks"][0]["tolerance"]["chosen_by"], "rule", kind)
            self.assertEqual([e.message for e in c.validator("validation_report").iter_errors(vr)], [], kind)
            p = subprocess.run([sys.executable, os.path.join(v17.REPO, "contracts", "validate.py"), "--bundle", b],
                               capture_output=True, text=True, cwd=v17.REPO)
            # the fixture pins no snapshot and carries no replay item (B4, B5 fail on a v17 bundle of it alike);
            # nothing else fails, the derived tolerance and its derivation included
            self.assertIn("failed_checks=['B4', 'B5']", p.stdout.strip().splitlines()[-1], (kind, p.stdout[-1500:]))
            self.assertNotIn("tolerance", " ".join(l for l in p.stdout.splitlines() if l.startswith("FAIL")), kind)


class TheVersion(unittest.TestCase):
    def test_v19_is_the_latest_and_changes_the_checks_and_the_start_task(self):
        v18 = template_mod.SOURCES["v18"]
        self.assertEqual(template_mod.LATEST, "v19")
        self.assertEqual(cards.tree_files(v18), cards.tree_files(V19))
        changed = sorted(r for r in cards.tree_files(v18) if cards.sha256_file(os.path.join(v18, r)) != cards.sha256_file(os.path.join(V19, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py", "tasks/001-start.md"])
        meta = cards.load_json(os.path.join(V19, "TEMPLATE.json"))
        self.assertEqual((meta["version"], meta["tolerance_rule"]["skill"]), ("v19", RULE))


if __name__ == "__main__":
    unittest.main()
