"""Template v28 (meta_agent/tasks/028; the person's standing rule for tolerances, branch 3: docs/ideas/20261118.md, 'Yes,
add literature span', 'Min-max of values'; docs/ideas/20261119.md, 'Yes, widen it'): a scientific task may carry
materials, entries that each name a material, say how its system compares, and give one value or one stated range of the
quantity. Where the reference states no uncertainty and the person gave no tolerance, literature_span@v1 gives the span
[lowest, highest] of those entries through the runner, tolerance_from_reference@v5 takes it before the last printed digit
and the run's own error, and the task is judged by that interval, chosen_by rule, from literature_span. The builder
derives it for a task that names no refinement; a bundle derives it itself, when its check runs, for a task that does,
and then makes no finer run. With fewer than two values and no stated range there is no span and the next branch applies.

The two unrelated kinds of the v23 test, a flow coefficient and a spectral peak. The entries are a test's own, shaped
around neither: every one names a material that does not exist and the numbers are chosen about each kind's result.
Every bundle call runs in a fresh process.

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

V27, V28 = template_mod.SOURCES["v27"], template_mod.SOURCES["v28"]
SPAN, RULE, WINDOW = "literature_span@v1", "tolerance_from_reference@v5", "series_within_window@v3"
HOW = "the same system and quantity, another code; a test's entry"


def entry(material, value=None, low=None, high=None, compares=HOW):
    e = {"material": "a test's material %s" % material, "compares": compares}
    if value is not None:
        e["value"] = value
    if low is not None:
        e.update(low=low, high=high)
    return e


# each kind: entries whose span holds the result as built, entries whose span lies above it, and the span of the first
ENTRIES = {
    "flow": ([entry("a", low=2.93, high=2.97), entry("b", value=2.9509)], [entry("a", value=2.96), entry("b", value=2.97)],
             (2.93, 2.97)),
    "spectrum": ([entry("a", value=502.1), entry("b", value=502.6)], [entry("a", value=502.5), entry("b", value=502.6)],
                 (502.1, 502.6)),
}


def task(kind, entries, refinement=False, uncertainty=None, tolerance=None):
    limit = v23.KINDS[kind][2]
    t = v23.task(kind, stated=limit, printed=repr(limit), refinement=refinement, tolerance=tolerance)
    if entries is not None:
        t["measure"]["materials"] = {"value": entries}
    if uncertainty is not None:
        t["measure"]["stated_uncertainty"] = {"value": uncertainty}
    return t


def built_task(bundle):
    return cards.load_json(os.path.join(bundle, "validation", "scientific", "sci-a.json"))


class TheSpanJudges(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v28-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_builder_derives_the_interval_and_the_result_within_it_passes(self):
        for kind in v23.KINDS:
            inside, above, (low, high) = ENTRIES[kind]
            b = v23.compose(self.tmp, kind, [task(kind, inside)], template=V28)
            want = {"interval": {"low": low, "high": high}, "unit": "1", "chosen_by": "rule", "rule": "docs/ideas/20261118.md",
                    "derived_by": "computed:" + SPAN, "from": "literature_span"}
            t = built_task(b)
            self.assertEqual(t["tolerance"], want, kind)
            d = t["tolerance_derivation"]
            self.assertEqual((d["skill"], d["span"]["skill"], d["span"]["verdict"]), (RULE, SPAN, "ran"), kind)
            self.assertEqual((d["inputs"]["span_low"], d["inputs"]["span_high"]), (low, high), kind)
            for ref in (SPAN, RULE, WINDOW):                     # the bundle carries what derives and judges the span
                self.assertTrue(os.path.isfile(os.path.join(b, "skills", ref, "skill.json")), (kind, ref))
            r = v23.validate(b)
            self.assertEqual((r["verdict"], r["tolerance"]), ("pass", want), (kind, r))
            self.assertEqual((r["interval_run"]["skill"], r["interval_run"]["outputs"]["state"]), (WINDOW, "within"), kind)

    def test_a_result_outside_the_span_fails_and_says_whose_interval_it_is(self):
        for kind in v23.KINDS:
            r = v23.validate(v23.compose(self.tmp, kind + "-above", [task(kind, ENTRIES[kind][1])], template=V28))
            self.assertEqual(r["verdict"], "fail", (kind, r))
            self.assertIn("below the interval", r["reason"], kind)
            self.assertIn("the span of the materials", r["reason"], kind)

    def test_a_refining_task_derives_the_span_in_the_bundle_and_makes_no_finer_run(self):
        for kind in v23.KINDS:
            inside, above, (low, high) = ENTRIES[kind]
            b = v23.compose(self.tmp, kind + "-refining", [task(kind, inside, refinement=True)], template=V28)
            self.assertNotIn("tolerance", built_task(b), kind)       # nothing derived when it was built: the bundle does it
            r = v23.validate(b)
            fine, built = v23.finer(kind)
            self.assertEqual((r["verdict"], r["measured"]), ("pass", {"value": built}), (kind, r))   # the result as built
            tol = r["tolerance"]
            self.assertEqual((tol["interval"], tol["chosen_by"], tol["from"], tol["derived_by"]),
                             ({"low": low, "high": high}, "rule", "literature_span", "computed:" + SPAN), kind)
            run = r["refinement"]["span_run"]
            self.assertEqual((run["skill"], run["verdict"], run["outputs"]["low"], run["outputs"]["high"]), (SPAN, "ran", low, high), kind)
            self.assertNotIn("finer", r["refinement"], kind)
            self.assertIn("the span of the task's materials", r["refinement"]["run_error_not_estimated"], kind)
            self.assertEqual(r["refinement"]["tolerance_run"]["skill"], RULE, kind)

    def test_the_check_prints_the_span_and_which_material_gave_each_edge(self):
        for kind in v23.KINDS:
            b = v23.compose(self.tmp, kind + "-printed", [task(kind, ENTRIES[kind][0], refinement=True)], template=V28)
            p = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "validate_tasks.py")], capture_output=True, text=True, cwd=b)
            self.assertIn("span of the materials: [", p.stdout, kind)
            self.assertIn("lowest from a test's material a", p.stdout, kind)
            self.assertIn("chosen_by rule, from literature_span", p.stdout, kind)

    def test_the_report_carries_the_interval_and_passes_its_schema(self):
        c = v17.contracts()
        for kind in v23.KINDS:
            for refinement in (False, True):
                b = v23.compose(self.tmp, "%s-report-%s" % (kind, refinement), [task(kind, ENTRIES[kind][0], refinement=refinement)], template=V28)
                out = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "validate_tasks.py"), "--json"],
                                     capture_output=True, text=True, cwd=b).stdout
                vr, _, sci = gate_mod.make_validation_report({"validate": json.loads(out), "replay": {"items": [], "ok": True}},
                                                             "build-x-0001", "req-x-001", "b", "meta-macbook-20261119-1", v23.NOW, bundle_path=b)
                self.assertEqual(sci, "pass", (kind, refinement))
                tol = vr["scientific"]["tasks"][0]["tolerance"]
                self.assertEqual((tol["chosen_by"], tol["from"], tol["interval"]),
                                 ("rule", "literature_span", dict(zip(("low", "high"), ENTRIES[kind][2]))), (kind, refinement))
                self.assertEqual([e.message for e in c.validator("validation_report").iter_errors(vr)], [], (kind, refinement))

    def test_one_value_and_no_range_is_no_span_and_the_next_branch_applies(self):
        for kind in v23.KINDS:
            one = [ENTRIES[kind][0][1]]
            b = v23.compose(self.tmp, kind + "-one", [task(kind, one)], template=V28)
            t = built_task(b)
            self.assertEqual(t["tolerance"]["from"], "last_printed_digit", kind)
            self.assertIn("fewer than two values", t["tolerance_derivation"]["span"]["outputs"]["why"], kind)
            r = v23.validate(v23.compose(self.tmp, kind + "-one-refining", [task(kind, one, refinement=True)], template=V28))
            self.assertIn(r["tolerance"]["from"], ("last_printed_digit", "run_numerical_error"), kind)
            self.assertIn("finer", r["refinement"], kind)                               # the last branch: the run refines
            self.assertIsNone(r["refinement"]["span_run"]["outputs"]["low"], kind)

    def test_a_stated_uncertainty_is_taken_before_the_span(self):
        for kind in v23.KINDS:
            for refinement in (False, True):
                b = v23.compose(self.tmp, "%s-stated-%s" % (kind, refinement),
                                [task(kind, ENTRIES[kind][0], refinement=refinement, uncertainty=0.25)], template=V28)
                r = v23.validate(b)
                self.assertEqual((r["tolerance"]["value"], r["tolerance"]["from"]), (0.25, "stated_uncertainty"), (kind, refinement))
                if refinement:
                    self.assertNotIn("finer", r["refinement"], kind)                    # an earlier branch: no finer run

    def test_a_person_s_tolerance_overrides_the_span(self):
        for kind in v23.KINDS:
            human = {"value": 10.0, "unit": "1", "chosen_by": "human"}
            for refinement in (False, True):
                b = v23.compose(self.tmp, "%s-person-%s" % (kind, refinement),
                                [task(kind, ENTRIES[kind][1], refinement=refinement, tolerance=human)], template=V28)
                r = v23.validate(b)
                self.assertEqual((r["verdict"], r["tolerance"]), ("pass", human), (kind, refinement))
                self.assertNotIn("refinement", r, kind)

    def test_a_task_without_materials_is_judged_as_under_v27(self):
        for kind in v23.KINDS:
            for refinement in (False, True):
                t = task(kind, None, refinement=refinement)
                r27 = v23.validate(v23.compose(self.tmp, "%s-plain27-%s" % (kind, refinement), [t], template=V27))
                r28 = v23.validate(v23.compose(self.tmp, "%s-plain28-%s" % (kind, refinement), [t], template=V28))
                self.assertEqual((r28["verdict"], r28["tolerance"]), (r27["verdict"], dict(r27["tolerance"], derived_by="computed:" + RULE)),
                                 (kind, refinement))
                self.assertEqual(r28.get("measured"), r27.get("measured"), (kind, refinement))


class TheBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v28-build-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_an_entry_that_does_not_say_how_its_material_compares_is_refused(self):
        for kind in v23.KINDS:
            entries = [ENTRIES[kind][0][0], dict(ENTRIES[kind][0][1], compares=" ")]
            for refinement in (False, True):
                with self.assertRaises(ValueError) as cm:
                    v23.compose(self.tmp, "%s-unsaid-%s" % (kind, refinement), [task(kind, entries, refinement=refinement)], template=V28)
                self.assertIn("does not say how", str(cm.exception), kind)

    def test_an_entry_without_a_material_or_with_a_value_and_a_range_is_refused(self):
        for kind in v23.KINDS:
            good = ENTRIES[kind][0][0]
            for bad, said in (({"compares": HOW, "value": 1.0}, "names no material"),
                              (dict(entry("c", value=1.0), low=0.5, high=1.5), "neither one value nor the two edges")):
                with self.assertRaises(ValueError) as cm:
                    v23.compose(self.tmp, kind + "-bad", [task(kind, [good, bad])], template=V28)
                self.assertIn(said, str(cm.exception), kind)

    def test_a_template_that_takes_no_span_refuses_materials(self):
        for kind in v23.KINDS:
            with self.assertRaises(ValueError) as cm:
                v23.compose(self.tmp, kind + "-old", [task(kind, ENTRIES[kind][0])], template=V27)
            self.assertIn("v28", str(cm.exception), kind)


class TheVersion(unittest.TestCase):
    def test_v28_is_the_latest_and_changes_one_script_its_card_and_two_texts(self):
        self.assertIn("v28", template_mod.SOURCES)                  # v29 is the latest since a stated uncertainty widens the span
        changed = sorted(r for r in cards.tree_files(V27) if cards.sha256_file(os.path.join(V27, r)) != cards.sha256_file(os.path.join(V28, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/validate_tasks.py", "tasks/001-start.md"])
        self.assertEqual(sorted(cards.tree_files(V27)), sorted(cards.tree_files(V28)))
        m = cards.load_json(os.path.join(V28, "TEMPLATE.json"))
        self.assertEqual((m["tolerance_rule"]["skill"], m["span_skill"]), (RULE, SPAN))
        self.assertIn(RULE, m["common_skills"])
        self.assertIn(SPAN, m["common_skills"])
        self.assertNotIn("tolerance_from_reference@v4", m["common_skills"])


if __name__ == "__main__":
    unittest.main()
