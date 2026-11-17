"""Template v12 (tasks/016; the person, 2026-11-17, docs/ideas/20261117.md): the decisions a run takes.

A quantity that enters a decision of the agent is computed by a library skill, and a value the engine reports is read
from it. The build fills CLAUDE.md's Decisions section with each decision the request names: the diagnostic skill that
takes it, the tool output it judges and the row that hands each criterion. It refuses, before anything is written, a
decision whose skill the bundle does not carry or is not a diagnostic, whose data no tool returns, or whose criterion no
row of the bundle's parameters hands. The library carries the two new kinds: estimate and diagnostic.

Two unrelated kinds: an engine whose acceptance must stay in a band and whose run must settle, and a spectrometer whose
sample temperature must settle. Each decision's skill is run through the bundle's own runner.

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
from meta_agent.src.intake import card as card_mod
from meta_agent.src.skills import catalogue as catalogue_mod

SETTLED, WINDOW, BOX = "series_settled@v1", "series_within_window@v1", "box_length_for_volume_fraction@v1"
SERIES = {"type": "array", "items": {"type": "number"}}

KINDS = {
    "engine": {
        "tools": {"equilibrate": {"acceptance": SERIES, "potential_energy": SERIES}},
        "rows": ["acceptance_window", "acceptance_low", "acceptance_high", "energy_window", "energy_tolerance"],
        "decisions": [
            {"decision": "the acceptance stays in its band", "skill": WINDOW,
             "data": {"tool": "equilibrate", "field": "acceptance", "input": "series"},
             "rows": {"window": "acceptance_window", "low": "acceptance_low", "high": "acceptance_high"}},
            {"decision": "the run has settled", "skill": SETTLED,
             "data": {"tool": "equilibrate", "field": "potential_energy", "input": "series"},
             "rows": {"window": "energy_window", "tolerance": "energy_tolerance"}}],
        "run": (WINDOW, {"series": [0.5, 0.31, 0.29, 0.3], "window": 3, "low": 0.2, "high": 0.4}, "within"),
    },
    "spectrometer": {
        "tools": {"read_temperature": {"temperatures": SERIES}},
        "rows": ["temperature_window", "temperature_tolerance"],
        "decisions": [
            {"decision": "the sample's temperature has settled", "skill": SETTLED,
             "data": {"tool": "read_temperature", "field": "temperatures", "input": "series"},
             "rows": {"window": "temperature_window", "tolerance": "temperature_tolerance"}}],
        "run": (SETTLED, {"series": [293.0, 296.0, 298.0, 298.0], "window": 2, "tolerance": None}, "undecided"),
    },
}


def contract(name, outputs):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": "the step %s" % name,
            "inputs": {"type": "object", "properties": {}}, "outputs": {"type": "object", "properties": dict(outputs)},
            "errors": ["invalid_input"], "side_effects": "none", "safety_gate": {"required": False, "place": "no side effects"},
            "idempotent": True, "timeout_s": None}


def compose(tmp, kind, decisions=None, rows=None, refs=(SETTLED, WINDOW, BOX)):
    k = KINDS[kind]
    tools = [{"name": n, "contract": contract(n, out), "errors": [],
              "adapter_source": "def run(payload):\n    return {}\n"} for n, out in k["tools"].items()]
    names = list(k["tools"])
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([t["contract"] for t in tools]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    params = {"rows": [{"name": r, "value": None, "unit": "1"} for r in (k["rows"] if rows is None else rows)]}
    iface = [{"id": "if-a", "call": {"tool": names[0], "input": {}}, "expected_verdict": "pass"}]
    path = os.path.join(tmp, kind)
    bundle_mod.compose(template_mod.SOURCES["v12"], path, fill, tools, {"capabilities": []},
                       {"safety": {}, "parameters": params}, iface, [], [], skills=catalogue_mod.take(list(refs)),
                       decisions=decisions)
    return path


class TheDecisions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v12-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_each_decision_names_its_skill_its_data_and_the_rows_of_its_criterion(self):
        for kind, k in KINDS.items():
            text = cards.read_text(os.path.join(compose(self.tmp, kind, k["decisions"]), "CLAUDE.md"))
            self.assertIn("## Decisions", text)
            for d in k["decisions"]:
                self.assertIn("run `%s` on the field `%s` that `%s` returns, as its `series`" % (
                    d["skill"], d["data"]["field"], d["data"]["tool"]), text, kind)
                for name, row in d["rows"].items():
                    self.assertIn("`%s` from the row `%s`" % (name, row), text)
            self.assertIn("the skill says `undecided` and the decision is the person's", text)
            self.assertEqual(card_mod.numbers_left(text, set()), [], kind)          # B6, by the gate's own rule

    def test_without_decisions_the_section_says_the_request_named_none(self):
        for kind in KINDS:
            text = cards.read_text(os.path.join(compose(self.tmp, kind), "CLAUDE.md"))
            self.assertIn("named no decision of this kind", text)

    def test_a_decision_the_bundle_cannot_take_is_refused_before_anything_is_written(self):
        for kind, k in KINDS.items():
            first = k["decisions"][0]
            wrong = {
                "a skill the bundle does not carry": dict(first, skill="series_trend@v1"),
                "an estimate, not a diagnostic": dict(first, skill=BOX),
                "a field no tool returns": dict(first, data=dict(first["data"], field="nothing")),
                "a criterion no row hands": dict(first, rows={k2: v for k2, v in first["rows"].items() if k2 != "window"}),
            }
            for why, d in wrong.items():
                with self.assertRaises(ValueError, msg=why):
                    compose(self.tmp, kind, [d])
                self.assertFalse(os.path.exists(os.path.join(self.tmp, kind)), why)
            with self.assertRaises(ValueError):
                compose(self.tmp, kind, k["decisions"], rows=k["rows"][1:])          # a row the parameters lack

    def test_the_intake_stage_judges_them_as_the_build_does(self):
        for kind, k in KINDS.items():
            card = {"skills": [SETTLED, WINDOW], "decisions": k["decisions"],
                    "tools": [{"contract": contract(n, out), "adapter_source": "x"} for n, out in k["tools"].items()],
                    "parameter_rows": [{"name": r} for r in k["rows"]]}
            self.assertEqual(card_mod.decisions_problems(card), [], kind)
            card["parameter_rows"] = card["parameter_rows"][1:]
            self.assertIn("is not a row of envelope/parameters.json", " ".join(card_mod.decisions_problems(card)))
            card["skills"] = [BOX]
            self.assertIn("is not one this bundle carries", " ".join(card_mod.decisions_problems(card)))
        self.assertEqual(card_mod.decisions_problems({"skills": []}), [])

    def test_a_decision_s_skill_runs_through_the_bundle_s_runner(self):
        for kind, k in KINDS.items():
            bundle = compose(self.tmp, kind, k["decisions"])
            ref, inputs, state = k["run"]
            p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "run_skill.py"), ref], input=json.dumps(inputs),
                               capture_output=True, text=True, cwd=bundle)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertIn('"state": "%s"' % state, p.stdout, (kind, p.stdout))


class TheSpecifiedCard(unittest.TestCase):
    """intake.decisions landed in the schema (537b245): a specified card that names a decision passes check 1's schema and
    the stage's own judgement, and a swept input that names its rows under `rows` is not taken for a row in words."""

    def card(self):
        from meta_agent.tests.test_intake import specified_example
        c = specified_example()
        c["skills"] = [SETTLED]
        c["parameter_rows"] = [{"name": "length_window", "value": None, "unit": "count"},
                               {"name": "length_tolerance", "value": None, "unit": "1"}]
        tool = (c.get("tool_contract") or c["tools"][0]["contract"])["name"]
        c["decisions"] = [{"decision": "the length has settled", "skill": SETTLED,
                           "data": {"tool": tool, "field": "length", "input": "series"},
                           "rows": {"window": "length_window", "tolerance": "length_tolerance"}}]
        return c

    def test_a_card_with_a_decision_passes_the_schema_and_the_stage(self):
        c = self.card()
        self.assertEqual(card_mod.schema_problems(c), [])
        self.assertEqual(card_mod.decisions_problems(c), [])
        c["decisions"][0]["rows"].pop("window")
        self.assertIn("the input window of series_settled@v1 is handed by no row", " ".join(card_mod.decisions_problems(c)))

    def test_a_swept_input_names_its_rows_under_rows(self):
        c = {"tools": [{"contract": contract("sweep", {}), "adapter_source": "x"}]}
        c["tools"][0]["contract"]["inputs"]["properties"]["rates"] = {
            "type": "array", "items": {"type": "number"}, "rows": ["rate_one", "rate_two"],
            "description": "one point per row rate_one and rate_two"}
        c["parameter_rows"] = [{"name": "rate_one"}, {"name": "rate_two"}]
        self.assertEqual(card_mod.row_problems(c), [])
        c["parameter_rows"] = [{"name": "rate_one"}]
        self.assertIn("rate_two", " ".join(card_mod.row_problems(c)))


