"""The bounds pass, the sheet of the fixture rheometer request and the property sources (tasks/007, the meta part).

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .

A bound is never typed here: every expected number is what a skill gives on the rows it is bound to, or
is read off the worked arithmetic beside it.
"""
import copy
import math
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

from meta_agent.src import cards, designer
from meta_agent.src.parameters import bounds, rules
from meta_agent.src.skills import LIBRARY, catalogue, runner
from meta_agent.src.sources import chemicals_adapter, nist_webbook

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
REPO = os.path.dirname(META)
REQ = os.path.join(META, "requests", "req-rheo-fixture-001")
EXAMPLES = os.path.join(REPO, "contracts", "examples")
SEAT = "meta-macbook-20261109-2"
NOW = "2026-11-10T04:00:00Z"
ENV = dict({k: v for k, v in os.environ.items() if k != "PYTHONPATH"}, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
USED = ["shear_rate_min_from_min_speed@v1", "shear_rate_max_from_max_speed@v1", "shear_rate_max_from_inertia@v1",
        "shear_stress_min_from_min_torque@v1", "shear_stress_max_from_max_torque@v1", "viscosity_min_measurable_at_rate@v1",
        "gap_min_from_particle_size@v1"]


def draft():
    d, _ = designer.looked_up(cards.load_json(os.path.join(REQ, "sheet_draft.json")))
    return d


def binding():
    return cards.load_json(os.path.join(REQ, "bounds_binding.json"))


def skills(library=LIBRARY):
    return [r for r in catalogue.build_index(library)["skills"] if r["kind"] == "bound"]


def run_in(library=LIBRARY):
    return lambda ref, inputs: runner.run(ref, inputs, library=library, now=NOW)


def apply(d=None, b=None, check=True):
    """The sheet for a draft and a binding, checked as if it lay in the request's folder."""
    path = os.path.join(REQ, "parameter_sheet.json") if check else None
    return bounds.apply(d or draft(), b or binding(), skills(), run_in(), SEAT, NOW, sheet_path=path, tree=REPO)


def row(sheet, name):
    return next(r for r in sheet["rows"] if r["name"] == name)


def bound(sheet, name, skill):
    return next(b for b in row(sheet, name)["bounds"] if b["basis"]["skill"] == skill)


def said(sheet):
    return rules.check4(sheet) + rules.check19(sheet, os.path.join(REQ, "parameter_sheet.json"), REPO)


def scratch_root():
    tmp = tempfile.mkdtemp(prefix="ma-sheet-")
    root = os.path.join(tmp, "meta_agent")
    os.makedirs(os.path.join(root, "requests"))
    dest = os.path.join(root, "requests", "req-rheo-fixture-001")
    os.makedirs(dest)
    for name in ("sheet_draft.json", "bounds_binding.json"):
        shutil.copy(os.path.join(REQ, name), os.path.join(dest, name))
    shutil.copytree(LIBRARY, os.path.join(root, "skills"), ignore=shutil.ignore_patterns("__pycache__"))
    return tmp, root, dest


class BoundSkills(unittest.TestCase):
    def test_ten_bound_skills_each_with_passing_cases(self):
        rows = skills()
        self.assertEqual(len(rows), 10)
        kinds = rules.skill_rules.load_kinds()
        for r in rows:
            d = catalogue.find(r["ref"])
            self.assertEqual(rules.skill_rules.problems(d, kinds), [], r["ref"])
            results = rules.skill_rules.run_cases_here(d)
            self.assertGreaterEqual(len(results), 2, r["ref"])
            self.assertTrue(all(x["verdict"] == "pass" for x in results), r["ref"])

    def test_each_bounds_one_parameter_on_one_side_and_holds_no_judgement(self):
        judgements = {"shear_rate_max_from_inertia@v1": "critical_reynolds_number", "gap_min_from_particle_size@v1": "gap_to_particle_ratio",
                      "timestep_max_from_courant@v1": "courant_limit", "timestep_max_from_diffusion@v1": "diffusion_number_limit",
                      "timestep_max_from_relaxation_time@v1": "resolved_fraction"}
        for r in skills():
            self.assertIn(r["side"], ("min", "max"))
            self.assertEqual(r["applies_to"]["parameters"], [r["parameter"]])
            self.assertEqual(len(r["outputs"]), 1)
            if r["ref"] in judgements:
                self.assertIn(judgements[r["ref"]], [i["name"] for i in r["inputs"]])
        self.assertEqual(sorted(r["ref"] for r in skills() if "rheotool" in (r["applies_to"].get("engines") or [])),
                         ["timestep_max_from_courant@v1", "timestep_max_from_diffusion@v1", "timestep_max_from_relaxation_time@v1"])

    def test_the_reynolds_number_is_a_plain_function_of_a_sibling_module(self):
        d = catalogue.find("shear_rate_max_from_inertia@v1")
        self.assertTrue(os.path.isfile(os.path.join(d, "scripts", "dimensionless.py")))
        rec = runner.run("shear_rate_max_from_inertia@v1", {"critical_reynolds_number": 4.0, "viscosity": 0.001, "density": 1000.0,
                                                           "cone_angle": 0.035, "cone_radius": 0.02}, now=NOW)
        rate = rec["outputs"]["shear_rate_max"]
        self.assertAlmostEqual(1000.0 * rate * 0.035 ** 3 * 0.02 ** 2 / 0.001, 4.0, places=9)   # the Reynolds number at the bound is the critical one


class Sheet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sheet = apply()

    def test_the_interval_is_the_highest_floor_and_the_lowest_ceiling_and_names_them(self):
        iv = row(self.sheet, "shear_rate")["interval"]
        self.assertEqual((iv["min_from"], iv["max_from"]), ("shear_rate_min_from_min_speed@v1", "shear_rate_max_from_inertia@v1"))
        self.assertEqual(iv["min"], bound(self.sheet, "shear_rate", "shear_rate_min_from_min_speed@v1")["value"])
        self.assertEqual(iv["max"], bound(self.sheet, "shear_rate", "shear_rate_max_from_inertia@v1")["value"])
        self.assertLess(iv["max"], bound(self.sheet, "shear_rate", "shear_rate_max_from_max_speed@v1")["value"])
        self.assertEqual(iv["unit"], "1/s")
        iv = row(self.sheet, "shear_stress")["interval"]
        self.assertEqual((iv["min_from"], iv["max_from"]), ("shear_stress_min_from_min_torque@v1", "shear_stress_max_from_max_torque@v1"))
        iv = row(self.sheet, "viscosity")["interval"]
        self.assertEqual((iv["max"], iv["max_from"], iv["min_from"]), (None, None, "viscosity_min_measurable_at_rate@v1"))

    def test_no_point_is_written_and_safety_rows_stay_null(self):
        for name in ("shear_rate", "shear_stress", "viscosity", "gap"):
            r = row(self.sheet, name)
            self.assertIsNone(r["value"])
            self.assertNotIn("recommendation", r)
        for name in ("max_torque_allowed", "max_angular_velocity_allowed"):
            r = row(self.sheet, name)
            self.assertTrue(r["safety_relevant"])
            self.assertIsNone(r["value"])
            self.assertNotIn("bounds", r)

    def test_every_bound_says_what_it_rests_on(self):
        n = 0
        for r in self.sheet["rows"]:
            for b in r.get("bounds", []):
                n += 1
                self.assertEqual(b["source"], "computed:%s" % b["basis"]["skill"])
                self.assertEqual((b["value_kind"], b["unit"]), ("computed", r["unit"]))
                self.assertTrue(b["basis"]["inputs"])
        self.assertEqual(n, 7)

    def test_a_bound_recomputed_by_its_skill_agrees_within_its_uncertainty(self):
        b = bound(self.sheet, "shear_rate", "shear_rate_max_from_max_speed@v1")
        again = runner.run(b["basis"]["skill"], {k: row(self.sheet, v)["value"] for k, v in b["basis"]["inputs"].items()}, now=NOW)
        exact = again["outputs"]["shear_rate_max"]
        self.assertAlmostEqual(exact, 300.0 / 0.035, places=9)
        self.assertEqual((b["value"], b["uncertainty"]), (8570.0, 130.0))
        self.assertLessEqual(abs(exact - b["value"]), b["uncertainty"])
        # first order: the cone angle's tolerance of 0.0005 rad in 0.035 rad carries over to the rate
        self.assertAlmostEqual(300.0 / 0.035 * 0.0005 / 0.035, 122.4, places=0)

    def test_a_bound_with_no_uncertain_input_is_exact_and_states_none(self):
        b = bound(self.sheet, "gap", "gap_min_from_particle_size@v1")
        self.assertIsNone(b["uncertainty"])
        self.assertEqual(b["value"], 10.0 * 1e-06)

    def test_the_grade_is_the_worst_of_e4_and_the_input_rows(self):
        self.assertEqual({r["name"]: r["grade"] for r in self.sheet["rows"] if r["name"] in ("cone_angle", "sample_viscosity")},
                         {"cone_angle": "E3", "sample_viscosity": "E5"})
        self.assertEqual(bound(self.sheet, "shear_rate", "shear_rate_max_from_max_speed@v1")["grade"], "E4")     # spec rows are E3
        self.assertEqual(bound(self.sheet, "shear_rate", "shear_rate_max_from_inertia@v1")["grade"], "E5")       # an assumed: row
        self.assertEqual(bound(self.sheet, "gap", "gap_min_from_particle_size@v1")["grade"], "E5")

    def test_skills_considered_covers_every_skill_that_applies(self):
        self.assertEqual([e["skill"] for e in self.sheet["skills_considered"]], USED)
        self.assertTrue(all(e["verdict"] == "used" and e["why"] for e in self.sheet["skills_considered"]))
        names = [r["name"] for r in self.sheet["rows"]]
        self.assertEqual(sorted(r["ref"] for r in bounds.applicable(skills(), names, self.sheet["tool_ref"])), sorted(USED))

    def test_checks_4_and_19_have_nothing_to_say(self):
        self.assertEqual(said(self.sheet), [])

    def test_a_skill_left_out_of_skills_considered_fails_check_19(self):
        bad = copy.deepcopy(self.sheet)
        bad["skills_considered"] = [e for e in bad["skills_considered"] if e["skill"] != "gap_min_from_particle_size@v1"]
        self.assertTrue(any("gap_min_from_particle_size@v1" in m and "skills_considered" in m for m in said(bad)))

    def test_a_typed_bound_fails_check_19(self):
        bad = copy.deepcopy(self.sheet)
        bound(bad, "shear_rate", "shear_rate_max_from_inertia@v1")["value"] = 500.0
        self.assertTrue(any("stated 500.0" in m for m in said(bad)))

    def test_the_same_files_give_the_same_sheet(self):
        self.assertEqual(apply(), self.sheet)


class EmptyInterval(unittest.TestCase):
    def test_two_bounds_that_cross_give_no_point_and_a_tradeoff_naming_both(self):
        d = draft()
        next(r for r in d["rows"] if r["name"] == "min_angular_velocity")["value"] = 10.0
        sheet = apply(d)
        r = row(sheet, "shear_rate")
        iv = r["interval"]
        self.assertGreater(iv["min"], iv["max"])
        self.assertEqual((iv["min_from"], iv["max_from"]), ("shear_rate_min_from_min_speed@v1", "shear_rate_max_from_inertia@v1"))
        self.assertIsNone(r["value"])
        rec = r["recommendation"]
        self.assertEqual((rec["mode"], rec["point"], rec["chosen_by"]), ("tradeoff", None, "human"))
        self.assertNotIn("candidates", rec)
        for ref in (iv["min_from"], iv["max_from"]):
            self.assertIn(ref, rec["reason"])
        self.assertEqual(said(sheet), [])
        bad = copy.deepcopy(sheet)
        row(bad, "shear_rate")["recommendation"]["point"] = 250.0
        self.assertTrue(any("empty" in m for m in said(bad)))


class Binding(unittest.TestCase):
    """A binding that cannot be carried out stops with a named error and no sheet."""

    def refused(self, error, change_binding=None, change_draft=None):
        d, b = draft(), binding()
        if change_binding:
            change_binding(b)
        if change_draft:
            change_draft(d)
        with self.assertRaises(error) as e:
            apply(d, b)
        return e.exception

    def entry(self, b, ref):
        return next(e for e in b["skills"] if e["skill"] == ref)

    def test_a_skill_that_applies_and_is_not_named(self):
        e = self.refused(bounds.NotConsidered, lambda b: b["skills"].pop())
        self.assertEqual(e.code, "not_considered")
        self.assertIn("gap_min_from_particle_size@v1", str(e))

    def test_not_applied_needs_a_reason(self):
        def change(b):
            self.entry(b, "gap_min_from_particle_size@v1").update(verdict="not_applied", why=" ")
        self.assertEqual(self.refused(bounds.NoReason, change).code, "no_reason")

    def test_not_applied_with_a_reason_leaves_no_bound_and_passes(self):
        b = binding()
        self.entry(b, "gap_min_from_particle_size@v1").update(verdict="not_applied", why="the fixture sample is a solution; it carries no particles")
        sheet = apply(None, b)
        self.assertNotIn("bounds", row(sheet, "gap"))
        self.assertEqual(sheet["skills_considered"][-1]["verdict"], "not_applied")
        self.assertEqual(said(sheet), [])

    def test_an_input_bound_to_a_row_that_is_not_there(self):
        def change(b):
            self.entry(b, "shear_rate_max_from_max_speed@v1")["inputs"]["cone_angle"] = "plate_angle"
        e = self.refused(bounds.MissingRow, change)
        self.assertEqual(e.code, "missing_row")
        self.assertIn("plate_angle", str(e))

    def test_an_input_bound_to_a_row_with_no_value(self):
        def change(b):
            self.entry(b, "viscosity_min_measurable_at_rate@v1")["inputs"]["shear_rate"] = "shear_rate"
        self.assertEqual(self.refused(bounds.NoValue, change).code, "no_value")

    def test_an_input_bound_to_a_row_in_another_unit(self):
        def change(b):
            self.entry(b, "shear_rate_max_from_max_speed@v1")["inputs"]["cone_angle"] = "cone_radius"
        e = self.refused(bounds.WrongUnit, change)
        self.assertEqual(e.code, "wrong_unit")
        self.assertIn("rad", str(e))

    def test_an_input_left_unbound_or_one_the_skill_does_not_take(self):
        def drop(b):
            del self.entry(b, "shear_rate_max_from_max_speed@v1")["inputs"]["cone_angle"]
        self.assertEqual(self.refused(bounds.InputNotBound, drop).code, "input_not_bound")

        def extra(b):
            self.entry(b, "shear_rate_max_from_max_speed@v1")["inputs"]["limit"] = "max_torque"
        self.assertEqual(self.refused(bounds.InputNotBound, extra).code, "input_not_bound")

    def test_a_skill_the_library_does_not_have(self):
        e = self.refused(bounds.UnknownSkill, lambda b: b["skills"].append({"skill": "shear_rate_max_from_nothing@v1", "verdict": "used", "inputs": {}}))
        self.assertEqual(e.code, "unknown_skill")

    def test_a_grade_is_derived_and_a_stated_one_must_be_it(self):
        def change(d):
            next(r for r in d["rows"] if r["name"] == "sample_viscosity")["grade"] = "E2"
        e = self.refused(bounds.NoGrade, None, change)
        self.assertEqual(e.code, "no_grade")
        self.assertIn("E5", str(e))

    def test_a_draft_cannot_carry_a_computed_value(self):
        def change(d):
            next(r for r in d["rows"] if r["name"] == "shear_rate").update(value=100.0, source="computed:typed_by_hand", value_kind="computed")
        self.refused(bounds.BindingError, None, change)

    def test_a_skill_that_fails_stops_the_pass(self):
        def change(d):
            next(r for r in d["rows"] if r["name"] == "cone_angle").update(value=0.0, uncertainty=None)
        e = self.refused(bounds.SkillFailed, None, change)
        self.assertEqual(e.code, "skill_failed")
        self.assertIn("ZeroDivisionError", str(e))


class Uncertainty(unittest.TestCase):
    def test_the_value_is_rounded_to_the_place_of_the_uncertaintys_second_figure(self):
        self.assertEqual(bounds._round_to_uncertainty(8571.428571428572, 122.44897959183822), (8570.0, 130.0))
        self.assertEqual(bounds._round_to_uncertainty(233.2361516034985, 10.26), (233.0, 11.0))
        self.assertEqual(bounds._round_to_uncertainty(2.857142857142857e-05, 4.0816e-07), (2.857e-05, 4.1e-07))
        for value, sigma in ((8571.428571428572, 122.44897959183822), (0.000596831036594608, 8.95e-06), (1.0, 0.5)):
            rounded, u = bounds._round_to_uncertainty(value, sigma)
            self.assertGreaterEqual(u, sigma * (1 - 1e-9))
            self.assertLessEqual(abs(rounded - value), u)

    def test_two_uncertain_inputs_add_in_quadrature(self):
        sheet = apply()
        b = bound(sheet, "shear_rate", "shear_rate_max_from_inertia@v1")
        exact = 4.0 * 0.001 / (1000.0 * 0.035 ** 3 * 0.02 ** 2)
        first_order = exact * math.sqrt((3 * 0.0005 / 0.035) ** 2 + (2 * 0.0001 / 0.02) ** 2)
        self.assertAlmostEqual(first_order, 10.3, places=1)
        self.assertEqual((b["value"], b["uncertainty"]), (233.0, 11.0))
        self.assertLessEqual(abs(exact - b["value"]), b["uncertainty"])


class ExampleSheet(unittest.TestCase):
    """The design seat's example sheet, made again from its rows and its bindings with its own library."""

    def test_the_pass_gives_the_example_sheets_bounds_interval_and_computed_row(self):
        path = os.path.join(EXAMPLES, "requests", "req-fixture-001", "parameter_sheet.json")
        example = cards.load_json(path)
        library = os.path.join(EXAMPLES, "skills")
        d = {k: copy.deepcopy(example[k]) for k in ("id", "rid", "tool", "tool_ref", "search_tiers_used")}
        b = {"skills": []}
        bases = {}
        d["rows"] = []
        for r in example["rows"]:
            r = copy.deepcopy(r)
            for x in r.pop("bounds", []):
                bases[x["basis"]["skill"]] = x["basis"]["inputs"]
            r.pop("interval", None)
            if "basis" in r:
                basis = r.pop("basis")
                bases[basis["skill"]] = basis["inputs"]
                r.update(value=None, source=None, grade=None, value_kind=None)
            if r.get("value") is not None:
                r.pop("grade", None)          # a grade is derived by the pass, not carried by the draft
            d["rows"].append(r)
        for e in example["skills_considered"]:
            b["skills"].append(dict(e, inputs=bases.get(e["skill"], {})) if e["verdict"] == "used" else dict(e))
        rows = [r for r in catalogue.build_index(library)["skills"] if r["kind"] == "bound"]
        sheet = bounds.apply(d, b, rows, run_in(library), example["author"], example["created_at"], sheet_path=path, tree=REPO)
        for name in ("time_step", "weissenberg_number"):
            want = row(example, name)
            got = row(sheet, name)
            for k in ("value", "source", "grade", "value_kind", "basis", "bounds", "interval"):
                self.assertEqual(got.get(k), want.get(k), "%s.%s" % (name, k))
        self.assertEqual(sheet["skills_considered"], example["skills_considered"])
        self.assertIsNone(row(sheet, "max_shear_rate_for_instrument")["value"])

    def test_a_value_skill_writes_nothing_on_a_safety_row(self):
        library = os.path.join(EXAMPLES, "skills")
        rows = [r for r in catalogue.build_index(library)["skills"] if r["kind"] == "bound"]
        d = {"id": "ps-x", "rows": [
            {"name": "relaxation_time", "value": 0.5, "unit": "s", "source": "assumed:x", "value_kind": "estimated"},
            {"name": "shear_rate", "value": 0.5, "unit": "1/s", "source": "assumed:x", "value_kind": "estimated"},
            {"name": "weissenberg_number", "value": None, "unit": "1", "safety_relevant": True}]}
        b = {"skills": [{"skill": "weissenberg_number@v1", "verdict": "used", "why": "both rows are on the sheet",
                         "inputs": {"relaxation_time": "relaxation_time", "shear_rate": "shear_rate"}}]}
        with self.assertRaises(bounds.SafetyRow) as e:
            bounds.apply(d, b, rows, run_in(library), SEAT, NOW)
        self.assertEqual(e.exception.code, "safety_row")


class Command(unittest.TestCase):
    def designer(self, *args):
        return subprocess.run([sys.executable, "-m", "meta_agent.src.designer"] + list(args), cwd=REPO, capture_output=True, text=True,
                              encoding="utf-8", env=ENV)

    def test_bounds_lists_what_a_model_reads_to_bind(self):
        p = self.designer("--bounds", REQ)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("7 bound skill(s) apply to lab_rheometer", p.stdout)
        self.assertIn("shear_rate_max_from_inertia@v1  [max of shear_rate]", p.stdout)
        self.assertNotIn("timestep", p.stdout)

    def test_sheet_writes_once_and_a_second_run_writes_nothing(self):
        tmp, root, dest = scratch_root()
        try:
            p = self.designer("--sheet", dest, "--seat", SEAT, "--now", NOW, "--root", root)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
            self.assertIn("floor shear_rate_min_from_min_speed@v1, ceiling shear_rate_max_from_inertia@v1", p.stdout)
            path = os.path.join(dest, "parameter_sheet.json")
            first = cards.read_text(path)
            p = self.designer("--sheet", dest, "--seat", SEAT, "--now", "2026-11-11T00:00:00Z", "--root", root)
            self.assertIn("nothing written", p.stdout)
            self.assertEqual(cards.read_text(path), first)
            self.assertEqual(sorted(os.listdir(dest)), ["bounds_binding.json", "parameter_sheet.json", "sheet_draft.json"])
            q = subprocess.run([sys.executable, os.path.join(REPO, "contracts", "tools", "sheets.py"), "check", path, tmp],
                               capture_output=True, text=True, encoding="utf-8", env=ENV)
            self.assertEqual((q.returncode, q.stdout.strip()), (0, "nothing to say"))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_changed_binding_is_the_next_revision_and_the_first_stays(self):
        tmp, root, dest = scratch_root()
        try:
            self.designer("--sheet", dest, "--seat", SEAT, "--now", NOW, "--root", root)
            b = cards.load_json(os.path.join(dest, "bounds_binding.json"))
            b["skills"][-1].update(verdict="not_applied", why="the fixture sample is a solution; it carries no particles")
            cards.write_json(os.path.join(dest, "v2_bounds_binding.json"), b)
            first = cards.read_text(os.path.join(dest, "parameter_sheet.json"))
            p = self.designer("--sheet", dest, "--seat", SEAT, "--now", NOW, "--root", root)
            self.assertIn("wrote  meta_agent/requests/req-rheo-fixture-001/v2_parameter_sheet.json", p.stdout)
            v2 = cards.load_json(os.path.join(dest, "v2_parameter_sheet.json"))
            self.assertEqual((v2["revision"], v2["supersedes"]), (2, "ps-rheo-fixture-001"))
            self.assertNotIn("bounds", row(v2, "gap"))
            self.assertEqual(cards.read_text(os.path.join(dest, "parameter_sheet.json")), first)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_binding_that_cannot_be_carried_out_is_refused_by_name(self):
        tmp, root, dest = scratch_root()
        try:
            b = cards.load_json(os.path.join(dest, "bounds_binding.json"))
            b["skills"][0]["inputs"]["cone_angle"] = "cone_radius"
            cards.write_json(os.path.join(dest, "bounds_binding.json"), b)
            p = self.designer("--sheet", dest, "--seat", SEAT, "--now", NOW, "--root", root)
            self.assertEqual(p.returncode, 1)
            self.assertIn("refused  wrong_unit", p.stdout)
            self.assertFalse(os.path.exists(os.path.join(dest, "parameter_sheet.json")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class RecordedSheet(unittest.TestCase):
    """The sheet recorded for the fixture rheometer request is what its draft and its binding give."""

    def test_the_record_is_what_the_pass_gives_and_checks_have_nothing_to_say(self):
        _, path = designer.latest_file(REQ, "parameter_sheet.json")
        recorded = cards.load_json(path)
        self.assertEqual(said(recorded), [])
        again = apply()
        for k in ("rows", "skills_considered", "tool_ref", "id", "rid"):
            self.assertEqual(recorded[k], again[k], k)
        iv = row(recorded, "shear_rate")["interval"]
        self.assertEqual((iv["min"], iv["max"]), (2.857e-05, 233.0))
        self.assertTrue(recorded["degraded"] or any(str(r.get("source")).startswith("database:chemicals@") for r in recorded["rows"]))


def fake_chemicals(version="9.9.9"):
    """A stand-in with the two functions the adapter calls; it computes nothing real."""
    pkg = types.ModuleType("chemicals")
    pkg.__version__ = version
    iapws = types.ModuleType("chemicals.iapws")
    iapws.iapws95_rho = lambda T, P: 998.0 + 0.0 * T * P
    viscosity = types.ModuleType("chemicals.viscosity")
    viscosity.mu_IAPWS = lambda T, rho: 0.001 + 0.0 * T * rho
    pkg.iapws, pkg.viscosity = iapws, viscosity
    return {"chemicals": pkg, "chemicals.iapws": iapws, "chemicals.viscosity": viscosity}


class Sources(unittest.TestCase):
    def with_fake(self, version="9.9.9"):
        saved = {k: sys.modules.get(k) for k in ("chemicals", "chemicals.iapws", "chemicals.viscosity")}
        sys.modules.update(fake_chemicals(version))

        def restore():
            for k, v in saved.items():
                if v is None:
                    sys.modules.pop(k, None)
                else:
                    sys.modules[k] = v
        self.addCleanup(restore)

    def lock(self, content):
        tmp = tempfile.mkdtemp(prefix="ma-lock-")
        self.addCleanup(shutil.rmtree, tmp, True)
        path = os.path.join(tmp, "tools.lock.json")
        cards.write_json(path, content)
        return path

    @unittest.skipIf(chemicals_adapter.load()[0] is not None, "chemicals is installed here; the absent path is tested where it is not")
    def test_absent_the_adapter_is_degraded_and_returns_a_gap_not_a_row(self):
        got = chemicals_adapter.water(293.15)
        self.assertEqual(got["rows"], [])
        self.assertEqual(len(got["degraded"]), 1)
        self.assertIn("chemicals is not installed", got["degraded"][0])
        self.assertEqual(got["gaps"][0]["searched"], ["database:chemicals"])
        self.assertIn("pins chemicals in tools.lock.json", got["gaps"][0]["requires"])
        st = chemicals_adapter.status()
        self.assertEqual((st["present"], st["ok"], st["version"]), (False, False, None))

    def test_the_repository_does_not_pin_or_carry_the_package(self):
        self.assertIsNone(chemicals_adapter.pinned_version())
        self.assertFalse(os.path.exists(os.path.join(REPO, "chemicals")))
        self.assertFalse(os.path.exists(os.path.join(META, "chemicals")))

    def test_present_and_pinned_it_returns_two_correlation_rows_with_their_conditions(self):
        self.with_fake()
        got = chemicals_adapter.water(293.15, lock_path=self.lock({"chemicals": {"version": "9.9.9"}}))
        self.assertEqual((got["degraded"], got["gaps"]), ([], []))
        self.assertEqual([r["name"] for r in got["rows"]], ["water_density", "water_viscosity"])
        table = bounds.grade_table()
        for r in got["rows"]:
            self.assertEqual((r["source"], r["value_kind"], r["uncertainty"]), ("database:chemicals@9.9.9", "correlation", None))
            self.assertEqual(table[("database", r["value_kind"])], "E4")
            self.assertEqual(r["conditions"]["temperature"], {"value": 293.15, "unit": "K"})
            self.assertEqual(r["conditions"]["pressure"], {"value": 101325.0, "unit": "Pa"})
        self.assertEqual([r["unit"] for r in got["rows"]], ["kg/m^3", "Pa.s"])

    def test_present_and_not_pinned_the_rows_come_with_a_degraded_line(self):
        self.with_fake()
        got = chemicals_adapter.water(293.15, lock_path=self.lock({}))
        self.assertEqual(len(got["rows"]), 2)
        self.assertIn("does not pin it", got["degraded"][0])
        got = chemicals_adapter.water(293.15, lock_path=self.lock({"chemicals": {"version": "1.0.0"}}))
        self.assertIn("pins 1.0.0", got["degraded"][0])

    def test_glycerol_water_is_a_gap_whether_or_not_the_package_is_there(self):
        for present in (False, True):
            if present:
                self.with_fake()
            got = chemicals_adapter.glycerol_water(293.15, 0.5)
            self.assertEqual(got["rows"], [])
            self.assertIn("no function for the mixture", got["gaps"][0]["reason"])

    def test_the_designer_takes_the_database_row_when_the_source_answers_and_keeps_the_drafts_when_it_does_not(self):
        raw = cards.load_json(os.path.join(REQ, "sheet_draft.json"))
        if chemicals_adapter.load()[0] is None:
            d, degraded = designer.looked_up(raw)
            r = next(x for x in d["rows"] if x["name"] == "sample_viscosity")
            self.assertEqual((r["value"], r["source"]), (0.001, "assumed:water_like_sample_at_room_temperature"))
            self.assertTrue(any("sample_viscosity keeps the draft's value" in line for line in degraded))
            self.assertTrue(all("lookup" not in x for x in d["rows"]))
        self.with_fake()
        d, degraded = designer.looked_up(raw)
        r = next(x for x in d["rows"] if x["name"] == "sample_viscosity")
        self.assertEqual((r["value"], r["source"], r["value_kind"]), (0.001, "database:chemicals@9.9.9", "correlation"))
        self.assertEqual(next(x for x in d["rows"] if x["name"] == "sample_density")["value"], 998.0)
        sheet = bounds.apply(d, binding(), skills(), run_in(), SEAT, NOW, sheet_path=os.path.join(REQ, "parameter_sheet.json"), tree=REPO)
        self.assertEqual(row(sheet, "sample_viscosity")["grade"], "E4")
        self.assertEqual(bound(sheet, "shear_rate", "shear_rate_max_from_inertia@v1")["grade"], "E5")   # the critical number is still assumed

    def test_only_the_adapter_names_the_package(self):
        src = os.path.join(META, "src")
        named = []
        for dirpath, dirnames, filenames in os.walk(src):
            dirnames[:] = [d for d in dirnames if d != "__pycache__" and not d.startswith("template_v")]
            for fn in filenames:
                if fn.endswith(".py") and 'import_module("chemicals' in cards.read_text(os.path.join(dirpath, fn)):
                    named.append(os.path.relpath(os.path.join(dirpath, fn), src).replace(os.sep, "/"))
        self.assertEqual(named, ["sources/chemicals_adapter.py"])

    def test_the_nist_webbook_stub_reads_nothing_and_names_the_page(self):
        got = nist_webbook.lookup("water", "viscosity")
        self.assertEqual((got["rows"], got["degraded"]), ([], []))
        self.assertIn("https://webbook.nist.gov/cgi/cbook.cgi?Name=water&Units=SI", got["gaps"][0]["requires"])
        text = cards.read_text(os.path.join(META, "src", "sources", "nist_webbook.py"))
        for word in ("urllib", "socket", "requests", "http.client", "subprocess"):
            self.assertNotIn("import " + word, text)

    @unittest.skipUnless(chemicals_adapter.load()[0] is not None, "chemicals is not installed: pinning and fetching it is the person's step")
    def test_water_at_twenty_celsius_is_within_one_percent_of_the_handbook_value(self):
        handbook = cards.load_json(os.path.join(HERE, "fixtures", "sources", "water_handbook.json"))
        got = chemicals_adapter.water(handbook["temperature"]["value"])
        mu = next(r for r in got["rows"] if r["name"] == "water_viscosity")["value"]
        self.assertLessEqual(abs(mu - handbook["viscosity"]["value"]) / handbook["viscosity"]["value"], handbook["relative_tolerance"])


if __name__ == "__main__":
    unittest.main()
