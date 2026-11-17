"""Template v10 (tasks/016, test run 20261116-8): what round four's bundle on an engine showed standing alone.

The runner of tools keeps the one install inside the bundle, pointing the installers' package caches at runs/cache
before the install the gate opens, and refuses an output whose field of unit count is below zero, where an adapter
returned a sentinel its contract does not declare. The text says which envelope file opens which gate, what leaves
folders under runs/, what each of the first two checks prints last, and whose a measured value's grade is.

Each runner test calls the runner of a copy of the template in a fresh process, with nothing of the Meta-Agent beside
it, on two unrelated kinds of tool: an engine (its stand-in starts a process) and an analysis tool with no side
effects. Nothing reaches the network: the install's stand-in only reports the cache its child process would use.

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
from meta_agent.tests.test_template_v8 import call, permission, self_check

PIXI = {"installer": "pixi", "channel": "conda-forge"}
COUNT_IO = {"inputs": {"type": "object", "properties": {"message": {"type": "string", "minLength": 1}}, "required": ["message"]},
            "outputs": {"type": "object", "properties": {"message": {"type": "string"},
                                                         "length": {"type": "integer", "unit": "count"}},
                        "required": ["message", "length"]}}
SEES_CACHE = (
    "import subprocess, sys\n"
    "def run(payload):\n"
    "    out = subprocess.run([sys.executable, '-c', 'import os; print(os.environ.get(\"PIXI_CACHE_DIR\", \"\"))'],\n"
    "                         capture_output=True, text=True, check=True)\n"
    "    return {'message': out.stdout.strip(), 'length': len(out.stdout.strip())}\n")
ENGINE = (
    "import subprocess, sys\n"
    "def run(payload):\n"
    "    if payload['message'] == 'last':\n"
    "        return {'message': 'last', 'length': -1}\n"
    "    out = subprocess.run([sys.executable, '-c', 'import sys; print(len(sys.argv[1]))', payload['message']],\n"
    "                         capture_output=True, text=True, check=True)\n"
    "    return {'message': payload['message'], 'length': int(out.stdout)}\n")
READER = ("def run(payload):\n"
          "    m = payload['message']\n"
          "    return {'message': m, 'length': -1 if m == 'last' else len(m)}\n")

# name: (side effects, opens_by, installs_from, adapter)
TOOLS = {
    "install": ("network", "execution_permission", PIXI, SEES_CACHE),
    "engine": ("runs_process", "execution_permission", None, ENGINE),
    "reader": ("none", None, None, READER),
}


def make_bundle():
    tmp = tempfile.mkdtemp(prefix="ma-template-v10-")
    bundle = os.path.join(tmp, "bundle")
    shutil.copytree(template_mod.SOURCES["v10"], bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, (effects, opens_by, installs, adapter) in TOOLS.items():
        gate = {"required": effects != "none", "place": "src/gate.py, consulted by src/run_tool.py before the call"}
        if opens_by:
            gate["opens_by"] = opens_by
        c = dict({"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": name,
                  "errors": ["invalid_input", "execution_failure", "refused_by_safety"], "side_effects": effects,
                  "safety_gate": gate, "idempotent": True, "timeout_s": None}, **COUNT_IO)
        if installs:
            c["installs_from"] = installs
        cards.write_json(os.path.join(bundle, "tools", name, "tool.json"), c)
        cards.write_text(os.path.join(bundle, "tools", name, "adapter.py"), adapter)
    p = permission("engine")
    p["package_sources"] = [dict(PIXI)]
    cards.write_json(os.path.join(bundle, "envelope", "execution_permission.json"), p)
    return tmp, bundle


class TheRunner(unittest.TestCase):
    def setUp(self):
        self.tmp, self.bundle = make_bundle()
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_install_keeps_its_package_cache_inside_the_bundle(self):
        got = call(self.bundle, "install")
        cache = os.path.realpath(got["message"])
        self.assertEqual(cache, os.path.realpath(os.path.join(self.bundle, "runs", "cache", "pixi_cache_dir")), got)
        self.assertTrue(os.path.isdir(cache))
        self.assertEqual(self_check(self.bundle)[0], 0)

    def test_no_other_call_moves_a_cache(self):
        for name in ("engine", "reader"):
            self.assertEqual(call(self.bundle, name), {"message": "four", "length": 4}, name)
        self.assertFalse(os.path.exists(os.path.join(self.bundle, "runs", "cache")))

    def test_a_count_below_zero_is_refused_as_the_contract_s_and_not_returned(self):
        for name in ("engine", "reader"):
            out = call(self.bundle, name, "last")
            self.assertEqual((out.get("artifact"), out.get("category")), ("error_contract", "execution_failure"), (name, out))
            self.assertIn("a count is never below zero", out["message"])
            self.assertEqual(out["evidence"]["output"]["length"], -1)


class TheTools(unittest.TestCase):
    def test_the_tools_section_says_which_file_opens_each_gate(self):
        c = {name: dict({"name": name, "description": name, "errors": [], "side_effects": effects, "idempotent": True,
                         "safety_gate": dict({"required": effects != "none", "place": "src/gate.py"},
                                             **({"opens_by": opens_by} if opens_by else {}))}, **COUNT_IO)
             for name, (effects, opens_by, installs, _) in TOOLS.items()}
        c["valve"] = dict(c["engine"], name="valve", safety_gate={"required": True, "place": "src/gate.py"})
        text = {name: bundle_mod.tools_section([tc]) for name, tc in c.items()}
        self.assertIn("opened by the lab's execution permission in `envelope/execution_permission.json`, as the one install",
                      text["install"])
        self.assertIn("required, at src/gate.py; opened by the lab's execution permission", text["engine"])
        self.assertIn("opened by the safety values in `envelope/safety.json`", text["valve"])
        self.assertIn("not required", text["reader"])
        self.assertIn("(integer, count)", text["engine"])


class TheVersion(unittest.TestCase):
    def test_v10_changes_the_text_and_the_runner_of_tools(self):
        v9, v10 = template_mod.SOURCES["v9"], template_mod.SOURCES["v10"]
        self.assertEqual(cards.tree_files(v9), cards.tree_files(v10))
        changed = sorted(r for r in cards.tree_files(v9) if cards.sha256_file(os.path.join(v9, r)) != cards.sha256_file(os.path.join(v10, r)))
        self.assertEqual(changed, ["CLAUDE.md", "README.md", "TEMPLATE.json", "src/run_tool.py", "tasks/001-start.md"])
        self.assertEqual(template_mod.LATEST, "v10")
        self.assertEqual(cards.sha256_file(os.path.join(v9, "src", "gate.py")), cards.sha256_file(os.path.join(v10, "src", "gate.py")))
        text = cards.read_text(os.path.join(v10, "CLAUDE.md"))
        self.assertEqual([ch for ch in text if ch.isdigit()], [])          # B6
        for words in ("An empty file therefore means that no tool here opens by safety values",
                      "the folder named cache inside the folder named runs",
                      "a folder there that you did not make was made by such a call",
                      "a reported value's grade is the builder's to derive"):
            self.assertIn(words, text)
        self.assertNotIn("A file with no entry means that no tool here requires a gate", text)
        self.assertIn("where it has any", cards.read_text(os.path.join(v10, "README.md")))
        task = cards.read_text(os.path.join(v10, "tasks", "001-start.md"))
        self.assertIn("`gate: self-check ok`", task)
        self.assertIn("gate: self-check ok", cards.read_text(os.path.join(v10, "src", "gate.py")))   # what the task quotes is printed
        self.assertNotIn("an OK line", task)


if __name__ == "__main__":
    unittest.main()
