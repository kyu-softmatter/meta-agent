"""The skill library, its runner and the skills part of a bundle (tasks/010, the meta part).

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .

Every device skill here runs on a recorded transcript written by hand from
tests/fixtures/rheometer/README.md, or inside a scratch bundle on mock adapters. Nothing is read from a
device and nothing opens a network or serial path (MP1).
"""
import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards, designer
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import LIBRARY, catalogue, rules, runner

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
REPO = os.path.dirname(META)
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
FIX = os.path.join(HERE, "fixtures", "rheometer")
REQ = os.path.join(META, "requests", "req-rheo-fixture-001")
SEAT = "meta-macbook-20261109-2"
NOW = "2026-11-09T12:00:00Z"
KINDS = ["bound", "data_analysis", "hardware_boot", "hardware_calibration", "hardware_connection", "hardware_control",
         "hardware_range", "hardware_state"]
HELD = ["bring_to_ready@v1", "calibrate@v1", "run_steady_shear@v1"]
# The skills these tests were written on. A skill added to the library changes no test here: a test asks that
# these are there and that every skill, whichever it is, keeps the library's rules (the design seat's reply
# meta_agent/inbox/seats/20261116-design-macbook-20261116-1-3.json: a test that every new skill must edit is a
# fault of the test). What a skill must be is check 22's.
NOT_FOR_THE_RHEOMETER = ["timestep_max_from_courant@v1", "timestep_max_from_diffusion@v1", "timestep_max_from_relaxation_time@v1",
                         "water_density_iapws_sr6@v1", "water_viscosity_iapws_sr6@v1", "water_viscosity_kestin_1978@v1",
                         "water_viscosity_relative_difference@v1"]
FOR_THE_RHEOMETER = ["bring_to_ready@v1", "calibrate@v1", "find_and_identify@v1", "flow_curve_fit@v1", "gap_min_from_particle_size@v1",
                     "read_ranges@v1", "read_status@v1", "run_steady_shear@v1", "shear_rate_max_from_inertia@v1",
                     "shear_rate_max_from_max_speed@v1", "shear_rate_min_from_min_speed@v1", "shear_stress_max_from_max_torque@v1",
                     "shear_stress_min_from_min_torque@v1", "viscosity_min_measurable_at_rate@v1"]
