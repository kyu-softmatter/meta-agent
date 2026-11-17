"""Template v8 (tasks/016; the person, 2026-11-16, docs/ideas/20261116.md): what opens a tool's gate.

A tool whose contract says safety_gate.opens_by execution_permission, and that starts a process or writes
files, runs where the bundle's envelope/execution_permission.json is a level a person confirmed that reaches an
engine or an instrument, and is refused otherwise with an error that names the level found; every other gated
tool still waits for safety values a person wrote.

Each test calls the runner of a copy of the template, in a fresh process, with nothing of the Meta-Agent beside
it, on two unrelated kinds of tool: one that starts a process (an engine; the stand-in starts the Python
interpreter) and one that writes a file. A tool that changes an instrument and a tool gated by safety values
stand beside them.

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

IO = {"inputs": {"type": "object", "properties": {"message": {"type": "string", "minLength": 1}}, "required": ["message"]},
      "outputs": {"type": "object", "properties": {"message": {"type": "string"}, "length": {"type": "integer"}},
                  "required": ["message", "length"]}}

ENGINE = (
    "import subprocess, sys\n"
    "def run(payload):\n"
    "    out = subprocess.run([sys.executable, '-c', 'import sys; print(len(sys.argv[1]))', payload['message']],\n"
    "                         capture_output=True, text=True, check=True)\n"
    "    return {'message': payload['message'], 'length': int(out.stdout)}\n")
WRITER = (
    "import os\n"
    "BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n"
    "def run(payload):\n"
    "    os.makedirs(os.path.join(BUNDLE, 'runs'), exist_ok=True)\n"
    "    with open(os.path.join(BUNDLE, 'runs', 'written.txt'), 'w') as f:\n"
    "        f.write(payload['message'])\n"
    "    return {'message': payload['message'], 'length': len(payload['message'])}\n")
STAGE = "def run(payload):\n    return {'message': payload['message'], 'length': 0}\n"

TOOLS = {
    "engine": ("runs_process", "execution_permission", ENGINE),
    "writer": ("writes_files", "execution_permission", WRITER),
    "stage": ("controls_instrument", "execution_permission", STAGE),     # B9 refuses this contract; the gate does too
    "valve": ("runs_process", None, ENGINE),                             # gated by safety values, as before v8
}


def permission(reaches, confirmed_by="human"):
    return {"artifact": "execution_permission", "schema_version": "0.1", "reaches": reaches,
            "words": "the words the profile has", "confirmed_by": confirmed_by, "date": "2026-11-16",
            "lab_profile_ref": "lab-fixture-01", "profile_revision": 1}


def make_bundle(perm):
    """A copy of template v8 with the four tools, safety.json naming one row left null, and `perm` as
    envelope/execution_permission.json (no file when None). Returns (tmp, bundle)."""
    tmp = tempfile.mkdtemp(prefix="ma-template-v8-")
    bundle = os.path.join(tmp, "bundle")
    shutil.copytree(template_mod.SOURCES["v8"], bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, (effects, opens_by, adapter) in TOOLS.items():
        gate = {"required": True, "place": "src/gate.py, consulted by src/run_tool.py before the call"}
        if opens_by:
            gate["opens_by"] = opens_by
        c = dict({"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": name,
                  "errors": ["invalid_input", "refused_by_safety"], "side_effects": effects, "safety_gate": gate,
                  "idempotent": True, "timeout_s": None}, **IO)
        cards.write_json(os.path.join(bundle, "tools", name, "tool.json"), c)
        cards.write_text(os.path.join(bundle, "tools", name, "adapter.py"), adapter)
    cards.write_json(os.path.join(bundle, "envelope", "safety.json"), {"largest_number_of_steps": None})
    if perm is not None:
        cards.write_json(os.path.join(bundle, "envelope", "execution_permission.json"), perm)
    return tmp, bundle


def call(bundle, tool, message="four"):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "run_tool.py"), tool], input=json.dumps({"message": message}),
                       capture_output=True, text=True, cwd=bundle)
    assert p.returncode == 0, p.stdout + p.stderr
    return json.loads(p.stdout)


def self_check(bundle):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "gate.py"), "--self-check"], capture_output=True,
                       text=True, cwd=bundle)
    return p.returncode, p.stdout


class WhatOpensTheGate(unittest.TestCase):
    def run_with(self, perm):
        tmp, bundle = make_bundle(perm)
        self.addCleanup(shutil.rmtree, tmp, True)
        return bundle, {name: call(bundle, name) for name in TOOLS}

    def assertRefused(self, out, code, *words):
        self.assertEqual(out.get("artifact"), "error_contract", out)
        self.assertEqual((out["category"], out["code"]), ("refused_by_safety", code), out)
        for w in words:
            self.assertIn(w, out["message"])

    def test_a_permission_that_reaches_an_engine_opens_the_engine_and_the_writer(self):
        for level in ("engine", "instrument"):
            bundle, got = self.run_with(permission(level))
            self.assertEqual(got["engine"], {"message": "four", "length": 4}, level)     # the process was started
            self.assertEqual(got["writer"], {"message": "four", "length": 4}, level)
            self.assertEqual(cards.read_text(os.path.join(bundle, "runs", "written.txt")), "four")
            # a tool that changes an instrument opens by no permission, an instrument one included
            self.assertRefused(got["stage"], "GATE-PERMISSION-001", "controls_instrument")
            # a tool gated by safety values waits for them as before, whatever the permission
            self.assertRefused(got["valve"], "GATE-SAFETY-001", "largest_number_of_steps")
            self.assertEqual(self_check(bundle)[0], 0)

    def test_a_lower_level_is_refused_and_the_refusal_names_it(self):
        for level in ("none", "mock", "sandbox"):
            bundle, got = self.run_with(permission(level))
            for name in ("engine", "writer"):
                self.assertRefused(got[name], "GATE-PERMISSION-001", "reaches %s" % level)
                self.assertEqual(got[name]["evidence"]["reaches"], level)
            self.assertFalse(os.path.exists(os.path.join(bundle, "runs", "written.txt")), level)   # nothing was written

    def test_without_the_file_the_tools_are_refused(self):
        bundle, got = self.run_with(None)
        for name in ("engine", "writer"):
            self.assertRefused(got[name], "GATE-PERMISSION-001", "no envelope/execution_permission.json")
            self.assertIsNone(got[name]["evidence"]["reaches"])
        self.assertEqual(self_check(bundle)[0], 0)          # a bundle with no permission file is a bundle as before

    def test_a_permission_no_person_confirmed_opens_nothing_and_fails_the_self_check(self):
        bundle, got = self.run_with(permission("engine", confirmed_by="meta-macbook-20261116-1"))
        for name in ("engine", "writer"):
            self.assertRefused(got[name], "GATE-PERMISSION-001", "not a level a person confirmed")
        code, out = self_check(bundle)
        self.assertEqual(code, 2, out)
        self.assertIn("execution_permission.json", out)

    def test_the_gate_reads_the_level_and_not_the_words(self):
        words = permission("sandbox")
        words["words"] = "as far as an engine and an instrument"
        _, got = self.run_with(words)
        self.assertRefused(got["engine"], "GATE-PERMISSION-001", "reaches sandbox")


class TheVersion(unittest.TestCase):
    def test_v8_changes_the_gate_and_the_text_about_it(self):
        v7, v8 = template_mod.SOURCES["v7"], template_mod.SOURCES["v8"]
        self.assertEqual(cards.tree_files(v7), cards.tree_files(v8))
        changed = sorted(r for r in cards.tree_files(v7) if cards.sha256_file(os.path.join(v7, r)) != cards.sha256_file(os.path.join(v8, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/gate.py"])
        self.assertEqual(template_mod.LATEST, "v8")
        text = cards.read_text(os.path.join(v8, "CLAUDE.md"))
        self.assertIn("envelope/execution_permission.json", text)
        self.assertEqual([c for c in text if c.isdigit()], [])     # B6: no number the snapshot does not carry


if __name__ == "__main__":
    unittest.main()
