# -*- coding: utf-8 -*-
"""Tests of contracts/tools/sheets.py: the example sheet is clean and every rejected fixture of checks 4
and 19 is refused for the reason its name gives (meta_agent/tasks/007, the design part).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import copy
import json
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import sheets  # noqa: E402

EXAMPLES = os.path.join(REPO, "contracts", "examples")
REJECTED = os.path.join(EXAMPLES, "rejected")
SHEET = os.path.join("requests", "req-fixture-001", "parameter_sheet.json")

REASONS = {
    "check19_bound_is_not_what_the_skill_gives": (19, "stated 0.002, and timestep_max_from_courant@v1 on the rows it names gives 0.001"),
    "check19_bound_graded_better_than_its_input": (19, "grade E4, and the worst of E4 and its inputs is E5"),
    "check19_interval_wider_than_its_bounds": (19, "interval.max is 0.01"),
    "check19_point_on_an_empty_interval": (19, "the interval is empty"),
    "check19_applicable_skill_left_out": (19, "applies to this sheet (time_step, rheotool) and is not in skills_considered"),
    "check19_not_applied_without_a_reason": (19, "is not applied and no reason is given"),
    "check19_computed_row_without_basis": (19, "a computed row names the skill and the rows it was computed from"),
    "check19_value_outside_its_interval": (19, "lies outside the interval the bounds give"),
    "check19_correlation_row_called_computed": (19, "a sheet keeps which value is a correlation"),
    "check04_safety_row_filled_by_a_seat": (4, "a safety value is null or written by a person"),
    "check04_safety_row_with_a_recommended_point": (4, "gets no recommended point"),
}


def load(root):
    path = os.path.join(root, SHEET)
    with open(path, "r", encoding="utf-8") as f:
        return path, json.load(f)


class Example(unittest.TestCase):
    def setUp(self):
        self.path, self.sheet = load(EXAMPLES)

    def test_the_example_sheet_is_clean(self):
        self.assertEqual(sheets.check4(self.sheet), [])
        self.assertEqual(sheets.check19(self.sheet, self.path, REPO), [])

    def test_its_interval_is_the_highest_floor_and_the_lowest_ceiling(self):
        row = sheets.rows_by_name(self.sheet)["time_step"]
        self.assertEqual((row["interval"]["min"], row["interval"]["max"]), (5e-05, 0.001))
        self.assertEqual(row["interval"]["max_from"], "timestep_max_from_courant@v1")
        self.assertIsNone(row["value"])

    def test_a_correlation_row_says_so_and_is_graded_by_its_worst_input(self):
        row = sheets.rows_by_name(self.sheet)["solvent_viscosity_at_run_temperature"]
        self.assertEqual((row["value_kind"], row["source"], row["grade"]), ("correlation", "correlation:arrhenius_viscosity@v1", "E5"))
        sheet = copy.deepcopy(self.sheet)
        sheets.rows_by_name(sheet)["activation_temperature"].update(grade="E2")
        self.assertTrue(any("grade E5, and the worst of E4 and its inputs is E4" in m for m in sheets.check19(sheet, self.path, REPO)))

    def test_a_person_may_write_a_safety_value(self):
        sheet = copy.deepcopy(self.sheet)
        row = sheets.rows_by_name(sheet)["max_shear_rate_for_instrument"]
        row.update(value=1000.0, author="human")
        self.assertEqual(sheets.check4(sheet), [])

    def test_a_tighter_assumption_lowers_the_grade_and_only_the_grade(self):
        sheet = copy.deepcopy(self.sheet)
        self.assertEqual(sheets.computed_grade(sheet, sheets.rows_by_name(sheet)["weissenberg_number"]["basis"]), "E4")
        sheets.rows_by_name(sheet)["shear_rate"]["grade"] = "E5"
        self.assertEqual(sheets.computed_grade(sheet, sheets.rows_by_name(sheet)["weissenberg_number"]["basis"]), "E5")
        self.assertIsNone(sheets.computed_grade(sheet, {"skill": "x@v1", "inputs": {"a": "no_such_row"}}))

    def test_a_stated_uncertainty_is_the_tolerance_of_the_recomputation(self):
        sheet = copy.deepcopy(self.sheet)
        bound = sheets.rows_by_name(sheet)["time_step"]["bounds"][0]
        bound["value"] = 0.00104                      # rounded by whoever wrote it
        sheets.rows_by_name(sheet)["time_step"]["interval"]["max"] = 0.00104
        self.assertTrue(any("stated 0.00104" in m for m in sheets.check19(sheet, self.path, REPO)))
        bound["uncertainty"] = 0.0001
        self.assertEqual(sheets.check19(sheet, self.path, REPO), [])

    def test_a_skill_for_another_tool_does_not_apply(self):
        sheet = copy.deepcopy(self.sheet)
        sheet["tool_ref"] = {"kind": "engine", "registry_id": "lammps"}
        found = sheets.check19(sheet, self.path, REPO)
        self.assertFalse(any("is not in skills_considered" in m for m in found), found)


class Estimates(unittest.TestCase):
    """A computed row may rest on an estimate, read at the output its basis names, and a swept parameter is a
    row per point, each with its own basis (the person's kinds of 2026-11-17; tasks/016)."""

    def setUp(self):
        self.path, base = load(EXAMPLES)
        self.sheet = copy.deepcopy(base)

    def add(self, *rows):
        self.sheet["rows"] = list(self.sheet.get("rows") or []) + list(rows)

    def given(self, name, value, unit):
        return {"name": name, "value": value, "unit": unit, "grade": "E2", "value_kind": "literature", "source": "literature:x"}

    def computed(self, name, value, unit, skill, inputs, output=None):
        basis = {"skill": skill, "inputs": inputs}
        if output:
            basis["output"] = output
        return {"name": name, "value": value, "unit": unit, "grade": "E4", "value_kind": "computed",
                "source": "computed:%s" % skill, "basis": basis}

    def problems(self):
        return sheets.check19(self.sheet, self.path, REPO)

    def test_a_sweep_of_a_simulation_box_and_an_instruments_scans_rest_on_estimates(self):
        box = "box_length_for_volume_fraction@v1"
        scans = "scans_for_signal_to_noise@v1"
        self.sheet["skills_considered"] = list(self.sheet.get("skills_considered") or []) + [
            {"skill": box, "verdict": "used"}, {"skill": scans, "verdict": "used"}]
        self.add(self.given("count_a", 8, "count"), self.given("count_b", 1000, "count"),
                 self.given("volume_a", 1.0, "engine_length^3"), self.given("volume_b", 0.5, "engine_length^3"),
                 self.given("phi_a", 0.5, "1"), self.given("phi_b", 0.25, "1"),
                 self.computed("box_length_a", 2.5198420997897464, "engine_length", box,
                               {"particle_count": "count_a", "particle_volume": "volume_a", "volume_fraction": "phi_a"}, "box_length"),
                 self.computed("box_length_b", 12.599210498948732, "engine_length", box,
                               {"particle_count": "count_b", "particle_volume": "volume_b", "volume_fraction": "phi_b"}, "box_length"),
                 self.given("snr_one", 10.0, "1"), self.given("scan_time", 2.0, "s"), self.given("snr_target", 50.0, "1"),
                 self.computed("scans_needed", 25, "count", scans,
                               {"single_scan_snr": "snr_one", "single_scan_time": "scan_time", "target_snr": "snr_target"}, "scan_count"))
        self.assertEqual(self.problems(), [])
        self.sheet["rows"][-5]["value"] = 13.0                      # box_length_b, stated wrong
        self.assertTrue(any("stated 13.0" in p for p in self.problems()), self.problems())
        self.sheet["rows"][-5]["value"] = 12.599210498948732
        del self.sheet["rows"][-1]["basis"]["output"]              # two outputs and none named
        self.assertTrue(any("names which output it is" in p for p in self.problems()), self.problems())


class Fixtures(unittest.TestCase):
    def test_each_fixture_is_refused_for_its_own_reason(self):
        on_disk = sorted(n for n in os.listdir(REJECTED) if n.startswith(("check19_", "check04_")))
        self.assertEqual(on_disk, sorted(REASONS), "a fixture of check 4 or 19 without a stated reason, or a reason without a fixture")
        for name, (check, reason) in sorted(REASONS.items()):
            root = os.path.join(REJECTED, name)
            path, sheet = load(root)
            found = sheets.check4(sheet) if check == 4 else sheets.check19(sheet, path, root)
            self.assertTrue(any(reason in m for m in found), "%s: %r not in %s" % (name, reason, found))


if __name__ == "__main__":
    unittest.main()
