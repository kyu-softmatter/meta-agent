"""Template v13 (tasks/016; the intake's analysis, 23bb51b): a scientific task measured through a library skill.

A scientific task may name an analysis: the skill, which field of its call's output is handed to which input, the rows
that hand its other inputs, and the output its reference judges. The bundle's src/validate_tasks.py makes the call, runs
the skill through src/run_skill.py on that field and those rows, and judges the skill's output against the reference; a
row that is absent or null leaves the task not_run, and an analysis the bundle cannot run is refused by the build.

Two unrelated kinds: an engine whose lattice call returns a particle count, judged through the estimate of the box that
holds them; and a spectrometer whose reading returns a sample's temperatures, judged through the mean the window
diagnostic gives. Every call runs in a fresh process in a bundle with nothing of the Meta-Agent beside it.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import copy
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
from meta_agent.src.intake import card as card_mod
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.src.skills import runner as runner_mod

BOX, WINDOW = "box_length_for_volume_fraction@v1", "series_within_window@v1"
HUMAN = {"value": 1e-9, "unit": "1", "chosen_by": "human", "date": "2026-11-17"}

KINDS = {
    "engine": {
        "tool": "lattice", "outputs": {"count": {"type": "integer", "unit": "count"}},
        "adapter": "def run(payload):\n    return {'count': 8}\n",
        "rows": {"volume": (1.0, "engine_length^3"), "fraction": (0.5, "1")},
        "analysis": {"skill": BOX, "data": {"field": "count", "input": "particle_count"},
                     "rows": {"particle_volume": "volume", "volume_fraction": "fraction"}, "output": "box_length"},
        "inputs": {"particle_count": 8, "particle_volume": 1.0, "volume_fraction": 0.5},
    },
    "spectrometer": {
        "tool": "read_temperature", "outputs": {"temperatures": {"type": "array", "items": {"type": "number"}}},
        "adapter": "def run(payload):\n    return {'temperatures': [296.0, 298.0, 299.0, 301.0]}\n",
        "rows": {"temperature_window": (2, "count"), "temperature_low": (297.0, "K"), "temperature_high": (302.0, "K")},
        "analysis": {"skill": WINDOW, "data": {"field": "temperatures", "input": "series"},
                     "rows": {"window": "temperature_window", "low": "temperature_low", "high": "temperature_high"},
                     "output": "last_mean"},
        "inputs": {"series": [296.0, 298.0, 299.0, 301.0], "window": 2, "low": 297.0, "high": 302.0},
    },
}


def expected(kind):
    """The skill's own output on the task's inputs, run by the Meta-Agent's runner: the stated value a source would give."""
    k = KINDS[kind]
    return runner_mod.run(k["analysis"]["skill"], k["inputs"])["outputs"][k["analysis"]["output"]]


def contract(k):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["tool"], "description": "the step",
            "inputs": {"type": "object", "properties": {}}, "outputs": {"type": "object", "properties": dict(k["outputs"])},
            "errors": ["invalid_input"], "side_effects": "none", "safety_gate": {"required": False, "place": "no side effects"},
            "idempotent": True, "timeout_s": None}


def task(kind, stated=None, tolerance=HUMAN, analysis=None):
    k = KINDS[kind]
    a = copy.deepcopy(analysis or k["analysis"])
    t = {"id": "sci-a", "name": "through %s" % a["skill"], "call": {"tool": k["tool"], "input": {}},
         "measure": {"stated": {a["output"]: expected(kind) if stated is None else stated}},
         "reference": {"source": "the skill's worked value"}, "analysis": a, "expected_verdict": "pass"}
    if tolerance:
        t["tolerance"] = dict(tolerance)
    return t


def compose(tmp, name, sci, rows=None, refs=(BOX, WINDOW)):
    """A bundle in tmp/<name>, of the kind its name starts with."""
    kind = name.split("-")[0]
    k = KINDS[kind]
    tools = [{"name": k["tool"], "contract": contract(k), "adapter_source": k["adapter"], "errors": []}]
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([contract(k)]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    given = k["rows"] if rows is None else rows
    params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in given.items()]}
    iface = [{"id": "if-a", "call": {"tool": k["tool"], "input": {}}, "expected_verdict": "pass"}]
    path = os.path.join(tmp, name)
    bundle_mod.compose(template_mod.SOURCES["v13"], path, fill, tools, {"capabilities": []},
                       {"safety": {}, "parameters": params}, iface, sci, [], skills=catalogue_mod.take(list(refs)))
    return path


