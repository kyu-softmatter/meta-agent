"""Template v27 (meta_agent/failures.jsonl rheotool-22, rheotool-23, rheotool-29, rheotool-32), shown on two unrelated
kinds each, neither rheology:

- src/validate_tasks.py prints under each scientific task the tolerance that judged it and, where the task refines, the
  run's own error with how it was estimated and its factor; under v26 they were in --json alone. The flow coefficient
  and the spectral peak of the v23 test.
- src/gate.py opens an install from a package source the lab's permission allows for named engines alone only in a
  bundle whose CAPABILITIES.json names one of them, as the builder's check B9 does (the person, 2026-11-18, 'Yes,
  covered'); under v26 the gate let it run in a bundle of any engine. The lattice engine and the temperature reader of
  the v13 test, as the bundles of hoomd_blue and cantera.
- the PostToolUse hook runs the gate's self-check by the project's path, so that it runs from another working
  directory; under v26 it failed there.
- the common set carries series_settled@v4, which says undecided for a window no row gives, where v3 raised.

And of the builder: CAPABILITIES.json names the document a tool profile's source names without cutting a sentence at
a slash or leaving a link that ends in one empty.

Every bundle call runs in a fresh process. Run from the repository root:
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
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.src.skills import runner as runner_mod
from meta_agent.src.tooling import profile as profile_mod
from meta_agent.tests import test_engine_scoped_sources as scoped
from meta_agent.tests import test_template_v13 as v13
from meta_agent.tests import test_template_v23 as v23
from meta_agent.tests import test_template_v24 as v24

V26, V27 = template_mod.SOURCES["v26"], template_mod.SOURCES["v27"]


def printed(bundle):
    return subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "validate_tasks.py")],
                          capture_output=True, text=True, cwd=bundle).stdout


class TheTextOutput(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v27-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_refined_task_prints_its_tolerance_and_the_run_s_error(self):
        for kind in v23.KINDS:
            fine, e = v24.run_error(kind)
            limit = v23.KINDS[kind][2]
            b = v23.compose(self.tmp, kind, [v23.task(kind, stated=limit, printed="%.9f" % limit)], template=V27)
            out = printed(b)
            tol = v23.validate(b)["tolerance"]
            self.assertIn("tolerance: %r %s, chosen_by rule, from run_numerical_error" % (tol["value"], tol["unit"]), out, kind)
            self.assertIn("run's own error: %r (two_grids, factor 3.0)" % e, out, kind)

    def test_v26_printed_neither(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            out = printed(v23.compose(self.tmp, kind + "-v26", [v23.task(kind, stated=limit, printed="%.9f" % limit)], template=V26))
            self.assertNotIn("tolerance:", out, kind)
            self.assertNotIn("run's own error", out, kind)

    def test_an_undecided_task_says_why_no_error_was_estimated(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            b = v23.compose(self.tmp, kind + "-empty", [v23.task(kind, stated=limit, printed=repr(limit))],
                            rows={"order": (None, "1")}, template=V27)
            out = printed(b)
            self.assertIn("run's own error: not estimated: the refinement's order row order has no value", out, kind)

    def test_a_person_s_tolerance_is_printed_as_theirs(self):
        for kind in v23.KINDS:
            limit = v23.KINDS[kind][2]
            human = {"value": 10.0, "unit": "1", "chosen_by": "human"}
            out = printed(v23.compose(self.tmp, kind + "-person", [v23.task(kind, stated=limit, tolerance=human)], template=V27))
            self.assertIn("tolerance: 10.0 1, chosen_by human", out, kind)
            self.assertNotIn("run's own error", out, kind)


def engine_bundle(tmp, kind, template, built_for, allowed_for):
    """A bundle of the v13 kind whose install tool reads pip from pypi, which the lab's permission allows for
    `allowed_for` alone, and whose CAPABILITIES.json names `built_for`."""
    k = v13.KINDS[kind]
    perm = designer.execution_permission(scoped.profile_root(os.path.join(tmp, "r-%s-%s-%s" % (kind, os.path.basename(template), built_for)), [allowed_for]), scoped.LAB)
    c = scoped.install_contract(k)
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([c]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in k["rows"].items()]}
    b = os.path.join(tmp, "%s-%s-%s" % (kind, os.path.basename(template), built_for))
    bundle_mod.compose(template, b, fill, [{"name": k["tool"], "contract": c, "adapter_source": k["adapter"], "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": params, "execution_permission": perm},
                       [{"id": "if-a", "call": {"tool": k["tool"], "input": {}}, "expected_verdict": "pass"}],
                       [v13.task(kind)], [], skills=catalogue_mod.take([k["analysis"]["skill"]]),
                       simulation=True, tool_kind="engine", engine=built_for)
    return b, k["tool"]


def before(bundle, tool):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "gate.py"), "--before", tool],
                       capture_output=True, text=True, cwd=bundle)
    return p.returncode, p.stdout


class TheRuntimeGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v27-gate-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_an_install_opens_for_its_own_engine_and_not_for_another(self):
        for kind, engine in scoped.ENGINES.items():
            other = [e for e in scoped.ENGINES.values() if e != engine][0]
            b, tool = engine_bundle(self.tmp, kind, V27, engine, engine)
            self.assertEqual(before(b, tool)[0], 0, kind)
            b, tool = engine_bundle(self.tmp, kind, V27, other, engine)
            code, out = before(b, tool)
            self.assertEqual(code, 3, kind)
            refusal = json.loads(out)
            self.assertEqual(refusal["code"], "GATE-NETWORK-001", kind)
            self.assertIn("allows only for the engines %s" % engine, refusal["message"], kind)

    def test_v26_let_it_run_for_another_engine(self):
        for kind, engine in scoped.ENGINES.items():
            other = [e for e in scoped.ENGINES.values() if e != engine][0]
            b, tool = engine_bundle(self.tmp, kind, V26, other, engine)
            self.assertEqual(before(b, tool)[0], 0, kind)


class TheHook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v27-hook-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def hook(self, template):
        b = v23.compose(self.tmp, "flow-" + os.path.basename(template), [], template=template)
        settings = cards.load_json(os.path.join(b, ".claude", "settings.json"))
        command = settings["hooks"]["PostToolUse"][0]["hooks"][0]["command"]
        elsewhere = os.path.join(self.tmp, "elsewhere")
        os.makedirs(elsewhere, exist_ok=True)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=b)
        return subprocess.run(command, shell=True, cwd=elsewhere, env=env, capture_output=True, text=True).returncode

    def test_the_self_check_runs_from_another_working_directory(self):
        self.assertEqual(self.hook(V27), 0)

    def test_v26_failed_there(self):
        self.assertNotEqual(self.hook(V26), 0)


class TheCommonSet(unittest.TestCase):
    def test_series_settled_v4_says_undecided_for_a_window_no_row_gives(self):
        common = cards.load_json(os.path.join(V27, "TEMPLATE.json"))["common_skills"]
        self.assertIn("series_settled@v4", common)
        self.assertNotIn("series_settled@v3", common)
        for series in ([293.0, 295.0, 297.0, 298.0, 299.0, 300.0], [0.62, 0.48, 0.41, 0.4, 0.41, 0.4, 0.4, 0.41]):
            inputs = {"series": series, "window": None, "tolerance": 0.05}
            self.assertEqual(runner_mod.run("series_settled@v3", inputs)["verdict"], "failed")
            r = runner_mod.run("series_settled@v4", inputs)
            self.assertEqual((r["verdict"], r["outputs"]["state"]), ("ran", "undecided"))


class TheDocumentName(unittest.TestCase):
    def test_a_path_a_link_and_a_sentence(self):
        self.assertEqual(profile_mod.document_name("meta_agent/tests/fixtures/echo/README.md"), "README.md")
        self.assertEqual(profile_mod.document_name("https://example.org/lattice-engine/"), "lattice-engine")
        self.assertEqual(profile_mod.document_name("the manual (meta_agent/inbox/materials/x/doc/spectrometer.pdf) and its examples"),
                         "the manual (spectrometer.pdf) and its examples")


class TheVersion(unittest.TestCase):
    def test_v27_is_the_latest_and_changes_the_gate_one_check_the_hook_and_text(self):
        self.assertEqual(template_mod.LATEST, "v27")
        changed = sorted(r for r in cards.tree_files(V26) if cards.sha256_file(os.path.join(V26, r)) != cards.sha256_file(os.path.join(V27, r)))
        self.assertEqual(changed, [".claude/settings.json", "CLAUDE.md", "TEMPLATE.json", "src/gate.py", "src/validate_tasks.py"])


if __name__ == "__main__":
    unittest.main()
