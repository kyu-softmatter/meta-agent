"""Template v7 (tasks/016, test run 20261116-4): the task validator judges a scientific task against the values
a source states, and a call that was not made is not_run.

Each test runs the validator of a copy of the template with one tool in it and nothing of the Meta-Agent
beside it, on fixtures of two unrelated kinds: the echo command and the status tool of the fixture rheometer.

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

from meta_agent.src import cards, designer
from meta_agent.src.build import template as template_mod
from meta_agent.src.validate import gate as gate_mod

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
EXACT = {"value": 0, "unit": "1", "chosen_by": "human"}
ECHO = os.path.join(HERE, "fixtures", "echo", "adapter.py")
STATUS = os.path.join(HERE, "fixtures", "rheometer", "adapters", "status.py")
UNAVAILABLE = (
    "def run(payload):\n"
    "    return {'artifact': 'error_contract', 'schema_version': '0.1', 'code': 'FX-UNAVAILABLE-001', 'category': 'unavailable',\n"
    "            'message': 'no reply', 'retryable': True, 'remediation': {'action': 'check the connection'}}\n")


def contract(request, name):
    intake = designer.latest_intake(os.path.join(META, "requests", request))[1]
    if "tool_contract" in intake:
        return intake["tool_contract"]
    return [t["contract"] for t in intake["tools"] if t["contract"]["name"] == name][0]


def stated_task(tid, tool, call_input, stated, tolerance):
    return {"id": tid, "name": tid, "call": {"tool": tool, "input": call_input}, "measure": {"stated": stated},
            "reference": {"kind": "source", "ref": "the fixture's page"}, "tolerance": tolerance, "expected_verdict": "pass"}


def judge(tool, tool_contract, adapter, tasks):
    """{task id: the validator's row} from a copy of template v7 that holds one tool and these scientific tasks."""
    tmp = tempfile.mkdtemp(prefix="ma-template-v7-")
    try:
        bundle = os.path.join(tmp, "bundle")
        shutil.copytree(template_mod.SOURCES["v7"], bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        cards.write_json(os.path.join(bundle, "tools", tool, "tool.json"), tool_contract)
        if os.path.isfile(adapter):
            shutil.copy(adapter, os.path.join(bundle, "tools", tool, "adapter.py"))
        else:
            cards.write_text(os.path.join(bundle, "tools", tool, "adapter.py"), adapter)
        for t in tasks:
            cards.write_json(os.path.join(bundle, "validation", "scientific", t["id"] + ".json"), t)
        p = subprocess.run([sys.executable, "-I", os.path.join("src", "validate_tasks.py"), "--json"], cwd=bundle,
                           capture_output=True, text=True, timeout=120)
        report = json.loads(p.stdout)
        return {t["id"]: t for t in report["scientific"]["tasks"]}, report
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class AgainstWhatASourceStates(unittest.TestCase):
    def test_the_echo_command(self):
        got, _ = judge("echo", contract("req-echo-001", "echo"), ECHO, [
            stated_task("a-equal", "echo", {"message": "soft matter"}, {"length": 11}, EXACT),
            stated_task("b-no-tolerance", "echo", {"message": "soft matter"}, {"length": 11}, None),
            stated_task("c-differs", "echo", {"message": "soft matter"}, {"length": 12}, EXACT),
            stated_task("d-a-seat-s-tolerance", "echo", {"message": "soft matter"}, {"length": 11},
                        {"value": 0, "unit": "1", "chosen_by": "meta-macbook-20261116-1"}),
            stated_task("e-the-call-fails", "echo", {"message": ""}, {"length": 0}, EXACT),
            stated_task("f-no-such-field", "echo", {"message": "soft matter"}, {"words": 2}, EXACT),
            {"id": "g-a-function", "name": "g-a-function", "call": {"tool": "echo", "input": {"message": "soft matter"}},
             "measure": {"output_field": "length", "reference_function": "len_message"},
             "reference": {"kind": "analytic", "ref": "len(message)"}, "tolerance": EXACT, "expected_verdict": "pass"},
            {"id": "h-neither", "name": "h-neither", "call": {"tool": "echo", "input": {"message": "x"}}, "measure": {},
             "reference": {"kind": "source", "ref": "nothing stated"}, "tolerance": EXACT, "expected_verdict": "pass"},
        ])
        self.assertEqual((got["a-equal"]["verdict"], got["a-equal"]["agreement"]), ("pass", 0))
        self.assertEqual(got["a-equal"]["reference"], {"length": 11})
        self.assertEqual(got["b-no-tolerance"]["verdict"], "undecided")
        self.assertEqual(got["c-differs"]["verdict"], "fail")
        self.assertIn("length (measured 11, stated 12)", got["c-differs"]["reason"])
        self.assertEqual(got["d-a-seat-s-tolerance"]["verdict"], "undecided")     # only a person chooses a tolerance
        self.assertEqual(got["e-the-call-fails"]["verdict"], "fail")              # a call that was made and failed
        self.assertIn("(invalid_input)", got["e-the-call-fails"]["reason"])
        self.assertEqual(got["f-no-such-field"]["verdict"], "fail")
        self.assertEqual(got["g-a-function"]["verdict"], "pass")                  # a reference function, as before
        self.assertEqual(got["h-neither"]["verdict"], "not_run")

    def test_the_fixture_rheometer_s_status(self):
        kelvin = {"value": 0.5, "unit": "K", "chosen_by": "human"}
        got, _ = judge("status", contract("req-rheo-fixture-001", "status"), STATUS, [
            stated_task("a-both-equal", "status", {}, {"temperature": 298.15, "gap": 0.00005}, EXACT),
            stated_task("b-one-differs", "status", {}, {"temperature": 298.15, "gap": 0.0001}, EXACT),
            stated_task("c-two-units-one-tolerance", "status", {}, {"temperature": 298.15, "gap": 0.0001}, kelvin),
            stated_task("d-one-field-inside", "status", {}, {"temperature": 298.4}, kelvin),
            stated_task("e-one-field-outside", "status", {}, {"temperature": 299.15}, kelvin),
        ])
        self.assertEqual(got["a-both-equal"]["verdict"], "pass")
        self.assertEqual(got["b-one-differs"]["verdict"], "fail")
        self.assertIn("gap (measured", got["b-one-differs"]["reason"])
        self.assertNotIn("temperature (", got["b-one-differs"]["reason"])
        # a tolerance in kelvin cannot judge a gap in metres: nothing is decided, and the reason says what to do
        self.assertEqual(got["c-two-units-one-tolerance"]["verdict"], "undecided")
        self.assertIn("a task states one field for each tolerance", got["c-two-units-one-tolerance"]["reason"])
        self.assertEqual(got["d-one-field-inside"]["verdict"], "pass")
        self.assertEqual(got["e-one-field-outside"]["verdict"], "fail")

    def test_a_call_that_was_not_made_is_not_run(self):
        gated = dict(contract("req-echo-001", "echo"), side_effects="runs_process", errors=["invalid_input", "refused_by_safety"],
                     safety_gate={"required": True, "place": "src/gate.py reads envelope/safety.json before the call"})
        got, report = judge("echo", gated, ECHO, [stated_task("a", "echo", {"message": "soft matter"}, {"length": 11}, EXACT)])
        self.assertEqual(got["a"]["verdict"], "not_run")          # no safety value is set: the gate refused the call
        self.assertIn("GATE-SAFETY-001 (refused_by_safety)", got["a"]["reason"])
        self.assertEqual(report["scientific"]["verdict"], "not_run")
        away = dict(contract("req-rheo-fixture-001", "status"), errors=["invalid_input", "unavailable"])
        got, _ = judge("status", away, UNAVAILABLE, [stated_task("a", "status", {}, {"temperature": 298.15}, EXACT)])
        self.assertEqual(got["a"]["verdict"], "not_run")          # the instrument did not answer
        self.assertIn("(unavailable)", got["a"]["reason"])

    def test_v7_changes_one_script_and_no_text(self):
        v6, v7 = template_mod.SOURCES["v6"], template_mod.SOURCES["v7"]
        self.assertEqual(cards.tree_files(v6), cards.tree_files(v7))
        changed = sorted(r for r in cards.tree_files(v6) if cards.sha256_file(os.path.join(v6, r)) != cards.sha256_file(os.path.join(v7, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        self.assertEqual(template_mod.LATEST, "v7")


class TheReport(unittest.TestCase):
    """src/validate/gate.py on what the validator of v7 prints."""

    def report(self, task):
        return {"validate": {"interface": {"verdict": "pass", "tasks": []}, "scientific": {"verdict": task["verdict"], "tasks": [task]},
                             "overall": task["verdict"]}, "replay": {"items": [], "ok": True}}

    def test_the_agreement_has_the_tolerance_s_unit_and_a_stated_reference_adds_no_number(self):
        task = {"id": "sci-1", "name": "the temperature the page states", "file": "sci-1.json", "verdict": "pass",
                "measured": {"temperature": 298.15}, "reference": {"temperature": 298.4}, "agreement": 0.25,
                "reference_spec": {"kind": "source", "ref": "the fixture's page", "number_names": ["stated", "difference"]},
                "tolerance": {"value": 0.5, "unit": "K", "chosen_by": "human"}}
        vr, _, sci = gate_mod.make_validation_report(self.report(task), "build-x-0001", "req-x-001", "meta_agent/builds/x/0001/bundle",
                                                     "meta-macbook-20261116-1", "2026-11-16T12:00:00Z")
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0.25, "unit": "K"})
        self.assertEqual(vr["numbers"], [])
        self.assertEqual(sci, "pass")


if __name__ == "__main__":
    unittest.main()
