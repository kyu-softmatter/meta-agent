"""Tests for S0 on the two fixture labs (tasks/001).

Run from the repository root:  python -m unittest discover -s meta_agent/tests -t .
"""
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from meta_agent.src.onboarding import cards, discover, wizard  # noqa: E402
from meta_agent.src.onboarding.bank import BANK, DERIVED  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "labs")
NOW = "2026-10-29T20:00:00Z"
SEAT = "meta-office-20261029-1"


def run_lab(name):
    src = discover.Source(os.path.join(FIX, name), kind="folder")
    disc = discover.discover("lab-fixture-" + name, [src], SEAT, NOW)
    rec = wizard.ask(disc, SEAT, NOW)
    prof = wizard.propose(disc, rec, SEAT, NOW)
    return disc, rec, prof


class RichLab(unittest.TestCase):
    def setUp(self):
        self.disc, self.rec, self.prof = run_lab("rich")

    def test_only_policy_questions_remain(self):
        asked = {q["field"] for q in self.rec["questions"]}
        policy = set(wizard.policy_fields()) - set(DERIVED)
        self.assertEqual(asked, policy)
        self.assertTrue(all(q["state_at_ask"] == "policy" for q in self.rec["questions"]))

    def test_inferred_fields_carry_evidence(self):
        f = self.disc["fields"]
        for name in ("preferred_engines", "software_env.language", "software_env.package_manager",
                     "software_env.os", "hardware.gpu", "hardware.hpc", "collaboration.first_agent",
                     "collaboration.existing_agents", "operational_constraints.licenses",
                     "conventions.unit_system", "existing_data", "validated_workflows"):
            self.assertEqual(f[name]["state"], "inferred", name)
            self.assertTrue(f[name]["evidence"], name)
        self.assertIn("hoomd_blue", f["preferred_engines"]["value"])
        self.assertIn("bd_cg", f["conventions.methods"]["value"])
        self.assertEqual(f["collaboration.first_agent"]["value"], False)
        self.assertIn("https://hoomd-blue.readthedocs.io/", self.disc["materials_seen"])

    def test_policy_fields_are_never_inferred(self):
        for name in wizard.policy_fields():
            self.assertEqual(self.disc["fields"][name]["state"], "unknown", name)

    def test_answers_confirm_only_what_the_person_wrote(self):
        a = cards.load_json(os.path.join(FIX, "rich_answers.json"))
        rec2, prof2 = wizard.apply_answers(self.rec, self.prof, a["answers"], a["answered_by"], a["date"], SEAT, NOW)
        self.assertEqual(rec2["revision"], 2)
        self.assertEqual(prof2["supersedes"], self.prof["id"])
        for f in wizard.policy_fields():
            leaf = wizard.get_leaf(prof2, f)
            self.assertEqual(leaf["state"], "confirmed", f)
            self.assertEqual(leaf["confirmed_by"], "human", f)
            self.assertEqual(leaf["date"], a["date"], f)
        self.assertEqual(wizard.get_leaf(prof2, "preferred_engines")["state"], "inferred")
        self.assertEqual(prof2["status"], "validated")
        self.assertEqual(rec2["status"], "done")

    def test_answers_must_come_from_a_person(self):
        with self.assertRaises(ValueError):
            wizard.apply_answers(self.rec, self.prof, {"policy.working_mode": "x"}, "meta-office-20261029-1",
                                 "2026-10-29", SEAT, NOW)


class EmptyLab(unittest.TestCase):
    def setUp(self):
        self.disc, self.rec, self.prof = run_lab("empty")

    def test_full_bank_is_asked(self):
        asked = [q["field"] for q in self.rec["questions"]]
        deferred = {f for f, _, _, cond in BANK if cond == "needs_existing_agents"}
        expected = [f for f, _, _, _ in BANK if f not in deferred]
        self.assertEqual(asked, expected)
        self.assertEqual(len(asked), 22)
        self.assertEqual(sorted(self.rec["held"]), sorted(deferred))

    def test_nothing_inferred(self):
        self.assertTrue(all(v["state"] == "unknown" for v in self.disc["fields"].values()))
        self.assertEqual(sorted(self.prof["held"]), sorted(self.disc["fields"]))


class Validator(unittest.TestCase):
    def test_outputs_pass_the_validator(self):
        out = tempfile.mkdtemp(prefix="ma-onb-")
        for name in ("rich", "empty"):
            disc, rec, prof = run_lab(name)
            d = os.path.join(out, "profiles", "lab-fixture-" + name)
            cards.write_json(os.path.join(d, "discovery_report.json"), disc)
            cards.write_json(os.path.join(d, "onboarding_record.json"), rec)
            cards.write_json(os.path.join(d, "lab_profile.json"), prof)
            cards.write_text(os.path.join(d, "proposal.md"), wizard.proposal_markdown(disc, rec, prof, discover.load_registry("engines")))
            if name == "rich":
                a = cards.load_json(os.path.join(FIX, "rich_answers.json"))
                rec2, prof2 = wizard.apply_answers(rec, prof, a["answers"], a["answered_by"], a["date"], SEAT, NOW)
                cards.write_json(os.path.join(d, "v2_onboarding_record.json"), rec2)
                cards.write_json(os.path.join(d, "v2_lab_profile.json"), prof2)
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, os.path.join(ROOT, "contracts", "validate.py"), out, "--strict"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("0 failed, 0 pending", p.stdout)


