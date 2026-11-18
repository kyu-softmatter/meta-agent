"""The unit of a scientific task's agreement in the validation report (failure line chem-1, tasks/020).

Test run chemical-kinetics/20261117-1 (collect-1): the report of build cantera-adiabatic/0001 gave the agreement of a
temperature measured against a page's printed value the unit '1', while the value was a difference in kelvin; with no
person's tolerance, src/validate/gate.py fell back to '1'. The agreement is a difference of the measured quantity, so its
unit is the unit the tool's contract declares for that output. Shown on two unrelated kinds: a temperature in chemical
equilibrium judged against a stated value, and a viscosity in rheology judged against a reference function. Where the
contract declares no unit, the report keeps what it did before: the tolerance's unit, otherwise '1'.
"""
import json
import os
import shutil
import tempfile
import unittest

from meta_agent.src.validate import gate as gate_mod

SEAT = "meta-macbook-20261117-4"
NOW = "2026-11-17T12:00:00Z"


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)


def report(task):
    return {"validate": {"interface": {"verdict": "pass", "tasks": []},
                         "scientific": {"verdict": task["verdict"], "tasks": [task]}, "overall": task["verdict"]},
            "replay": {"items": [], "ok": True}}


class TheAgreementHasTheMeasuredQuantitysUnit(unittest.TestCase):

    def setUp(self):
        self.bundle = tempfile.mkdtemp(prefix="agreement-unit-")

    def tearDown(self):
        shutil.rmtree(self.bundle, ignore_errors=True)

    def tool(self, name, outputs):
        write(os.path.join(self.bundle, "tools", name, "tool.json"),
              {"artifact": "tool", "name": name, "outputs": {"type": "object", "properties": outputs}})

    def task(self, file, item):
        write(os.path.join(self.bundle, "validation", "scientific", file), item)

    def built(self, task):
        vr, _, _ = gate_mod.make_validation_report(report(task), "build-x-0001", "req-x-001", "meta_agent/builds/x/0001/bundle",
                                                   SEAT, NOW, bundle_path=self.bundle)
        return vr

    def test_a_temperature_against_a_stated_value_without_a_tolerance_is_in_kelvin(self):
        # chemical equilibrium: the adiabatic flame temperature against the value a page prints
        self.tool("flame_point", {"flame_temperature": {"type": "number", "unit": "K"},
                                  "pressure": {"type": "number", "unit": "Pa"}})
        self.task("sci-1.json", {"id": "sci-1", "call": {"tool": "flame_point", "input": {}},
                                 "measure": {"stated": {"flame_temperature": 1066}}})
        vr = self.built({"id": "sci-1", "name": "flame temperature against the page", "file": "sci-1.json",
                         "verdict": "undecided", "measured": {"flame_temperature": 1066.25},
                         "reference": {"flame_temperature": 1066}, "agreement": 0.25, "tolerance": None,
                         "reference_spec": {"kind": "source", "ref": "the page"}})
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0.25, "unit": "K"})
        self.assertEqual(vr["numbers"], [])

    def test_a_viscosity_against_a_reference_function_is_in_pascal_seconds_and_so_are_its_numbers(self):
        # rheology: a Newtonian fluid's viscosity against the value the runner computes without the tool
        self.tool("steady_shear", {"viscosity": {"type": "number", "unit": "Pa.s"},
                                   "shear_rate": {"type": "number", "unit": "1/s"}})
        self.task("sci-1.json", {"id": "sci-1", "call": {"tool": "steady_shear", "input": {}},
                                 "measure": {"output_field": "viscosity", "reference_function": "newtonian"}})
        vr = self.built({"id": "sci-1", "name": "viscosity against the analytic value", "file": "sci-1.json",
                         "verdict": "undecided", "measured": 1.002, "reference": 1.0, "agreement": 0.002, "tolerance": None,
                         "reference_spec": {"kind": "analytic", "ref": "newtonian",
                                            "number_names": ["sci1_reference_viscosity", "sci1_agreement"]}})
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0.002, "unit": "Pa.s"})
        self.assertEqual({n["name"]: n["unit"] for n in vr["numbers"]},
                         {"sci1_reference_viscosity": "Pa.s", "sci1_agreement": "Pa.s"})

    def test_fields_of_different_units_take_no_unit_from_the_contract(self):
        self.tool("flame_point", {"flame_temperature": {"type": "number", "unit": "K"},
                                  "pressure": {"type": "number", "unit": "Pa"}})
        self.task("sci-1.json", {"id": "sci-1", "call": {"tool": "flame_point", "input": {}},
                                 "measure": {"stated": {"flame_temperature": 1066, "pressure": 101325}}})
        vr = self.built({"id": "sci-1", "name": "two fields", "file": "sci-1.json", "verdict": "undecided",
                         "measured": {"flame_temperature": 1066.25, "pressure": 101325}, "agreement": 0.25,
                         "reference": {"flame_temperature": 1066, "pressure": 101325}, "tolerance": None,
                         "reference_spec": {"kind": "source", "ref": "the page"}})
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0.25, "unit": "1"})

    def test_a_contract_with_no_unit_keeps_the_report_as_it_was(self):
        # the echo fixture: a count whose contract declares no unit
        self.tool("echo", {"length": {"type": "integer", "minimum": 0}})
        self.task("sci-1.json", {"id": "sci-1", "call": {"tool": "echo", "input": {}},
                                 "measure": {"output_field": "length", "reference_function": "len_message"}})
        task = {"id": "sci-1", "name": "a count", "file": "sci-1.json", "verdict": "undecided", "measured": 11,
                "reference": 11, "agreement": 0, "tolerance": None,
                "reference_spec": {"kind": "analytic", "ref": "len(message)", "number_names": ["ref_count", "agreement"]}}
        vr = self.built(task)
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0, "unit": "1"})
        self.assertEqual({n["unit"] for n in vr["numbers"]}, {"1"})
        tol = dict(task, tolerance={"value": 1, "unit": "count", "chosen_by": "human"}, verdict="pass")
        self.assertEqual(self.built(tol)["scientific"]["tasks"][0]["agreement"], {"value": 0, "unit": "count"})

    def test_a_unit_the_registry_does_not_hold_is_not_carried_into_the_report(self):
        self.tool("echo", {"length": {"type": "integer", "unit": "character"}})
        self.task("sci-1.json", {"id": "sci-1", "call": {"tool": "echo", "input": {}},
                                 "measure": {"output_field": "length", "reference_function": "len_message"}})
        vr = self.built({"id": "sci-1", "name": "a count", "file": "sci-1.json", "verdict": "undecided", "measured": 11,
                         "reference": 11, "agreement": 0, "tolerance": None,
                         "reference_spec": {"kind": "analytic", "ref": "len(message)"}})
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0, "unit": "1"})

    def test_without_a_bundle_path_the_report_is_as_it_was(self):
        task = {"id": "sci-1", "name": "t", "file": "sci-1.json", "verdict": "undecided", "measured": {"t": 1.5},
                "reference": {"t": 1}, "agreement": 0.5, "tolerance": None, "reference_spec": {"kind": "source", "ref": "p"}}
        vr, _, _ = gate_mod.make_validation_report(report(task), "build-x-0001", "req-x-001", "b", SEAT, NOW)
        self.assertEqual(vr["scientific"]["tasks"][0]["agreement"], {"value": 0.5, "unit": "1"})


if __name__ == "__main__":
    unittest.main()
