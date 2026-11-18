# -*- coding: utf-8 -*-
"""Tests of contracts/tools/skills.py: the example skills are clean, and every rejected fixture of check 22
is refused for the reason its name gives (meta_agent/tasks/010, the design part).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import skills  # noqa: E402

EXAMPLES = os.path.join(REPO, "contracts", "examples", "skills")
REJECTED = os.path.join(REPO, "contracts", "examples", "rejected")
KINDS = skills.load_kinds()

# fixture -> (the skill folder in it that is wrong, what check 22 must say about it)
REASONS = {
    "check22_skill_opens_a_file": ("shear_rate_max_from_max_speed@v1", "calls open()"),
    "check22_skill_imports_socket": ("read_status@v1", "imports socket"),
    "check22_device_skill_holds_a_limit": ("read_status@v1", "compares against the number 320"),
    "check22_tool_not_named": ("read_status@v1", "calls the tool identify, which calls_tools does not name"),
    "check22_worked_case_fails": ("shear_rate_max_from_max_speed@v1", "case a cone of 0.035 rad at 300 rad/s: expected"),
    "check22_no_worked_case": ("read_status@v1", "holds no case that runs"),
    "check22_write_device_not_held": ("bring_to_ready@v1", "is held until a person releases it"),
    "check22_boot_not_verified_ready": ("bring_to_ready@v1", "returning ready"),
    "check22_boot_code_and_steps_disagree": ("bring_to_ready@v1", "the code follows the sequence it declares"),
    "check22_manifest_and_folder_disagree": ("shear_rate_max_from_max_speed@v1", "and the folder says"),
    "check22_unknown_kind": ("shear_rate_max_from_max_speed@v1", "is not in contracts/skill_kinds.json"),
    "check22_uses_a_skill_that_is_not_there": ("bring_to_ready@v1", "which is not in this library"),
    "check22_bound_one_worked_case": ("gap_min_from_particle_size@v1", "two worked cases that run, with inputs that differ"),
    "check22_bound_two_outputs": ("box_edge_from_volume@v1", "a bound skill gives one output"),
    "check22_estimate_one_worked_case": ("scans_for_signal_to_noise@v1", "an estimate skill carries two worked cases"),
    "check22_diagnostic_without_an_undecided_case": ("series_settled@v1", "a worked case that expects state undecided"),
    "check22_common_skill_shown_on_one_kind": ("series_settled@v1", "shown on at least two unrelated kinds of system"),
}


def skill_dir(root, name):
    for d in skills.find_skill_dirs(root):
        if os.path.basename(d) == name:
            return d
    raise AssertionError("%s is not under %s" % (name, root))


class Examples(unittest.TestCase):
    def test_every_example_skill_is_clean_and_its_cases_pass(self):
        found = skills.find_skill_dirs(EXAMPLES)
        self.assertEqual(sorted(os.path.basename(d) for d in found),
                         ["arrhenius_viscosity@v1", "box_length_for_volume_fraction@v1", "bring_to_ready@v1", "read_status@v1",
                          "scans_for_signal_to_noise@v1", "series_settled@v1", "shear_rate_max_from_max_speed@v1",
                          "timestep_max_from_courant@v1", "timestep_max_from_relaxation_time@v1",
                          "timestep_min_from_step_budget@v1", "weissenberg_number@v1"])
        for d in found:
            self.assertEqual(skills.problems(d, KINDS), [], d)
            verdicts = [r["verdict"] for r in skills.run_cases_here(d)]
            self.assertIn("pass", verdicts)
            self.assertNotIn("fail", verdicts)

    def test_the_boot_sequence_stops_and_calls_nothing_more(self):
        d = skill_dir(EXAMPLES, "bring_to_ready@v1")
        by_name = {r["name"]: r for r in skills.run_cases_here(d)}
        self.assertEqual(by_name["the gate refuses the first device step: no call after it"]["verdict"], "pass")
        self.assertEqual(by_name["a person's step not confirmed: it waits and calls nothing"]["verdict"], "pass")
        self.assertEqual(by_name["on the bench"]["verdict"], "not_run")


class Fixtures(unittest.TestCase):
    def test_each_fixture_is_refused_for_its_own_reason(self):
        on_disk = sorted(n for n in os.listdir(REJECTED) if n.startswith("check22_"))
        self.assertEqual(on_disk, sorted(REASONS), "a check 22 fixture without a stated reason, or a reason without a fixture")
        for name, (folder, reason) in sorted(REASONS.items()):
            found = skills.problems(skill_dir(os.path.join(REJECTED, name), folder), KINDS)
            self.assertTrue(any(reason in m for m in found), "%s: %r not in %s" % (name, reason, found))


class Reading(unittest.TestCase):
    def test_front_matter(self):
        text = "---\nname: operator\ndescription: runs the plan\nskills: [a@v1, b@v2]\nside_effects:\n  - read_device\n  - write_device\n---\n\nbody\n"
        self.assertEqual(skills.front_matter(text)["name"], "operator")
        self.assertEqual(skills.front_list(text, "skills"), ["a@v1", "b@v2"])
        self.assertEqual(skills.front_list(text, "side_effects"), ["read_device", "write_device"])
        self.assertEqual(skills.front_list("no front matter", "skills"), [])

    def test_a_case_compares_numbers_within_a_relative_tolerance(self):
        self.assertTrue(skills._same({"x": 1.0}, {"x": 1.0 + 1e-12, "more": 1}, 1e-9))
        self.assertFalse(skills._same({"x": 1.0}, {"x": 1.001}, 1e-9))
        self.assertFalse(skills._same({"ready": True}, {"ready": 1}, 1e-9))
        self.assertTrue(skills._same({"a": [1, {"b": None}]}, {"a": [1, {"b": None}]}, 1e-9))




class Common(unittest.TestCase):
    """A common skill every simulation bundle carries, and a skill adapted from one (the person, 2026-11-18;
    meta_agent/tasks/025)."""

    def cases_on(self, systems):
        import json, tempfile
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "cases.json"), "w", encoding="utf-8") as f:
            json.dump([{"name": "case %d" % i, "system": s} for i, s in enumerate(systems)], f)
        return d

    def test_a_common_skill_on_two_unrelated_kinds_and_no_engine_is_clean(self):
        d = self.cases_on(["molecular dynamics of a protein", "chemical equilibrium of a flame"])
        self.assertEqual(skills.common_problems(d, {"common": True, "applies_to": {"engines": [], "parameters": []}}), [])

    def test_a_common_skill_that_names_an_engine_is_refused(self):
        d = self.cases_on(["molecular dynamics", "finite elements"])
        found = skills.common_problems(d, {"common": True, "applies_to": {"engines": ["gromacs"]}})
        self.assertTrue(any("applies to no particular engines" in m for m in found), found)

    def test_an_adapted_skill_names_its_engine_and_is_not_common(self):
        d = self.cases_on(["molecular dynamics"])
        self.assertEqual(skills.common_problems(d, {"adapted_from": "series_settled@v2", "applies_to": {"engines": ["gromacs"]}}), [])
        found = skills.common_problems(d, {"adapted_from": "series_settled@v2", "applies_to": {"engines": []}})
        self.assertTrue(any("names the engine it is for" in m for m in found), found)


if __name__ == "__main__":
    unittest.main()


class DescriptionNumbers(unittest.TestCase):
    """What `skills.py check` notes about a description a bundle prints (tasks/016, run 20261117-1)."""

    def numbers(self, description):
        import shutil
        import tempfile
        d = tempfile.mkdtemp(prefix="desc-")
        self.addCleanup(shutil.rmtree, d, True)
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write("---\nname: x\ndescription: %s\n---\n\n# x\n" % description)
        return skills.description_numbers(d)

    def test_a_formula_and_a_range_are_noted_and_words_are_not(self):
        # two unrelated kinds: a lattice count of a simulation box and a fluid property's range of validity
        self.assertTrue(self.numbers("The volume fraction sqrt(2)/3 a^3 / L^3 of octahedra in a cubic box."))
        self.assertEqual(self.numbers("Viscosity of water from 265.15 K to 423.15 K."), ["265.15", "423.15"])
        self.assertEqual(self.numbers("The particle count of a body-centred cubic lattice of m cells a side."), [])
        self.assertEqual(self.numbers("As printed by hoomd 7.2.2."), [])