class TheLibrary(unittest.TestCase):
    def test_the_library_carries_an_estimate_and_diagnostics(self):
        rows = {r["ref"]: r for r in catalogue_mod.take([SETTLED, WINDOW, BOX])}
        self.assertEqual((rows[SETTLED]["kind"], rows[WINDOW]["kind"], rows[BOX]["kind"]), ("diagnostic", "diagnostic", "estimate"))
        for ref in (SETTLED, WINDOW):
            self.assertIn("undecided", json.dumps(cards.load_json(os.path.join(rows[ref]["folder"], "cases.json"))))


class TheVersion(unittest.TestCase):
    def test_v12_changes_the_text_only(self):
        v11, v12 = template_mod.SOURCES["v11"], template_mod.SOURCES["v12"]
        self.assertEqual(cards.tree_files(v11), cards.tree_files(v12))
        changed = sorted(r for r in cards.tree_files(v11) if cards.sha256_file(os.path.join(v11, r)) != cards.sha256_file(os.path.join(v12, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json"])
        self.assertEqual(template_mod.LATEST, "v12")
        meta = cards.load_json(os.path.join(v12, "TEMPLATE.json"))
        self.assertEqual((meta["version"], "decisions_section" in meta["placeholders"]), ("v12", True))
        text = cards.read_text(os.path.join(v12, "CLAUDE.md"))
        self.assertEqual([ch for ch in text if ch.isdigit()], [])
        self.assertIn("{{decisions_section}}", text)
        self.assertIn("is read from that output and is not computed again", text)


if __name__ == "__main__":
    unittest.main()
