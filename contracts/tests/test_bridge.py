# -*- coding: utf-8 -*-
"""Tests of contracts/tools/bridge.py: a hand-over carried unchanged, on the person's word (tasks/031).

Run from the repository root:  python -m unittest discover -s contracts/tests

Of two unrelated kinds on purpose (the person, 2026-11-11, and 2026-11-20 'Rheometer → rheology engine'):
the accepted fixtures under contracts/examples/bridge/, DFT→MD and rheometer → rheology engine.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import bridge  # noqa: E402

EXAMPLES = os.path.join(REPO, "contracts", "examples", "bridge")
KINDS = [("dft-md", "qe-h2-bond", "handover-h2-bond.json", "hoomd-h2-bond"),
         ("rheometer-engine", "rheometer-fluid", "handover-zero-shear-viscosity.json", "rheology-engine-couette")]


PERSON = {"by": "person"}
SESSION = {"by": "session", "session": "test-session-1", "words": "carry the card to the other agent"}


class Carry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="bridge-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def pair(self, kind, producer, receiver):
        dest = os.path.join(self.tmp, kind)
        os.makedirs(os.path.join(dest, receiver))
        shutil.copytree(os.path.join(EXAMPLES, kind, producer, "outbox"), os.path.join(dest, producer, "outbox"))
        return os.path.join(dest, producer), os.path.join(dest, receiver)

    def test_a_card_crosses_byte_for_byte_with_its_envelope(self):
        for kind, producer, card, receiver in KINDS:
            p, r = self.pair(kind, producer, receiver)
            src = os.path.join(p, "outbox", card)
            env_path, payload = bridge.carry(src, r, "human", PERSON)
            with open(src, "rb") as a, open(payload, "rb") as b:
                raw = a.read()
                self.assertEqual(raw, b.read())
            env = json.load(open(env_path))
            self.assertEqual(env["author"], "bridge")
            self.assertEqual(env["numbers"], [])
            self.assertEqual(env["trigger"], "human")
            self.assertEqual(env["payload"]["sha256"], "sha256:" + hashlib.sha256(raw).hexdigest())
            self.assertEqual(os.path.basename(os.path.dirname(env_path)), json.load(open(src))["thread"])

    def test_a_second_carry_is_the_next_round(self):
        kind, producer, card, receiver = KINDS[1]
        p, r = self.pair(kind, producer, receiver)
        bridge.carry(os.path.join(p, "outbox", card), r, "human", PERSON)
        env2, payload2 = bridge.carry(os.path.join(p, "outbox", card), r, "human", PERSON)
        self.assertTrue(os.path.basename(env2).startswith("r2_"))
        self.assertTrue(os.path.basename(payload2).startswith("r2_"))

    def test_refused_without_the_persons_word(self):
        kind, producer, card, receiver = KINDS[0]
        p, r = self.pair(kind, producer, receiver)
        with self.assertRaises(bridge.Refused):
            bridge.carry(os.path.join(p, "outbox", card), r, "meta-macbook-20261120-1", PERSON)
        self.assertFalse(os.path.exists(os.path.join(r, "inbox")))

    def test_refused_outside_an_outbox_and_for_another_card(self):
        kind, producer, card, receiver = KINDS[0]
        p, r = self.pair(kind, producer, receiver)
        runs = os.path.join(p, "runs")
        os.makedirs(runs)
        shutil.copy(os.path.join(p, "outbox", card), runs)
        with self.assertRaises(bridge.Refused):
            bridge.carry(os.path.join(runs, card), r, "human", PERSON)
        other = os.path.join(p, "outbox", "note.json")
        json.dump({"card": "observation"}, open(other, "w"))
        with self.assertRaises(bridge.Refused):
            bridge.carry(other, r, "human", PERSON)

    def test_the_envelope_says_who_ran_the_bridge(self):
        # tasks/032, bridge-2: the person, or a session on the person's quoted words, on both kinds
        for (kind, producer, card, receiver), ran_by in zip(KINDS, (SESSION, PERSON)):
            p, r = self.pair(kind, producer, receiver)
            env_path, _ = bridge.carry(os.path.join(p, "outbox", card), r, "human", ran_by)
            env = json.load(open(env_path))
            self.assertEqual(env["ran_by"], ran_by)
            self.assertEqual(env["released_by"], "human")
            self.assertIn("session test-session-1" if ran_by is SESSION else "ran by the person",
                          "\n".join(bridge.board(r)))

    def test_refused_without_saying_who_ran_it(self):
        kind, producer, card, receiver = KINDS[1]
        p, r = self.pair(kind, producer, receiver)
        for ran_by in (None, {}, {"by": "seat"}, {"by": "session", "session": "s1"},
                       {"by": "session", "session": "s1", "words": "  "}, {"by": "person", "words": "x"}):
            with self.assertRaises(bridge.Refused):
                bridge.carry(os.path.join(p, "outbox", card), r, "human", ran_by)
        self.assertFalse(os.path.exists(os.path.join(r, "inbox")))

    def test_the_command_line_requires_ran_by(self):
        kind, producer, card, receiver = KINDS[0]
        p, r = self.pair(kind, producer, receiver)
        src = os.path.join(p, "outbox", card)
        with self.assertRaises(SystemExit):
            bridge.main(["carry", "--card", src, "--to", r, "--released-by", "human"])
        self.assertEqual(bridge.main(["carry", "--card", src, "--to", r, "--released-by", "human",
                                      "--ran-by", "session", "--session", "s1"]), 1)
        self.assertEqual(bridge.main(["carry", "--card", src, "--to", r, "--released-by", "human",
                                      "--ran-by", "session", "--session", "s1", "--words", "carry it"]), 0)

    def test_the_board_sees_a_changed_copy(self):
        kind, producer, card, receiver = KINDS[1]
        p, r = self.pair(kind, producer, receiver)
        _, payload = bridge.carry(os.path.join(p, "outbox", card), r, "human", PERSON)
        self.assertIn("unchanged", "\n".join(bridge.board(r)))
        with open(payload, "a") as f:
            f.write(" ")
        self.assertIn("CHANGED", "\n".join(bridge.board(r)))


if __name__ == "__main__":
    unittest.main()
