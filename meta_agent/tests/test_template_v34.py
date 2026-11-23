"""Template v34 and the builder (tasks/032, at the design role's ask 20261120-design-macbook-20261120-2-5; the person,
2026-11-20, 'Held item, shown pending (Recommended)' and 'Compare in its printed unit (Recommended)'; dftmd-16).

- A held scientific item is reported not_run with its reason and what it needs, makes no call, and bundle check B5
  prints it pending; the builder refuses one without its reason or needs, expected otherwise, naming a reference
  function, or under a template before v34.
- A reference printed in another unit than the measured quantity is compared in its printed unit: the bundle's checker
  converts the measured value through unit_convert@v1 and the registry the bundle carries, the rule's tolerance and the
  agreement are in the printed unit, and the builder's validation report records measured.converted_from, which
  check 12 recomputes.
- A hand-over's definition names the tool field each of the skill's inputs came from (record_tool).

Two unrelated kinds: a DFT rest length fitted in bohr against a bond length printed in angstrom, and a viscosity measured
in Pa.s against one printed in mPa.s. Each tool is a mock adapter that returns its output and starts no engine.

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
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.src.validate import gate as gate_mod

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V33, V34 = template_mod.SOURCES["v33"], template_mod.SOURCES["v34"]
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
BOHR, ANGSTROM = 5.29177210544e-11, 1e-10

# each kind: the tool, the output it returns, the field's unit and description, the analysis (or none), the stated
# field, the reference as printed and its unit, the measured unit, the person's tolerance (or none: the rule's)
KINDS = {
    "dft": {"tool": "scan_mock", "output": {"energy_curve": [[1.3, -2.298], [1.4, -2.3], [1.5, -2.298]]},
            "field": "energy_curve", "unit": "Ry", "description": "pairs of a bond length in bohr and the total energy in Ry",
            "analysis": {"skill": "harmonic_well_fit@v1", "data": {"field": "energy_curve", "input": "points"}, "rows": {},
                         "output": "rest_position"},
            "stated": "rest_position", "printed": "0.74144", "ref_unit": "Angstrom", "measured_unit": "bohr",
            "measured": 1.4, "tolerance": None},
    "viscosity": {"tool": "measure_mock", "output": {"viscosity": 0.00098}, "field": "viscosity", "unit": "Pa.s",
                  "description": "the dynamic viscosity the plateau gives", "analysis": None,
                  "stated": "viscosity", "printed": "0.98", "ref_unit": "mPa.s", "measured_unit": "Pa.s",
                  "measured": 0.00098, "tolerance": {"value": 0.05, "unit": "mPa.s", "chosen_by": "human"}},
}
FACTOR = {"dft": BOHR / ANGSTROM, "viscosity": 1.0 / 0.001}


def contract(k):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["tool"], "description": "a mock that returns its output",
            "inputs": {"type": "object", "properties": {}, "required": []},
            "outputs": {"type": "object", "properties": {k["field"]: {"type": "array" if k["analysis"] else "number",
                                                                      "unit": k["unit"], "description": k["description"]}},
                        "required": [k["field"]]},
            "errors": ["invalid_input"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "a mock touches nothing"}, "idempotent": True, "timeout_s": None}


def adapter(k):
    return "def run(payload):\n    return %r\n" % (k["output"],)


def task(k, **change):
    t = {"id": "sci-1", "name": "the %s against a value printed in %s" % (k["stated"], k["ref_unit"]),
         "call": {"tool": k["tool"], "input": {}},
         "measure": {"stated": {k["stated"]: float(k["printed"])}, "printed": {k["stated"]: k["printed"]},
                     "unit": k["measured_unit"]},
         "reference": {"kind": "source", "ref": "a test's reference, printed in %s" % k["ref_unit"], "unit": k["ref_unit"]},
         "expected_verdict": "fail"}
    if k["analysis"]:
        t["analysis"] = dict(k["analysis"])
    if k["tolerance"]:
        t["tolerance"] = dict(k["tolerance"])
        t["expected_verdict"] = "pass"
    t.update(change)
    return t


def held(k, **change):
    t = {"id": "sci-2", "name": "a comparison that cannot be judged yet", "call": {"tool": k["tool"], "input": {}},
         "measure": {}, "reference": {"kind": "source", "ref": "a measured value with no tolerance yet"},
         "held": {"reason": "no tolerance can be given yet", "needs": "published values for the span"},
         "tolerance": None, "expected_verdict": "not_run"}
    t.update(change)
    return t


def compose(tmp, name, k, tasks, rows=None, template=V34):
    path = os.path.join(tmp, name, "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    fill = {"agent_name": name, "template": "agent@test", "rid": "req-%s" % name, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([contract(k)]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    skills = [k["analysis"]["skill"]] if k["analysis"] else []
    answers = {"id": "if-1", "name": "the mock answers", "call": {"tool": k["tool"], "input": {}},
               "expected": {"output": dict(k["output"])}, "expected_verdict": "pass"}
    bundle_mod.compose(template, path, fill, [{"name": k["tool"], "contract": contract(k), "adapter_source": adapter(k), "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": rows or []}}, [answers], tasks,
                       [dict(answers, id="rp-001")], skills=catalogue_mod.take(skills) if skills else [], simulation=False)
    return path


class AReferenceIsComparedInItsPrintedUnit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v34-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_measured_value_is_converted_and_the_report_passes_check_12(self):
        for kind, k in KINDS.items():
            path = compose(self.tmp, kind, k, [task(k)])
            item = cards.load_json(os.path.join(path, "validation", "scientific", "sci-1.json"))
            self.assertEqual(item["tolerance"]["unit"], k["ref_unit"], kind)          # the rule's, or the person's, in it
            self.assertTrue(os.path.isfile(os.path.join(path, "envelope", "units.json")), kind)
            self.assertTrue(os.path.isdir(os.path.join(path, "skills", "unit_convert@v1")), kind)
            report = gate_mod.run_bundle(path)
            t = report["validate"]["scientific"]["tasks"][0]
            conv = t["measured_converted"]
            self.assertEqual((conv["unit"], conv["converted_from"]["unit"], conv["converted_by"]),
                             (k["ref_unit"], k["measured_unit"], "computed:unit_convert@v1"), kind)
            self.assertAlmostEqual(conv["converted_from"]["value"], k["measured"], places=9, msg=kind)
            self.assertAlmostEqual(conv["value"], k["measured"] * FACTOR[kind], places=9, msg=kind)
            self.assertAlmostEqual(t["measured"][k["stated"]], conv["value"], places=12, msg=kind)
            self.assertEqual(t["verdict"], "pass" if k["tolerance"] else "fail", (kind, t.get("reason")))
            vr, _, _ = gate_mod.make_validation_report(report, "build-%s-0001" % kind, "req-%s" % kind,
                                                        "builds/%s/0001/bundle" % kind, "meta-macbook-20261120-3",
                                                        bundle_path=path)
            row = vr["scientific"]["tasks"][0]
            self.assertEqual(row["measured"]["unit"], k["ref_unit"], kind)
            self.assertEqual(row["agreement"]["unit"], k["ref_unit"], kind)
            judged = os.path.join(self.tmp, "judged-" + kind)
            os.makedirs(judged)
            cards.write_json(os.path.join(judged, "validation_report.json"), vr)
            p = subprocess.run([sys.executable, VALIDATE, judged, "--checks", "1,2,12"], capture_output=True, text=True)
            self.assertIn("VERDICT PASS", p.stdout.strip().splitlines()[-1], (kind, p.stdout[-2500:]))

    def test_a_task_that_names_no_measured_unit_is_refused(self):
        for kind, k in KINDS.items():
            t = task(k)
            t["measure"].pop("unit")
            with self.assertRaises(ValueError) as cm:
                compose(os.path.join(self.tmp, "a"), kind, k, [t])
            self.assertIn("measure.unit does not name", str(cm.exception), kind)

    def test_units_of_two_dimensions_are_refused(self):
        k = KINDS["viscosity"]
        t = task(k)
        t["measure"]["unit"] = "K"
        with self.assertRaises(ValueError) as cm:
            compose(self.tmp, "v", k, [t])
        self.assertIn("not of one dimension", str(cm.exception))

    def test_v33_refuses_a_printed_unit(self):
        for kind, k in KINDS.items():
            with self.assertRaises(ValueError) as cm:
                compose(os.path.join(self.tmp, "old"), kind, k, [task(k)], template=V33)
            self.assertIn("needs template v34", str(cm.exception), kind)


class AHeldComparisonIsShownPending(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v34-held-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_it_is_not_run_with_its_reason_and_b5_shows_it_pending(self):
        for kind, k in KINDS.items():
            path = compose(self.tmp, kind, k, [task(k), held(k)])
            report = gate_mod.run_bundle(path)
            t = next(x for x in report["validate"]["scientific"]["tasks"] if x["id"] == "sci-2")
            self.assertEqual(t["verdict"], "not_run", kind)
            self.assertEqual(t["reason"], "held: no tolerance can be given yet; it needs published values for the span", kind)
            p = subprocess.run([sys.executable, VALIDATE, "--bundle", path, "--checks", "B5"], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, (kind, p.stdout[-2000:]))
            self.assertIn("held comparison", p.stdout, kind)

    def test_the_builder_refuses_a_held_item_as_b5_would(self):
        k = KINDS["viscosity"]
        for change, words in (({"held": {"reason": "no tolerance yet"}}, "held.needs"),
                              ({"expected_verdict": "fail"}, "expected not_run"),
                              ({"measure": {"reference_function": "len_message"}}, "names no reference function")):
            with self.assertRaises(ValueError) as cm:
                compose(os.path.join(self.tmp, words.replace(" ", "-")), "v", k, [task(k), held(k, **change)])
            self.assertIn(words, str(cm.exception))
        with self.assertRaises(ValueError) as cm:
            compose(os.path.join(self.tmp, "old"), "v", k, [held(k)], template=V33)
        self.assertIn("needs template v34", str(cm.exception))


class TheDefinitionNamesTheToolsField(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v34-def-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def giver(self, kind, template=V34):
        k = KINDS[kind]
        skill = k["analysis"]["skill"] if k["analysis"] else "standard_error_of_independent_estimates@v2"
        inp = "points" if k["analysis"] else "estimates"
        output = "force_constant" if k["analysis"] else "mean"
        unit = "Ry/bohr^2" if k["analysis"] else "Pa.s"
        row = {"name": "handed", "value": None, "unit": unit, "handover": {"gives": {
            "thread": "thr-x", "to_agent": "other", "to_build": "other/0001", "skill": skill, "output": output,
            "record_inputs": {inp: k["field"]}, "record_inputs_from": "one_result" if k["analysis"] else "each_result",
            "record_tool": k["tool"], "what": "a value for the other agent"}}}
        path = os.path.join(self.tmp, kind, "0001", "bundle")
        os.makedirs(os.path.dirname(path))
        fill = {"agent_name": kind, "template": "agent@test", "rid": "req-x", "purpose": "p", "science_task": "t",
                "tools_section": bundle_mod.tools_section([contract(k)]), "must_not": bundle_mod.must_not_section([]),
                "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
        bundle_mod.compose(template, path, fill, [{"name": k["tool"], "contract": contract(k), "adapter_source": adapter(k), "errors": []}],
                           {"capabilities": []}, {"safety": {}, "parameters": {"rows": [row]}}, [], [], [],
                           skills=catalogue_mod.take([skill]), simulation=False)
        return k, path, skill, inp

    def test_the_card_names_the_field_each_input_came_from(self):
        for kind in KINDS:
            k, path, skill, inp = self.giver(kind)
            decl = cards.load_json(os.path.join(path, "envelope", "handovers.json"))
            self.assertEqual(decl["gives"][0]["record_fields"], {inp: {"tool": k["tool"], "field": k["field"], "description": k["description"]}})
            runs = os.path.join(path, "runs")
            os.makedirs(runs)
            results = [k["output"]] if k["analysis"] else [{"viscosity": v, "conditions": {"geometry": "cone"}} for v in (0.98, 1.0, 1.02)]
            names = []
            for i, r in enumerate(results):
                r = dict(r, conditions={"geometry": "cone"}) if k["analysis"] else r
                cards.write_json(os.path.join(runs, "r%d.json" % i), r)
                names.append("runs/r%d.json" % i)
            inputs = {inp: results[0][k["field"]] if k["analysis"] else [r[k["field"]] for r in results]}
            p = subprocess.run([sys.executable, "src/run_skill.py", skill, "--record", "runs/fit.json"], cwd=path,
                               input=json.dumps(inputs), capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            p = subprocess.run([sys.executable, "src/handover.py", "write", "--record", "runs/fit.json", "--runs"] + names,
                               cwd=path, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            card = json.loads(p.stdout)["card"]
            self.assertIn("; its input %s was the field %s of the result of %s: %s" % (inp, k["field"], k["tool"], k["description"]),
                          card["numbers"][0]["conditions"]["definition"], kind)

    def test_v33_refuses_a_record_tool(self):
        with self.assertRaises(ValueError) as cm:
            self.giver("viscosity", template=V33)
        self.assertIn("record_tool", str(cm.exception) + "record_tool")


class TheVersion(unittest.TestCase):
    def test_v34_is_the_latest_and_changes_two_scripts_its_text_and_its_card(self):
        self.assertIn("v34", template_mod.SOURCES)                  # v35 is the latest since run folders and process counts
        self.assertEqual(sorted(set(cards.tree_files(V34)) ^ set(cards.tree_files(V33))), [])
        both = set(cards.tree_files(V33)) & set(cards.tree_files(V34))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V33, r)) != cards.sha256_file(os.path.join(V34, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/handover.py", "src/validate_tasks.py"])


if __name__ == "__main__":
    unittest.main()
