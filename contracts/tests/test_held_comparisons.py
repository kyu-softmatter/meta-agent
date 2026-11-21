# -*- coding: utf-8 -*-
"""Tests of bundle check B5 on a held comparison: a scientific comparison that cannot be judged yet stands as a
held item, with why and what it needs, and the gate shows it pending, never as a gate filled (the person,
2026-11-20, "Held item, shown pending (Recommended)"; tasks/032, dftmd-12).

Run from the repository root:  python -m unittest discover -s contracts/tests

On copies of two committed bundles of unrelated kinds: a Quantum ESPRESSO agent (a fitted bond length against a
measured one) and a rheometer agent (a torque range against the device's specification).
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts"))
import validate  # noqa: E402

KINDS = ("meta_agent/builds/qe-h2-bond/0001/bundle", "meta_agent/builds/rheo-fixture/0004/bundle")


class HeldComparison(unittest.TestCase):
    def bundle(self, rel, change):
        d = tempfile.mkdtemp(prefix="b5-held-")
        self.addCleanup(shutil.rmtree, d, True)
        dest = os.path.join(d, "bundle")
        shutil.copytree(os.path.join(REPO, *rel.split("/")), dest,
                        ignore=shutil.ignore_patterns("runs", ".pixi", "__pycache__"))
        path = os.path.join(dest, "validation", "scientific", "sci-1.json")
        with open(path, encoding="utf-8") as f:
            item = json.load(f)
        change(item)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(item, f)
        report = validate.Report(quiet=True)
        validate.checkB5(dest, "bundle", report)
        return [m for _, _, m in report.fails], [m for c, _, m in report.pendings if c == "B5"]

    @staticmethod
    def held(item, **extra):
        item.setdefault("measure", {}).pop("reference_function", None)
        item["expected_verdict"] = "not_run"
        item["held"] = {"reason": "no reference function can judge it yet",
                        "needs": "a reference function or the person's tolerance"}
        item.update(extra)

    def test_a_held_comparison_passes_b5_and_shows_pending(self):
        for rel in KINDS:
            fails, pendings = self.bundle(rel, self.held)
            self.assertEqual(fails, [], rel)
            self.assertEqual(len(pendings), 1, rel)
            self.assertIn("held comparison", pendings[0])

    def test_a_held_comparison_says_why_and_what_it_needs(self):
        for rel in KINDS:
            for broken in ({"reason": "why"}, {"needs": "what"}, {"reason": " ", "needs": "what"}, "held"):
                fails, pendings = self.bundle(rel, lambda it: (self.held(it), it.update(held=broken)))
                self.assertTrue(any("held.reason" in m for m in fails), (rel, broken))
                self.assertEqual(pendings, [])

    def test_a_held_comparison_is_not_run_and_names_no_reference_function(self):
        for rel in KINDS:
            fails, _ = self.bundle(rel, lambda it: self.held(it, expected_verdict="pass"))
            self.assertTrue(any("expected not_run" in m for m in fails), rel)
            fails, _ = self.bundle(rel, lambda it: (self.held(it), it["measure"].update(reference_function="ref")))
            self.assertTrue(any("names no reference function" in m for m in fails), rel)

    def test_only_a_scientific_comparison_may_be_held(self):
        rel = KINDS[1]
        d = tempfile.mkdtemp(prefix="b5-held-")
        self.addCleanup(shutil.rmtree, d, True)
        dest = os.path.join(d, "bundle")
        shutil.copytree(os.path.join(REPO, *rel.split("/")), dest, ignore=shutil.ignore_patterns("runs"))
        idir = os.path.join(dest, "validation", "interface")
        name = sorted(n for n in os.listdir(idir) if n.endswith(".json"))[0]
        with open(os.path.join(idir, name), encoding="utf-8") as f:
            item = json.load(f)
        item["held"] = {"reason": "why", "needs": "what"}
        with open(os.path.join(idir, name), "w", encoding="utf-8") as f:
            json.dump(item, f)
        report = validate.Report(quiet=True)
        validate.checkB5(dest, "bundle", report)
        self.assertTrue(any("only a scientific comparison" in m for _, _, m in report.fails))


if __name__ == "__main__":
    unittest.main()
