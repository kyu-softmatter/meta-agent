"""Template v29 (meta_agent/tasks/028; the person, 2026-11-19, 'Widen by uncertainty', docs/ideas/20261119.md; the design
role's ask 20261119-design-macbook-20261117-1-4): an entry of a scientific task's materials that gives one value may
carry the uncertainty its material states for it. literature_span@v2 takes such an entry as the range from the value
less that uncertainty to the value plus it, with no multiplier, one stated range, so that it gives a span by itself. The
builder refuses an uncertainty below zero, one beside a range, and any under a template whose span skill would pass over
it.

The two unrelated kinds of the v23 test, a flow coefficient and a spectral peak. The entries are a test's own: each kind
has two values whose span, taken alone, lies above the result as built, and an uncertainty on the lower one that
reaches down past it. Every bundle call runs in a fresh process.

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
from meta_agent.tests import test_template_v17 as v17
from meta_agent.tests import test_template_v23 as v23
from meta_agent.tests import test_template_v28 as v28

V28, V29 = template_mod.SOURCES["v28"], template_mod.SOURCES["v29"]
SPAN, RULE = "literature_span@v2", "tolerance_from_reference@v5"
KIND_OF = "the same system and quantity, another code; the uncertainty is a standard deviation; a test's entry"


def widened(material, value, uncertainty):
    return dict(v28.entry(material, value=value, compares=KIND_OF), uncertainty=uncertainty)


# each kind: the lower value with its uncertainty, the higher value alone, the span with the uncertainty, and the span of
# the two values alone, which lies above the result as built
KINDS = {
    "flow": ((2.96, 0.02), 2.97, (2.94, 2.98), (2.96, 2.97)),
    "spectrum": ((502.5, 0.2), 502.6, (502.3, 502.7), (502.5, 502.6)),
}


def entries(kind, uncertainty=True, alone=False):
    (value, u), other, _, _ = KINDS[kind]
    first = widened("a", value, u) if uncertainty else v28.entry("a", value=value)
    return [first] if alone else [first, v28.entry("b", value=other)]


class AStatedUncertaintyWidensTheSpan(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v29-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_builder_derives_the_widened_interval_and_the_result_within_it_passes(self):
        for kind in v23.KINDS:
            low, high = KINDS[kind][2]
            b = v23.compose(self.tmp, kind, [v28.task(kind, entries(kind))], template=V29)
            t = v28.built_task(b)
            self.assertEqual((t["tolerance"]["interval"], t["tolerance"]["from"], t["tolerance"]["derived_by"]),
                             ({"low": low, "high": high}, "literature_span", "computed:" + SPAN), kind)
            so = t["tolerance_derivation"]["span"]["outputs"]
            self.assertEqual((so["values"], so["ranges"]), (1, 1), kind)       # the widened value counts as one stated range
            self.assertTrue(os.path.isfile(os.path.join(b, "skills", SPAN, "skill.json")), kind)
            r = v23.validate(b)
            self.assertEqual((r["verdict"], r["interval_run"]["outputs"]["state"]), ("pass", "within"), (kind, r))

    def test_the_same_values_without_the_uncertainty_fail_the_same_result(self):
        for kind in v23.KINDS:
            r = v23.validate(v23.compose(self.tmp, kind + "-alone", [v28.task(kind, entries(kind, uncertainty=False))], template=V29))
            self.assertEqual((r["verdict"], r["tolerance"]["interval"]), ("fail", dict(zip(("low", "high"), KINDS[kind][3]))), (kind, r))

    def test_a_refining_task_derives_the_widened_span_in_the_bundle_and_makes_no_finer_run(self):
        for kind in v23.KINDS:
            low, high = KINDS[kind][2]
            r = v23.validate(v23.compose(self.tmp, kind + "-refining", [v28.task(kind, entries(kind), refinement=True)], template=V29))
            self.assertEqual((r["verdict"], r["tolerance"]["interval"], r["tolerance"]["derived_by"]),
                             ("pass", {"low": low, "high": high}, "computed:" + SPAN), (kind, r))
            run = r["refinement"]["span_run"]
            self.assertEqual((run["skill"], run["outputs"]["values"], run["outputs"]["ranges"]), (SPAN, 1, 1), kind)
            self.assertNotIn("finer", r["refinement"], kind)

    def test_one_value_with_its_uncertainty_gives_a_span_by_itself(self):
        for kind in v23.KINDS:
            (value, u), _, _, _ = KINDS[kind]
            for refinement in (False, True):
                b = v23.compose(self.tmp, "%s-single-%s" % (kind, refinement),
                                [v28.task(kind, entries(kind, alone=True), refinement=refinement)], template=V29)
                r = v23.validate(b)
                self.assertEqual(r["tolerance"]["from"], "literature_span", (kind, refinement, r))
                iv = r["tolerance"]["interval"]
                self.assertAlmostEqual(iv["low"], value - u, places=9)
                self.assertAlmostEqual(iv["high"], value + u, places=9)
                self.assertEqual(r["verdict"], "pass", (kind, refinement))
            # the same single value without its uncertainty is no span: the next branch applies
            t = v28.built_task(v23.compose(self.tmp, kind + "-single-plain", [v28.task(kind, entries(kind, uncertainty=False, alone=True))], template=V29))
            self.assertEqual(t["tolerance"]["from"], "last_printed_digit", kind)

    def test_an_uncertainty_of_zero_is_a_range_of_no_width(self):
        for kind in v23.KINDS:
            (value, _), _, _, _ = KINDS[kind]
            t = v28.built_task(v23.compose(self.tmp, kind + "-zero", [v28.task(kind, [widened("a", value, 0)])], template=V29))
            self.assertEqual(t["tolerance"]["interval"], {"low": value, "high": value}, kind)

    def test_entries_without_an_uncertainty_are_judged_as_under_v28(self):
        for kind in v23.KINDS:
            for which in (0, 1):
                for refinement in (False, True):
                    t = v28.task(kind, v28.ENTRIES[kind][which], refinement=refinement)
                    name = "%s-plain%%d-%d-%s" % (kind, which, refinement)
                    r28 = v23.validate(v23.compose(self.tmp, name % 28, [t], template=V28))
                    r29 = v23.validate(v23.compose(self.tmp, name % 29, [t], template=V29))
                    self.assertEqual((r29["verdict"], r29["tolerance"]), (r28["verdict"], dict(r28["tolerance"], derived_by="computed:" + SPAN)),
                                     (kind, which, refinement))

    def test_the_report_carries_the_widened_interval_and_passes_its_schema(self):
        c = v17.contracts()
        for kind in v23.KINDS:
            b = v23.compose(self.tmp, kind + "-report", [v28.task(kind, entries(kind), refinement=True)], template=V29)
            out = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "validate_tasks.py"), "--json"],
                                 capture_output=True, text=True, cwd=b).stdout
            vr, _, sci = gate_mod.make_validation_report({"validate": json.loads(out), "replay": {"items": [], "ok": True}},
                                                         "build-x-0001", "req-x-001", "b", "meta-macbook-20261119-1", v23.NOW, bundle_path=b)
            self.assertEqual(sci, "pass", kind)
            self.assertEqual(vr["scientific"]["tasks"][0]["tolerance"]["interval"], dict(zip(("low", "high"), KINDS[kind][2])), kind)
            self.assertEqual([e.message for e in c.validator("validation_report").iter_errors(vr)], [], kind)


class TheBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v29-build-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def refused(self, kind, name, given, said, template=V29):
        for refinement in (False, True):
            with self.assertRaises(ValueError) as cm:
                v23.compose(self.tmp, "%s-%s-%s" % (kind, name, refinement), [v28.task(kind, given, refinement=refinement)], template=template)
            self.assertIn(said, str(cm.exception), (kind, name))

    def test_an_uncertainty_below_zero_or_not_a_number_is_refused(self):
        for kind in v23.KINDS:
            (value, u), other, _, _ = KINDS[kind]
            self.refused(kind, "negative", [widened("a", value, -u), v28.entry("b", value=other)], "not a number at or above zero")
            self.refused(kind, "words", [widened("a", value, "small")], "not a number at or above zero")

    def test_an_uncertainty_beside_a_range_is_refused(self):
        for kind in v23.KINDS:
            low, high = KINDS[kind][2]
            self.refused(kind, "range", [dict(v28.entry("a", low=low, high=high), uncertainty=0.1)], "beside no single value")

    def test_a_template_whose_span_skill_takes_no_uncertainty_refuses_it(self):
        for kind in v23.KINDS:
            self.refused(kind, "old", entries(kind), "v29", template=V28)


class TheVersion(unittest.TestCase):
    def test_v29_is_the_latest_and_changes_its_card_and_two_texts(self):
        self.assertIn("v29", template_mod.SOURCES)                  # v30 is the latest since the engine waits through src/engine_wait.py
        changed = sorted(r for r in cards.tree_files(V28) if cards.sha256_file(os.path.join(V28, r)) != cards.sha256_file(os.path.join(V29, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/validate_tasks.py"])
        self.assertEqual(sorted(cards.tree_files(V28)), sorted(cards.tree_files(V29)))
        m = cards.load_json(os.path.join(V29, "TEMPLATE.json"))
        self.assertEqual((m["tolerance_rule"]["skill"], m["span_skill"]), (RULE, SPAN))
        self.assertIn(SPAN, m["common_skills"])
        self.assertNotIn("literature_span@v1", m["common_skills"])


if __name__ == "__main__":
    unittest.main()
