"""Recall on a fixture store of five hand-written cases (tasks/006).

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import tempfile
import unittest

from meta_agent.src.cases import recall as recall_mod
from meta_agent.src.cases import rules

HERE = os.path.dirname(os.path.abspath(__file__))
STORE = os.path.join(HERE, "fixtures", "cases")
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


if __name__ == "__main__":
    unittest.main()
