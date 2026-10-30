"""The Designer on the echo request (tasks/002): S1 to S7 in a scratch copy of meta_agent/.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import copy
import json
import os
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


if __name__ == "__main__":
    unittest.main()
