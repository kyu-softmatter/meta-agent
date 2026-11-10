# -*- coding: utf-8 -*-
"""Tests of contracts/tools/seats.py and `bootstrap.py seat` (meta_agent/tasks/009, part 1).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import copy
import json
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import seats  # noqa: E402

TABLE = {
    "machines": {"office": "a computer", "macbook": "another"},
    "roles": {
        "design": {"paths": ["*", "contracts/"], "excludes": [], "owns": ["design"]},
        "meta": {"paths": ["meta_agent/"], "excludes": ["meta_agent/CLAUDE.md"], "owns": ["meta_agent"]},
    },
    "seats": [
        {"seat": "design-office-20261029-1", "committer_email": "design-office-20261029-1@seat.invalid",
         "role": "design", "machine": "office", "seated_by": "the person", "status": "active",
         "owns": ["design"], "paths": ["*", "contracts/"], "excludes": []},
    ],
}


def with_entry(table, entry):
    new = copy.deepcopy(table)
    new["seats"].append(entry)
    return new


class Names(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(seats.parse_name("meta-macbook-20261109-2"), ("meta", "macbook", "20261109", 2))
        for bad in ("meta-macbook-20261109-0", "meta-macbook-20261340-1", "Meta-macbook-20261109-1", "meta-20261109-1", None):
            self.assertIsNone(seats.parse_name(bad), bad)

    def test_next_name_skips_issued_numbers(self):
        table = with_entry(TABLE, seats.entry_for(TABLE, "meta-office-20261109-1", "self"))
        self.assertEqual(seats.next_name(TABLE, "meta", "office", "20261109"), "meta-office-20261109-1")
        self.assertEqual(seats.next_name(table, "meta", "office", "20261109"), "meta-office-20261109-2")
        self.assertEqual(seats.next_name(table, "meta", "macbook", "20261109"), "meta-macbook-20261109-1")

    def test_entry_is_the_roles_row(self):
        e = seats.entry_for(TABLE, "meta-macbook-20261109-1", "self, rule")
        self.assertEqual((e["paths"], e["excludes"], e["owns"]), (["meta_agent/"], ["meta_agent/CLAUDE.md"], ["meta_agent"]))
        self.assertEqual(e["committer_email"], "meta-macbook-20261109-1@seat.invalid")
        self.assertEqual(seats.entry_problems(TABLE, e), [])


class Table(unittest.TestCase):
    def test_clean_table(self):
        self.assertEqual(seats.table_problems(TABLE), [])

    def test_the_repositorys_table_is_clean(self):
        self.assertEqual(seats.table_problems(seats.load()), [])

    def test_wider_path_unknown_machine_unknown_role_duplicate(self):
        e = seats.entry_for(TABLE, "meta-office-20261109-1", "self")
        e["paths"].append("contracts/")
        self.assertTrue(any("paths differ" in m for m in seats.table_problems(with_entry(TABLE, e))))
        e = seats.entry_for(TABLE, "meta-office-20261109-1", "self")
        e["seat"], e["committer_email"], e["machine"] = "meta-lab-20261109-1", "meta-lab-20261109-1@seat.invalid", "lab"
        self.assertTrue(any("machine tag" in m for m in seats.table_problems(with_entry(TABLE, e))))
        e = dict(TABLE["seats"][0], seat="operator-office-20261109-1", committer_email="operator-office-20261109-1@seat.invalid", role="operator")
        self.assertTrue(any("a new role" in m for m in seats.table_problems(with_entry(TABLE, e))))
        self.assertTrue(any("issued twice" in m for m in seats.table_problems(with_entry(TABLE, TABLE["seats"][0]))))


class SelfRegistration(unittest.TestCase):
    NAME = "meta-macbook-20261109-1"
    EMAIL = "meta-macbook-20261109-1@seat.invalid"

    def judge(self, new, email=None, day="20261109", old=TABLE):
        return seats.self_registration(json.dumps(old), json.dumps(new), email or self.EMAIL, day)

    def test_a_clean_self_registration(self):
        new = with_entry(TABLE, seats.entry_for(TABLE, self.NAME, "self, under the standing rule"))
        self.assertEqual(self.judge(new), (True, []))

    def test_not_a_candidate_when_the_entry_is_someone_elses(self):
        new = with_entry(TABLE, seats.entry_for(TABLE, self.NAME, "self"))
        self.assertEqual(self.judge(new, email="meta-office-20261029-1@seat.invalid"), (False, []))
        self.assertEqual(self.judge(TABLE), (False, []))

    def test_what_the_rule_refuses(self):
        def problems(mutate, day="20261109"):
            e = seats.entry_for(TABLE, self.NAME, "self, under the standing rule")
            new = with_entry(TABLE, e)
            mutate(new, new["seats"][-1])
            cand, out = self.judge(new, day=day)
            self.assertTrue(cand)
            return " | ".join(out)
        self.assertIn("paths differ", problems(lambda t, e: e["paths"].append("contracts/")))
        self.assertIn("excludes differ", problems(lambda t, e: e.update(excludes=[])))
        self.assertIn("seated_by", problems(lambda t, e: e.update(seated_by="the person, 2026-11-09")))
        self.assertIn("status", problems(lambda t, e: e.update(status="retired")))
        self.assertIn("more of contracts/seats.json", problems(lambda t, e: t["machines"].update(lab="new")))
        self.assertIn("more of contracts/seats.json", problems(lambda t, e: t["roles"]["meta"]["paths"].append("docs/")))
        self.assertIn("day of the commit", problems(lambda t, e: None, day="20261201"))

    def test_a_role_widened_in_the_same_commit_does_not_help(self):
        e = seats.entry_for(TABLE, self.NAME, "self")
        e["paths"].append("docs/")
        new = with_entry(TABLE, e)
        new["roles"]["meta"]["paths"].append("docs/")
        cand, out = self.judge(new)
        self.assertTrue(cand)
        self.assertTrue(any("paths differ" in m for m in out) and any("more of" in m for m in out))


class SeatCommand(unittest.TestCase):
    def run_seat(self, *args):
        return subprocess.run([sys.executable, os.path.join(REPO, "bootstrap.py"), "seat"] + list(args),
                              cwd=REPO, capture_output=True, text=True, encoding="utf-8")

    def test_prints_a_name_and_the_roles_row_and_writes_nothing(self):
        before = open(seats.SEATS_PATH, encoding="utf-8").read()
        p = self.run_seat("meta", "--machine", "macbook")
        self.assertEqual(p.returncode, 0, p.stderr)
        name = p.stdout.split()[1]
        self.assertEqual(seats.parse_name(name)[:2], ("meta", "macbook"))
        entry = json.loads([l for l in p.stdout.splitlines() if l.startswith("entry")][0].split(None, 1)[1])
        self.assertEqual(entry["paths"], seats.load()["roles"]["meta"]["paths"])
        self.assertEqual(open(seats.SEATS_PATH, encoding="utf-8").read(), before)

    def test_refuses_an_unlisted_machine_and_role(self):
        self.assertNotEqual(self.run_seat("meta", "--machine", "lab").returncode, 0)
        self.assertNotEqual(self.run_seat("operator", "--machine", "macbook").returncode, 0)


if __name__ == "__main__":
    unittest.main()
