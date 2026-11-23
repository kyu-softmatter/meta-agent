# -*- coding: utf-8 -*-
"""Tests of bundle check B19: a bundle of template v40 or later carries the grade table (dft-14; the person,
2026-11-23, "Yes, carry a copy (Recommended)"). The rejected fixtures are an engine bundle without the table
and an instrument bundle whose copy widens a row; here, what passes. Two unrelated kinds: a DFT engine and a
laboratory balance.

Run from the repository root:  python -m unittest discover -s contracts/tests
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

with open(os.path.join(REPO, "contracts", "grades.json"), encoding="utf-8") as _f:
    TABLE = json.load(_f)


class B19(unittest.TestCase):
    def judge(self, version, kind, table=None):
        d = tempfile.mkdtemp(prefix="b19-")
        self.addCleanup(shutil.rmtree, d, True)
        os.makedirs(os.path.join(d, "envelope"))
        with open(os.path.join(d, "TEMPLATE.json"), "w", encoding="utf-8") as f:
            json.dump({"schema_version": "0.1", "template": "agent", "version": version}, f)
        with open(os.path.join(d, "CAPABILITIES.json"), "w", encoding="utf-8") as f:
            json.dump({"schema_version": "0.1", "tool_kind": kind}, f)
        if table is not None:
            with open(os.path.join(d, "envelope", "grades.json"), "w", encoding="utf-8") as f:
                json.dump(table, f)
        report = validate.Report(quiet=True)
        validate.checkB19(d, "bundle", report)
        return [m for _, _, m in report.fails]

    def test_a_copy_of_the_table_passes(self):
        for kind in ("engine", "instrument"):
            self.assertEqual(self.judge("v40", kind, TABLE), [], kind)

    def test_a_copy_made_before_a_row_was_added_passes(self):
        older = dict(TABLE, rules=TABLE["rules"][:-1])
        self.assertEqual(self.judge("v41", "engine", older), [])
        retired = json.loads(json.dumps(TABLE))
        retired["rules"][0]["retired_on"] = "2026-12-01"    # a row's retired_on aside, on either side, it is the row
        self.assertEqual(self.judge("v41", "instrument", retired), [])

    def test_a_missing_table_or_another_forbidden_list_fails(self):
        self.assertEqual(len(self.judge("v40", "engine")), 1)
        self.assertEqual(len(self.judge("v40", "instrument", dict(TABLE, forbidden_grades=[]))), 1)

    def test_a_bundle_of_an_earlier_template_is_not_judged(self):
        self.assertEqual(self.judge("v39", "engine"), [])


if __name__ == "__main__":
    unittest.main()
