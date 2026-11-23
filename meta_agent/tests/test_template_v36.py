"""Template v36 and the builder, at the design role's ask 20261117-design-macbook-20261117-2-4 (tasks/018; dft-13 and
the meta side of dft-14, from the Quantum ESPRESSO test of round three, runs dft/20261117-20 and dft/20261117-22).

- The bundle's runner checks an output field's enum and const for every type (v35 looked at a string's enum alone), so
  a contract can say that a call which answers ended well: an output that reports an engine ended otherwise comes back
  as an error, and the interface task and the replay item that expected an output fail and say why.
- The builder refuses an interface task or a replay item that expects an output and names no field of it (it would
  pass whatever the call returns), or names a field the tool's contract does not declare.
- classify-knowledge names a value an engine printed in its maker's own run as computed, its kind of source and its
  grade waiting for the person's word.

Two unrelated kinds: a DFT engine's example run whose script ended with exit status 1 against a contract that allows 0
alone, and an optical spectrometer whose reading came back saturated against a contract that allows false alone. Each
tool is a mock adapter that returns its output and starts no engine and reaches no instrument.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.validate import gate as gate_mod

OLD_V, NEW_V = template_mod.SOURCES["v35"], template_mod.SOURCES["v36"]

# each kind: the tool, the field that says how the call ended and the one value the contract allows for it, the output
# of a call that ended well and of one that did not, and another field an item may name
KINDS = {
    "dft": {"tool": "run_example_mock", "status": "exit_status", "type": "integer", "allowed": 0,
            "good": {"example": "example01", "exit_status": 0}, "bad": {"example": "example01", "exit_status": 1},
            "other": "example", "description": "the exit status the example's script ended with"},
    "spectrometer": {"tool": "read_spectrum_mock", "status": "saturated", "type": "boolean", "allowed": False,
                     "good": {"peak_nm": 532.1, "saturated": False}, "bad": {"peak_nm": 532.1, "saturated": True},
                     "other": "peak_nm", "description": "whether the detector was saturated during the exposure"},
}


def contract(k):
    other_type = "string" if k["other"] == "example" else "number"
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["tool"], "description": "a mock that returns its output",
            "inputs": {"type": "object", "properties": {}, "required": []},
            "outputs": {"type": "object", "properties": {k["other"]: {"type": other_type, "description": "what was read"},
                                                         k["status"]: {"type": k["type"], "const": k["allowed"],
                                                                       "description": k["description"]}},
                        "required": [k["other"], k["status"]]},
            "errors": ["invalid_input", "execution_failure"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "a mock touches nothing"}, "idempotent": True, "timeout_s": None}


def adapter(output):
    return "def run(payload):\n    return %r\n" % (output,)


def item(k, iid, expected_output):
    return {"id": iid, "name": "the mock answers", "call": {"tool": k["tool"], "input": {}},
            "expected": {"output": expected_output}, "expected_verdict": "pass"}


def compose(tmp, name, k, output, interface, replay, template):
    path = os.path.join(tmp, name, "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    fill = {"agent_name": name, "template": "agent@test", "rid": "req-%s" % name, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([contract(k)]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    bundle_mod.compose(template, path, fill, [{"name": k["tool"], "contract": contract(k), "adapter_source": adapter(output),
                                               "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": []}}, interface, [], replay,
                       skills=[], simulation=False)
    return path


class AnOutputThatEndedOtherwiseFails(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v36-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def verdicts(self, kind, output, template):
        k = KINDS[kind]
        want = {k["other"]: output[k["other"]]}                   # the item names a field, not how the call ended
        path = compose(os.path.join(self.tmp, template[-3:] + ("-good" if output == k["good"] else "-bad")), kind, k,
                       output, [item(k, "if-1", want)], [item(k, "rp-001", want)], template)
        report = gate_mod.run_bundle(path)
        return report["validate"]["interface"]["tasks"][0], report["replay"]

    def test_a_call_that_ended_otherwise_fails_its_interface_task_and_its_replay_item(self):
        for kind, k in KINDS.items():
            iface, replay = self.verdicts(kind, k["bad"], NEW_V)
            self.assertEqual(iface["verdict"], "fail", kind)
            self.assertIn("output.%s: not %s" % (k["status"], "0" if k["type"] == "integer" else "false"), iface["detail"], kind)
            self.assertIn("execution_failure", iface["detail"], kind)
            self.assertFalse(replay["ok"], kind)

    def test_a_call_that_ended_well_passes(self):
        for kind, k in KINDS.items():
            iface, replay = self.verdicts(kind, k["good"], NEW_V)
            self.assertEqual(iface["verdict"], "pass", (kind, iface["detail"]))
            self.assertTrue(replay["ok"], kind)

    def test_under_the_old_version_the_same_call_passed(self):
        # the fault of dft-13, kept as it was: the old runner looked at no integer's or boolean's const
        for kind, k in KINDS.items():
            iface, replay = self.verdicts(kind, k["bad"], OLD_V)
            self.assertEqual(iface["verdict"], "pass", kind)
            self.assertTrue(replay["ok"], kind)


class TheBuilderRefusesAnItemThatNamesNoField(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v36-b-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_an_output_with_no_field_is_refused(self):
        for kind, k in KINDS.items():
            for where in ("interface", "replay"):
                bad = [item(k, "x-1", {})]
                with self.assertRaises(ValueError) as cm:
                    compose(os.path.join(self.tmp, where), kind, k, k["good"], bad if where == "interface" else [],
                            bad if where == "replay" else [], NEW_V)
                self.assertIn("names no field of it", str(cm.exception), (kind, where))

    def test_a_field_the_contract_does_not_declare_is_refused(self):
        for kind, k in KINDS.items():
            with self.assertRaises(ValueError) as cm:
                compose(self.tmp, kind, k, k["good"], [item(k, "if-1", {"stauts": 0})], [], NEW_V)
            self.assertIn("does not declare", str(cm.exception), kind)

    def test_the_old_version_builds_it_as_before(self):
        for kind, k in KINDS.items():
            path = compose(os.path.join(self.tmp, "old"), kind, k, k["good"], [item(k, "if-1", {})], [], OLD_V)
            self.assertTrue(os.path.isfile(os.path.join(path, "validation", "interface", "if-1.json")), kind)


class TheVersion(unittest.TestCase):
    def test_classify_knowledge_names_a_makers_reference_output(self):
        with open(os.path.join(NEW_V, ".claude", "skills", "classify-knowledge", "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("a reference output shipped with the maker's examples", text)
        self.assertIn("its kind of value `computed`", text)
        self.assertIn("Do not choose one.", text)

    def test_it_is_the_latest_and_changes_two_scripts_one_skill_and_its_card(self):
        self.assertIn("v36", template_mod.SOURCES)                  # v37 is the latest since pairs are judged one measurand
        self.assertEqual(sorted(set(cards.tree_files(NEW_V)) ^ set(cards.tree_files(OLD_V))), [])
        both = set(cards.tree_files(OLD_V)) & set(cards.tree_files(NEW_V))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(OLD_V, r)) != cards.sha256_file(os.path.join(NEW_V, r)))
        self.assertEqual(changed, [".claude/skills/classify-knowledge/SKILL.md", "TEMPLATE.json", "src/replay.py",
                                   "src/run_tool.py"])


if __name__ == "__main__":
    unittest.main()
