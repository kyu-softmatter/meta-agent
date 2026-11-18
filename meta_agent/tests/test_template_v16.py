"""Template v16 (tasks/019; failures.jsonl cfd-2, cfd-7, cfd-10, cfd-11; dft-2), after the CFD test's clone and its
bundle standing alone.

cfd-7: a scientific task's agreement is a library skill's output. src/validate_tasks.py takes each measured value's
error against its reference from measurement_error@v1 through src/run_skill.py, judges the magnitude against the
person's tolerance and prints each run; the build puts the skill into every bundle with a scientific task, and a bundle
without it fails the task and says so.
cfd-2: a tool keeps every error contract of a category; the runner returns the first as its own.

Two unrelated kinds: an engine whose lattice call returns a particle count, judged through the estimate of the box that
holds them; and a spectrometer whose reading returns a sample's temperatures, judged through the window's mean. Every
call runs in a fresh process in a bundle with nothing of the Meta-Agent beside it.

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
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.src.skills import runner as runner_mod
from meta_agent.tests import test_template_v13 as v13

AGREEMENT = "measurement_error@v1"
V16 = template_mod.SOURCES["v16"]


def compose(tmp, name, sci, errors=(), inputs=None):
    """A v16 bundle in tmp/<name>, of the kind its name starts with, carrying the skills of its analysis only."""
    kind = name.split("-")[0]
    k = v13.KINDS[kind]
    c = v13.contract(k)
    c["errors"] = sorted({e["category"] for e in errors} | {"invalid_input"})
    if inputs is not None:
        c["inputs"] = inputs
    tools = [{"name": k["tool"], "contract": c, "adapter_source": k["adapter"], "errors": list(errors)}]
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([c]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in k["rows"].items()]}
    iface = [{"id": "if-a", "call": {"tool": k["tool"], "input": {}}, "expected_verdict": "pass"}]
    path = os.path.join(tmp, name)
    bundle_mod.compose(V16, path, fill, tools, {"capabilities": []}, {"safety": {}, "parameters": params}, iface, sci, [],
                       skills=catalogue_mod.take([k["analysis"]["skill"]]))
    return path


def error(code, category):
    return {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category,
            "message": "the input is not one this tool takes (%s)" % code, "retryable": False,
            "remediation": {"action": "correct the input"}}


class TheAgreement(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v16-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_build_puts_the_agreement_skill_into_a_bundle_with_a_scientific_task(self):
        for kind in v13.KINDS:
            b = compose(self.tmp, kind, [v13.task(kind)])
            self.assertTrue(os.path.isfile(os.path.join(b, "skills", AGREEMENT, "skill.json")), kind)
            self.assertIn(AGREEMENT, cards.read_text(os.path.join(b, "CLAUDE.md")), kind)

    def test_no_scientific_task_carries_no_agreement_skill(self):
        b = compose(self.tmp, "engine-none", [])
        self.assertFalse(os.path.exists(os.path.join(b, "skills", AGREEMENT)))

    def test_the_agreement_is_the_skill_s_magnitude_and_each_run_is_printed(self):
        for kind, k in v13.KINDS.items():
            off = v13.expected(kind) + 0.5
            r = v13.validate(compose(self.tmp, kind + "-off", [v13.task(kind, stated=off)]))
            out = k["analysis"]["output"]
            want = runner_mod.run(AGREEMENT, {"measured": v13.expected(kind), "reference": off})["outputs"]
            self.assertEqual(r["verdict"], "fail", (kind, r))
            self.assertEqual(r["agreement"], want["magnitude"], kind)
            run = r["agreement_runs"][out]
            self.assertEqual((run["skill"], run["verdict"]), (AGREEMENT, "ran"), kind)
            self.assertEqual(run["outputs"], want, kind)
            self.assertLess(run["outputs"]["error"], 0, kind)           # the measured value lies below the reference

    def test_on_the_reference_it_passes_and_without_a_tolerance_it_is_undecided(self):
        for kind in v13.KINDS:
            self.assertEqual(v13.validate(compose(self.tmp, kind + "-on", [v13.task(kind)]))["verdict"], "pass", kind)
            r = v13.validate(compose(self.tmp, kind + "-free", [v13.task(kind, tolerance=None)]))
            self.assertEqual(r["verdict"], "undecided", kind)
            self.assertIn(AGREEMENT, json.dumps(r["agreement_runs"]), kind)

    def test_a_bundle_without_the_skill_fails_the_task_and_says_so(self):
        for kind in v13.KINDS:
            b = compose(self.tmp, kind + "-cut", [v13.task(kind)])
            shutil.rmtree(os.path.join(b, "skills", AGREEMENT))
            r = v13.validate(b)
            self.assertEqual(r["verdict"], "fail", kind)
            self.assertIn("does not carry %s" % AGREEMENT, r["reason"], kind)


class TheErrors(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v16-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_every_contract_of_a_category_is_kept_and_the_runner_returns_the_first(self):
        for kind, k in v13.KINDS.items():
            errs = [error("X-INPUT-001", "invalid_input"), error("X-INPUT-002", "invalid_input")]
            b = compose(self.tmp, kind + "-errs", [], errors=errs, inputs={
                "type": "object", "required": ["size"], "properties": {"size": {"type": "number", "unit": "1"}}})
            d = os.path.join(b, "tools", k["tool"], "errors")
            self.assertEqual(sorted(os.listdir(d)), ["invalid_input.X-INPUT-002.json", "invalid_input.json"], kind)
            p = subprocess.run([sys.executable, "-I", os.path.join(b, "src", "run_tool.py"), k["tool"]],
                               input=json.dumps({"size": "not a number"}), capture_output=True, text=True, cwd=b)
            out = json.loads(p.stdout)
            self.assertEqual((out.get("category"), out.get("code")), ("invalid_input", "X-INPUT-001"), (kind, out))


class TheVersion(unittest.TestCase):
    def test_v16_changes_what_it_says(self):
        v15 = template_mod.SOURCES["v15"]
        self.assertIn("v16", template_mod.SOURCES)                  # v17 is the latest since cfd-13
        self.assertEqual(cards.tree_files(v15), cards.tree_files(V16))
        changed = sorted(r for r in cards.tree_files(v15) if cards.sha256_file(os.path.join(v15, r)) != cards.sha256_file(os.path.join(V16, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/run_tool.py", "src/validate_tasks.py", "tasks/001-start.md"])
        meta = cards.load_json(os.path.join(V16, "TEMPLATE.json"))
        self.assertEqual((meta["version"], meta["agreement_skill"]), ("v16", AGREEMENT))
        start = cards.read_text(os.path.join(V16, "tasks", "001-start.md"))
        self.assertIn("run it again after the install", start)
        self.assertIn("**Status** line is the builder's", start)
        self.assertIn("is in UTC", cards.read_text(os.path.join(V16, "CLAUDE.md")))


if __name__ == "__main__":
    unittest.main()
