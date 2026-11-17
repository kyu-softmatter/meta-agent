"""The Designer on the echo request (tasks/002): S1 to S7 in a scratch copy of meta_agent/.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards, designer
from meta_agent.src.intake import goal as goal_mod
from meta_agent.src.intake import card as intake_card

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
REPO = os.path.dirname(META)
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
SEAT = "meta-office-20261029-1"
NOW = "2026-10-29T19:30:00Z"


def scratch_root():
    """A meta_agent-like tree: the fixture lab's profile and the echo fixture, nothing else."""
    tmp = tempfile.mkdtemp(prefix="ma-designer-")
    root = os.path.join(tmp, "meta_agent")
    shutil.copytree(os.path.join(META, "profiles", "lab-fixture-rich"), os.path.join(root, "profiles", "lab-fixture-rich"))
    shutil.copytree(os.path.join(META, "tests", "fixtures", "echo"), os.path.join(root, "tests", "fixtures", "echo"))
    return tmp, root


def load_intake():
    return cards.load_json(os.path.join(META, "requests", "req-echo-001", "intake.json"))


class EchoRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.root = scratch_root()
        cls.intake = load_intake()
        cls.out = designer.run(cls.intake, SEAT, "0001", NOW, cls.root)
        cls.req = os.path.join(cls.root, "requests", "req-echo-001")
        cls.build_dir = os.path.join(cls.root, "builds", "echo", "0001")
        cls.bundle = os.path.join(cls.build_dir, "bundle")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def card(self, *parts):
        return cards.load_json(os.path.join(*parts))

    def test_goal_has_no_numbers(self):
        goal = self.card(self.req, "agent_goal.json")
        self.assertEqual(goal["numbers"], [])
        self.assertEqual(goal_mod.numbers_in(goal), [])
        self.assertEqual(goal["requested_by"], "human")

    def test_goal_with_a_number_is_refused(self):
        bad = copy.deepcopy(self.intake)
        bad["paragraph"] = "echo the text and expect 5 characters back"
        with self.assertRaises(ValueError):
            goal_mod.make_goal(bad, SEAT, NOW)

    def test_profile_claims_are_documentary_and_runtime_is_a_gap(self):
        tp = self.card(self.req, "tool_profile.json")
        self.assertTrue(all(c["basis"] == "documentation" for c in tp["claims"]))
        self.assertTrue(all(c["evidence"] for c in tp["claims"] if c["kind"] != "unknown"))
        self.assertTrue(all(c.get("requires") for c in tp["claims"] if c["kind"] == "unknown"))
        reasons = {g["reason"] for g in tp["gaps"]}
        self.assertIn("permission_required", reasons)
        self.assertNotIn("runtime", {c["basis"] for c in tp["claims"]})
        self.assertIsNone(tp["analysis_permission"])

    def test_recall_leaves_gaps_naming_where_it_looked(self):
        g2 = self.card(self.req, "v2_agent_goal.json")
        self.assertEqual(g2["revision"], 2)
        self.assertEqual(g2["supersedes"], "goal-echo-001")
        self.assertTrue(g2["case_refs"] or g2["case_gaps"])
        self.assertTrue(all(g["searched"] for g in g2["case_gaps"] + g2["kb_gaps"]))
        brief = self.card(self.req, "knowledge_brief.json")
        self.assertTrue(brief["kb_version"].startswith("kb@"))

    def test_six_axes_synthesis_and_spec(self):
        for n in range(1, 7):
            a = self.card(self.req, "spec_a%d.json" % n)
            self.assertEqual(a["axis"], "A%d" % n)
            self.assertTrue(a["reads"])
        spec = self.card(self.req, "agent_spec.json")
        self.assertEqual(spec["held"], [])
        self.assertEqual(spec["status"], "validated")
        self.assertEqual(sorted(spec["axis_refs"]), ["A1", "A2", "A3", "A4", "A5", "A6"])

    def test_template_is_materialised_under_its_hash(self):
        name = self.out["template"]
        self.assertRegex(name, r"^agent@[0-9a-f]{12}$")
        tdir = os.path.join(self.root, "templates", name)
        for rel in ("CLAUDE.md", ".claude/settings.json", "src/gate.py", "src/replay.py", "src/validate_tasks.py",
                    "envelope/safety.json", "tools/.gitkeep", "validation/interface/.gitkeep", "replay/.gitkeep"):
            self.assertTrue(os.path.exists(os.path.join(tdir, rel)), rel)
        self.assertEqual(cards.load_json(os.path.join(tdir, "envelope", "safety.json")), {})

    def test_bundle_surface_and_hash(self):
        for rel in ("CLAUDE.md", ".claude/settings.json", "CAPABILITIES.json", "envelope/safety.json", "envelope/snapshot.json",
                    "envelope/parameters.json", "tasks/001-start.md", "failures.jsonl", "src/gate.py", "src/run_tool.py",
                    "tools/echo/tool.json", "tools/echo/adapter.py", "tools/echo/errors/invalid_input.json",
                    "validation/interface/if-1.json", "validation/scientific/sci-1.json", "replay/rp-001.json"):
            self.assertTrue(os.path.exists(os.path.join(self.bundle, rel)), rel)
        build = self.card(self.build_dir, "build.json")
        self.assertEqual(build["bundle_sha256"], cards.sha256_tree(self.bundle))
        self.assertEqual(build["template_version"], self.out["template"])
        self.assertIsNone(build["landed_at"])
        self.assertEqual(build["gate_verdict"]["interface"], "pass")
        self.assertEqual(build["gate_verdict"]["scientific"], "undecided")
        self.assertTrue(os.path.exists(os.path.join(self.build_dir, build["diff_from_template"])))
        claude = cards.read_text(os.path.join(self.bundle, "CLAUDE.md"))
        self.assertNotIn("{{", claude)
        self.assertIn("### `echo`", claude)

    def test_capabilities_carry_no_inferred_claim(self):
        cap = self.card(self.bundle, "CAPABILITIES.json")
        self.assertTrue(cap["observed"])
        self.assertTrue(all(c["kind"] == "observed" for c in cap["observed"]))
        self.assertTrue(all(c["kind"] == "derived" for c in cap["derived"]))
        self.assertFalse(any(c.get("kind") == "inferred" for c in cap["observed"] + cap["derived"] + cap["unverified"]))
        self.assertTrue(any("maximum message length" in g["what"] for g in cap["gaps"]))

    def test_validation_report_reads_the_gates(self):
        vr = self.card(self.build_dir, "validation_report.json")
        self.assertEqual(vr["environment"], "mock")
        self.assertEqual([t["verdict"] for t in vr["interface"]["tasks"]], ["pass", "pass", "pass"])
        sci = vr["scientific"]["tasks"]
        self.assertEqual(len(sci), 1)
        self.assertEqual(sci[0]["verdict"], "not_run")
        self.assertIsNone(sci[0]["tolerance"])
        self.assertIn("undecided", sci[0]["reason"])
        self.assertEqual(vr["overall"], "undecided")
        self.assertEqual(sorted(n["name"] for n in vr["numbers"]), ["sci1_agreement", "sci1_reference_count"])

    def test_bundle_runs_alone_in_a_fresh_process(self):
        env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        env.pop("PYTHONPATH", None)
        p = subprocess.run([sys.executable, "-I", os.path.join("src", "replay.py")], cwd=self.bundle, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("replay: 2 item(s), 2 as expected, 0 not; OK", p.stdout)
        p = subprocess.run([sys.executable, "-I", os.path.join("src", "gate.py"), "--self-check"], cwd=self.bundle, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_a_second_run_from_the_intake_is_stopped_and_writes_nothing(self):
        before = cards.sha256_tree(self.root)
        with self.assertRaises(designer.Stopped) as e:
            designer.run(self.intake, SEAT, "0001", NOW, self.root)
        self.assertIn("has its specification already", str(e.exception))
        self.assertEqual(cards.sha256_tree(self.root), before)

    def test_a_person_s_tolerance_makes_the_scientific_gate_decide(self):
        decided = copy.deepcopy(self.intake)
        decided["scientific_tasks"][0]["tolerance"] = {"value": 0, "unit": "1", "chosen_by": "human"}
        decided["scientific_tasks"][0]["expected_verdict"] = "pass"
        tmp, root = scratch_root()
        try:
            out = designer.run(decided, SEAT, "0002", NOW, root)
            self.assertEqual(out["gates"], {"interface": "pass", "scientific": "pass", "overall": "pass"})
            build = cards.load_json(os.path.join(root, "builds", "echo", "0002", "build.json"))
            self.assertEqual(build["status"], "validated")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_the_rows_an_intake_names_reach_the_axes_and_the_report_says_where_the_gates_ran(self):
        """Test run 20261116-4: the Designer handed neither the parameter rows nor the safety rows of an intake to
        the A4 and A5 axes, so a tool that needs the gate was held for want of a safety row the intake had named."""
        gated = copy.deepcopy(self.intake)
        gated["tool_contract"].update(side_effects="runs_process", errors=["invalid_input", "refused_by_safety"],
                                      safety_gate={"required": True, "place": "src/gate.py reads envelope/safety.json before the call"})
        gated["safety_rows"] = [{"name": "longest_message", "unit": "count"}]
        gated["parameter_rows"] = [{"name": "message_length", "value": None, "unit": "count"}]
        for item in gated["interface_tasks"] + gated["replay_items"]:
            item["expected"] = {"error": {"category": "refused_by_safety", "code": "GATE-SAFETY-001"}}
        tmp, root = scratch_root()
        try:
            out = designer.run(gated, SEAT, "0001", NOW, root)
            req = os.path.join(root, "requests", "req-echo-001")
            self.assertEqual(cards.load_json(os.path.join(req, "spec_a5.json"))["content"]["rows"], gated["safety_rows"])
            self.assertEqual(cards.load_json(os.path.join(req, "spec_a4.json"))["content"]["rows"], gated["parameter_rows"])
            self.assertEqual(out["held"], [])          # a safety row is named, so nothing is held for want of one
            bundle = os.path.join(root, "builds", "echo", "0001", "bundle")
            self.assertEqual(cards.load_json(os.path.join(bundle, "envelope", "safety.json")), {"longest_message": None})
            self.assertEqual(out["gates"]["interface"], "pass")     # the refusal the tasks expect is the refusal they got
            report = cards.load_json(os.path.join(root, "builds", "echo", "0001", "validation_report.json"))
            self.assertEqual(report["environment"], "mock")         # no contract names an external program
            # the same request specified again from the same intake keeps the rows: nothing differs
            cards.write_json(os.path.join(req, "intake.json"), gated)
            self.assertEqual(designer.respecify(req, SEAT, NOW, root), [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        without = copy.deepcopy(gated)
        del without["safety_rows"]
        tmp, root = scratch_root()
        try:
            out = designer.run(without, SEAT, "0001", NOW, root)
            self.assertEqual(len(out["held"]), 1)      # as before: a gate with no safety row named is held
            self.assertIn("no safety row is named", str(out["held"][0]))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        external = copy.deepcopy(self.intake)
        external["tool_contract"]["calls_external"] = {"program": "echo", "license": "none stated", "bundled": False}
        tmp, root = scratch_root()
        try:
            designer.run(external, SEAT, "0001", NOW, root)
            report = cards.load_json(os.path.join(root, "builds", "echo", "0001", "validation_report.json"))
            self.assertEqual(report["environment"], "sandbox")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_validator_accepts_the_scratch_tree(self):
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertIn("0 failed, 0 pending", p.stdout, p.stdout + p.stderr)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_without_a_store_the_goal_and_the_two_axes_name_where_recall_looked(self):
        for name in ("v2_agent_goal.json", "spec_a4.json", "spec_a5.json"):
            c = self.card(self.req, name)
            self.assertEqual(c["case_refs"], [], name)
            self.assertEqual(len(c["case_gaps"]), 1, name)
            self.assertEqual(c["case_gaps"][0]["searched"][0], "meta_agent/cases (absent) (0 case(s) read)", name)
            self.assertTrue(c["case_gaps"][0]["searched"][1].startswith("level 1, the signature: science_task="), name)
        a4 = self.card(self.req, "spec_a4.json")["case_gaps"][0]["searched"][1]
        self.assertIn("parameter_names=message", a4)


class EchoRequestWithAStore(unittest.TestCase):
    """S3 with cases to find (tasks/006): the fixture store stands where meta_agent/cases/ would."""

    @staticmethod
    def run_once():
        tmp, root = scratch_root()
        shutil.copytree(os.path.join(META, "tests", "fixtures", "cases"), os.path.join(root, "cases"))
        designer.run(load_intake(), SEAT, "0001", NOW, root)
        return tmp, root

    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.root = cls.run_once()
        cls.req = os.path.join(cls.root, "requests", "req-echo-001")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_the_goal_carries_the_case_recall_found(self):
        g2 = cards.load_json(os.path.join(self.req, "v2_agent_goal.json"))
        self.assertEqual(g2["case_gaps"], [])
        self.assertEqual([r["id"] for r in g2["case_refs"]], ["case-fx-echo-length"])
        ref = g2["case_refs"][0]
        self.assertEqual(ref["path"], "meta_agent/cases/case-fx-echo-length.json")
        self.assertEqual(ref["hash"], "sha256:" + cards.sha256_file(os.path.join(self.root, "cases", "case-fx-echo-length.json")))
        self.assertTrue(ref["note"].startswith("level 1 (weight 6: science_task, executes); cue: a tool reports a count"))

    def test_a4_searches_with_the_tool_s_parameters_and_a5_with_the_safety_rows(self):
        a4 = cards.load_json(os.path.join(self.req, "spec_a4.json"))
        self.assertIn("weight 8: science_task, executes, parameter_names", a4["case_refs"][0]["note"])
        a5 = cards.load_json(os.path.join(self.req, "spec_a5.json"))
        self.assertIn("weight 6: science_task, executes", a5["case_refs"][0]["note"])

    def test_a_second_run_writes_an_identical_goal(self):
        tmp, root = self.run_once()
        try:
            for name in ("v2_agent_goal.json", "spec_a4.json", "spec_a5.json"):
                first = cards.read_text(os.path.join(self.req, name))
                second = cards.read_text(os.path.join(root, "requests", "req-echo-001", name))
                self.assertEqual(first, second, name)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_validator_accepts_a_goal_with_case_refs(self):
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True,
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertIn("0 failed, 0 pending", p.stdout, p.stdout + p.stderr)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        checks = re.search(r"checks run \[([^\]]*)\]", p.stdout).group(1)
        self.assertIn("5", [c.strip() for c in checks.split(",")])


class Rebuild(unittest.TestCase):
    """--rebuild: S5 and S6 again on a request that exists, as a new build, with no request card written."""

    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.root = scratch_root()
        designer.run(load_intake(), SEAT, "0001", NOW, cls.root)
        cls.req = os.path.join(cls.root, "requests", "req-echo-001")
        shutil.copy(os.path.join(META, "requests", "req-echo-001", "intake.json"), os.path.join(cls.req, "intake.json"))
        cls.first = os.path.join(cls.root, "builds", "echo", "0001")
        cls.before = (cards.sha256_tree(cls.req), cards.sha256_tree(cls.first))
        cls.out = designer.rebuild(cls.req, "meta-macbook-20261112-1", None, "2026-11-12T12:00:00Z", cls.root)
        cls.second = os.path.join(cls.root, "builds", "echo", "0002")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_it_is_the_next_build_and_names_its_parent(self):
        build = cards.load_json(os.path.join(self.second, "build.json"))
        self.assertEqual((build["id"], build["lineage"]["parent_build"]), ("build-echo-0002", "build-echo-0001"))
        self.assertEqual(build["spec_ref"], cards.load_json(os.path.join(self.req, "agent_spec.json"))["id"])
        self.assertEqual(build["bundle_path"], "meta_agent/builds/echo/0002/bundle")
        self.assertEqual(build["bundle_sha256"], cards.sha256_tree(os.path.join(self.second, "bundle")))
        self.assertEqual(build["template_version"], self.out["template"])
        self.assertIn("rebuilt from spec-echo-001 revision", build["note"])
        self.assertIsNone(build["landed_at"])
        self.assertEqual(self.out["files"], ["meta_agent/builds/echo/0002/bundle/", "meta_agent/builds/echo/0002/diff_from_template.txt",
                                             "meta_agent/builds/echo/0002/validation_report.json",
                                             "meta_agent/builds/echo/0002/build.json"])

    def test_the_request_and_the_first_build_are_as_they_were(self):
        self.assertEqual((cards.sha256_tree(self.req), cards.sha256_tree(self.first)), self.before)

    def test_the_gates_are_read_off_the_new_bundle(self):
        self.assertEqual(self.out["gates"], {"interface": "pass", "scientific": "undecided", "overall": "undecided"})
        self.assertTrue(self.out["replay_ok"])
        vr = cards.load_json(os.path.join(self.second, "validation_report.json"))
        self.assertEqual(vr["id"], "vr-echo-0002")
        self.assertEqual(vr["id"], cards.load_json(os.path.join(self.second, "build.json"))["gate_verdict"]["validation_report_ref"])

    def test_the_new_bundle_and_the_tree_pass_the_validator(self):
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, VALIDATE, "--bundle", os.path.join(self.second, "bundle")], capture_output=True,
                           text=True, env=env, cwd=REPO)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(p.stdout.strip().splitlines()[-1].startswith("VERDICT PASS mode=bundle"), p.stdout)
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("bundles=2 failed=0 pending=0", p.stdout.strip().splitlines()[-1])

    def test_a_build_id_that_exists_is_refused_and_nothing_is_written(self):
        with self.assertRaises(FileExistsError):
            designer.rebuild(self.req, SEAT, "0001", NOW, self.root)
        with self.assertRaises(ValueError):
            designer.rebuild(self.req, SEAT, "two", NOW, self.root)
        self.assertEqual(sorted(os.listdir(os.path.join(self.root, "builds", "echo"))), ["0001", "0002"])

    def test_a_request_with_no_build_is_refused(self):
        tmp, root = scratch_root()
        try:
            req = os.path.join(root, "requests", "req-echo-001")
            shutil.copytree(self.req, req)
            with self.assertRaises(FileNotFoundError) as e:
                designer.rebuild(req, SEAT, None, NOW, root)
            self.assertIn("a first build is made with --intake", str(e.exception))
            self.assertFalse(os.path.exists(os.path.join(root, "builds")))
            self.assertFalse(os.path.exists(os.path.join(root, "templates")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class RecallAgain(unittest.TestCase):
    """--recall on a request that exists: the next revision when the store changed the answer, else nothing."""

    def test_the_next_revision_is_written_once(self):
        tmp, root = scratch_root()
        try:
            designer.run(load_intake(), SEAT, "0001", NOW, root)
            req = os.path.join(root, "requests", "req-echo-001")
            self.assertIsNone(designer.recall_again(req, SEAT, NOW, root))          # no store: the gap stands
            shutil.copytree(os.path.join(META, "tests", "fixtures", "cases"), os.path.join(root, "cases"))
            path = designer.recall_again(req, SEAT, "2026-11-09T12:00:00Z", root)
            self.assertEqual(os.path.basename(path), "v3_agent_goal.json")
            g3 = cards.load_json(path)
            self.assertEqual((g3["revision"], g3["supersedes"], g3["created_at"]), (3, "goal-echo-001", "2026-11-09T12:00:00Z"))
            self.assertEqual([r["id"] for r in g3["case_refs"]], ["case-fx-echo-length"])
            self.assertEqual(g3["case_gaps"], [])
            self.assertIsNone(designer.recall_again(req, SEAT, "2026-11-09T13:00:00Z", root))
            self.assertEqual(designer.latest_goal(req)[0], 3)
            p = subprocess.run([sys.executable, VALIDATE, tmp, "--strict"], capture_output=True, text=True,
                               env=dict(os.environ, PYTHONUTF8="1"))
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class Respecify(unittest.TestCase):
    """--respecify: S4 again on a request whose intake was revised, here the echo request, a kind that is not
    rheology (the rheometer fixture's own revision is the record under requests/req-rheo-fixture-001)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp, cls.root = scratch_root()
        designer.run(load_intake(), SEAT, "0001", NOW, cls.root)
        cls.req = os.path.join(cls.root, "requests", "req-echo-001")
        shutil.copy(os.path.join(META, "requests", "req-echo-001", "intake.json"), os.path.join(cls.req, "intake.json"))
        cls.nothing = designer.respecify(cls.req, SEAT, NOW, cls.root)
        cls.before = cards.sha256_tree(cls.req)
        revised = load_intake()
        revised["tool_contract"]["outputs"]["properties"]["echoed_at"] = {"description": "declared for this test and returned by nothing"}
        revised["tool_contract"]["outputs"]["properties"]["length"]["unit"] = "character"
        cards.write_json(os.path.join(cls.req, "v2_intake.json"), revised)
        cls.written = designer.respecify(cls.req, "meta-macbook-20261116-1", "2026-11-16T12:00:00Z", cls.root)
        cls.again = designer.respecify(cls.req, "meta-macbook-20261116-1", "2026-11-16T13:00:00Z", cls.root)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_an_intake_that_was_not_revised_writes_nothing(self):
        self.assertEqual(self.nothing, [])

    def test_only_what_differs_is_written_as_the_next_revision(self):
        self.assertEqual([os.path.basename(p) for p in self.written], ["v2_spec_a2.json", "v2_synthesis.json", "v2_agent_spec.json"])
        self.assertEqual(self.again, [])
        a2 = cards.load_json(os.path.join(self.req, "v2_spec_a2.json"))
        self.assertEqual((a2["revision"], a2["supersedes"], a2["author"]), (2, "spec-echo-001-a2", "meta-macbook-20261116-1"))
        self.assertEqual(a2["content"]["callable_tools"][0]["outputs"], ["echoed_at", "length", "message"])
        spec = cards.load_json(os.path.join(self.req, "v2_agent_spec.json"))
        self.assertEqual((spec["revision"], spec["supersedes"]), (2, "spec-echo-001"))
        self.assertEqual(spec["axis_refs"], {"A1": "spec_a1.json", "A2": "v2_spec_a2.json", "A3": "spec_a3.json",
                                             "A4": "spec_a4.json", "A5": "spec_a5.json", "A6": "spec_a6.json"})
        self.assertEqual(spec["synthesis_ref"], "v2_synthesis.json")
        self.assertEqual(cards.load_json(os.path.join(self.req, "v2_synthesis.json"))["axis_refs"],
                         ["spec_a1.json", "v2_spec_a2.json", "spec_a3.json", "spec_a4.json", "spec_a5.json", "spec_a6.json"])
        first = cards.load_json(os.path.join(self.req, "spec_a1.json"))["content"]["directory"]
        self.assertEqual(first, "meta_agent/builds/echo/0001/bundle")

    def test_no_earlier_card_is_touched(self):
        tmp = tempfile.mkdtemp(prefix="ma-respecify-")
        try:
            kept = os.path.join(tmp, "req")
            shutil.copytree(self.req, kept)
            for name in os.listdir(kept):
                if name.startswith("v2_") and name != "v2_agent_goal.json":
                    os.remove(os.path.join(kept, name))
            self.assertEqual(cards.sha256_tree(kept), self.before)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_a_rebuild_reads_the_latest_intake_and_specification(self):
        out = designer.rebuild(self.req, "meta-macbook-20261116-1", None, "2026-11-16T14:00:00Z", self.root)
        build_dir = os.path.join(self.root, "builds", "echo", "0002")
        build = cards.load_json(os.path.join(build_dir, "build.json"))
        self.assertIn("rebuilt from spec-echo-001 revision 2, unchanged, and the intake's revision 2", build["note"])
        contract = cards.load_json(os.path.join(build_dir, "bundle", "tools", "echo", "tool.json"))
        self.assertIn("echoed_at", contract["outputs"]["properties"])
        text = cards.read_text(os.path.join(build_dir, "bundle", "CLAUDE.md"))
        self.assertIn("`length` (integer, character)", text)
        self.assertIn("`echoed_at` (any; declared for this test and returned by nothing)", text)
        cap = cards.load_json(os.path.join(build_dir, "bundle", "CAPABILITIES.json"))
        self.assertEqual(cap["held"], [])
        self.assertEqual(cap["source"], "the documentation of echo (README.md), as the builder read it; the document is not in this directory")
        self.assertEqual([i for k in ("observed", "derived", "unverified") for i in cap[k] if "not_here" in i], [])
        self.assertTrue(out["replay_ok"])
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, VALIDATE, "--bundle", os.path.join(build_dir, "bundle")], capture_output=True,
                           text=True, env=env, cwd=REPO)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_a_request_that_was_never_specified_is_refused(self):
        tmp, root = scratch_root()
        try:
            req = os.path.join(root, "requests", "req-echo-001")
            cards.write_json(os.path.join(req, "intake.json"), load_intake())
            with self.assertRaises(FileNotFoundError):
                designer.respecify(req, SEAT, NOW, root)
            self.assertEqual(os.listdir(req), ["intake.json"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def echo_card_draft():
    """The echo request as a draft of the intake card: its record, less the rid, with the person's words."""
    draft = {k: v for k, v in load_intake().items() if k != "rid"}
    draft["persons_words"] = {"verbatim": "An agent that returns what it is given, to try the pipeline on.", "date": "2026-10-29"}
    draft["questions_for_the_person"] = []
    # the card's schema names no gap_reason on a row of the reading, which the record carries on one row
    draft["tool_reading"] = [{k: v for k, v in row.items() if k != "gap_reason"} for row in draft["tool_reading"]]
    return draft


class FromAnIntakeCard(unittest.TestCase):
    """--intake on the request's first card: the stage decides whether the Designer runs, a goal that exists is
    kept, and a lab whose policy is open is met with its questions before anything is written."""

    def setUp(self):
        self.tmp, self.root = scratch_root()
        self.req = os.path.join(self.root, "requests", "req-echo-001")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def specified(self):
        path, card = intake_card.write(self.req, "req-echo-001", echo_card_draft(), SEAT, NOW)
        self.assertEqual((os.path.basename(path), card["stage"], card["revision"]), ("intake.json", "specified", 1))
        return path, card

    def test_a_specified_card_is_built_from_and_the_tree_passes_the_validator(self):
        path, card = self.specified()
        out = designer.run(card, SEAT, "0001", NOW, self.root, intake_path=path)
        self.assertEqual(out["gates"], {"interface": "pass", "scientific": "undecided", "overall": "undecided"})
        self.assertEqual(out["kept"], [])
        self.assertTrue(os.path.isfile(os.path.join(self.req, "agent_goal.json")))
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_a_card_at_reading_stops_the_designer_with_its_questions(self):
        draft = {k: v for k, v in echo_card_draft().items() if k not in ("tool_contract", "error_contracts", "interface_tasks",
                                                                         "scientific_tasks", "replay_items")}
        draft["questions_for_the_person"] = [{"n": 1, "needed_before": "the goal", "question": "Is the reading right?"}]
        path, card = intake_card.write(self.req, "req-echo-001", draft, SEAT, NOW)
        self.assertEqual(card["stage"], "reading")
        with self.assertRaises(designer.Stopped) as e:
            designer.run(card, SEAT, "0001", NOW, self.root, intake_path=path)
        self.assertIn("is at the stage reading", str(e.exception))
        self.assertIn("question 1, needed before the goal: Is the reading right?", str(e.exception))
        self.assertEqual(os.listdir(self.req), ["intake.json"])
        self.assertFalse(os.path.exists(os.path.join(self.root, "builds")))
        p = subprocess.run([sys.executable, "-m", "meta_agent.src.designer", "--intake", path, "--seat", SEAT, "--root", self.root],
                           cwd=REPO, capture_output=True, text=True, env=dict(os.environ, PYTHONUTF8="1"))
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("nothing was written", p.stdout)

    def test_a_goal_that_exists_is_kept_and_the_recall_is_its_next_revision(self):
        path, card = self.specified()
        goal = goal_mod.make_goal(card, "meta-macbook-20261116-1", "2026-11-16T09:00:00Z")
        goal["priorities"] = ["the person's own order", "small bundle"]
        cards.write_json(os.path.join(self.req, "agent_goal.json"), goal)
        with open(os.path.join(self.req, "agent_goal.json"), "rb") as f:
            before = f.read()
        out = designer.run(card, SEAT, "0001", NOW, self.root, intake_path=path)
        with open(os.path.join(self.req, "agent_goal.json"), "rb") as f:
            self.assertEqual(f.read(), before)
        self.assertEqual(out["kept"], ["meta_agent/requests/req-echo-001/agent_goal.json"])
        self.assertNotIn("meta_agent/requests/req-echo-001/agent_goal.json", out["files"])
        second = cards.load_json(os.path.join(self.req, "v2_agent_goal.json"))
        self.assertEqual((second["revision"], second["supersedes"], second["priorities"]),
                         (2, goal["id"], ["the person's own order", "small bundle"]))
        self.assertTrue(second["case_refs"] or second["case_gaps"])

    def test_a_lab_whose_policy_is_open_is_met_with_its_questions(self):
        lab = os.path.join(self.root, "profiles", "lab-fixture-rich")
        for name in ("v2_lab_profile.json", "v2_onboarding_record.json"):
            os.remove(os.path.join(lab, name))
        path, card = self.specified()
        with self.assertRaises(designer.Stopped) as e:
            designer.run(card, SEAT, "0001", NOW, self.root, intake_path=path)
        said = str(e.exception)
        self.assertIn("policy field(s) no person has confirmed", said)
        record = cards.load_json(os.path.join(lab, "onboarding_record.json"))
        for q in record["questions"]:
            self.assertIn("%s: %s" % (q["field"], q["question"]), said)
        self.assertIn("python -m meta_agent.src.onboarding --lab-id lab-fixture-rich", said)
        self.assertEqual(os.listdir(self.req), ["intake.json"])
        self.assertEqual(designer.open_policy(self.root, "a-lab-this-tree-does-not-hold"), None)

    def test_a_request_whose_latest_intake_went_back_to_reading_is_not_specified_or_built_again(self):
        path, card = self.specified()
        designer.run(card, SEAT, "0001", NOW, self.root, intake_path=path)
        intake_card.write(self.req, "req-echo-001", {"tool_contract": None}, SEAT, NOW, note="the contract is withdrawn for this test")
        before = cards.sha256_tree(self.root)
        for again in (designer.respecify, designer.rebuild):
            with self.assertRaises(designer.Stopped) as e:
                again(self.req, SEAT, now=NOW, root=self.root)
            self.assertIn("is at the stage reading", str(e.exception))
        self.assertEqual(cards.sha256_tree(self.root), before)

    def test_an_intake_that_is_not_the_latest_is_not_run(self):
        path, card = self.specified()
        newer, _ = intake_card.write(self.req, "req-echo-001", {"priorities": ["small bundle"]}, SEAT, NOW, note="the person's word")
        self.assertEqual(os.path.basename(newer), "v2_intake.json")
        with self.assertRaises(designer.Stopped) as e:
            designer.run(card, SEAT, "0001", NOW, self.root, intake_path=path)
        self.assertIn("is not the latest intake", str(e.exception))


class ExecutionPermission(unittest.TestCase):
    """The person, 2026-11-16 (docs/ideas/20261116.md): a tool that starts an engine or writes files opens by the lab's
    confirmed execution permission. The Designer copies the level from the profile a build names into
    envelope/execution_permission.json, and writes none where the profile carries the permission as words."""

    LAB = "lab-kyu-softmatter"

    def setUp(self):
        self.tmp, self.root = scratch_root()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        shutil.copytree(os.path.join(META, "profiles", self.LAB), os.path.join(self.root, "profiles", self.LAB))

    def intake(self, lab, effects="runs_process", expect=None, installs=None):
        i = copy.deepcopy(load_intake())
        i["lab_profile_ref"] = lab
        i["tool_contract"].update(side_effects=effects, errors=["invalid_input", "refused_by_safety"],
                                  safety_gate={"required": True, "place": "src/gate.py, consulted by src/run_tool.py before the call",
                                               "opens_by": "execution_permission"})
        if installs:
            i["tool_contract"]["installs_from"] = installs
        if expect:
            for item in i["interface_tasks"] + i["replay_items"] + i["scientific_tasks"]:
                item["expected"] = {"error": {"category": "refused_by_safety", "code": expect}}
                if "measure" in item:
                    item.update(expected_verdict="not_run")
        return i

    def test_the_level_is_copied_from_the_profile_and_words_give_none(self):
        p = designer.execution_permission(META, self.LAB)
        self.assertEqual((p["reaches"], p["confirmed_by"], p["lab_profile_ref"]), ("engine", "human", self.LAB))
        latest = designer.latest_file(os.path.join(META, "profiles", self.LAB), "lab_profile.json")[1]
        self.assertEqual(p["profile_revision"], cards.load_json(latest)["revision"])
        self.assertEqual(p["package_sources"], [{"installer": "pixi", "channel": "conda-forge"}])
        self.assertIsNone(designer.execution_permission(META, "lab-fixture-rich"))     # its profile has words only
        # an earlier revision with words only gives none either: the level is never read off the sentence
        words_only = os.path.join(self.tmp, "words")
        os.makedirs(os.path.join(words_only, "profiles", self.LAB))
        shutil.copy(os.path.join(META, "profiles", self.LAB, "v2_lab_profile.json"),
                    os.path.join(words_only, "profiles", self.LAB, "v2_lab_profile.json"))
        self.assertIsNone(designer.execution_permission(words_only, self.LAB))

    def test_an_engine_tool_is_built_open_on_the_lab_s_permission_and_the_tree_passes(self):
        for effects, installs in (("runs_process", None), ("writes_files", None),
                                  ("network", {"installer": "pixi", "channel": "conda-forge"})):
            tmp, root = scratch_root()
            try:
                shutil.copytree(os.path.join(META, "profiles", self.LAB), os.path.join(root, "profiles", self.LAB))
                out = designer.run(self.intake(self.LAB, effects, installs=installs), SEAT, "0001", NOW, root)
                bundle = os.path.join(root, "builds", "echo", "0001", "bundle")
                perm = cards.load_json(os.path.join(bundle, "envelope", "execution_permission.json"))
                self.assertEqual(perm, designer.execution_permission(root, self.LAB))
                self.assertEqual(out["held"], [], effects)                   # no safety row is asked of such a tool
                self.assertEqual(out["gates"]["interface"], "pass", effects)  # the calls ran: the gate opened
                a5 = cards.load_json(os.path.join(root, "requests", "req-echo-001", "spec_a5.json"))["content"]
                self.assertIn("execution_permission.json", a5["gate"])
                p = subprocess.run([sys.executable, VALIDATE, tmp, "--strict"], capture_output=True, text=True,
                                   env=dict(os.environ, PYTHONUTF8="1"))
                self.assertIn("0 failed, 0 pending", p.stdout, p.stdout + p.stderr)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

    def test_an_install_from_a_source_the_lab_did_not_allow_stops_the_designer(self):
        for installs in ({"installer": "pip", "channel": "pypi"}, None):
            with self.assertRaises(designer.Stopped) as e:
                designer.run(self.intake(self.LAB, "network", installs=installs), SEAT, "0001", NOW, self.root)
            self.assertIn("pip/pypi, which the lab's permission does not list" if installs else "names no installs_from",
                          str(e.exception))
            self.assertFalse(os.path.exists(os.path.join(self.root, "requests")))

    def test_what_an_intake_holds_is_held_by_the_specification(self):
        """Round three of the clone test: a request held a capability (a step the person had not allowed) that the
        Designer had no place to carry."""
        i = self.intake(self.LAB)
        i["held"] = [{"item": "tool engine_gpu", "reason": "no GPU on this computer; the person has not said"}, "a second engine"]
        out = designer.run(i, SEAT, "0001", NOW, self.root)
        spec = cards.load_json(os.path.join(self.root, "requests", "req-echo-001", "agent_spec.json"))
        for item in i["held"]:
            self.assertIn(item, spec["held"])
            self.assertIn(item, out["held"])
        self.assertEqual(spec["status"], "held")

    def test_a_lab_with_words_only_stops_the_designer_and_nothing_is_written(self):
        with self.assertRaises(designer.Stopped) as e:
            designer.run(self.intake("lab-fixture-rich"), SEAT, "0001", NOW, self.root)
        self.assertIn("no level a person confirmed", str(e.exception))
        self.assertFalse(os.path.exists(os.path.join(self.root, "requests")))
        self.assertFalse(os.path.exists(os.path.join(self.root, "builds")))

    def test_a_level_below_an_engine_is_held_and_the_gate_refuses_naming_it(self):
        folder = os.path.join(self.root, "profiles", self.LAB)
        rev, path = designer.latest_file(folder, "lab_profile.json")
        lower = cards.load_json(path)
        lower.update(revision=rev + 1, supersedes=lower["id"])
        lower["policy"]["execution_permission"]["value"] = {"reaches": "sandbox", "words": "mock and sandbox"}
        cards.write_json(os.path.join(folder, "v%d_lab_profile.json" % (rev + 1)), lower)
        out = designer.run(self.intake(self.LAB, expect="GATE-PERMISSION-001"), SEAT, "0001", NOW, self.root)
        self.assertEqual(len(out["held"]), 1)
        self.assertIn("the level sandbox, which opens no engine", str(out["held"][0]))
        self.assertEqual(out["gates"]["interface"], "pass")          # every call was refused, as the tasks expect
        bundle = os.path.join(self.root, "builds", "echo", "0001", "bundle")
        self.assertEqual(cards.load_json(os.path.join(bundle, "envelope", "execution_permission.json"))["reaches"], "sandbox")


if __name__ == "__main__":
    unittest.main()
