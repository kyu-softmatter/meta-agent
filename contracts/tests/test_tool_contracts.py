# -*- coding: utf-8 -*-
"""Tests of contracts/tools/tool_contracts.py: what bundle check B16 says (tasks/015).

Run from the repository root:  python -m unittest discover -s contracts/tests

The contracts here are of two unrelated kinds on purpose (the person, 2026-11-11): a command that
returns text, and an instrument's status.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import tool_contracts as tc  # noqa: E402


def command():
    return {
        "artifact": "tool_contract", "name": "echo",
        "inputs": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
        "outputs": {"type": "object", "properties": {"message": {"type": "string"}, "length": {"type": "integer"}},
                    "required": ["message", "length"]},
    }


def instrument():
    return {
        "artifact": "tool_contract", "name": "status",
        "inputs": {"type": "object", "properties": {}, "required": []},
        "outputs": {"type": "object",
                    "properties": {"state": {"type": "string"}, "homed": {"type": "boolean"}},
                    "required": ["state", "homed"]},
    }


class Contract(unittest.TestCase):
    def test_a_contract_that_declares_what_it_requires_passes(self):
        self.assertEqual(tc.problems(command()), [])
        self.assertEqual(tc.problems(instrument()), [])

    def test_a_required_output_that_is_not_declared_is_named(self):
        c = instrument()
        c["outputs"]["required"].append("fault")
        self.assertEqual(tc.problems(c), ["outputs: `fault` is under required and is not declared under properties"])

    def test_a_required_input_that_is_not_declared_is_named(self):
        c = command()
        c["inputs"]["required"].append("repeat")
        self.assertEqual(tc.problems(c), ["inputs: `repeat` is under required and is not declared under properties"])

    def test_required_with_no_properties_at_all(self):
        c = command()
        del c["inputs"]["properties"]
        self.assertEqual(tc.problems(c), ["inputs: `message` is under required and is not declared under properties"])

    def test_it_reads_every_depth(self):
        c = instrument()
        c["outputs"]["properties"]["readings"] = {
            "type": "array",
            "items": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name", "value"]},
        }
        self.assertEqual(tc.problems(c),
                         ["outputs.properties.readings.items: `value` is under required and is not declared under properties"])
        c = command()
        c["outputs"]["anyOf"] = [{"properties": {"message": {}}, "required": ["message"]},
                                 {"properties": {}, "required": ["error"]}]
        self.assertEqual(tc.problems(c),
                         ["outputs.anyOf[1]: `error` is under required and is not declared under properties"])

    def test_a_declared_field_need_not_be_required(self):
        c = instrument()
        c["outputs"]["properties"]["temperature"] = {"type": "number"}
        self.assertEqual(tc.problems(c), [])

    def test_a_contract_with_no_schemas_or_of_another_shape_is_not_its_to_name(self):
        self.assertEqual(tc.problems({"artifact": "tool_contract", "name": "x"}), [])
        self.assertEqual(tc.problems({"inputs": "none", "outputs": ["a"]}), [])
        self.assertEqual(tc.problems([]), ["the contract is not an object"])


class Bundle(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ma-tool-contracts-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, relpath, data):
        path = os.path.join(self.root, *relpath.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(data if isinstance(data, str) else json.dumps(data))

    def bundle(self, version):
        self.write("TEMPLATE.json", {"template": "agent", "version": version})
        bad_status = instrument()
        bad_status["outputs"]["required"].append("fault")
        bad_echo = command()
        bad_echo["inputs"]["required"].append("repeat")
        self.write("tools/status/tool.json", bad_status)
        self.write("tools/echo/tool.json", bad_echo)

    def test_a_bundle_of_the_version_it_binds_from_is_judged_tool_by_tool(self):
        self.bundle("v%d" % tc.B16_FROM)
        self.assertEqual(tc.bundle_problems(self.root), [
            ("tools/echo/tool.json", "inputs: `repeat` is under required and is not declared under properties"),
            ("tools/status/tool.json", "outputs: `fault` is under required and is not declared under properties"),
        ])

    def test_a_later_version_is_judged_too(self):
        self.bundle("v%d" % (tc.B16_FROM + 1))
        self.assertEqual(len(tc.bundle_problems(self.root)), 2)

    def test_an_earlier_template_is_not_judged(self):
        self.bundle("v%d" % (tc.B16_FROM - 1))
        self.assertEqual(tc.bundle_problems(self.root), [])

    def test_a_bundle_with_no_template_file_is_not_judged(self):
        self.write("tools/status/tool.json", {"outputs": {"required": ["fault"]}})
        self.assertEqual(tc.bundle_problems(self.root), [])

    def test_good_contracts_and_no_tools_pass(self):
        self.write("TEMPLATE.json", {"template": "agent", "version": "v%d" % tc.B16_FROM})
        self.assertEqual(tc.bundle_problems(self.root), [])
        self.write("tools/status/tool.json", instrument())
        self.write("tools/echo/tool.json", command())
        self.assertEqual(tc.bundle_problems(self.root), [])

    def test_a_contract_that_cannot_be_read_is_left_to_b7(self):
        self.write("TEMPLATE.json", {"template": "agent", "version": "v%d" % tc.B16_FROM})
        self.write("tools/status/tool.json", "{not json")
        self.assertEqual(tc.bundle_problems(self.root), [])

    def test_the_command_says_what_the_check_would(self):
        self.write("good.json", command())
        bad = instrument()
        bad["outputs"]["required"].append("fault")
        self.write("bad.json", bad)
        self.assertEqual(tc.main(["check", os.path.join(self.root, "good.json")]), 0)
        self.assertEqual(tc.main(["check", os.path.join(self.root, "bad.json")]), 1)
        self.assertEqual(tc.main(["check", os.path.join(self.root, "absent.json")]), 2)


if __name__ == "__main__":
    unittest.main()
