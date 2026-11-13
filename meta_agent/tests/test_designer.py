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

    def test_a_second_build_with_the_same_id_is_refused(self):
        with self.assertRaises(FileExistsError):
            designer.run(self.intake, SEAT, "0001", NOW, self.root)

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


if __name__ == "__main__":
    unittest.main()
