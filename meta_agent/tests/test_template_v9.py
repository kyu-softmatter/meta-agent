"""Template v9 (tasks/016, test run 20261116-5): the one network call a bundle may make is an install of its own
packages from a source the lab's permission lists.

A tool that reaches the network runs only where its contract names installs_from {installer, channel}, its gate opens
by the execution permission, and envelope/execution_permission.json reaches an engine and lists that pair under
package_sources. Every other network tool is refused, whatever its contract asks of the gate. Each test calls the
runner of a copy of the template in a fresh process, with nothing of the Meta-Agent beside it, on two unrelated
kinds of tool: an install (its stand-in adapter fetches nothing) and an engine (its stand-in starts a process).

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import template as template_mod
from meta_agent.tests.test_template_v8 import ENGINE, IO, call, permission, self_check

INSTALLED = "def run(payload):\n    return {'message': payload['message'], 'length': len(payload['message'])}\n"
PIXI = {"installer": "pixi", "channel": "conda-forge"}

# name: (side effects, opens_by, installs_from, gate required, adapter)
TOOLS = {
    "install": ("network", "execution_permission", PIXI, True, INSTALLED),
    "install_unasked": ("network", "execution_permission", PIXI, False, INSTALLED),   # asks for no gate; is asked anyway
    "install_pypi": ("network", "execution_permission", {"installer": "pip", "channel": "pypi"}, True, INSTALLED),
    "fetch": ("network", "execution_permission", None, True, INSTALLED),             # the network, and no install
    "download": ("network", None, PIXI, True, INSTALLED),                            # gated by safety values
    "engine": ("runs_process", "execution_permission", None, True, ENGINE),
}


def make_bundle(perm, safety_set=False):
    tmp = tempfile.mkdtemp(prefix="ma-template-v9-")
    bundle = os.path.join(tmp, "bundle")
    shutil.copytree(template_mod.SOURCES["v9"], bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, (effects, opens_by, installs, required, adapter) in TOOLS.items():
        gate = {"required": required, "place": "src/gate.py, consulted by src/run_tool.py before the call"}
        if opens_by:
            gate["opens_by"] = opens_by
        c = dict({"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": name,
                  "errors": ["invalid_input", "refused_by_safety"], "side_effects": effects, "safety_gate": gate,
                  "idempotent": True, "timeout_s": None}, **IO)
        if installs:
            c["installs_from"] = installs
        cards.write_json(os.path.join(bundle, "tools", name, "tool.json"), c)
        cards.write_text(os.path.join(bundle, "tools", name, "adapter.py"), adapter)
    row = {"value": 1, "set_by": "human", "date": "2026-11-16"} if safety_set else None
    cards.write_json(os.path.join(bundle, "envelope", "safety.json"), {"largest_download": row})
    if perm is not None:
        cards.write_json(os.path.join(bundle, "envelope", "execution_permission.json"), perm)
    return tmp, bundle


def with_sources(level, *pairs):
    p = permission(level)
    p["package_sources"] = [dict(s) for s in pairs]
    return p


class TheOneNetworkCall(unittest.TestCase):
    def run_with(self, perm, safety_set=False):
        tmp, bundle = make_bundle(perm, safety_set)
        self.addCleanup(shutil.rmtree, tmp, True)
        return bundle, {name: call(bundle, name) for name in TOOLS}

    def assertRefused(self, out, code, *words):
        self.assertEqual(out.get("artifact"), "error_contract", out)
        self.assertEqual((out["category"], out["code"]), ("refused_by_safety", code), out)
        for w in words:
            self.assertIn(w, out["message"])

    def test_an_install_from_a_listed_source_runs_beside_the_engine(self):
        for level in ("engine", "instrument"):
            bundle, got = self.run_with(with_sources(level, PIXI))
            for name in ("install", "install_unasked", "engine"):
                self.assertEqual(got[name], {"message": "four", "length": 4}, (level, name))
            self.assertRefused(got["install_pypi"], "GATE-NETWORK-001", "pip/pypi", "does not list")
            self.assertRefused(got["fetch"], "GATE-NETWORK-001", "names no installs_from")
            self.assertEqual(self_check(bundle)[0], 0)

    def test_a_second_listed_pair_opens_its_own_install_only(self):
        _, got = self.run_with(with_sources("engine", PIXI, {"installer": "pip", "channel": "pypi"}))
        self.assertEqual(got["install_pypi"], {"message": "four", "length": 4})
        self.assertRefused(got["fetch"], "GATE-NETWORK-001")

    def test_a_network_tool_gated_by_safety_values_is_refused_even_with_them_set(self):
        _, got = self.run_with(with_sources("engine", PIXI), safety_set=True)
        self.assertRefused(got["download"], "GATE-NETWORK-001", "does not open by the execution permission")

    def test_no_source_listed_or_a_level_below_an_engine_opens_no_install(self):
        _, got = self.run_with(permission("engine"))                         # a v8 permission: no package_sources
        self.assertRefused(got["install"], "GATE-NETWORK-001", "does not list")
        self.assertEqual(got["engine"], {"message": "four", "length": 4})   # the engine is opened as in v8
        _, got = self.run_with(with_sources("sandbox", PIXI))
        self.assertRefused(got["install"], "GATE-PERMISSION-001", "reaches sandbox")
        self.assertRefused(got["install_unasked"], "GATE-PERMISSION-001", "reaches sandbox")
        _, got = self.run_with(None)
        self.assertRefused(got["install"], "GATE-NETWORK-001")
        self.assertRefused(got["engine"], "GATE-PERMISSION-001", "no envelope/execution_permission.json")


class TheVersion(unittest.TestCase):
    def test_v9_changes_the_gate_its_sentences_and_the_settings(self):
        v8, v9 = template_mod.SOURCES["v8"], template_mod.SOURCES["v9"]
        self.assertEqual(cards.tree_files(v8), cards.tree_files(v9))
        changed = sorted(r for r in cards.tree_files(v8) if cards.sha256_file(os.path.join(v8, r)) != cards.sha256_file(os.path.join(v9, r)))
        self.assertEqual(changed, [".claude/settings.json", "CLAUDE.md", "TEMPLATE.json", "src/gate.py"])
        self.assertEqual(template_mod.LATEST, "v9")
        text = cards.read_text(os.path.join(v9, "CLAUDE.md"))
        self.assertIn("The one network call this agent may make is an install", text)
        self.assertEqual([c for c in text if c.isdigit()], [])
        deny = cards.load_json(os.path.join(v9, ".claude", "settings.json"))["permissions"]["deny"]
        self.assertIn("Write(envelope/execution_permission.json)", deny)


if __name__ == "__main__":
    unittest.main()
