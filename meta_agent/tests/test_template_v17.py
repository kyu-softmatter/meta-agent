"""Template v17 and the validation report (tasks/019; failures.jsonl cfd-13, cfd-14), after round two of the CFD test.

cfd-13: the bundle's runner of tools raised TypeError when an input's type is a list of JSON Schema types, such as
["integer", "null"]; v17 accepts a value of any of them, checks it further as the one it is, and refuses a value of
none of them with an invalid_input error contract.
cfd-14: the builder's validation report kept the agreement but not the runs of the skill that gave it; each run is now a
number of the report whose source names the skill and the task, and the task's reason names the skill.

Two unrelated kinds, the engine and the spectrometer of the v13 and v16 tests; every bundle call runs in a fresh process.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import importlib.util
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
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.src.validate import gate as gate_mod
from meta_agent.tests import test_template_v13 as v13

V17 = template_mod.SOURCES["v17"]
AGREEMENT = "measurement_error@v1"
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEAT = "meta-macbook-20261117-2"
NOW = "2026-11-17T22:00:00Z"
STEPS = {"type": ["integer", "null"], "unit": "count", "default": None}


def contracts():
    spec = importlib.util.spec_from_file_location("contracts_validate", os.path.join(REPO, "contracts", "validate.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.Contracts()


def compose(tmp, name, sci, template=V17):
    """A bundle of the kind its name starts with, whose tool takes an optional input typed integer or null."""
    kind = name.split("-")[0]
    k = v13.KINDS[kind]
    c = v13.contract(k)
    c["inputs"] = {"type": "object", "properties": {"steps": dict(STEPS)}}
    tools = [{"name": k["tool"], "contract": c, "adapter_source": k["adapter"], "errors": []}]
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([c]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in k["rows"].items()]}
    iface = [{"id": "if-a", "call": {"tool": k["tool"], "input": {}}, "expected_verdict": "pass"}]
    path = os.path.join(tmp, name)
    bundle_mod.compose(template, path, fill, tools, {"capabilities": []}, {"safety": {}, "parameters": params}, iface, sci, [],
                       skills=catalogue_mod.take([k["analysis"]["skill"]]))
    return path


def call(bundle, tool, payload):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "run_tool.py"), tool],
                       input=json.dumps(payload), capture_output=True, text=True, cwd=bundle)
    return p.returncode, p.stdout, p.stderr


class ATypeList(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v17-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_v16_raises_on_it_and_v17_takes_either_type(self):
        for kind, k in v13.KINDS.items():
            old = compose(self.tmp, kind + "-v16", [], template=template_mod.SOURCES["v16"])
            code, _, err = call(old, k["tool"], {"steps": 3})
            self.assertNotEqual(code, 0, kind)
            self.assertIn("TypeError", err, kind)
            new = compose(self.tmp, kind + "-v17", [])
            for payload in ({"steps": 3}, {"steps": None}, {}):
                code, out, err = call(new, k["tool"], payload)
                self.assertEqual(code, 0, (kind, payload, err))
                self.assertNotEqual(json.loads(out).get("artifact"), "error_contract", (kind, payload, out))

    def test_a_value_of_neither_type_is_refused_with_an_error_contract(self):
        for kind, k in v13.KINDS.items():
            b = compose(self.tmp, kind + "-bad", [])
            for payload in ({"steps": "three"}, {"steps": 2.5}, {"steps": True}):
                code, out, err = call(b, k["tool"], payload)
                self.assertEqual(code, 0, (kind, payload, err))
                e = json.loads(out)
                self.assertEqual((e.get("artifact"), e.get("category")), ("error_contract", "invalid_input"), (kind, payload))
                self.assertIn("expected one of integer, null", e.get("message", ""), (kind, payload))


class TheReportKeepsTheAgreementRuns(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = contracts()

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v17-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def report(self, bundle):
        out = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "validate_tasks.py"), "--json"],
                             capture_output=True, text=True, cwd=bundle).stdout
        return {"validate": json.loads(out), "replay": {"items": [], "ok": True}}

    def test_each_run_is_a_number_naming_the_skill_and_the_report_passes_its_schema(self):
        for kind, k in v13.KINDS.items():
            off = v13.expected(kind) + 0.5
            t = v13.task(kind, stated=off, tolerance=None)
            t["reference"] = {"kind": "source", "ref": "the skill's worked value"}      # the report's form of a reference
            b = compose(self.tmp, kind + "-off", [t])
            vr, _, sci = gate_mod.make_validation_report(self.report(b), "build-%s-0001" % kind, "req-%s-001" % kind,
                                                         "meta_agent/builds/%s/0001/bundle" % kind, SEAT, NOW, bundle_path=b)
            self.assertEqual(sci, "undecided", kind)
            field = k["analysis"]["output"]
            n = [x for x in vr["numbers"] if x["name"] == "sci-a.%s.error" % field]
            self.assertEqual(len(n), 1, (kind, vr["numbers"]))
            self.assertEqual(n[0]["source"], "computed:%s@meta_agent/builds/%s/0001/bundle/validation/scientific/sci-a.json#%s"
                             % (AGREEMENT, kind, field))
            self.assertAlmostEqual(n[0]["value"], v13.expected(kind) - off, places=12)
            self.assertEqual(n[0]["grade"], self.c.grade_table[("computed", n[0]["value_kind"])], kind)
            task = vr["scientific"]["tasks"][0]
            self.assertIn("given by %s" % AGREEMENT, task["reason"], kind)
            self.assertEqual([e.message for e in self.c.validator("validation_report").iter_errors(vr)], [], kind)

    def test_a_report_of_an_earlier_bundle_has_no_such_number(self):
        task = {"id": "sci-1", "name": "x", "file": "sci-1.json", "verdict": "undecided", "measured": 1.0, "reference": 2.0,
                "agreement": 1.0}
        vr, _, _ = gate_mod.make_validation_report({"validate": {"interface": {"verdict": "pass", "tasks": []},
                                                                 "scientific": {"verdict": "undecided", "tasks": [task]},
                                                                 "overall": "undecided"},
                                                    "replay": {"items": [], "ok": True}}, "build-x-0001", "req-x-001", "b", SEAT, NOW)
        self.assertEqual([x for x in vr["numbers"] if x["name"].endswith(".error")], [])
        self.assertNotIn("given by", vr["scientific"]["tasks"][0]["reason"])


class TheVersion(unittest.TestCase):
    def test_v17_changes_the_runner_of_tools_alone(self):
        v16 = template_mod.SOURCES["v16"]
        self.assertIn("v17", template_mod.SOURCES)                  # v18 is the latest since the ask 1-14
        self.assertEqual(cards.tree_files(v16), cards.tree_files(V17))
        changed = sorted(r for r in cards.tree_files(v16) if cards.sha256_file(os.path.join(v16, r)) != cards.sha256_file(os.path.join(V17, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/run_tool.py"])
        self.assertEqual(cards.load_json(os.path.join(V17, "TEMPLATE.json"))["version"], "v17")


if __name__ == "__main__":
    unittest.main()
