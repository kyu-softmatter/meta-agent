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
                         ["arrhenius_viscosity@v1", "bring_to_ready@v1", "read_status@v1", "shear_rate_max_from_max_speed@v1",
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


if __name__ == "__main__":
    unittest.main()