def validate(bundle):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "validate_tasks.py"), "--json"],
                       capture_output=True, text=True, cwd=bundle)
    return json.loads(p.stdout)["scientific"]["tasks"][0]


class TheAnalysis(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v13-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_skill_s_output_on_the_call_s_field_is_what_the_reference_judges(self):
        for kind, k in KINDS.items():
            r = validate(compose(self.tmp, kind, [task(kind)]))
            self.assertEqual(r["verdict"], "pass", (kind, r))
            out = k["analysis"]["output"]
            self.assertEqual(r["measured"], {out: expected(kind)})
            self.assertEqual(r["analysis"]["skill"], k["analysis"]["skill"])
            self.assertEqual(r["analysis"]["inputs"], k["inputs"])
            self.assertEqual(r["analysis"]["verdict"], "ran")

    def test_a_value_off_the_reference_fails_and_no_tolerance_is_undecided(self):
        for kind in KINDS:
            r = validate(compose(self.tmp, kind + "-off", [task(kind, stated=expected(kind) + 1.0)]))
            self.assertEqual(r["verdict"], "fail", (kind, r))
            r = validate(compose(self.tmp, kind + "-none", [task(kind, tolerance=None)]))
            self.assertEqual(r["verdict"], "undecided", (kind, r))

    def test_a_row_absent_or_null_leaves_the_task_not_run(self):
        for kind, k in KINDS.items():
            first = sorted(k["analysis"]["rows"].items())[0][1]
            nulled = dict(k["rows"], **{first: (None, k["rows"][first][1])})
            r = validate(compose(self.tmp, kind + "-null", [task(kind)], rows=nulled))
            self.assertEqual(r["verdict"], "not_run", (kind, r))
            self.assertIn("the row %s" % first, r["reason"])
            self.assertIn("has no value yet", r["reason"])

    def test_the_build_refuses_an_analysis_the_bundle_cannot_run(self):
        for kind, k in KINDS.items():
            wrong = {
                "a skill the bundle does not carry": dict(k["analysis"], skill="series_trend@v1"),
                "an output the skill does not give": dict(k["analysis"], output="nothing"),
                "a field the call does not return": dict(k["analysis"], data=dict(k["analysis"]["data"], field="nothing")),
                "an input no row hands": dict(k["analysis"], rows=dict(sorted(k["analysis"]["rows"].items())[1:])),
            }
            for why, a in wrong.items():
                with self.assertRaises(ValueError, msg=why):
                    compose(self.tmp, kind + "-wrong", [task(kind, analysis=a, stated=0.0)])
                self.assertFalse(os.path.exists(os.path.join(self.tmp, kind + "-wrong")), why)
            with self.assertRaises(ValueError):
                compose(self.tmp, kind + "-norow", [task(kind)], rows={})

    def test_the_intake_stage_judges_an_analysis_as_the_build_does(self):
        for kind, k in KINDS.items():
            card = {"skills": [BOX, WINDOW], "scientific_tasks": [task(kind)],
                    "tools": [{"contract": contract(k), "adapter_source": "x"}],
                    "parameter_rows": [{"name": n} for n in k["rows"]]}
            self.assertEqual(card_mod.decisions_problems(card), [], kind)
            card["scientific_tasks"][0]["analysis"]["output"] = "nothing"
            self.assertIn("gives no output nothing", " ".join(card_mod.decisions_problems(card)))


class TheVersion(unittest.TestCase):
    def test_v13_changes_one_script(self):
        v12, v13 = template_mod.SOURCES["v12"], template_mod.SOURCES["v13"]
        self.assertEqual(cards.tree_files(v12), cards.tree_files(v13))
        changed = sorted(r for r in cards.tree_files(v12) if cards.sha256_file(os.path.join(v12, r)) != cards.sha256_file(os.path.join(v13, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        self.assertIn("v13", template_mod.SOURCES)                  # v14 is the latest since tasks/021
        self.assertEqual(cards.load_json(os.path.join(v13, "TEMPLATE.json"))["version"], "v13")


if __name__ == "__main__":
    unittest.main()
