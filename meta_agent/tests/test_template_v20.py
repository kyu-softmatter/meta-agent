"""Template v20 and the builder (tasks/025; the person, 2026-11-18, docs/ideas/20261118.md): every simulation bundle
carries the common set of library skills its template names, and a build adapts one to its engine as a next version
(adapted_from, its engine named) that takes the common one's place and that the difference from the template lists.
The agreement skill is the common measurement_error@v2, read from TEMPLATE.json, and is not adapted.

Two unrelated kinds, the engine and the spectrometer tools of the v13 test, each built as an engine's bundle; the same
tool built as an instrument's carries no common set. Every bundle call runs in a fresh process.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.src.skills import rules
from meta_agent.tests import test_template_v13 as v13

V20 = template_mod.SOURCES["v20"]
COMMON = cards.load_json(os.path.join(V20, "TEMPLATE.json"))["common_skills"]
AGREEMENT = "measurement_error@v2"


def compose(tmp, name, sci, simulation=True, adaptations=None, refs=None):
    kind = name.split("-")[0]
    k = v13.KINDS[kind]
    c = v13.contract(k)
    tools = [{"name": k["tool"], "contract": c, "adapter_source": k["adapter"], "errors": []}]
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([c]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    params = {"rows": [{"name": n, "value": v, "unit": u} for n, (v, u) in k["rows"].items()]}
    iface = [{"id": "if-a", "call": {"tool": k["tool"], "input": {}}, "expected_verdict": "pass"}]
    path = os.path.join(tmp, name)
    bundle_mod.compose(V20, path, fill, tools, {"capabilities": []}, {"safety": {}, "parameters": params}, iface, sci, [],
                       skills=catalogue_mod.take(refs if refs is not None else [k["analysis"]["skill"]]),
                       simulation=simulation, adaptations=adaptations)
    return path


def carried(bundle):
    return sorted(os.listdir(os.path.join(bundle, "skills")))


def adapted(tmp, base, version, engine="fenicsx", **change):
    """A next version of a common skill, as a build makes it for its engine, in a folder of its own."""
    src = catalogue_mod.find(base)
    m = cards.load_json(os.path.join(src, "skill.json"))
    ref = "%s@v%d" % (m["id"], version)
    folder = os.path.join(tmp, "adapted-%s-%s" % (engine, base), ref)
    shutil.copytree(src, folder, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    m.update(version=version, adapted_from=base, applies_to={"parameters": [], "engines": [engine] if engine else []})
    m.pop("common", None)
    m.update(change)
    cards.write_json(os.path.join(folder, "skill.json"), m)
    return folder


class TheCommonSet(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v20-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_every_common_skill_is_common_and_passes_check_22(self):
        kinds = rules.load_kinds()
        for ref in COMMON:
            d = catalogue_mod.find(ref)
            self.assertTrue(cards.load_json(os.path.join(d, "skill.json")).get("common"), ref)
            self.assertEqual(rules.problems(d, kinds), [], ref)

    def test_a_simulation_bundle_of_each_kind_carries_the_set_and_an_instrument_s_does_not(self):
        for kind, k in v13.KINDS.items():
            b = compose(self.tmp, kind, [v13.task(kind)])
            named = k["analysis"]["skill"]
            want = {named} | {c for c in COMMON if bundle_mod.skill_id(c) != bundle_mod.skill_id(named)}
            self.assertEqual(carried(b), sorted(want), kind)              # a version the specification names stays
            for ref in want - {named}:
                self.assertIn(ref, cards.read_text(os.path.join(b, "CLAUDE.md")), (kind, ref))
            i = compose(self.tmp, kind + "-instrument", [v13.task(kind)], simulation=False)
            self.assertEqual(carried(i), sorted({k["analysis"]["skill"], AGREEMENT}), kind)

    def test_a_version_the_specification_names_is_kept_and_not_doubled(self):
        b = compose(self.tmp, "engine-named", [v13.task("engine")], refs=["box_length_for_volume_fraction@v1", "series_maximum@v1"])
        have = carried(b)
        self.assertIn("series_maximum@v1", have)
        self.assertNotIn("series_maximum@v2", have)

    def test_the_agreement_comes_from_the_common_measurement_error(self):
        for kind in v13.KINDS:
            r = v13.validate(compose(self.tmp, kind + "-agree", [v13.task(kind)]))
            self.assertEqual(r["verdict"], "pass", (kind, r))
            self.assertEqual({run["skill"] for run in r["agreement_runs"].values()}, {AGREEMENT}, kind)


class AnAdaptation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v20-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_it_takes_the_common_one_s_place_and_the_difference_lists_it(self):
        for kind, engine in (("engine", "fenicsx"), ("spectrometer", "meep")):
            folder = adapted(self.tmp, "series_maximum@v2", 3, engine=engine)
            b = compose(self.tmp, kind + "-adapted", [v13.task(kind)], adaptations=[folder])
            have = carried(b)
            self.assertIn("series_maximum@v3", have, kind)
            self.assertNotIn("series_maximum@v2", have, kind)
            self.assertEqual(rules.problems(os.path.join(b, "skills", "series_maximum@v3"), rules.load_kinds()), [], kind)
            diff = bundle_mod.diff_from_template(V20, b)
            self.assertIn("adapted   skills/series_maximum@v3  from series_maximum@v2, for %s" % engine, diff, kind)

    def test_what_is_not_an_adaptation_is_refused_before_anything_is_written(self):
        wrong = {
            "names no engine": adapted(self.tmp, "series_maximum@v2", 3, engine=None),
            "not a later version": adapted(self.tmp, "series_settled@v3", 3),
            "from outside the set": adapted(self.tmp, "series_maximum@v2", 3, engine="lammps", adapted_from="series_maximum@v1"),
            "itself common": adapted(self.tmp, "series_within_window@v3", 4, engine="gromacs", common=True),
            "the agreement skill": adapted(self.tmp, AGREEMENT, 3),
        }
        for why, folder in wrong.items():
            with self.assertRaises(ValueError, msg=why):
                compose(self.tmp, "engine-wrong", [v13.task("engine")], adaptations=[folder])
            self.assertFalse(os.path.exists(os.path.join(self.tmp, "engine-wrong")), why)
        with self.assertRaises(ValueError):
            compose(self.tmp, "engine-instrument", [v13.task("engine")], simulation=False,
                    adaptations=[adapted(self.tmp, "series_maximum@v2", 3, engine="cantera")])


class TheVersion(unittest.TestCase):
    def test_v20_changes_one_script(self):
        v19 = template_mod.SOURCES["v19"]
        self.assertIn("v20", template_mod.SOURCES)                  # v21 is the latest since the run-error skill
        self.assertEqual(cards.tree_files(v19), cards.tree_files(V20))
        changed = sorted(r for r in cards.tree_files(v19) if cards.sha256_file(os.path.join(v19, r)) != cards.sha256_file(os.path.join(V20, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "src/validate_tasks.py"])
        meta = cards.load_json(os.path.join(V20, "TEMPLATE.json"))
        self.assertEqual((meta["version"], meta["agreement_skill"]), ("v20", AGREEMENT))
        self.assertIn(AGREEMENT, meta["common_skills"])
        self.assertEqual(meta["tolerance_rule"]["skill"], "tolerance_from_reference@v2")


if __name__ == "__main__":
    unittest.main()
