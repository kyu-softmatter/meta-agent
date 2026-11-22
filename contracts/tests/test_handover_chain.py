# -*- coding: utf-8 -*-
"""A hand-over card's produced_by as a chain of steps (tasks/034, at the ask 20261121-meta-macbook-20261120-4-9).

Run from the repository root:  python -m unittest discover -s contracts/tests

Of two unrelated kinds on purpose (the person, 2026-11-11): the producers of the accepted bridge fixtures under
contracts/examples/bridge/, DFT→MD and rheometer → rheology engine. Check 1 takes a chain whose every step names
its skill and its record, and refuses a step without its record and a card naming both forms at once.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
PRODUCERS = [os.path.join("dft-md", "qe-h2-bond", "outbox", "handover-h2-bond.json"),
             os.path.join("rheometer-engine", "rheometer-fluid", "outbox", "handover-zero-shear-viscosity.json")]


class HandoverChain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="handover-chain-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def judge(self, rel, produced_by):
        with open(os.path.join(REPO, "contracts", "examples", "bridge", rel), encoding="utf-8") as f:
            card = json.load(f)
        one = card["produced_by"]
        card["produced_by"] = produced_by(one)
        dest = os.path.join(self.tmp, os.path.basename(os.path.dirname(os.path.dirname(rel))))
        shutil.rmtree(dest, ignore_errors=True)
        os.makedirs(os.path.join(dest, "outbox"))
        with open(os.path.join(dest, "outbox", os.path.basename(rel)), "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2, ensure_ascii=False)
        run = subprocess.run([sys.executable, VALIDATE, self.tmp, "--checks", "1"], cwd=REPO,
                             capture_output=True, text=True)
        return run.returncode, run.stdout + run.stderr

    def test_a_chain_of_steps_is_taken(self):
        for rel in PRODUCERS:
            code, out = self.judge(rel, lambda one: {"chain": [
                {"step": "fit", "skill": one["skill"], "record": one["record"]},
                {"step": "convert", "skill": "unit_convert@v2", "record": "runs/0002/record.json"}]})
            self.assertEqual(code, 0, rel + "\n" + out)

    def test_one_skill_and_record_is_still_taken(self):
        for rel in PRODUCERS:
            code, out = self.judge(rel, lambda one: one)
            self.assertEqual(code, 0, rel + "\n" + out)

    def test_a_step_without_its_record_is_refused(self):
        for rel in PRODUCERS:
            code, _ = self.judge(rel, lambda one: {"chain": [{"step": "fit", "skill": one["skill"]}]})
            self.assertNotEqual(code, 0, rel)

    def test_an_empty_chain_is_refused(self):
        for rel in PRODUCERS:
            code, _ = self.judge(rel, lambda one: {"chain": []})
            self.assertNotEqual(code, 0, rel)

    def test_both_forms_at_once_are_refused(self):
        for rel in PRODUCERS:
            code, _ = self.judge(rel, lambda one: dict(one, chain=[{"step": "fit", **one}]))
            self.assertNotEqual(code, 0, rel)


if __name__ == "__main__":
    unittest.main()
