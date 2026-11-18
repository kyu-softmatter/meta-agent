"""S6 on a bundle whose tool starts an engine already on the computer (request req-rheotool-001: the rheoTool engine in
its Colima container, reached by docker). Its gates run only in an isolated copy outside the repository, where the
lab's permission lets the engine run; none of its calls is made in the builder's tree, which would run the engine
inside the repository (meta_agent/CLAUDE.md, Tier 0). Without a permission a person confirmed, the gate refuses every
such call and the gates run in the tree as before. A bundle with no such tool is untouched.

Two unrelated kinds, neither of them rheology: a flow coefficient and a spectral peak, each a program the adapter starts
(the interpreter itself stands in for the engine) that writes into the bundle's runs/ as an engine's case would.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.validate import gate as gate_mod

KINDS = {"flow": ("solve_flow", "drag_coefficient", 2.95), "spectrum": ("scan_spectrum", "peak_wavelength", 502.3)}
PERMISSION = {"artifact": "execution_permission", "schema_version": "0.1", "reaches": "engine",
              "words": "as far as a simulation engine on this computer; no instrument", "confirmed_by": "human",
              "date": "2026-11-18", "lab_profile_ref": "lab-fixture", "profile_revision": 1}


def adapter(field, value):
    return ("import os, subprocess, sys\n"
            "BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
            "def run(payload):\n"
            "    case = os.path.join(BUNDLE, 'runs', 'case')\n"
            "    os.makedirs(case, exist_ok=True)\n"
            "    p = subprocess.run([sys.executable, '-c', 'print(%r)'], capture_output=True, text=True, cwd=case)\n"
            "    open(os.path.join(case, 'log'), 'w').write(p.stdout)\n"
            "    return {%r: float(p.stdout)}\n" % (value, field))


def contract(tool, field, engine=True):
    c = {"artifact": "tool_contract", "schema_version": "0.1", "name": tool, "description": "starts the engine",
         "inputs": {"type": "object", "properties": {}, "required": []},
         "outputs": {"type": "object", "properties": {field: {"type": "number", "unit": "1"}}, "required": [field]},
         "errors": ["invalid_input", "permission_required"], "side_effects": "runs_process",
         "safety_gate": {"required": True, "place": "src/gate.py", "opens_by": "execution_permission"},
         "idempotent": True, "timeout_s": None}
    if engine:
        c["calls_external"] = {"program": "the engine", "license": "GPL-3.0", "bundled": False}
    return c


def compose(tmp, kind, permission=True, engine=True):
    tool, field, value = KINDS[kind]
    con = contract(tool, field, engine)
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([con]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    envelope = {"safety": {}, "parameters": {"rows": []}}
    if permission:
        envelope["execution_permission"] = dict(PERMISSION)
    path = os.path.join(tmp, "%s-%s-%s" % (kind, permission, engine))
    sci = [{"id": "sci-a", "name": "the value", "call": {"tool": tool, "input": {}}, "measure": {"stated": {field: value}},
            "reference": {"kind": "source", "ref": "a test's reference"},
            "tolerance": {"value": 0.0, "unit": "1", "chosen_by": "human"}, "expected_verdict": "pass"}]
    bundle_mod.compose(template_mod.SOURCES[template_mod.LATEST], path, fill,
                       [{"name": tool, "contract": con, "adapter_source": adapter(field, value), "errors": []}],
                       {"capabilities": []}, envelope, [], sci, [], skills=[], simulation=False)
    return path


class AnEngineInPlaceRunsOnlyInACopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-engine-in-place-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_gates_run_in_a_copy_and_the_tree_is_untouched(self):
        for kind in KINDS:
            b = compose(self.tmp, kind)
            self.assertEqual([n for n, _ in gate_mod.engine_tools(b)], [KINDS[kind][0]], kind)
            before = set(os.listdir(tempfile.gettempdir()))
            report, why, tree_safe = gate_mod.in_a_copy(b)
            self.assertFalse(tree_safe, kind)
            self.assertIsNone(why, kind)                                   # the copy was removed
            self.assertEqual(report["validate"]["scientific"]["verdict"], "pass", (kind, report["validate"]))
            self.assertEqual(report["validate"]["scientific"]["tasks"][0]["measured"], {KINDS[kind][1]: KINDS[kind][2]}, kind)
            self.assertFalse(os.path.exists(os.path.join(b, "runs", "case")), kind)    # no call was made in the tree
            left = [n for n in set(os.listdir(tempfile.gettempdir())) - before if n.startswith("ma-s6-engine-")]
            self.assertEqual(left, [], kind)

    def test_without_a_permission_the_gate_refuses_and_the_tree_is_safe(self):
        for kind in KINDS:
            b = compose(self.tmp, kind, permission=False)
            report, why, tree_safe = gate_mod.in_a_copy(b)
            self.assertIsNone(report, kind)
            self.assertTrue(tree_safe, kind)
            self.assertIn("no execution permission", why, kind)
            r = gate_mod.run_bundle(b)
            self.assertEqual(r["validate"]["scientific"]["tasks"][0]["verdict"], "not_run", (kind, r["validate"]))
            self.assertFalse(os.path.exists(os.path.join(b, "runs", "case")), kind)

    def test_a_tool_that_names_no_external_program_is_not_an_engine_in_place(self):
        for kind in KINDS:
            b = compose(self.tmp, kind, engine=False)
            self.assertEqual(gate_mod.engine_tools(b), [], kind)
            self.assertEqual(gate_mod.in_a_copy(b), (None, None, True), kind)


if __name__ == "__main__":
    unittest.main()
