"""Recall on a fixture store of five hand-written cases (tasks/006).

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

from meta_agent.src.cases import recall as recall_mod
from meta_agent.src.cases import rules
from meta_agent.src.cases import seed_sma

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "fixtures", "cases")
SMA = os.path.join(HERE, "fixtures", "sma")
REPO = os.path.dirname(os.path.dirname(HERE))
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
SEAT = "meta-macbook-20261109-1"
NOW = "2026-11-09T12:00:00Z"
ECHO_TASK = "return the text it is given and report that text's character count"


def ids(result):
    return [h["id"] for h in result["hits"]]


class Recall(unittest.TestCase):
    def search(self, signature):
        return recall_mod.recall(signature, STORE, "meta_agent/tests/fixtures/cases")

    def test_the_fixture_index_is_what_its_cards_give(self):
        self.assertIsNone(rules.index_problem(STORE))
        self.assertEqual(len(recall_mod.load_store(STORE)), 5)

    def test_level_1_finds_the_case_of_the_same_signature(self):
        r = self.search({"science_task": ECHO_TASK, "executes": "analysis"})
        self.assertEqual(r["level"], 1)
        self.assertEqual(ids(r), ["case-fx-echo-length"])
        hit = r["hits"][0]
        self.assertEqual(hit["matched"], ["science_task", "executes"])
        self.assertEqual(hit["weight"], recall_mod.WEIGHTS["science_task"] + recall_mod.WEIGHTS["executes"])
        self.assertTrue(hit["cue"])

    def test_a_scalar_meets_whatever_its_case_and_spacing(self):
        r = self.search({"engine": "  HOOMD ", "executes": "engine"})
        self.assertEqual(ids(r), ["case-fx-shear-range"])

    def test_executes_alone_is_not_a_level_1_hit(self):
        r = self.search({"science_task": "something nobody did", "executes": "engine"})
        self.assertIsNone(r["level"])
        self.assertEqual(r["hits"], [])

    def test_level_2_matches_cause_class_and_executes_alone(self):
        r = self.search({"science_task": "optical trapping stiffness", "executes": "instrument", "cause_class": "unit_mismatch"})
        self.assertEqual(r["level"], 2)
        self.assertEqual(ids(r), ["case-fx-unit-mismatch"])
        self.assertEqual(r["hits"][0]["matched"], ["executes", "cause_class"])

    def test_level_2_needs_both_fields_equal(self):
        r = self.search({"science_task": "optical trapping stiffness", "executes": "engine", "cause_class": "unit_mismatch"})
        self.assertIsNone(r["level"])

    def test_the_class_unknown_meets_nothing(self):
        met = recall_mod.meetings({"cause_class": "unknown", "executes": "none"}, {"cause_class": "unknown", "executes": "none"})
        self.assertEqual(met, {"executes": 1})

    def test_a_miss_is_a_gap_naming_the_signature_searched(self):
        r = self.search({"science_task": "protein folding", "executes": "engine", "engine": "gromacs"})
        self.assertIsNone(r["level"])
        refs, gaps = recall_mod.refs_and_gaps(r)
        self.assertEqual(refs, [])
        self.assertEqual(len(gaps), 1)
        searched = gaps[0]["searched"]
        self.assertIn("meta_agent/tests/fixtures/cases/index.json (5 case(s) read)", searched)
        self.assertIn("level 1, the signature: science_task=protein folding; executes=engine; engine=gromacs", searched)
        self.assertIn("level 2 not searched: the signature states no cause_class", searched)
        self.assertTrue(gaps[0]["requires"])

    def test_an_absent_store_is_a_gap_and_not_an_error(self):
        r = recall_mod.recall({"engine": "hoomd"}, os.path.join(HERE, "fixtures", "no-such", "cases"), "nowhere/cases")
        self.assertEqual(r["store"], "nowhere/cases (absent)")
        refs, gaps = recall_mod.refs_and_gaps(r)
        self.assertEqual(gaps[0]["reason"], "no cases store to search")

    def test_two_runs_give_the_same_bytes(self):
        sig = {"engine": "lammps", "executes": "engine", "methods": ["molecular dynamics"]}
        a = json.dumps(self.search(sig), sort_keys=True)
        b = json.dumps(self.search(sig), sort_keys=True)
        self.assertEqual(a, b)

    def test_a_point_inside_the_range_meets_and_one_outside_does_not(self):
        inside = self.search({"condition_tags": ["shear_rate_1/s:10"]})
        self.assertEqual(ids(inside), ["case-fx-shear-range"])
        self.assertEqual(inside["hits"][0]["matched"], ["condition_tags"])
        outside = self.search({"condition_tags": ["shear_rate_1/s:1e4"]})
        self.assertEqual(outside["hits"], [])
        overlap = self.search({"condition_tags": ["shear_rate_1/s:5e2..5e3"]})
        self.assertEqual(ids(overlap), ["case-fx-shear-range"])
        apart = self.search({"condition_tags": ["shear_rate_1/s:2e3..5e3"]})
        self.assertEqual(apart["hits"], [])
        other_name = self.search({"condition_tags": ["strain_rate_1/s:10"]})
        self.assertEqual(other_name["hits"], [])

    def test_hits_are_ordered_grade_then_supports_then_weight_then_id(self):
        r = self.search({"engine": "lammps"})
        self.assertEqual(ids(r), ["case-fx-lammps-b", "case-fx-lammps-a"])   # E2 before E3, whatever the count

        def hit(cid, grade, supports, weight):
            return {"id": cid, "grade": grade, "supports": supports, "weight": weight}
        ordered = recall_mod.order([hit("d", "E3", 1, 4), hit("c", "E3", 1, 9), hit("b", "E3", 7, 1), hit("a", "E5", 9, 9),
                                    hit("e", "E3", 1, 4)])
        self.assertEqual([h["id"] for h in ordered], ["b", "c", "d", "e", "a"])

    def test_refs_resolve_in_the_index_as_check_5_reads_it(self):
        r = self.search({"science_task": ECHO_TASK, "executes": "analysis"})
        refs, gaps = recall_mod.refs_and_gaps(r)
        self.assertEqual(gaps, [])
        spec = rules.STORES["case_refs"]
        for ref in refs:
            self.assertIsNone(rules.ref_problem(ref, STORE, spec))
            self.assertTrue(ref["note"].startswith("level 1 (weight 6: science_task, executes); cue: "))


class WhatIsNotRecalled(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-cases-")
        self.store = os.path.join(self.tmp, "cases")
        shutil.copytree(STORE, self.store)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rewrite(self, name, change):
        path = os.path.join(self.store, name)
        with open(path, "r", encoding="utf-8") as f:
            case = json.load(f)
        change(case)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(case, f, indent=2, ensure_ascii=False)
            f.write("\n")
        return case

    def reindex(self):
        self.assertEqual(rules.main(["index", self.store]), 0)

    def test_a_stale_index_is_refused(self):
        self.rewrite("case-fx-lammps-a.json", lambda c: c.update(lesson="changed after the index was written"))
        with self.assertRaises(recall_mod.RecallError):
            recall_mod.recall({"engine": "lammps"}, self.store)

    def test_a_dropped_seed_a_superseded_and_a_refused_case_are_not_recalled(self):
        self.rewrite("case-fx-lammps-a.json", lambda c: c["signature"]["condition_tags"].append("seed_verdict:drop"))
        self.rewrite("case-fx-lammps-b.json", lambda c: c.update(superseded_by="case-fx-lammps-a"))
        self.rewrite("case-fx-shear-range.json", lambda c: c.update(status="refused"))
        self.reindex()
        self.assertEqual(recall_mod.recall({"engine": "lammps"}, self.store)["hits"], [])
        self.assertEqual(recall_mod.recall({"engine": "hoomd"}, self.store)["hits"], [])
        self.assertEqual(recall_mod.recall({"engine": "hoomd"}, self.store)["cases_read"], 2)

    def test_only_the_latest_revision_of_an_id_is_recalled(self):
        v2 = self.rewrite("case-fx-lammps-a.json", lambda c: None)
        v2["revision"] = 2
        v2["signature"]["engine"] = "gromacs"
        with open(os.path.join(self.store, "v2_case-fx-lammps-a.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(v2, f, indent=2, ensure_ascii=False)
            f.write("\n")
        self.reindex()
        self.assertEqual(ids(recall_mod.recall({"engine": "lammps"}, self.store)), ["case-fx-lammps-b"])
        hit = recall_mod.recall({"engine": "gromacs"}, self.store)["hits"][0]
        self.assertEqual((hit["id"], hit["revision"]), ("case-fx-lammps-a", 2))


class SeedSma(unittest.TestCase):
    """The seed script on a three-line fixture failures.jsonl, read as files (tasks/006)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-seed-")
        self.out = os.path.join(self.tmp, "cases")
        with open(os.path.join(SMA, "drafts.json"), "r", encoding="utf-8") as f:
            self.drafts = json.load(f)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def case(self, n):
        with open(os.path.join(self.out, "sma", "simulation-%03d.json" % n), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_three_lines_give_three_drafts_with_the_expected_verdicts(self):
        report = seed_sma.seed(SMA, self.out, SEAT, self.drafts, NOW, files=True)
        self.assertEqual(report["written"], ["case-sma-simulation-001", "case-sma-simulation-002", "case-sma-simulation-003"])
        self.assertEqual(report["verdicts"], {"transfer": 1, "downgrade": 1, "drop": 1})
        self.assertEqual([(r["source"], r["lines"]) for r in report["sources"]], [("simulation", 3)])
        one, two, three = self.case(1), self.case(2), self.case(3)
        self.assertEqual([c["signature"]["condition_tags"][-1] for c in (one, two, three)],
                         ["seed_verdict:drop", "seed_verdict:transfer", "seed_verdict:downgrade"])
        self.assertEqual([c["grade"] for c in (one, two, three)], ["E5", "E3", "E5"])
        self.assertEqual([c["kind"] for c in (one, two, three)], ["success", "failure", "failure"])
        for c in (one, two, three):
            self.assertEqual((c["status"], c["cause_status"], c["numbers"], c["cause_class"]), ("draft", "observed", [], "unknown"))
            self.assertEqual((c["source_repo_commit"], c["source_agent"]), ("d68ee7d2", "simulation_agent"))
            self.assertEqual(c["signature"]["executes"], "engine")
            self.assertEqual(c["count"]["supports"], 1)
        self.assertEqual(two["signature"]["engine"], "hoomd")
        self.assertNotIn("engine", one["signature"])
        self.assertEqual(three["signature"]["observables"], ["tracer_diffusivity"])
        self.assertEqual(three["what_happened"], "planned: a fixture: ten frames of tracer_diffusivity data; actual: a fixture: nine frames")
        self.assertEqual(two["what_happened"], "a fixture: the run on hoomd was refused because the time step had no bound")
        self.assertEqual(two["evidence"], [{"kind": "commit", "ref": "soft-matter-agents@d68ee7d2 simulation_agent/failures.jsonl:2"}])
        self.assertEqual(two["cue"], "a fixture cue for line two")
        self.assertEqual(two["count"]["last_seen"], "2026-01-06")
        self.assertIn("Verdict transfer by rule F2", two["note"])
        self.assertIn("Verdict drop by rule F1", one["note"])
        self.assertIn("Verdict downgrade by rule F6", three["note"])

    def test_a_second_run_changes_no_file(self):
        seed_sma.seed(SMA, self.out, SEAT, self.drafts, NOW, files=True)
        path = os.path.join(self.out, "sma", "simulation-002.json")
        with open(path, "rb") as f:
            before = f.read()
        report = seed_sma.seed(SMA, self.out, SEAT, self.drafts, "2026-12-01T00:00:00Z", files=True)
        self.assertEqual(report["written"], [])
        self.assertEqual(len(report["kept"]), 3)
        with open(path, "rb") as f:
            self.assertEqual(f.read(), before)

    def test_a_line_without_a_draft_gets_no_case(self):
        drafts = {k: v for k, v in self.drafts.items() if not k.endswith("002")}
        report = seed_sma.seed(SMA, self.out, SEAT, drafts, NOW, files=True)
        self.assertEqual(report["no_draft"], ["case-sma-simulation-002"])
        self.assertFalse(os.path.exists(os.path.join(self.out, "sma", "simulation-002.json")))

    def test_the_command_writes_the_index_and_the_validator_accepts_the_store(self):
        env = dict(os.environ, PYTHONUTF8="1")
        cmd = [sys.executable, "-m", "meta_agent.src.cases.seed_sma", SMA, "--files", "--seat", SEAT, "--out", self.out,
               "--drafts", os.path.join(SMA, "drafts.json"), "--now", NOW]
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("verdicts   transfer 1, downgrade 1, drop 1", p.stdout)
        self.assertIsNone(rules.index_problem(self.out))
        p = subprocess.run([sys.executable, VALIDATE, self.tmp, "--strict"], capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("3 cards", p.stdout)
        # a dropped seed is in the store and is not recalled; the transferred one is
        r = recall_mod.recall({"engine": "hoomd", "condition_tags": ["sma_kind:success"]}, self.out)
        self.assertEqual([h["id"] for h in r["hits"]], ["case-sma-simulation-002"])

    def test_the_command_refuses_to_write_into_the_checkout(self):
        p = subprocess.run([sys.executable, "-m", "meta_agent.src.cases.seed_sma", self.tmp, "--files", "--seat", SEAT,
                            "--out", os.path.join(self.tmp, "cases")], cwd=REPO, capture_output=True, text=True,
                           env=dict(os.environ, PYTHONUTF8="1"))
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("nothing is written into the checkout", p.stderr)

    def test_the_other_verdict_rules(self):
        def v(source, line):
            return seed_sma.verdict_of(source, line)
        self.assertEqual(v("microscope", {"kind": "deviation", "detail": {"shape_to_remember": "x"}}), ("F3", "downgrade"))
        self.assertEqual(v("microscope", {"kind": "refusal", "detail": {"what_is_left": "x"}}), ("F2", "transfer"))
        self.assertEqual(v("bridge", {"kind": "refusal", "detail": {"what": "x"}}), ("F4", "downgrade"))
        self.assertEqual(v("librarian", {"kind": "abandoned_attempt", "detail": {"shape_to_remember": "x"}}), ("F5", "transfer"))
        self.assertEqual(v("librarian", {"kind": "abandoned_attempt", "detail": {"what": "x"}}), ("F6", "downgrade"))
        self.assertEqual(v("incident", {"evidence": [{"kind": "prose_only", "ref": "x"}]}), ("I1", "downgrade"))
        self.assertEqual(v("incident", {"evidence": [{"kind": "prose_only", "ref": "x"}, {"kind": "commit", "ref": "y"}]}), ("I2", "transfer"))

    def test_an_incident_takes_its_class_as_a_tag_and_as_the_cause_only_when_registered(self):
        classes = {"guard_covers_one_route_of_two": "x", "unknown": "y"}
        line = {"id": "INC-fixture-01", "on": None, "recorded_on": "2026-02-03", "class": "guard-covers-one-route-of-two",
                "what": "a fixture", "evidence": [{"kind": "commit", "ref": "abc"}]}
        draft = self.drafts["case-sma-simulation-001"]
        verdict, card = seed_sma.case_of("incident", "harness", "7bc5a0f9~1", "contracts/harness/incidents.jsonl", "none",
                                         7, line, draft, SEAT, NOW, classes)
        self.assertEqual((verdict, card["id"], card["kind"]), ("transfer", "case-sma-incident-007", "incident"))
        self.assertEqual(card["cause_class"], "guard_covers_one_route_of_two")
        self.assertEqual(card["signature"]["cause_class"], card["cause_class"])
        self.assertIn("sma_class:guard-covers-one-route-of-two", card["signature"]["condition_tags"])
        self.assertEqual(card["count"]["last_seen"], "2026-02-03")
        self.assertIn("no day of its own", card["note"])
        line["class"] = "a-class-nobody-registered"
        _, card = seed_sma.case_of("incident", "harness", "7bc5a0f9~1", "contracts/harness/incidents.jsonl", "none",
                                   8, line, draft, SEAT, NOW, classes)
        self.assertEqual(card["cause_class"], "unknown")


if __name__ == "__main__":
    unittest.main()
