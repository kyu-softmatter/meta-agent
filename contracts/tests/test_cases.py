# -*- coding: utf-8 -*-
"""Tests of contracts/tools/cases.py: condition tags, a store's index and how a reference resolves
(meta_agent/tasks/006, the design part).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import cases  # noqa: E402


class Tags(unittest.TestCase):
    def test_the_three_forms(self):
        self.assertEqual(cases.parse_tag("vendor_spec_vs_bench"), ("vendor_spec_vs_bench", "name", None, None))
        self.assertEqual(cases.parse_tag("geometry:cone_plate"), ("geometry", "value", "cone_plate", None))
        self.assertEqual(cases.parse_tag("temperature_K:298.15"), ("temperature_K", "number", 298.15, 298.15))
        self.assertEqual(cases.parse_tag("shear_rate_1/s:1e-2..1e3"), ("shear_rate_1/s", "range", 0.01, 1000.0))
        self.assertEqual(cases.parse_tag("shear_rate_1/s:1e3..1e-2")[1], "reversed")
        for bad in ("two words", ":x", "name:", "name:1..", "name:a..b", "", None, 3):
            self.assertIsNone(cases.parse_tag(bad), bad)

    def test_when_two_tags_meet(self):
        r = "shear_rate_1/s:1e-2..1e3"
        self.assertTrue(cases.tags_meet(r, "shear_rate_1/s:5"))            # a number inside the range
        self.assertTrue(cases.tags_meet("shear_rate_1/s:5", r))
        self.assertTrue(cases.tags_meet(r, "shear_rate_1/s:1e3"))          # the end counts
        self.assertFalse(cases.tags_meet(r, "shear_rate_1/s:1e4"))
        self.assertTrue(cases.tags_meet("shear_rate_1/s:1e-2..1", "shear_rate_1/s:0.5..10"))
        self.assertFalse(cases.tags_meet("shear_rate_1/s:1e-2..1", "shear_rate_1/s:2..10"))
        self.assertFalse(cases.tags_meet("a:1..2", "b:1..2"))              # another name
        self.assertTrue(cases.tags_meet("geometry:cone_plate", "geometry:cone_plate"))
        self.assertFalse(cases.tags_meet("geometry:cone_plate", "geometry:parallel_plate"))
        self.assertTrue(cases.tags_meet("vendor_spec_vs_bench", "vendor_spec_vs_bench"))
        self.assertFalse(cases.tags_meet("geometry", "geometry:cone_plate"))
        self.assertFalse(cases.tags_meet("a:2..1", "a:1.5"))               # a reversed range meets nothing


class Index(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="cases-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store = os.path.join(self.dir, "cases")
        os.makedirs(os.path.join(self.store, "sma"))
        self.card("case-a.json", "case-a", 1)
        self.card(os.path.join("sma", "case-b.json"), "case-b", 1)
        self.card(os.path.join("sma", "v2_case-b.json"), "case-b", 2)
        with open(os.path.join(self.store, "notes.json"), "w", encoding="utf-8") as f:
            json.dump({"not": "a card"}, f)

    def card(self, relpath, cid, revision):
        with open(os.path.join(self.store, relpath), "w", encoding="utf-8") as f:
            json.dump({"card": "case", "id": cid, "revision": revision}, f)

    def write_index(self):
        with open(os.path.join(self.store, "index.json"), "w", encoding="utf-8") as f:
            json.dump(cases.build_index(self.store), f)

    def test_the_index_is_what_the_cards_give_and_is_stable(self):
        idx = cases.build_index(self.store)
        self.assertEqual([(r["id"], r["revision"], r["path"]) for r in idx["cases"]],
                         [("case-a", 1, "cases/case-a.json"), ("case-b", 1, "cases/sma/case-b.json"), ("case-b", 2, "cases/sma/v2_case-b.json")])
        self.assertEqual(idx, cases.build_index(self.store))
        self.assertEqual(cases.index_problem(self.store), "no index.json")
        self.write_index()
        self.assertIsNone(cases.index_problem(self.store))
        self.card("case-c.json", "case-c", 1)                      # a card the index has not seen
        self.assertIn("regenerate", cases.index_problem(self.store))

    def test_how_a_reference_resolves(self):
        self.write_index()
        spec = cases.STORES["case_refs"]
        rows = cases.build_index(self.store)["cases"]
        self.assertIsNone(cases.ref_problem({"id": "case-a"}, self.store, spec))
        self.assertIsNone(cases.ref_problem({"id": "case-b", "version": "2"}, self.store, spec))
        self.assertIsNone(cases.ref_problem({"id": "case-a", "hash": rows[0]["hash"]}, self.store, spec))
        self.assertIn("not in cases/index.json", cases.ref_problem({"id": "case-z"}, self.store, spec))
        self.assertIn("no revision 3", cases.ref_problem({"id": "case-b", "version": "3"}, self.store, spec))
        self.assertIn("hash", cases.ref_problem({"id": "case-a", "hash": "sha256:" + "0" * 64}, self.store, spec))

    def test_the_store_is_the_nearest_one_at_or_above_the_card(self):
        card = os.path.join(self.dir, "requests", "req-1", "agent_goal.json")
        os.makedirs(os.path.dirname(card))
        self.assertEqual(cases.store_for(card, self.dir, "cases"), self.store)
        self.assertIsNone(cases.store_for(card, self.dir, "knowledge"))
        self.assertIsNone(cases.store_for(card, os.path.join(self.dir, "requests"), "cases"))   # never above the tree


class TheExampleStore(unittest.TestCase):
    def test_its_index_is_current(self):
        self.assertIsNone(cases.index_problem(os.path.join(REPO, "contracts", "examples", "cases")))


if __name__ == "__main__":
    unittest.main()
