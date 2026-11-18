"""Template v22 (failures.jsonl cfd-19; the report's schema at eb41e50): a tolerance the person gave as an acceptance
interval {low, high} is judged by inclusion, its edges as written, through series_within_window@v3 run on the one
measured value; the build carries that skill into a bundle with such a task; a bundle of v21 does not judge by it.

Two unrelated kinds, the engine and the spectrometer of the v13 test, each built as an instrument's bundle (no common
set), so that the skill is there only because the interval asks for it.

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
from meta_agent.src.validate import gate as gate_mod
from meta_agent.tests import test_template_v13 as v13
from meta_agent.tests import test_template_v17 as v17
from meta_agent.tests import test_template_v20 as v20

V22 = template_mod.SOURCES["v22"]
WINDOW = "series_within_window@v3"


def interval(low, high):
    return {"interval": {"low": low, "high": high}, "unit": "1", "chosen_by": "human", "source": "a test's interval"}


def build(tmp, name, low, high, template=V22):
    kind = name.split("-")[0]
    t = v13.task(kind, tolerance=interval(low, high))
    t["reference"] = {"kind": "source", "ref": "a test's interval"}
    orig = v20.V20
    v20.V20 = template
    try:
        return v20.compose(tmp, name, [t], simulation=False)
    finally:
        v20.V20 = orig


class AnInterval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v22-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_inside_passes_below_and_above_fail_and_an_edge_is_inside(self):
        for kind in v13.KINDS:
            x = v13.expected(kind)
            cases = {"in": (x - 1, x + 1, "pass"), "below": (x + 1, x + 2, "fail"), "above": (x - 2, x - 1, "fail"),
                     "edge": (x, x + 1, "pass")}
            for label, (low, high, want) in cases.items():
                b = build(self.tmp, "%s-%s" % (kind, label), low, high)
                self.assertIn(WINDOW, v20.carried(b), (kind, label))
                r = v13.validate(b)
                self.assertEqual(r["verdict"], want, (kind, label, r))
                self.assertEqual((r["interval_run"]["skill"], r["interval_run"]["verdict"]), (WINDOW, "ran"), (kind, label))

    def test_a_v21_bundle_does_not_judge_by_an_interval(self):
        for kind in v13.KINDS:
            x = v13.expected(kind)
            b = build(self.tmp, kind + "-v21", x - 1, x + 1, template=template_mod.SOURCES["v21"])
            self.assertEqual(v13.validate(b)["verdict"], "undecided", kind)

    def test_the_report_passes_its_schema(self):
        c = v17.contracts()
        for kind in v13.KINDS:
            x = v13.expected(kind)
            b = build(self.tmp, kind + "-report", x - 1, x + 1)
            out = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "validate_tasks.py"), "--json"],
                                 capture_output=True, text=True, cwd=b).stdout
            vr, _, sci = gate_mod.make_validation_report({"validate": json.loads(out), "replay": {"items": [], "ok": True}},
                                                         "build-x-0001", "req-x-001", "b", "meta-macbook-20261117-2",
                                                         "2026-11-18T18:30:00Z", bundle_path=b)
            self.assertEqual(sci, "pass", kind)
            self.assertEqual([e.message for e in c.validator("validation_report").iter_errors(vr)], [], kind)


class TheVersion(unittest.TestCase):
    def test_v22_changes_one_script(self):
        v21 = template_mod.SOURCES["v21"]
        self.assertIn("v22", template_mod.SOURCES)                  # v23 is the latest since the refinement
        changed = sorted(r for r in cards.tree_files(v21) if cards.sha256_file(os.path.join(v21, r)) != cards.sha256_file(os.path.join(V22, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        self.assertEqual(cards.load_json(os.path.join(V22, "TEMPLATE.json"))["interval_skill"], WINDOW)


if __name__ == "__main__":
    unittest.main()
