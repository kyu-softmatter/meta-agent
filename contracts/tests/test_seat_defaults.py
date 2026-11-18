# -*- coding: utf-8 -*-
"""Tests of a copy's first seat (the person, 2026-11-18, docs/ideas/20261118.md, "A distributed copy seats meta
by default"): `bootstrap.py seat` with no role takes the table's default role, meta, and a role the person names
still holds; `bootstrap.py machine TAG DESCRIPTION` records the tag the person of a new copy gives its computer,
in contracts/seats.json and in the clone's git configuration, so that the copy's first seat is not refused.

Each test builds a temporary repository from this one's bootstrap.py and contracts/tools/seats.py with a small
seats table, so the real contracts/seats.json is never touched.

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import copy
import datetime
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import seats  # noqa: E402

TODAY = datetime.date.today().strftime("%Y%m%d")
TABLE = {
    "default_role": "meta",
    "machines": {"office": "a computer"},
    "roles": {
        "design": {"paths": ["*", "contracts/"], "excludes": [], "owns": ["design"]},
        "meta": {"paths": ["meta_agent/"], "excludes": ["meta_agent/CLAUDE.md"], "owns": ["meta_agent"]},
    },
    "seats": [],
}


def run(cwd, *cmd):
    return subprocess.run(list(cmd), cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")


class Copy(unittest.TestCase):
    machine = "office"
    table = TABLE

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="seat-defaults-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        os.makedirs(os.path.join(self.dir, "contracts", "tools"))
        os.makedirs(os.path.join(self.dir, "hooks-none"))
        shutil.copy(os.path.join(REPO, "bootstrap.py"), self.dir)
        shutil.copy(os.path.join(REPO, "contracts", "tools", "seats.py"), os.path.join(self.dir, "contracts", "tools"))
        with open(os.path.join(self.dir, "contracts", "seats.json"), "w", encoding="utf-8") as f:
            f.write(seats.dump(copy.deepcopy(self.table)))
        for args in (("init", "-q"), ("config", "user.name", "a person"), ("config", "user.email", "person@example.invalid"),
                     ("config", "core.hooksPath", "hooks-none"), ("config", "commit.gpgsign", "false")):
            self.assertEqual(run(self.dir, "git", *args).returncode, 0)
        if self.machine:
            run(self.dir, "git", "config", "meta-agent.machine", self.machine)
        run(self.dir, "git", "add", "bootstrap.py", "contracts")
        run(self.dir, "git", "commit", "-q", "-m", "start")

    def boot(self, *args):
        return run(self.dir, sys.executable, "bootstrap.py", *args)

    def loaded(self):
        return seats.load(os.path.join(self.dir, "contracts", "seats.json"))


class DefaultRole(Copy):
    def test_no_role_named_takes_the_default_meta(self):
        p = self.boot("seat")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stdout.split()[1], "meta-office-%s-1" % TODAY)
        self.assertIn("default role", p.stdout)

    def test_a_named_role_still_holds(self):
        p = self.boot("seat", "design")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(p.stdout.split()[1], "design-office-%s-1" % TODAY)
        self.assertNotIn("default role", p.stdout)

    def test_the_default_written_is_the_meta_row(self):
        p = self.boot("seat", "--write")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        entry = self.loaded()["seats"][-1]
        self.assertEqual(entry["role"], "meta")
        self.assertEqual(entry["paths"], TABLE["roles"]["meta"]["paths"])


class NoDefault(Copy):
    table = dict(TABLE, default_role=None)

    def test_no_role_and_no_default_is_refused(self):
        p = self.boot("seat")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("names no default role", p.stdout + p.stderr)


class NewComputer(Copy):
    machine = None

    def test_a_copy_with_no_tag_says_how_to_give_one(self):
        p = self.boot("seat")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("bootstrap.py machine", p.stdout + p.stderr)

    def test_without_write_nothing_changes(self):
        p = self.boot("machine", "lab", "the lab's workstation")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertNotIn("lab", self.loaded()["machines"])
        self.assertEqual(run(self.dir, "git", "config", "--get", "meta-agent.machine").stdout.strip(), "")

    def test_the_tag_is_recorded_and_the_first_seat_follows(self):
        p = self.boot("machine", "lab", "the lab's workstation", "--write")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(self.loaded()["machines"]["lab"], "the lab's workstation")
        self.assertEqual(run(self.dir, "git", "config", "--get", "meta-agent.machine").stdout.strip(), "lab")
        self.assertIn("its own commit", p.stdout)
        s = self.boot("seat")
        self.assertEqual(s.returncode, 0, s.stdout + s.stderr)
        self.assertEqual(s.stdout.split()[1], "meta-lab-%s-1" % TODAY)

    def test_a_known_tag_or_a_bad_tag_is_refused(self):
        for tag in ("office", "Lab-2", ""):
            p = self.boot("machine", tag, "a computer", "--write")
            self.assertNotEqual(p.returncode, 0, tag)
        self.assertEqual(sorted(self.loaded()["machines"]), ["office"])

    def test_a_description_is_required(self):
        p = self.boot("machine", "lab", "--write")
        self.assertNotEqual(p.returncode, 0)
        self.assertNotIn("lab", self.loaded()["machines"])


if __name__ == "__main__":
    unittest.main()