SEED = sorted(FOR_THE_RHEOMETER + NOT_FOR_THE_RHEOMETER)
SESSION_SKILLS = ["choose-session-level", "classify-knowledge", "run-skill"]
# the skill the latest template puts into every bundle with a scientific task, for its agreement (tasks/019, cfd-7;
# the common measurement_error@v2 from template v20, tasks/025; @v3, whose outputs name their unit's input, from v31),
# read off the latest template's card
from meta_agent.src.build import template as _template_mod  # noqa: E402
AGREEMENT = cards.load_json(os.path.join(_template_mod.SOURCE, "TEMPLATE.json"))["agreement_skill"]
ENV = dict({k: v for k, v in os.environ.items() if k != "PYTHONPATH"}, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")


def validator_b_checks():
    """The bundle checks the validator implements, read from its source (`B_IMPLEMENTED`): the list is the
    validator's, so a bundle check added in contracts/ is asked of the bundle here without this file changing."""
    tree = ast.parse(cards.read_text(VALIDATE))
    for node in tree.body:
        if isinstance(node, ast.Assign) and [getattr(t, "id", None) for t in node.targets] == ["B_IMPLEMENTED"]:
            return ast.literal_eval(node.value)
    raise AssertionError("contracts/validate.py assigns no B_IMPLEMENTED")


def inputs(name):
    return cards.load_json(os.path.join(FIX, "inputs", name + ".json"))


def transcript(name):
    return runner.Transcript(cards.load_json(os.path.join(FIX, "transcripts", name + ".json")))


def run(ref, inp, tr=None):
    return runner.run(ref, inputs(inp), transcript(tr) if tr else None, now=NOW)


def calls(record):
    return [(c["tool"], c["verdict"]) for c in record["tool_calls"]]


def load_intake():
    """The request's intake as it stands: its latest revision."""
    return designer.latest_intake(REQ)[1]


def scratch_root():
    """A meta_agent-like tree: the fixture lab's profile, the fixture rheometer and the skill library."""
    tmp = tempfile.mkdtemp(prefix="ma-skills-build-")
    root = os.path.join(tmp, "meta_agent")
    shutil.copytree(os.path.join(META, "profiles", "lab-fixture-rich"), os.path.join(root, "profiles", "lab-fixture-rich"))
    shutil.copytree(FIX, os.path.join(root, "tests", "fixtures", "rheometer"))
    shutil.copytree(LIBRARY, os.path.join(root, "skills"), ignore=shutil.ignore_patterns("__pycache__"))
    return tmp, root


def design(root, intake=None):
    """S1 to S6 on the fixture rheometer request, in a scratch tree. Returns (the bundle's path, what run() returned)."""
    out = designer.run(intake or load_intake(), SEAT, "0001", NOW, root)
    return os.path.join(root, "builds", "rheo-fixture", "0001", "bundle"), out


def run_skill_in(bundle, ref, payload):
    """The bundle's own runner, as the built agent would call it: a fresh interpreter in the bundle's folder."""
    p = subprocess.run([sys.executable, "-I", os.path.join("src", "run_skill.py"), ref], cwd=bundle, input=json.dumps(payload),
                       capture_output=True, text=True, encoding="utf-8", env=ENV, timeout=120)
    return p.returncode, (json.loads(p.stdout) if p.stdout.strip().startswith("{") else p.stdout + p.stderr)


class Catalogue(unittest.TestCase):
    def test_the_skills_the_tests_stand_on_are_there_and_each_of_their_kinds_has_one(self):
        rows = catalogue.build_index()["skills"]
        refs = [r["ref"] for r in rows]
        self.assertEqual(len(refs), len(set(refs)))
        self.assertEqual(sorted(set(SEED) - set(refs)), [], "a skill these tests stand on is gone from the library")
        self.assertLessEqual(set(KINDS), {r["kind"] for r in rows})
        self.assertLessEqual({r["kind"] for r in rows}, set(rules.load_kinds()["kinds"]))
        self.assertEqual(sorted(set(HELD) - {r["ref"] for r in rows if r["status"] == "held"}), [])
        self.assertTrue(all(r["side_effect"] == "write_device" for r in rows if r["status"] == "held"))

    def test_a_skill_added_to_the_library_changes_no_test_here(self):
        """The library with one more skill in it, a copy of a seed skill under a new id: the index takes it and
        every assertion about the seed skills holds as before."""
        tmp = tempfile.mkdtemp(prefix="ma-skills-")
        try:
            lib = os.path.join(tmp, "skills")
            shutil.copytree(LIBRARY, lib, ignore=shutil.ignore_patterns("__pycache__", "index.json"))
            src = catalogue.find("shear_rate_max_from_max_speed@v1")
            new = os.path.join(os.path.dirname(src).replace(LIBRARY, lib), "shear_rate_max_copy_for_this_test@v1")
            shutil.copytree(src, new, ignore=shutil.ignore_patterns("__pycache__"))
            manifest = cards.load_json(os.path.join(new, "skill.json"))
            manifest["id"] = "shear_rate_max_copy_for_this_test"
            cards.write_json(os.path.join(new, "skill.json"), manifest)
            text = cards.read_text(os.path.join(new, "SKILL.md")).replace("shear_rate_max_from_max_speed", "shear_rate_max_copy_for_this_test")
            cards.write_text(os.path.join(new, "SKILL.md"), text)
            rows = catalogue.build_index(lib)["skills"]
            refs = {r["ref"] for r in rows}
            self.assertIn("shear_rate_max_copy_for_this_test@v1", refs)
            self.assertEqual(sorted(set(SEED) - refs), [])
            self.assertLessEqual(set(FOR_THE_RHEOMETER), {r["ref"] for r in catalogue.select(rows, instrument="lab_rheometer")})
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_second_build_is_identical_and_is_the_file_on_disk(self):
        tmp = tempfile.mkdtemp(prefix="ma-skills-")
        try:
            lib = os.path.join(tmp, "skills")
            shutil.copytree(LIBRARY, lib, ignore=shutil.ignore_patterns("__pycache__", "index.json"))
            first = cards.read_text(catalogue.write_index(lib))
            second = cards.read_text(catalogue.write_index(lib))
            self.assertEqual(first, second)
            self.assertEqual(first, cards.read_text(os.path.join(LIBRARY, "index.json")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        self.assertTrue(catalogue.index_is_current())

    def test_list_filters_and_says_what_a_model_reads(self):
        rows = catalogue.build_index()["skills"]
        self.assertEqual([r["ref"] for r in catalogue.select(rows, kind="hardware_state")], ["read_status@v1"])
        self.assertLessEqual({"flow_curve_fit@v1", "run_steady_shear@v1", "shear_rate_max_from_inertia@v1",
                              "shear_rate_max_from_max_speed@v1", "shear_rate_min_from_min_speed@v1"},
                             {r["ref"] for r in catalogue.select(rows, parameter="shear_rate")})
        self.assertLessEqual({"timestep_max_from_courant@v1", "timestep_max_from_diffusion@v1", "timestep_max_from_relaxation_time@v1"},
                             {r["ref"] for r in catalogue.select(rows, kind="bound", parameter="time_step")})
        for_it = {r["ref"] for r in catalogue.select(rows, instrument="lab_rheometer")}
        self.assertLessEqual(set(FOR_THE_RHEOMETER), for_it)
        self.assertEqual(for_it & set(NOT_FOR_THE_RHEOMETER), set())
        self.assertEqual(catalogue.select(rows, instrument="an_instrument_no_skill_names"), [])
        text = catalogue.listing(catalogue.select(rows, kind="bound"))
        self.assertIn("shear_rate_max_from_max_speed@v1", text)
        self.assertIn("inputs: max_angular_velocity (rad/s), cone_angle (rad)", text)

    def test_command_line_lists_the_library(self):
        p = subprocess.run([sys.executable, "-m", "meta_agent.src.skills", "list"], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stderr)
        rows = catalogue.build_index()["skills"]
        self.assertIn("%d skill(s) over %d kind(s)" % (len(rows), len({r["kind"] for r in rows})), p.stdout)

    def test_a_skill_check_22_would_fault_is_not_indexed(self):
        tmp = tempfile.mkdtemp(prefix="ma-skills-")
        try:
            lib = os.path.join(tmp, "skills")
            bad = os.path.join(lib, "data_analysis", "flow_curve_fit@v1")
            shutil.copytree(catalogue.find("flow_curve_fit@v1"), bad, ignore=shutil.ignore_patterns("__pycache__"))
            with open(os.path.join(bad, "scripts", "flow_curve_fit.py"), "a", encoding="utf-8") as f:
                f.write("\nimport socket\n")
            with self.assertRaises(ValueError) as e:
                catalogue.build_index(lib)
            self.assertIn("imports socket", str(e.exception))
            self.assertEqual(runner.run("flow_curve_fit@v1", inputs("flow_curve"), library=lib)["verdict"], "refused")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Cases(unittest.TestCase):
    def test_every_case_of_every_skill_passes_through_the_runner(self):
        ran = 0
        for ref, d in sorted(catalogue.skill_dirs().items()):
            for case in cards.load_json(os.path.join(d, "cases.json")):
                if case.get("not_run"):
                    continue
                tr = runner.Transcript(case["transcript"]) if "transcript" in case else None
                rec = runner.run(ref, case.get("inputs", {}), tr, now=NOW)
                label = "%s: %s" % (ref, case["name"])
                self.assertEqual(rec["verdict"], "ran", "%s: %s" % (label, rec["why"]))
                self.assertTrue(rules._same(case["expect"], rec["outputs"], case.get("tolerance", {}).get("rel", 1e-9)), label)
                if "expect_calls" in case:
                    self.assertEqual([c["tool"] for c in rec["tool_calls"]], case["expect_calls"], label)
                ran += 1
        self.assertGreaterEqual(ran, 8)

    def test_check_22_has_nothing_to_say_about_any_skill(self):
        kinds = rules.load_kinds()
        for ref, d in sorted(catalogue.skill_dirs().items()):
            self.assertEqual(rules.problems(d, kinds), [], ref)

    def test_held_skills_leave_the_bench_not_run(self):
        for ref in HELD:
            cases = cards.load_json(os.path.join(catalogue.find(ref), "cases.json"))
            self.assertIn("requires bench", [c.get("not_run") for c in cases], ref)

    def test_no_device_skill_compares_against_a_number_or_imports_beyond_the_list(self):
        for ref, d in sorted(catalogue.skill_dirs().items()):
            self.assertEqual(rules.source_problems(d, rules.read_manifest(d)), [], ref)


class Runner(unittest.TestCase):
    def test_a_skill_with_no_side_effect_needs_no_runner(self):
        rec = run("flow_curve_fit@v1", "flow_curve")
        self.assertEqual((rec["verdict"], rec["runner"], rec["tool_calls"]), ("ran", "none", []))
        self.assertAlmostEqual(rec["outputs"]["flow_index"], 0.5012217653619976, places=12)
        self.assertEqual(rec["outputs"]["value_kind"], "computed")
        self.assertIn("flow_curve_fit@v1", rec["outputs"]["basis"])
        self.assertEqual(run("shear_rate_max_from_max_speed@v1", "bound")["outputs"], {"shear_rate_max": 300.0 / 0.035})

    def test_a_device_skill_without_a_runner_is_refused(self):
        for ref, inp in (("read_status@v1", "status"), ("bring_to_ready@v1", "boot_confirmed"), ("run_steady_shear@v1", "control"),
                         ("calibrate@v1", "calibrate_self"), ("find_and_identify@v1", "connection"), ("read_ranges@v1", "ranges")):
            rec = run(ref, inp)
            self.assertEqual((rec["verdict"], rec["outputs"], rec["tool_calls"]), ("refused", None, []), ref)
            self.assertIn("no tool runner was given", rec["why"])

    def test_a_held_skill_runs_on_a_transcript_only(self):
        class Live(object):          # anything that is not a recorded transcript
            def __init__(self):
                self.called = []

            def call(self, name, payload=None):
                self.called.append(name)
                return {"ok": True}
        live = Live()
        for ref, inp in (("bring_to_ready@v1", "boot_confirmed"), ("run_steady_shear@v1", "control"), ("calibrate@v1", "calibrate_self")):
            rec = runner.run(ref, inputs(inp), live, now=NOW)
            self.assertEqual(rec["verdict"], "refused", ref)
            self.assertIn("held", rec["why"])
        self.assertEqual(live.called, [])
        rec = runner.run("read_status@v1", {}, live, now=NOW)      # a usable skill takes the runner it is given
        self.assertEqual((rec["verdict"], rec["runner"], live.called), ("ran", "given", ["status"]))

    def test_inputs_are_compared_with_the_manifest_before_anything_runs(self):
        rec = runner.run("shear_rate_max_from_max_speed@v1", {"max_angular_velocity": 300.0}, now=NOW)
        self.assertEqual(rec["verdict"], "refused")
        self.assertIn("input cone_angle is missing", rec["why"])
        rec = runner.run("shear_rate_max_from_max_speed@v1", dict(inputs("bound"), limit=1.0), now=NOW)
        self.assertEqual(rec["verdict"], "refused")
        self.assertIn("input limit is not one the manifest names", rec["why"])
        self.assertEqual(runner.run("no_such_skill@v1", {}, now=NOW)["verdict"], "refused")

    def test_an_output_the_manifest_does_not_name_fails_the_run(self):
        tmp = tempfile.mkdtemp(prefix="ma-skills-")
        try:
            lib = os.path.join(tmp, "skills")
            d = os.path.join(lib, "bound", "shear_rate_max_from_max_speed@v1")
            shutil.copytree(catalogue.find("shear_rate_max_from_max_speed@v1"), d, ignore=shutil.ignore_patterns("__pycache__"))
            path = os.path.join(d, "scripts", "bound.py")
            cards.write_text(path, cards.read_text(path).replace('{"shear_rate_max":', '{"extra": True, "shear_rate_max":'))
            rec = runner.run("shear_rate_max_from_max_speed@v1", inputs("bound"), library=lib, now=NOW)
            self.assertEqual(rec["verdict"], "failed")
            self.assertIn("output extra is not one the manifest names", rec["why"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_record_says_what_ran_and_is_never_written_over(self):
        rec = run("find_and_identify@v1", "connection", "connection_one_answers")
        self.assertEqual((rec["skill"], rec["version"], rec["kind"], rec["status"], rec["runner"]),
                         ("find_and_identify", 1, "hardware_connection", "usable", "transcript"))
        self.assertEqual(rec["inputs"], {"address": None})
        self.assertEqual(calls(rec), [("list_devices", "ok"), ("open_session", "ok"), ("identify", "ok"), ("close_session", "ok")])
        self.assertEqual(rec["tool_calls"][1]["input"], {"address": "mock:rheo-1"})
        self.assertEqual(rec["skill_sha256"], cards.sha256_tree(catalogue.find("find_and_identify@v1")))
        self.assertEqual({c["kind"] for c in rec["outputs"]["identity"]}, {"observed"})
        self.assertNotIn("card", rec)
        self.assertNotIn("artifact", rec)
        tmp = tempfile.mkdtemp(prefix="ma-skills-")
        try:
            path = runner.write_record(os.path.join(tmp, "run.json"), rec)
            self.assertEqual(cards.load_json(path), rec)
            with self.assertRaises(FileExistsError):
                runner.write_record(path, rec)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_call_beyond_the_transcript_fails_the_run(self):
        rec = run("bring_to_ready@v1", "boot_confirmed", "empty")
        self.assertEqual(rec["verdict"], "failed")
        self.assertIn("beyond the recorded transcript", rec["why"])

    def test_command_line_run_writes_a_record(self):
        tmp = tempfile.mkdtemp(prefix="ma-skills-")
        try:
            out = os.path.join(tmp, "run.json")
            p = subprocess.run([sys.executable, "-m", "meta_agent.src.skills", "run", "run_steady_shear@v1",
                                "--inputs", os.path.join(FIX, "inputs", "control.json"),
                                "--transcript", os.path.join(FIX, "transcripts", "control_gate_refuses.json"),
                                "--record", out, "--now", NOW], cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
            self.assertEqual(p.returncode, 0, p.stderr)
            rec = cards.load_json(out)
            self.assertEqual(rec, json.loads(p.stdout))
            self.assertEqual((rec["ran_at"], calls(rec)), (NOW, [("status", "ok"), ("set_shear_rate", "refused")]))
            p = subprocess.run([sys.executable, "-m", "meta_agent.src.skills", "run", "run_steady_shear@v1",
                                "--inputs", os.path.join(FIX, "inputs", "control.json")], cwd=REPO, capture_output=True,
                               text=True, encoding="utf-8", env=ENV)
            self.assertEqual(p.returncode, 3)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class HeldSkillsOnATranscript(unittest.TestCase):
    def test_boot_with_a_refusing_gate_makes_no_call_after_it(self):
        rec = run("bring_to_ready@v1", "boot_confirmed", "boot_gate_refuses")
        self.assertEqual(calls(rec), [("initialise", "refused")])
        self.assertEqual((rec["outputs"]["ready"], rec["outputs"]["stopped_at"], rec["outputs"]["refused"]), (False, 3, True))

    def test_boot_stops_where_a_verification_fails(self):
        rec = run("bring_to_ready@v1", "boot_confirmed", "boot_second_verification_fails")
        self.assertEqual([c["tool"] for c in rec["tool_calls"]], ["initialise", "status", "home", "status"])
        self.assertEqual((rec["outputs"]["ready"], rec["outputs"]["stopped_at"]), (False, 4))
        self.assertIn("homed was not read back", rec["outputs"]["why"])

    def test_boot_waits_for_the_person_and_calls_nothing(self):
        rec = run("bring_to_ready@v1", "boot_one_step_unanswered", "empty")
        self.assertEqual((rec["verdict"], rec["tool_calls"]), ("ran", []))
        self.assertEqual((rec["outputs"]["stopped_at"], rec["outputs"]["waiting_for"]), (2, "person"))

    def test_boot_is_ready_only_when_the_last_check_says_so(self):
        rec = run("bring_to_ready@v1", "boot_confirmed", "boot_whole")
        self.assertEqual(rec["outputs"], {"ready": True, "stopped_at": None, "verdict": "ready"})
        self.assertEqual([c["tool"] for c in rec["tool_calls"]], ["initialise", "status", "home", "status", "status"])

    def test_control_with_a_refusing_gate_makes_no_call_after_it(self):
        rec = run("run_steady_shear@v1", "control", "control_gate_refuses")
        self.assertEqual(calls(rec), [("status", "ok"), ("set_shear_rate", "refused")])
        self.assertEqual((rec["outputs"]["completed"], rec["outputs"]["stopped_at"], rec["outputs"]["refused"]), (False, "set", True))

    def test_control_runs_the_step_and_always_stops(self):
        rec = run("run_steady_shear@v1", "control", "control_whole_step")
        self.assertEqual([c["tool"] for c in rec["tool_calls"]], ["status", "set_shear_rate", "start", "status", "status", "stop"])
        self.assertEqual(rec["tool_calls"][1]["input"], {"shear_rate": 10.0})
        self.assertEqual((rec["outputs"]["completed"], rec["outputs"]["run_id"], rec["outputs"]["stop_confirmed"]), (True, "run-fx-1", True))

    def test_calibration_self_returns_a_calibration_number_with_its_expiry(self):
        rec = run("calibrate@v1", "calibrate_self", "calibrate_self")
        self.assertEqual(calls(rec), [("self_calibrate", "ok")])
        cal = rec["outputs"]["calibration"]
        self.assertEqual((cal["source"], cal["expires"], cal["value_kind"]), ("calibration:cal-fx-0001", "2027-05-09", "measured"))
        self.assertNotIn("grade", cal)        # the grade is derived from contracts/grades.json, never stated

    def test_calibration_self_with_a_refusing_gate_returns_no_number(self):
        rec = run("calibrate@v1", "calibrate_self", "calibrate_gate_refuses")
        self.assertEqual(calls(rec), [("self_calibrate", "refused")])
        self.assertEqual((rec["outputs"]["calibrated"], rec["outputs"]["refused"]), (False, True))
        self.assertNotIn("calibration", rec["outputs"])

    def test_calibration_assisted_drafts_a_design_and_calls_nothing(self):
        rec = run("calibrate@v1", "calibrate_assisted", "empty")
        self.assertEqual((rec["verdict"], rec["tool_calls"]), ("ran", []))
        design = rec["outputs"]["calibration_design"]
        self.assertEqual((design["card"], design["status"], design["mode"], design["quantity"]),
                         ("calibration_design", "draft", "assisted", "torque"))
        self.assertEqual((design["acceptance"]["limit"], design["acceptance"]["author"], design["confirmed_by"]), (None, None, None))
        self.assertEqual((design["reference"]["what"], design["interval"]), (None, None))
        self.assertEqual(len(design["open_questions"]), 3)
        self.assertEqual(rec["outputs"]["open_questions"], design["open_questions"])

    def test_calibration_unknown_returns_a_gap(self):
        rec = run("calibrate@v1", "calibrate_unknown", "empty")
        self.assertEqual((rec["outputs"]["mode"], rec["tool_calls"]), ("unknown", []))
        self.assertEqual(rec["outputs"]["gap"]["requires"], "the section of the manual on the normal force transducer")
        self.assertEqual(rec["outputs"]["gap"]["searched"], ["tool_profile.self_calibration"])


class Bundle(unittest.TestCase):
    """The Designer on the fixture rheometer request: a specification that names skills and subagents, and its build."""

    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.root = scratch_root()
        cls.intake = load_intake()
        cls.bundle, cls.out = design(cls.root)
        cls.req = os.path.join(cls.root, "requests", "req-rheo-fixture-001")
        cls.build_dir = os.path.dirname(cls.bundle)
        cls.built = [r for r in cls.intake["skills"] if r not in HELD]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_specification_names_the_skills_the_held_ones_and_the_drawing(self):
        spec = cards.load_json(os.path.join(self.req, "agent_spec.json"))
        self.assertEqual(spec["skills"], self.intake["skills"])
        self.assertEqual(spec["subagents"], self.intake["subagents"])
        self.assertEqual(sorted(h["item"] for h in spec["held"]), sorted("skill %s" % r for r in HELD))
        self.assertEqual(spec["status"], "held")
        a2 = cards.load_json(os.path.join(self.req, "spec_a2.json"))["content"]
        self.assertEqual([t["name"] for t in a2["callable_tools"]], [t["contract"]["name"] for t in self.intake["tools"]])
        self.assertEqual({t["side_effects"] for t in a2["callable_tools"]}, {"reads_instrument"})
        self.assertEqual(a2["subagents"], ["operator", "analyst"])
        build = cards.load_json(os.path.join(self.build_dir, "build.json"))
        self.assertEqual(build["held"], spec["held"])
        self.assertEqual(build["bundle_sha256"], cards.sha256_tree(self.bundle))
        self.assertEqual((self.out["skills"], self.out["subagents"]), (self.built, ["operator", "analyst"]))

    def test_the_named_skills_are_in_the_bundle_unchanged_and_the_held_ones_are_not(self):
        have = sorted(os.listdir(os.path.join(self.bundle, "skills")))
        self.assertEqual(have, sorted(self.built + [AGREEMENT]))      # v16 adds the agreement skill (cfd-7)
        for ref in self.built + [AGREEMENT]:
            self.assertEqual(cards.sha256_tree(os.path.join(self.bundle, "skills", ref)), cards.sha256_tree(catalogue.find(ref)), ref)

    def test_subagents_are_written_with_their_skills_and_side_effects(self):
        adir = os.path.join(self.bundle, ".claude", "agents")
        self.assertEqual(sorted(os.listdir(adir)), ["analyst.md", "operator.md"])
        got = {}
        for name in ("operator", "analyst"):
            text = cards.read_text(os.path.join(adir, name + ".md"))
            fm = rules.front_matter(text)
            self.assertEqual(fm["name"], name)
            self.assertTrue(fm["description"])
            got[name] = (rules.front_list(text, "skills"), rules.front_list(text, "side_effects"))
            self.assertIn("python src/run_skill.py", text)
        self.assertIn('description: "Uses the hardware skills: finds', cards.read_text(os.path.join(adir, "operator.md")))
        self.assertEqual(bundle_mod.front_value("touches no device"), "touches no device")
        self.assertEqual(got["operator"], (["find_and_identify@v1", "read_status@v1", "read_ranges@v1"], ["read_device"]))
        self.assertEqual(got["analyst"], (["shear_rate_max_from_max_speed@v1", "flow_curve_fit@v1"], ["none"]))

    def test_claude_md_names_every_skill_and_subagent(self):
        text = cards.read_text(os.path.join(self.bundle, "CLAUDE.md"))
        self.assertNotIn("{{", text)
        for ref in self.built:
            self.assertIn("`%s`" % ref, text)
        for ref in HELD:
            self.assertNotIn(ref, text)
        for name in ("operator", "analyst"):
            self.assertIn("`%s`" % name, text)
        self.assertIn("src/run_skill.py", text)

    def test_the_bundle_has_one_session_skill_which_names_the_runner(self):
        sdir = os.path.join(self.bundle, ".claude", "skills")
        self.assertEqual(sorted(os.listdir(sdir)), SESSION_SKILLS)
        for name in SESSION_SKILLS:
            self.assertEqual(cards.sha256_tree(os.path.join(sdir, name)) == cards.sha256_tree(
                os.path.join(template_mod.SOURCE, ".claude", "skills", name)), name != bundle_mod.SESSION_SKILL, name)
        here = os.path.join(sdir, bundle_mod.SESSION_SKILL, "SKILL.md")
        there = os.path.join(template_mod.SOURCE, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md")
        self.assertEqual(cards.read_text(here), cards.read_text(there))
        text = cards.read_text(here)
        self.assertIn("python src/run_skill.py", text)
        self.assertTrue(os.path.isfile(os.path.join(self.bundle, "src", "run_skill.py")))
        for never in ("`envelope/safety.json`", "`CLAUDE.md`", "`.claude/`", "`skills/`", "`tools/`", "`src/`"):
            self.assertIn(never, text.split("## What a session never changes")[1], never)
        self.assertIn("`failures.jsonl`", text.split("## What a session may change")[1].split("## What a session never changes")[0])
        claude = cards.read_text(os.path.join(self.bundle, "CLAUDE.md"))
        self.assertIn("`%s`" % bundle_mod.SESSION_SKILL, claude)
        for rule in ("you do not compute it yourself", "A change to any of them is a new build"):
            self.assertIn(rule, claude)

    def test_every_library_skill_has_a_page_rendered_from_its_manifest(self):
        lib = os.path.join(self.bundle, ".claude", "skills", bundle_mod.SESSION_SKILL, "library")
        self.assertEqual(sorted(os.listdir(lib)), sorted(["index.md"] + [r + ".md" for r in self.built + [AGREEMENT]]))
        index = cards.read_text(os.path.join(lib, "index.md"))
        for ref in self.built:
            manifest = cards.load_json(os.path.join(self.bundle, "skills", ref, "skill.json"))
            page = cards.read_text(os.path.join(lib, ref + ".md"))
            self.assertEqual(page, bundle_mod.skill_page(ref, manifest), ref)
            self.assertIn("`%s`" % ref, index)
            self.assertIn("python src/run_skill.py %s < inputs.json" % ref, page)
            for field in manifest["inputs"] + manifest["outputs"]:
                self.assertIn("- `%s` (%s)" % (field["name"], field["unit"]), page)
            for tool in manifest.get("calls_tools", []):
                self.assertIn("`%s`" % tool, page)
            for word in (manifest["kind"], manifest["side_effect"], manifest["status"], manifest["summary"]):
                self.assertIn(word, page)
            self.assertFalse(page.startswith("---"), "a page has no front matter: nothing loads it as a skill")
        for ref in HELD:
            self.assertNotIn(ref, index)
        self.assertEqual(index, bundle_mod.library_index(
            [(r, cards.load_json(os.path.join(self.bundle, "skills", r, "skill.json"))) for r in self.built + [AGREEMENT]]))

    def test_the_bundle_passes_every_b_check(self):
        p = subprocess.run([sys.executable, VALIDATE, "--bundle", self.bundle], capture_output=True, text=True, encoding="utf-8",
                           env=ENV, cwd=REPO)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        last = p.stdout.strip().splitlines()[-1]
        self.assertTrue(last.startswith("VERDICT PASS mode=bundle"), last)
        self.assertIn("failed=0", last)
        ran = ast.literal_eval(p.stdout.split("checks run ", 1)[1].splitlines()[0])
        self.assertEqual(sorted(ran), sorted(validator_b_checks()))
        self.assertTrue({"B1", "B8", "B11"} <= set(ran), ran)

    def test_the_whole_tree_passes_the_validator(self):
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True, encoding="utf-8",
                           env=ENV, cwd=REPO)
        self.assertEqual(p.returncode, 0, p.stdout[-2000:] + p.stderr)
        self.assertIn("bundles=1 failed=0 pending=0", p.stdout.strip().splitlines()[-1])

    def test_check_22_has_nothing_to_say_about_the_bundles_skills(self):
        kinds = rules.load_kinds()
        dirs = rules.find_skill_dirs(os.path.join(self.bundle, "skills"))
        self.assertEqual(len(dirs), 6)                                 # the five named and the agreement skill
        for d in dirs:
            self.assertEqual(rules.problems(d, kinds), [], d)

    def test_the_gates_are_read_off_the_bundle(self):
        self.assertEqual(self.out["gates"], {"interface": "pass", "scientific": "not_run", "overall": "not_run"})
        self.assertTrue(self.out["replay_ok"])

    def test_the_bundle_runs_a_device_skill_through_its_own_tool_runner(self):
        code, rec = run_skill_in(self.bundle, "read_status@v1", {})
        self.assertEqual(code, 0, rec)
        self.assertEqual((rec["verdict"], rec["runner"], rec["outputs"]["verdict"]), ("ran", "src/run_tool.py", "ready"))
        self.assertEqual(calls(rec), [("status", "ok")])
        code, rec = run_skill_in(self.bundle, "find_and_identify@v1", {"address": None})
        self.assertEqual([c["tool"] for c in rec["tool_calls"]], ["list_devices", "open_session", "identify", "close_session"])
        self.assertEqual((rec["outputs"]["identified"], rec["outputs"]["session_closed"]), (True, True))
        code, rec = run_skill_in(self.bundle, "flow_curve_fit@v1", inputs("flow_curve"))
        self.assertEqual((code, rec["tool_calls"]), (0, []))
        self.assertAlmostEqual(rec["outputs"]["consistency"], 2.017261675862101, places=12)

    def test_the_bundles_runner_refuses_what_the_manifest_does_not_allow(self):
        code, rec = run_skill_in(self.bundle, "read_ranges@v1", {})
        self.assertEqual((code, rec["verdict"]), (3, "refused"))
        self.assertIn("input quantities is missing", rec["why"])
        code, _ = run_skill_in(self.bundle, "bring_to_ready@v1", {"person_confirmed": [1, 2]})
        self.assertEqual(code, 2)                 # a held skill is not in the bundle at all

    def test_the_diff_from_the_template_names_what_the_build_added(self):
        diff = cards.read_text(os.path.join(self.build_dir, "diff_from_template.txt"))
        for line in ("added     .claude/agents/operator.md", "added     .claude/agents/analyst.md",
                     "added     skills/read_status@v1/skill.json", "added     tools/status/tool.json",
                     "removed   skills/.gitkeep", "modified  CLAUDE.md"):
            self.assertIn(line, diff)


class Gate(unittest.TestCase):
    """Inside a bundle the gate is asked on every call a skill makes, and a refusal is what the skill is told."""

    def test_a_gated_tool_refuses_and_the_skill_reports_it(self):
        tmp, root = scratch_root()
        try:
            bundle, _ = design(root)
            # in the scratch bundle only: the status tool now asks for the gate, and a safety row is not set
            path = os.path.join(bundle, "tools", "status", "tool.json")
            contract = cards.load_json(path)
            contract.update(side_effects="controls_instrument", errors=["invalid_input", "refused_by_safety"],
                            safety_gate={"required": True, "place": "src/gate.py before the adapter is called"})
            cards.write_json(path, contract)
            cards.write_json(os.path.join(bundle, "envelope", "safety.json"), {"torque_max": None})
            code, rec = run_skill_in(bundle, "read_status@v1", {})
            self.assertEqual((code, rec["verdict"]), (0, "ran"))
            self.assertEqual(calls(rec), [("status", "refused")])
            self.assertEqual(rec["outputs"]["verdict"], "unknown")
            self.assertEqual(rec["outputs"]["error"]["category"], "refused_by_safety")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Drawing(unittest.TestCase):
    """What B11 would fail is refused by the Designer before anything is written."""

    def refused(self, change, expect):
        tmp, root = scratch_root()
        try:
            intake = load_intake()
            change(intake)
            with self.assertRaises(ValueError) as e:
                design(root, intake)
            self.assertIn(expect, str(e.exception))
            self.assertFalse(os.path.exists(os.path.join(root, "requests")))
            self.assertFalse(os.path.exists(os.path.join(root, "builds")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_held_skill_is_not_given_to_a_subagent(self):
        self.refused(lambda i: i["subagents"][0]["skills"].append("run_steady_shear@v1"), "operator names run_steady_shear@v1")

    def test_only_the_operator_may_list_write_device(self):
        self.refused(lambda i: i["subagents"][1]["side_effects"].append("write_device"), "only operator may")

    def test_side_effects_cover_the_skills_a_subagent_names(self):
        self.refused(lambda i: i["subagents"][1]["skills"].append("read_status@v1"), "analyst names read_status@v1, which is read_device")

    def test_a_skill_needs_its_tools_in_the_bundle(self):
        self.refused(lambda i: i.update(tools=[t for t in i["tools"] if t["contract"]["name"] != "ranges"]),
                     "read_ranges@v1 calls the tool ranges")

    def test_a_reading_skill_calls_no_tool_that_changes_something(self):
        def change(i):
            next(t for t in i["tools"] if t["contract"]["name"] == "status")["contract"]["side_effects"] = "controls_instrument"
        self.refused(change, "read_status@v1 says it only reads the device and calls status")

    def test_a_subagent_names_only_skills_the_specification_names(self):
        self.refused(lambda i: i["skills"].remove("flow_curve_fit@v1"), "analyst names flow_curve_fit@v1")

    def test_a_skill_the_library_lacks(self):
        self.refused(lambda i: i["skills"].append("no_such_skill@v1"), "the library has no skill no_such_skill@v1")

    def test_compose_refuses_a_held_skill_and_a_template_without_the_skill_runner(self):
        rows = catalogue.take(["read_status@v1", "bring_to_ready@v1"])
        effects = {"status": "reads_instrument", "initialise": "controls_instrument", "home": "controls_instrument"}
        with self.assertRaises(ValueError) as e:
            bundle_mod.check_drawing(rows, [], effects, template_mod.SOURCE)
        self.assertIn("bring_to_ready@v1 is held", str(e.exception))
        with self.assertRaises(ValueError) as e:
            bundle_mod.check_drawing(rows[:1], [], effects, template_mod.SOURCES["v1"])
        self.assertIn("has no src/run_skill.py", str(e.exception))


class Template(unittest.TestCase):
    def test_the_old_version_stays_under_its_name_and_the_new_one_has_its_own(self):
        self.assertEqual(template_mod.template_name(template_mod.SOURCES["v1"]), "agent@21f0dd569975")
        self.assertTrue(os.path.isdir(os.path.join(META, "templates", "agent@21f0dd569975")))
        latest = template_mod.template_name()
        self.assertEqual(template_mod.template_name(template_mod.SOURCES["v2"]), "agent@79909cd133f1")
        self.assertTrue(os.path.isdir(os.path.join(META, "templates", "agent@79909cd133f1")))
        self.assertEqual(template_mod.template_name(template_mod.SOURCES["v3"]), "agent@a46172e0b6f0")
        self.assertTrue(os.path.isdir(os.path.join(META, "templates", "agent@a46172e0b6f0")))
        self.assertEqual(template_mod.template_name(template_mod.SOURCES["v4"]), "agent@0637edb9a3d1")
        self.assertTrue(os.path.isdir(os.path.join(META, "templates", "agent@0637edb9a3d1")))
        self.assertNotIn(latest, ("agent@21f0dd569975", "agent@79909cd133f1", "agent@a46172e0b6f0", "agent@0637edb9a3d1"))
        self.assertEqual(template_mod.template_name(template_mod.SOURCES["v5"]), "agent@afb9ec0fb292")
        self.assertTrue(os.path.isdir(os.path.join(META, "templates", "agent@afb9ec0fb292")))
        self.assertNotEqual(latest, "agent@afb9ec0fb292")
        self.assertEqual(template_mod.template_name(template_mod.SOURCES["v6"]), "agent@0553834d7c17")
        self.assertTrue(os.path.isdir(os.path.join(META, "templates", "agent@0553834d7c17")))
        self.assertNotEqual(latest, "agent@0553834d7c17")
        self.assertEqual(cards.load_json(os.path.join(template_mod.SOURCE, "TEMPLATE.json"))["version"], template_mod.LATEST)

    def test_every_folder_under_templates_is_a_version_and_every_build_s_template_is_there(self):
        """A version is materialized by the Designer at a build and by nothing else (test run 20261116-4: a session
        left a folder made by hand from a tree it then changed). So templates/ holds only what a version's tree
        gives, under that tree's name, and the latest version need not be there before a build names it."""
        names = {template_mod.template_name(root): root for root in template_mod.SOURCES.values()}
        # and the trees a merged line built from, kept because builds name them (template.KEPT; the merge of 2026-11-23)
        names.update({template_mod.template_name(root): root for root in template_mod.KEPT.values()})
        from meta_agent.src.build import hubs as hubs_mod      # the hub template's versions, named hub@<hash> (tasks/033)
        names.update({hubs_mod.template_name(root): root for root in hubs_mod.SOURCES.values()})
        there = sorted(n for n in os.listdir(os.path.join(META, "templates")) if os.path.isdir(os.path.join(META, "templates", n)))
        for name in there:
            self.assertIn(name, names, "templates/%s is the materialization of no version" % name)
            self.assertEqual(cards.sha256_tree(os.path.join(META, "templates", name)), cards.sha256_tree(names[name]), name)
        builds = os.path.join(META, "builds")
        for agent in sorted(os.listdir(builds)):
            for build_id in sorted(os.listdir(os.path.join(builds, agent))):
                card = os.path.join(builds, agent, build_id, "build.json")
                if os.path.isfile(card):
                    self.assertIn(cards.load_json(card)["template_version"], there, "%s/%s" % (agent, build_id))

    def test_v6_changes_text_and_no_script(self):
        v5, v6 = template_mod.SOURCES["v5"], template_mod.SOURCES["v6"]
        self.assertEqual(cards.tree_files(v5), cards.tree_files(v6))
        changed = sorted(r for r in cards.tree_files(v5) if cards.sha256_file(os.path.join(v5, r)) != cards.sha256_file(os.path.join(v6, r)))
        self.assertEqual(changed, [".claude/skills/run-skill/SKILL.md", "CLAUDE.md", "TEMPLATE.json"])
        rules_text = cards.read_text(os.path.join(v6, "CLAUDE.md"))
        for said in ("`README.md` says what each folder is", "`TEMPLATE.json` records the template",   # (d)
                     "A claim that carries `not_here` names tools this directory does not have",       # (e)
                     "with `--record <file>` it also writes what it printed",                          # (a)
                     "The runner of tools prints and writes no file.",
                     "are checks of this directory and not calls of a tool",
                     "The comparison is the script's and is not made by eye.",                         # (c)
                     "The builder derives it from a table that this directory does not carry",         # (g)
                     "`at`, the time; `task`, the task or the question; `needed`", "`would_settle`"):  # (h)
            self.assertIn(said, rules_text)
        self.assertNotIn("A grade is derived, never stated by hand", rules_text)
        # B6: a bundle's CLAUDE.md carries no number its snapshot does not, so the statuses are told in words there
        self.assertEqual([c for c in rules_text if c.isdigit()], [])
        skill = cards.read_text(os.path.join(v6, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md"))
        for said in ("## What the status a runner ends with means", "## When a task has you make a replay item's call",   # (b), (c)
                     "unless you add `--record <file>`", "`3` the runner refused it before any of its code ran"):
            self.assertIn(said, skill)
        self.assertEqual(rules.front_matter(skill), rules.front_matter(
            cards.read_text(os.path.join(v5, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md"))))
        for name in SESSION_SKILLS:
            text = cards.read_text(os.path.join(v6, ".claude", "skills", name, "SKILL.md"))
            self.assertEqual("src/" in text, name == bundle_mod.SESSION_SKILL, "%s: only one session skill names a runner" % name)

    def test_the_statuses_the_skill_tells_are_the_runners_own(self):
        """What run-skill says a status means is read against the two runners of the template, by running them."""
        tmp, root = scratch_root()
        try:
            bundle, _ = design(root, load_intake())
            def status(args, stdin):
                return subprocess.run([sys.executable] + args, cwd=bundle, input=stdin, capture_output=True, text=True,
                                      encoding="utf-8", env=ENV).returncode
            self.assertEqual(status(["src/run_skill.py", "read_status@v1"], "{}"), 0)
            self.assertEqual(status(["src/run_skill.py", "shear_rate_max_from_max_speed@v1"], "{}"), 3)
            self.assertEqual(status(["src/run_skill.py", "no_such_skill@v1"], "{}"), 2)
            self.assertEqual(status(["src/run_skill.py"], "{}"), 1)
            record = os.path.join(bundle, "runs-test.record.json")
            self.assertEqual(status(["src/run_skill.py", "read_status@v1", "--record", record], "{}"), 0)
            self.assertEqual(cards.load_json(record)["verdict"], "ran")
            self.assertEqual(status(["src/run_skill.py", "read_status@v1", "--record", record], "{}"), 1)
            self.assertEqual(status(["src/run_tool.py", "status"], "{}"), 0)
            self.assertEqual(status(["src/run_tool.py", "status"], '{"x": 1}'), 0)
            self.assertEqual(status(["src/run_tool.py", "no_such_tool"], "{}"), 2)
            self.assertEqual(status(["src/run_tool.py"], "{}"), 1)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_bundle_names_units_and_tells_what_is_not_here(self):
        """(e), (f) of the test run 20261116-2: the units the contract names stand in CLAUDE.md, and CAPABILITIES.json
        names no path of the builder's tree and marks a claim about a tool the bundle does not carry."""
        tmp, root = scratch_root()
        try:
            bundle, _ = design(root, load_intake())
            text = cards.read_text(os.path.join(bundle, "CLAUDE.md"))
            self.assertIn("`temperature` (number, K)", text)
            self.assertIn("`gap` (number, m)", text)
            self.assertIn("`fault` (any; null, or a sentence that says what the fault is)", text)
            cap = cards.load_json(os.path.join(bundle, "CAPABILITIES.json"))
            self.assertNotIn("meta_agent/", json.dumps(cap))
            self.assertEqual(cap["source"], "the documentation of fixture_rheometer (README.md), as the builder read it; "
                                            "the document is not in this directory")
            here = set(os.listdir(os.path.join(bundle, "tools")))
            self.assertEqual(sorted(h["skill"] for h in cap["held"]), ["bring_to_ready@v1", "calibrate@v1", "run_steady_shear@v1"])
            for h in cap["held"]:
                self.assertEqual(set(h["calls_tools"]) & here, set())
            marked = [i for k in ("observed", "derived", "unverified") for i in cap[k] if i.get("not_here")]
            self.assertTrue(marked)
            for i in marked:
                self.assertEqual(set(i["not_here"]) & here, set())
            changes = [i for i in cap["observed"] if i["claim"].startswith("initialise, home, set_shear_rate")][0]
            self.assertEqual(changes["not_here"], ["home", "initialise", "self_calibrate", "set_shear_rate", "start", "stop"])
            reads = [i for i in cap["observed"] if i["claim"].startswith("status returns")][0]
            self.assertNotIn("not_here", reads)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_v5_changes_text_only(self):
        v4, v5 = template_mod.SOURCES["v4"], template_mod.SOURCES["v5"]
        self.assertEqual(cards.tree_files(v4), cards.tree_files(v5))
        changed = sorted(r for r in cards.tree_files(v4) if cards.sha256_file(os.path.join(v4, r)) != cards.sha256_file(os.path.join(v5, r)))
        self.assertEqual(changed, [".claude/skills/run-skill/SKILL.md", "CLAUDE.md", "TEMPLATE.json", "tasks/001-start.md"])
        start = cards.read_text(os.path.join(v5, "tasks", "001-start.md"))
        self.assertIn("prints `undecided` or `not_run`", start)
        self.assertIn("Neither is a pass.", start)
        rules_text = cards.read_text(os.path.join(v5, "CLAUDE.md"))
        self.assertNotIn("every value is `null`", rules_text)
        self.assertIn("A file with no entry means that no tool here requires a gate.", rules_text)
        self.assertIn("which it makes when it first writes there", rules_text)
        self.assertIn("An input that nothing here gives is treated the same way.", rules_text)
        skill = cards.read_text(os.path.join(v5, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md"))
        self.assertIn("## When a skill needs an input that nothing here gives", skill)
        self.assertEqual(rules.front_matter(skill), rules.front_matter(
            cards.read_text(os.path.join(v4, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md"))))
        for name in SESSION_SKILLS:
            text = cards.read_text(os.path.join(v5, ".claude", "skills", name, "SKILL.md"))
            self.assertEqual("src/" in text, name == bundle_mod.SESSION_SKILL, "%s: only one session skill names a runner" % name)

    def test_the_subagents_section_says_who_runs_a_skill(self):
        text = bundle_mod.subagents_section([{"name": bundle_mod.WRITER, "description": "Uses the hardware skills",
                                              "skills": ["read_status@v1"], "side_effects": ["read_device"]}])
        self.assertIn("A skill that changes a device is run by `%s` only." % bundle_mod.WRITER, text)
        self.assertIn("Any other skill you may run yourself through the runner, or give to the subagent that lists it", text)
        self.assertEqual(bundle_mod.subagents_section([]), "This agent has no subagents.")

    def test_v4_changes_text_only(self):
        v3, v4 = template_mod.SOURCES["v3"], template_mod.SOURCES["v4"]
        self.assertEqual(cards.tree_files(v3), cards.tree_files(v4))
        changed = sorted(r for r in cards.tree_files(v3) if cards.sha256_file(os.path.join(v3, r)) != cards.sha256_file(os.path.join(v4, r)))
        self.assertEqual(changed, [".claude/skills/run-skill/SKILL.md", "CLAUDE.md", "TEMPLATE.json", "tasks/001-start.md"])
        skill = cards.read_text(os.path.join(v4, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md"))
        self.assertIn("python src/run_tool.py <tool> < input.json", skill)
        self.assertIn("python src/run_skill.py <id@vN> < inputs.json", skill)
        self.assertIn("a tool called", rules.front_matter(skill)["description"])
        self.assertIn("ends with a failure status whenever the overall verdict is not `pass`",
                      cards.read_text(os.path.join(v4, "tasks", "001-start.md")))
        for name in SESSION_SKILLS:
            text = cards.read_text(os.path.join(v4, ".claude", "skills", name, "SKILL.md"))
            self.assertEqual("src/" in text, name == bundle_mod.SESSION_SKILL, "%s: only one session skill names a runner" % name)

    def test_v3_adds_the_session_skill_to_v2_and_changes_no_script(self):
        v2, v3 = template_mod.SOURCES["v2"], template_mod.SOURCES["v3"]
        f2, f3 = set(cards.tree_files(v2)), set(cards.tree_files(v3))
        self.assertEqual(sorted(f3 - f2), [".claude/skills/choose-session-level/SKILL.md", ".claude/skills/classify-knowledge/SKILL.md",
                                           ".claude/skills/run-skill/SKILL.md", ".claude/skills/run-skill/library/index.md"])
        self.assertEqual(f2 - f3, set())
        changed = sorted(r for r in f2 if cards.sha256_file(os.path.join(v2, r)) != cards.sha256_file(os.path.join(v3, r)))
        self.assertEqual(changed, ["CLAUDE.md", "README.md", "TEMPLATE.json"])
        skill = cards.read_text(os.path.join(v3, ".claude", "skills", bundle_mod.SESSION_SKILL, "SKILL.md"))
        self.assertEqual(rules.front_matter(skill)["name"], bundle_mod.SESSION_SKILL)
        self.assertIn("python src/run_skill.py", skill)
        claude = cards.read_text(os.path.join(v3, "CLAUDE.md"))
        for name in SESSION_SKILLS:
            text = cards.read_text(os.path.join(v3, ".claude", "skills", name, "SKILL.md"))
            self.assertEqual(rules.front_matter(text)["name"], name)
            self.assertIn("`%s`" % name, claude)
            self.assertEqual("src/" in text, name == bundle_mod.SESSION_SKILL, "%s: only one session skill names the runner" % name)
            self.assertNotIn("contracts/", text)
        self.assertIsNone(bundle_mod.session_skill_dir(v2))

    def test_a_template_before_v3_gets_no_pages(self):
        tmp = tempfile.mkdtemp(prefix="ma-skills-pages-")
        try:
            old = os.path.join(tmp, "bundle")
            shutil.copytree(template_mod.SOURCES["v2"], old)
            self.assertEqual(bundle_mod.add_pages(old, []), [])
            self.assertFalse(os.path.exists(os.path.join(old, ".claude", "skills")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_rows_an_intake_names_reach_the_axes_of_the_rheometer_request_too(self):
        tmp, root = scratch_root()
        try:
            intake = load_intake()
            intake["parameter_rows"] = [{"name": "shear_rate", "value": None, "unit": "1/s"}]
            intake["safety_rows"] = [{"name": "highest_angular_velocity", "unit": "rad/s"}]
            bundle, _ = design(root, intake)
            req = os.path.join(root, "requests", "req-rheo-fixture-001")
            self.assertEqual(cards.load_json(os.path.join(req, "spec_a4.json"))["content"]["rows"], intake["parameter_rows"])
            self.assertEqual(cards.load_json(os.path.join(req, "spec_a5.json"))["content"]["rows"], intake["safety_rows"])
            self.assertEqual(cards.load_json(os.path.join(bundle, "envelope", "safety.json")), {"highest_angular_velocity": None})
            rows = cards.load_json(os.path.join(bundle, "envelope", "parameters.json"))["rows"]
            # from template v42 the build adds a row, the person's, for each input of a named skill nothing gives (rheo-5)
            self.assertEqual([r for r in rows if not r.get("for_skill_inputs")], intake["parameter_rows"])
            self.assertTrue(all(r["value"] is None for r in rows if r.get("for_skill_inputs")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_build_with_no_skills_fills_both_sections(self):
        tmp, root = scratch_root()
        try:
            intake = load_intake()
            intake.update(skills=[], subagents=[])
            bundle, _ = design(root, intake)
            text = cards.read_text(os.path.join(bundle, "CLAUDE.md"))
            # a build that names no skill still carries the agreement skill, since every bundle has a scientific task (v16)
            self.assertEqual(os.listdir(os.path.join(bundle, "skills")), [AGREEMENT])
            self.assertIn(AGREEMENT, text)
            self.assertNotIn("has no skills", text)
            lib = os.path.join(bundle, ".claude", "skills", bundle_mod.SESSION_SKILL, "library")
            self.assertEqual(sorted(os.listdir(lib)), ["index.md", AGREEMENT + ".md"])
            self.assertIn("This agent has no subagents.", text)
            self.assertFalse(os.path.exists(os.path.join(bundle, ".claude", "agents")))
            spec = cards.load_json(os.path.join(root, "requests", "req-rheo-fixture-001", "agent_spec.json"))
            self.assertNotIn("skills", spec)
            self.assertEqual(spec["held"], [])
            p = subprocess.run([sys.executable, VALIDATE, "--bundle", bundle], capture_output=True, text=True, encoding="utf-8",
                               env=ENV, cwd=REPO)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class RecordedBuild(unittest.TestCase):
    """The build recorded under meta_agent/builds/rheo-fixture/0001: what its cards say is what is on disk."""

    def test_the_record_agrees_with_its_cards_and_the_library(self):
        build_dir = os.path.join(META, "builds", "rheo-fixture", "0001")
        build = cards.load_json(os.path.join(build_dir, "build.json"))
        spec = cards.load_json(os.path.join(REQ, "agent_spec.json"))
        bundle = os.path.join(REPO, *build["bundle_path"].split("/"))
        self.assertEqual(build["spec_ref"], spec["id"])
        self.assertEqual(build["bundle_sha256"], cards.sha256_tree(bundle))
        self.assertEqual(build["held"], spec["held"])
        self.assertIsNone(build["landed_at"])
        held = {h["item"].split()[-1] for h in spec["held"]}
        self.assertEqual(sorted(held), HELD)
        carried = sorted(os.listdir(os.path.join(bundle, "skills")))
        self.assertEqual(carried, sorted(r for r in spec["skills"] if r not in held))
        for ref in carried:
            self.assertEqual(cards.sha256_tree(os.path.join(bundle, "skills", ref)), cards.sha256_tree(catalogue.find(ref)), ref)
        for a in spec["subagents"]:
            text = cards.read_text(os.path.join(bundle, ".claude", "agents", a["name"] + ".md"))
            self.assertEqual(rules.front_list(text, "skills"), a["skills"])
            self.assertEqual(rules.front_list(text, "side_effects"), a["side_effects"])


if __name__ == "__main__":
    unittest.main()
