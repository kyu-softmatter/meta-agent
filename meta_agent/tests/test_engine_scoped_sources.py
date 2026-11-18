"""A package source the person allowed for named engines alone (the person, 2026-11-18, docs/ideas/20261118.md,
'Yes, covered'; the schema's engines, 3a0c4ec): the Designer copies the engines of each pair from the lab's profile into
the bundle's execution permission, and the builder writes the engine's registry id into CAPABILITIES.json beside
tool_kind, so that bundle check B9 opens such a source's install only in a bundle of one of those engines.
Two unrelated kinds, neither rheology: the lattice engine and the temperature reader of the v13 test, built as the
bundles of the engines hoomd_blue and cantera; each passes B9 with its own engine and fails it with the other's.
Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import copy
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
from meta_agent.tests import test_template_v13 as v13
from meta_agent.tests import test_template_v20 as v20

V23 = template_mod.SOURCES["v23"]
META = os.path.join(v20.REPO, "meta_agent")
LAB = "lab-kyu-softmatter"
SOURCE = {"installer": "pip", "channel": "pypi"}
ENGINES = {"engine": "hoomd_blue", "spectrometer": "cantera"}


def profile_root(tmp, engines):
    """A root holding the lab's newest profile with one more pair, pip from pypi, allowed for the named engines alone."""
    folder = os.path.join(tmp, "profiles", LAB)
    os.makedirs(folder)
    latest = designer.latest_file(os.path.join(META, "profiles", LAB), "lab_profile.json")[1]
    p = cards.load_json(latest)
    p["policy"]["execution_permission"]["value"]["package_sources"].append(dict(SOURCE, engines=list(engines)))
    cards.write_json(os.path.join(folder, os.path.basename(latest)), p)
    return tmp


def install_contract(k):
    c = v13.contract(k)
    c.update(side_effects="network", installs_from=dict(SOURCE),
             safety_gate={"required": True, "place": "src/gate.py, consulted by src/run_tool.py before the call",
                          "opens_by": "execution_permission"})
    return c


def b9_fails(bundle):
    out = subprocess.run([sys.executable, os.path.join(v20.REPO, "contracts", "validate.py"), "--bundle", bundle],
                         capture_output=True, text=True, cwd=v20.REPO).stdout
    return [l for l in out.splitlines() if l.startswith("FAIL") and "B9" in l]


class EngineScopedSources(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-engine-scope-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_designer_keeps_a_pair_s_engines_and_adds_none_to_a_pair_without(self):
        p = designer.execution_permission(profile_root(os.path.join(self.tmp, "r"), ["hoomd_blue"]), LAB)
        pairs = {(s["installer"], s["channel"]): s for s in p["package_sources"]}
        self.assertEqual(pairs[("pip", "pypi")]["engines"], ["hoomd_blue"])
        self.assertNotIn("engines", pairs[("pixi", "conda-forge")])

    def test_the_engine_id_is_the_intake_s_registry_id_for_an_engine_alone(self):
        self.assertEqual(designer.engine_id({"tool": {"kind": "engine", "registry_id": "cantera"}}), "cantera")
        self.assertIsNone(designer.engine_id({"tool": {"kind": "instrument", "registry_id": "x"}}))
        self.assertIsNone(designer.engine_id({}))

    def test_an_engine_s_bundle_opens_the_source_for_its_own_engine_and_not_for_another(self):
        for kind, k in v13.KINDS.items():
            engine, other = ENGINES[kind], [e for e in ENGINES.values() if e != ENGINES[kind]][0]
            perm = designer.execution_permission(profile_root(os.path.join(self.tmp, "r-" + kind), [engine]), LAB)
            c = install_contract(k)
            fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
                    "tools_section": bundle_mod.tools_section([c]), "must_not": bundle_mod.must_not_section([]),
                    "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
            params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in k["rows"].items()]}
            b = os.path.join(self.tmp, kind)
            bundle_mod.compose(V23, b, fill, [{"name": k["tool"], "contract": c, "adapter_source": k["adapter"], "errors": []}],
                               {"capabilities": []}, {"safety": {}, "parameters": params, "execution_permission": perm},
                               [{"id": "if-a", "call": {"tool": k["tool"], "input": {}}, "expected_verdict": "pass"}],
                               [v13.task(kind)], [], skills=catalogue_mod.take([k["analysis"]["skill"]]),
                               simulation=True, tool_kind="engine", engine=engine)
            cap = cards.load_json(os.path.join(b, "CAPABILITIES.json"))
            self.assertEqual((cap["tool_kind"], cap["engine"]), ("engine", engine), kind)
            self.assertEqual(b9_fails(b), [], kind)
            cards.write_json(os.path.join(b, "CAPABILITIES.json"), dict(cap, engine=other))
            self.assertTrue(b9_fails(b), kind)


if __name__ == "__main__":
    unittest.main()
