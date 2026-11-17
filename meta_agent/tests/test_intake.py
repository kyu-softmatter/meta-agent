"""The stage that writes a request's first card (tasks/016; contracts/schemas/intake.schema.json).

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .

The drafts are taken from the two examples of the schema, contracts/examples/requests/req-fixture-002 (a
request that waits, on an engine) and req-fixture-003 (a specified one, on an echo tool): two unrelated
kinds, neither of them rheology.
"""
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.intake import card as card_mod

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
REPO = os.path.dirname(META)
EXAMPLES = os.path.join(REPO, "contracts", "examples", "requests")
SEAT = "meta-macbook-20261116-1"
NOW = "2026-11-16T12:00:00Z"
ENV = dict(os.environ, PYTHONUTF8="1")


def example(rid):
    return cards.load_json(os.path.join(EXAMPLES, rid, "intake.json"))


def draft_of(card):
    return {k: copy.deepcopy(v) for k, v in card.items() if k not in card_mod.STAGE_WRITES}


class Write(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-intake-")
        self.root = os.path.join(self.tmp, "meta_agent")
        self.req = os.path.join(self.root, "requests", "req-fixture-002")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def first(self):
        return card_mod.write(self.req, "req-fixture-002", draft_of(example("req-fixture-002")), SEAT, NOW)

    def test_the_two_examples_are_what_their_drafts_give(self):
        for rid, stage in (("req-fixture-002", "reading"), ("req-fixture-003", "specified")):
            ex = example(rid)
            self.assertEqual(card_mod.problems(ex), [], rid)
            card = card_mod.make(rid, draft_of(ex), ex["author"], ex["created_at"])
            self.assertEqual(card["stage"], stage)
            self.assertEqual({k: v for k, v in card.items() if k != "assumptions"}, {k: v for k, v in ex.items() if k != "assumptions"})

    def test_the_first_card_is_revision_one_at_reading_and_a_same_draft_writes_nothing(self):
        path, card = self.first()
        self.assertEqual(os.path.basename(path), "intake.json")
        self.assertEqual((card["card"], card["id"], card["revision"], card["stage"], card["status"], card["numbers"]),
                         ("intake", "intake-fixture-002", 1, "reading", "draft", []))
        self.assertNotIn("supersedes", card)
        self.assertEqual(card["persons_words"]["verbatim"], "이것을 자동화 하고싶어")
        again, same = card_mod.write(self.req, "req-fixture-002", draft_of(example("req-fixture-002")), SEAT, NOW, note="nothing")
        self.assertIsNone(again)
        self.assertEqual(os.listdir(self.req), ["intake.json"])

    def test_a_draft_holds_only_what_changes_and_gives_the_next_revision(self):
        self.first()
        with self.assertRaises(card_mod.Refused) as e:
            card_mod.write(self.req, "req-fixture-002", {"gui_choice": "none"}, SEAT, NOW)
        self.assertIn("give --note", str(e.exception))
        path, card = card_mod.write(self.req, "req-fixture-002", {"gui_choice": "none", "notes": None}, SEAT, NOW,
                                    note="the person said no interface is wanted")
        self.assertEqual(os.path.basename(path), "v2_intake.json")
        self.assertEqual((card["revision"], card["supersedes"], card["gui_choice"], card["stage"]), (2, "intake-fixture-002", "none", "reading"))
        self.assertNotIn("notes", card)
        self.assertEqual(card["paragraph"], example("req-fixture-002")["paragraph"])
        self.assertEqual(card_mod.latest(self.req), (2, path))

    def test_the_person_s_answer_is_recorded_verbatim_and_not_written_over(self):
        self.first()
        path, card = card_mod.answer(self.req, "req-fixture-002", 2, "튜토리얼 그대로 끝까지 돌려줘", "2026-11-16", SEAT,
                                     gloss="Run the tutorial as it is, to the end.", recorded_in="docs/ideas/20261116.md", now=NOW)
        self.assertEqual(os.path.basename(path), "v2_intake.json")
        self.assertEqual(card["questions_for_the_person"][1]["answer"]["verbatim"], "튜토리얼 그대로 끝까지 돌려줘")
        self.assertEqual([q["n"] for q in card_mod.waiting(card)], [1])
        self.assertIn("the person's answer to question 2", card["revision_note"])
        for n in (2, 7):
            with self.assertRaises(card_mod.Refused):
                card_mod.answer(self.req, "req-fixture-002", n, "x", "2026-11-16", SEAT, now=NOW)
        self.assertEqual(sorted(os.listdir(self.req)), ["intake.json", "v2_intake.json"])

    def test_the_card_is_specified_when_it_carries_the_contract_and_the_tasks(self):
        self.first()
        spec = example("req-fixture-003")
        with self.assertRaises(card_mod.Refused) as e:      # a contract with no task: the schema's rule
            card_mod.write(self.req, "req-fixture-002", {"tool_contract": spec["tool_contract"]}, SEAT, NOW, note="the contract")
        self.assertIn("interface_tasks", str(e.exception))
        path, card = card_mod.write(self.req, "req-fixture-002", {k: spec[k] for k in ("tool_contract", "interface_tasks",
                                    "scientific_tasks", "replay_items")}, SEAT, NOW, note="the contract and the tasks are written")
        self.assertEqual((card["stage"], card["revision"]), ("specified", 2))

    def test_what_is_refused_writes_nothing(self):
        good = draft_of(example("req-fixture-002"))
        bad = [dict(good, stage="specified"), dict(good, numbers=[]), dict(good, a_field_of_my_own=1),
               dict(good, paragraph="an agent that runs 4 stages"), dict(good, must_not=["run more than 3 times"]),
               dict(good, questions_for_the_person=[{"n": 2, "needed_before": "the goal", "question": "q"}]),
               dict(good, executes="sometimes"), {k: v for k, v in good.items() if k != "persons_words"}, ["not an object"]]
        for draft in bad:
            with self.assertRaises(card_mod.Refused, msg=str(draft)[:80]):
                card_mod.write(self.req, "req-fixture-002", draft, SEAT, NOW)
        self.assertFalse(os.path.exists(self.req))
        self.first()
        with self.assertRaises(card_mod.Refused):
            card_mod.write(self.req, "req-another-001", good, SEAT, NOW, note="x")

    def test_a_record_of_before_the_card_is_followed_by_a_card(self):
        req = os.path.join(self.root, "requests", "req-echo-001")
        os.makedirs(req)
        shutil.copy(os.path.join(META, "requests", "req-echo-001", "intake.json"), os.path.join(req, "intake.json"))
        self.assertFalse(card_mod.is_card(cards.load_json(os.path.join(req, "intake.json"))))
        record = cards.load_json(os.path.join(req, "intake.json"))
        with self.assertRaises(card_mod.Refused):      # the record as it is lacks what a card must carry
            card_mod.write(req, "req-echo-001", {"gui_choice": record["gui_choice"], "note": "x"}, SEAT, NOW, note="x")
        path, card = card_mod.write(req, "req-echo-001", {
            "persons_words": {"verbatim": "An agent that returns what it is given.", "date": "2026-10-29"},
            "questions_for_the_person": [],
            "tool_reading": [{k: v for k, v in row.items() if k != "gap_reason"} for row in record["tool_reading"]]},
            SEAT, NOW, note="the record of before the card, as a card")
        self.assertEqual((os.path.basename(path), card["revision"], card["stage"]), ("v2_intake.json", 2, "specified"))
        self.assertNotIn("supersedes", card)

    def test_the_command_writes_says_what_waits_and_the_tree_passes_the_validator(self):
        draft = os.path.join(self.tmp, "draft.json")
        cards.write_json(draft, draft_of(example("req-fixture-002")))
        base = [sys.executable, "-m", "meta_agent.src.intake", "--root", self.root]
        p = subprocess.run(base + ["write", "--rid", "req-fixture-002", "--draft", draft, "--seat", SEAT, "--now", NOW],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("wrote  meta_agent/requests/req-fixture-002/intake.json", p.stdout)
        self.assertIn("stage  reading, revision 1", p.stdout)
        p = subprocess.run(base + ["waiting", "--rid", "req-fixture-002"], cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertIn("2 question(s) wait for the person", p.stdout)
        p = subprocess.run(base + ["answer", "--rid", "req-fixture-002", "--n", "1", "--verbatim", "엔진까지", "--gloss", "As far as an engine.",
                                   "--date", "2026-11-16", "--seat", SEAT, "--now", NOW], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        p = subprocess.run(base + ["check", os.path.join(self.req, "v2_intake.json")], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        cards.write_json(draft, {"stage": "specified"})
        p = subprocess.run(base + ["write", "--rid", "req-fixture-002", "--draft", draft, "--seat", SEAT, "--note", "x"],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 1)
        self.assertIn("refused  stage is written by the stage", p.stdout)
        p = subprocess.run([sys.executable, os.path.join(REPO, "contracts", "validate.py"), self.tmp, "--checks", "1,7"],
                           capture_output=True, text=True, env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