class StepThreeAlone(unittest.TestCase):
    """--answers on a folder that already holds a lab's cards: Step three alone, on two fixture labs."""

    def folder(self, name):
        out = tempfile.mkdtemp(prefix="ma-onb3-")
        d = os.path.join(out, "profiles", "lab-fixture-" + name)
        disc, rec, prof = run_lab(name)
        cards.write_json(os.path.join(d, "discovery_report.json"), disc)
        cards.write_json(os.path.join(d, "onboarding_record.json"), rec)
        cards.write_json(os.path.join(d, "lab_profile.json"), prof)
        cards.write_text(os.path.join(d, "proposal.md"), wizard.proposal_markdown(disc, rec, prof, discover.load_registry("engines")))
        return out, d, rec, prof

    def hashes(self, d, names):
        import hashlib
        out = {}
        for n in names:
            with open(os.path.join(d, n), "rb") as f:
                out[n] = hashlib.sha256(f.read()).hexdigest()
        return out

    def run_main(self, argv):
        import contextlib, io
        from meta_agent.src.onboarding.__main__ import main
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            code = main(argv)
        return code, printed.getvalue()

    def test_the_answers_become_the_next_revision_and_no_card_is_written_again(self):
        out, d, rec, prof = self.folder("rich")
        first = ("discovery_report.json", "onboarding_record.json", "lab_profile.json", "proposal.md")
        before = self.hashes(d, first)
        answers = os.path.join(FIX, "rich_answers.json")
        code, printed = self.run_main(["--lab-id", "lab-fixture-rich", "--out", d, "--answers", answers, "--seat", SEAT, "--now", NOW])
        self.assertEqual(code, 0)
        self.assertEqual(self.hashes(d, first), before)
        self.assertEqual(sorted(os.listdir(d)), sorted(first + ("v2_lab_profile.json", "v2_onboarding_record.json")))
        a = cards.load_json(answers)
        rec2, prof2 = wizard.apply_answers(rec, prof, a["answers"], a["answered_by"], a["date"], SEAT, NOW)
        self.assertEqual(cards.load_json(os.path.join(d, "v2_onboarding_record.json")), rec2)
        self.assertEqual(cards.load_json(os.path.join(d, "v2_lab_profile.json")), prof2)
        self.assertEqual(prof2["status"], "validated")
        self.assertIn("still open: none", printed)
        env = dict(os.environ, PYTHONUTF8="1")
        p = subprocess.run([sys.executable, os.path.join(ROOT, "contracts", "validate.py"), out, "--strict"],
                           capture_output=True, text=True, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def test_a_lab_with_more_left_open_stays_a_draft_and_takes_later_answers_as_a_third_revision(self):
        out, d, rec, prof = self.folder("empty")
        asked = [q["field"] for q in rec["questions"]]
        self.assertGreater(len(asked), 1)
        one = os.path.join(out, "one.json")
        cards.write_json(one, {"answered_by": "human", "date": "2026-11-16", "answers": {"policy.publication_scope": "this lab"}})
        code, printed = self.run_main(["--lab-id", "lab-fixture-empty", "--out", d, "--answers", one, "--seat", SEAT, "--now", NOW])
        prof2 = cards.load_json(os.path.join(d, "v2_lab_profile.json"))
        self.assertEqual((prof2["revision"], prof2["status"]), (2, "draft"))
        self.assertEqual(prof2["policy"]["publication_scope"]["confirmed_by"], "human")
        self.assertEqual(prof2["policy"]["working_mode"]["state"], "unknown")
        two = os.path.join(out, "two.json")
        cards.write_json(two, {"answered_by": "human", "date": "2026-11-16", "answers": {"policy.working_mode": "in batches"}})
        self.run_main(["--lab-id", "lab-fixture-empty", "--out", d, "--answers", two, "--seat", SEAT, "--now", NOW])
        prof3 = cards.load_json(os.path.join(d, "v3_lab_profile.json"))
        self.assertEqual(prof3["revision"], 3)
        self.assertEqual(prof3["policy"]["publication_scope"]["value"], "this lab")
        self.assertEqual(prof3["policy"]["working_mode"]["value"], "in batches")

    def test_what_was_not_asked_another_lab_and_a_seat_as_the_one_who_answers_are_refused(self):
        out, d, rec, prof = self.folder("rich")
        bad = os.path.join(out, "bad.json")
        cards.write_json(bad, {"answered_by": "human", "date": "2026-11-16", "answers": {"policy.not_a_field": True}})
        with self.assertRaises(ValueError):
            self.run_main(["--lab-id", "lab-fixture-rich", "--out", d, "--answers", bad, "--seat", SEAT])
        with self.assertRaises(ValueError):
            self.run_main(["--lab-id", "lab-fixture-other", "--out", d, "--answers", os.path.join(FIX, "rich_answers.json"), "--seat", SEAT])
        seat = os.path.join(out, "seat.json")
        cards.write_json(seat, {"answered_by": SEAT, "date": "2026-11-16", "answers": {"policy.working_mode": "x"}})
        with self.assertRaises(ValueError):
            self.run_main(["--lab-id", "lab-fixture-rich", "--out", d, "--answers", seat, "--seat", SEAT])
        self.assertEqual(len(os.listdir(d)), 4)


if __name__ == "__main__":
    unittest.main()
