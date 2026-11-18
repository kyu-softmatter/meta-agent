"""Template v15 (tasks/023, failure line dft-7): a built agent reads data from hosts the lab's permission lists.

Round two of the Quantum ESPRESSO test built an agent that held its fetch tools, since the gate of v14 opened a network
tool only as an install. From v15 a tool that reaches the network opens, by the execution permission at an engine or
further, as an install (installs_from, judged against package_sources), as a read of data (fetches_from, every host
judged against data_sources with the same access), or as both; neither list opens the other, and a tool naming neither
is refused. The runner looks for an installer only for a tool that names installs_from.

Each test calls the runner of a copy of the template in a fresh process, with nothing of the Meta-Agent beside it, on two
unrelated kinds of read: an electronic-structure engine's pseudopotentials and example inputs, from the two hosts the
person allowed for this lab (docs/ideas/20261117.md), and a weather station's archive, from a host a fixture permission
lists. The Designer's copy of data_sources is tested in test_designer.py (DataSources).

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
from meta_agent.tests.test_template_v8 import IO, permission, self_check

READ = "def run(payload):\n    return {'message': payload['message'], 'length': len(payload['message'])}\n"
PIXI = {"installer": "pixi", "channel": "conda-forge"}
ANON = "read_only_anonymous"


def host(name, access=ANON):
    return {"host": name, "access": access}


# each kind: the hosts its read names, and the permission's data_sources that list them
KINDS = {
    "electronic_structure": {"reads": [host("pseudopotentials.quantum-espresso.org"), host("gitlab.com")]},
    "weather_station": {"reads": [host("archive.weather-station.example.org")]},
}


def tools_of(kind):
    """name: (opens_by, installs_from, fetches_from)"""
    reads = KINDS[kind]["reads"]
    return {
        "fetch": ("execution_permission", None, reads),
        "fetch_unlisted": ("execution_permission", None, reads + [host("mirror.example.net")]),
        "fetch_other_access": ("execution_permission", None, [dict(reads[0], access="read_write")]),
        "fetch_by_safety": (None, None, reads),
        "install": ("execution_permission", PIXI, None),
        "install_and_fetch": ("execution_permission", PIXI, reads),
        "neither": ("execution_permission", None, None),
    }


def make_bundle(kind, perm):
    tmp = tempfile.mkdtemp(prefix="ma-template-v15-")
    bundle = os.path.join(tmp, "bundle")
    shutil.copytree(template_mod.SOURCES["v15"], bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, (opens_by, installs, fetches) in tools_of(kind).items():
        gate = {"required": True, "place": "src/gate.py, consulted by src/run_tool.py before the call"}
        if opens_by:
            gate["opens_by"] = opens_by
        c = dict({"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": name,
                  "errors": ["invalid_input", "refused_by_safety", "unavailable"], "side_effects": "network",
                  "safety_gate": gate, "idempotent": True, "timeout_s": None}, **IO)
        if installs:
            c["installs_from"] = installs
        if fetches:
            c["fetches_from"] = fetches
        cards.write_json(os.path.join(bundle, "tools", name, "tool.json"), c)
        cards.write_text(os.path.join(bundle, "tools", name, "adapter.py"), READ)
    cards.write_json(os.path.join(bundle, "envelope", "safety.json"),
                     {"largest_download": {"value": 1, "set_by": "human", "date": "2026-11-17"}})
    if perm is not None:
        cards.write_json(os.path.join(bundle, "envelope", "execution_permission.json"), perm)
    return tmp, bundle


def call(bundle, tool, path_dir):
    """The runner in a fresh process whose PATH is path_dir alone: an installer is there only where a test put one."""
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "run_tool.py"), tool],
                       input=json.dumps({"message": "four"}), capture_output=True, text=True, cwd=bundle,
                       env={"PATH": path_dir, "PYTHONUTF8": "1"})
    assert p.returncode == 0, p.stdout + p.stderr
    return json.loads(p.stdout)


def listing(level, package_sources=(), data_sources=()):
    p = permission(level)
    if package_sources:
        p["package_sources"] = [dict(s) for s in package_sources]
    if data_sources:
        p["data_sources"] = [dict(h) for h in data_sources]
    return p


OK = {"message": "four", "length": 4}


class AReadOfDataFromListedHosts(unittest.TestCase):
    def setUp(self):
        self.path = tempfile.mkdtemp(prefix="ma-path-")
        self.addCleanup(shutil.rmtree, self.path, True)

    def put_installer(self, name):
        exe = os.path.join(self.path, name)
        cards.write_text(exe, "#!/bin/sh\nexit 0\n")
        os.chmod(exe, 0o755)

    def run_with(self, kind, perm):
        tmp, bundle = make_bundle(kind, perm)
        self.addCleanup(shutil.rmtree, tmp, True)
        return bundle, {name: call(bundle, name, self.path) for name in tools_of(kind)}

    def assertRefused(self, out, code, *words):
        self.assertEqual(out.get("artifact"), "error_contract", out)
        self.assertEqual((out["category"], out["code"]), ("refused_by_safety", code), out)
        for w in words:
            self.assertIn(w, out["message"])

    def test_a_read_from_every_listed_host_runs_with_no_installer_on_the_computer(self):
        for kind in KINDS:
            for level in ("engine", "instrument"):
                bundle, got = self.run_with(kind, listing(level, data_sources=KINDS[kind]["reads"]))
                self.assertEqual(got["fetch"], OK, (kind, level))
                self.assertRefused(got["fetch_unlisted"], "GATE-NETWORK-001", "mirror.example.net (read_only_anonymous)",
                                   "does not list under data_sources")
                self.assertRefused(got["fetch_other_access"], "GATE-NETWORK-001", "(read_write)")
                self.assertRefused(got["fetch_by_safety"], "GATE-NETWORK-001", "does not open by the execution permission")
                self.assertRefused(got["neither"], "GATE-NETWORK-001", "names neither installs_from nor fetches_from")
                self.assertEqual(self_check(bundle)[0], 0)

    def test_data_sources_open_no_install_and_package_sources_open_no_read(self):
        for kind in KINDS:
            self.put_installer("pixi")
            _, got = self.run_with(kind, listing("engine", data_sources=KINDS[kind]["reads"]))
            self.assertRefused(got["install"], "GATE-NETWORK-001", "pixi/conda-forge", "does not list under package_sources")
            self.assertRefused(got["install_and_fetch"], "GATE-NETWORK-001", "does not list under package_sources")
            _, got = self.run_with(kind, listing("engine", package_sources=[PIXI]))
            self.assertEqual(got["install"], OK, kind)
            self.assertRefused(got["fetch"], "GATE-NETWORK-001", "does not list under data_sources")
            self.assertRefused(got["install_and_fetch"], "GATE-NETWORK-001", "does not list under data_sources")
            _, got = self.run_with(kind, listing("engine", package_sources=[PIXI], data_sources=KINDS[kind]["reads"]))
            self.assertEqual((got["install"], got["fetch"], got["install_and_fetch"]), (OK, OK, OK), kind)

    def test_the_installer_is_looked_for_only_for_an_install(self):
        perm = listing("engine", package_sources=[PIXI], data_sources=KINDS["weather_station"]["reads"])
        _, got = self.run_with("weather_station", perm)                  # nothing on PATH
        self.assertEqual(got["fetch"], OK)
        for name in ("install", "install_and_fetch"):
            self.assertEqual((got[name]["category"], got[name]["code"]), ("unavailable", "%s-INSTALLER-MISSING" % name.upper()))

    def test_a_level_below_an_engine_or_no_permission_opens_no_read(self):
        for kind in KINDS:
            _, got = self.run_with(kind, listing("sandbox", data_sources=KINDS[kind]["reads"]))
            self.assertRefused(got["fetch"], "GATE-PERMISSION-001", "reaches sandbox")
            _, got = self.run_with(kind, None)
            self.assertRefused(got["fetch"], "GATE-NETWORK-001", "does not list under data_sources")


class TheVersion(unittest.TestCase):
    def test_v15_changes_the_gate_the_runner_and_their_sentences(self):
        v14, v15 = template_mod.SOURCES["v14"], template_mod.SOURCES["v15"]
        self.assertEqual(cards.tree_files(v14), cards.tree_files(v15))
        changed = sorted(r for r in cards.tree_files(v14)
                         if cards.sha256_file(os.path.join(v14, r)) != cards.sha256_file(os.path.join(v15, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/gate.py", "src/run_tool.py"])
        self.assertEqual(template_mod.LATEST, "v15")
        self.assertEqual(cards.load_json(os.path.join(v15, "TEMPLATE.json"))["version"], "v15")
        text = cards.read_text(os.path.join(v15, "CLAUDE.md"))
        self.assertIn("A read of data: its contract names `fetches_from`", text)
        self.assertNotIn("The one network call this agent may make", text)
        self.assertEqual([c for c in text if c.isdigit()], [])


if __name__ == "__main__":
    unittest.main()
