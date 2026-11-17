"""Parameter rows a contract names (tasks/016, run 20261117-3; bundle check B17, landed in 1b9c759).

A contract input that a parameter row gives names that row under `row`, where B17 reads it, and not in its
description alone; the intake stage refuses the second. The rows a bundle's envelope/parameters.json is made from are
the intake's parameter_rows, or where it gives none the request's newest parameter_sheet; the Designer takes them so,
and stops with nothing written where a contract names a row that neither gives (the clone's failure line hpmc-r9-1).

Two unrelated kinds: an engine whose render takes a size and whose compression takes a number of steps, and a
spectrometer whose reading takes an integration time.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src import designer
from meta_agent.src.intake import card as card_mod

# kind: (tool, input, the row that gives it, a second input nested under settings)
KINDS = {"engine": ("render", "size", "render_size", "compress_steps"),
         "spectrometer": ("read_spectrum", "integration", "integration_time", "dark_frames")}


def contract(kind, in_words=False, named=True):
    tool, key, row, nested = KINDS[kind]
    prop = {"type": "number", "unit": "1", "description": ("taken from the row %s" % row) if in_words else "the setting"}
    if named:
        prop["row"] = row
    deep = {"type": "object", "properties": {nested: dict({"type": "integer", "unit": "count"}, **({"row": nested} if named else {}))}}
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": tool, "description": tool,
            "inputs": {"type": "object", "properties": {key: prop, "settings": deep}, "required": [key]},
            "outputs": {"type": "object", "properties": {}}, "errors": ["invalid_input"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "no side effects"}, "idempotent": True, "timeout_s": None}


def intake(kind, rows=None, **kw):
    c = {"rid": "req-%s" % kind, "stage": "specified", "tools": [{"contract": contract(kind, **kw), "adapter_source": "x"}]}
    if rows is not None:
        c["parameter_rows"] = [{"name": n, "value": None, "unit": "1"} for n in rows]
    return c


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-rows-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def req(self, kind, sheets=()):
        """A request folder with the given sheets, oldest first, each a list of row names."""
        d = os.path.join(self.tmp, kind)
        os.makedirs(d, exist_ok=True)
        for i, names in enumerate(sheets):
            fn = "parameter_sheet.json" if i == 0 else "v%d_parameter_sheet.json" % (i + 1)
            cards.write_json(os.path.join(d, fn), {"card": "parameter_sheet", "revision": i + 1,
                                                   "rows": [{"name": n, "value": None, "unit": "1"} for n in names]})
        return d

    @staticmethod
    def both(kind):
        return [KINDS[kind][2], KINDS[kind][3]]


class TheIntakeStage(Fixture):
    def test_a_row_named_in_words_alone_is_refused_and_one_named_under_row_is_not(self):
        for kind in KINDS:
            words = " ".join(card_mod.row_problems(intake(kind, rows=self.both(kind), in_words=True, named=False)))
            self.assertIn("its description names the row %s in words" % KINDS[kind][2], words, kind)
            self.assertEqual(card_mod.row_problems(intake(kind, rows=self.both(kind), in_words=True)), [], kind)

    def test_ordinary_words_after_row_are_not_a_row(self):
        c = intake("engine", rows=self.both("engine"), named=False)
        c["tools"][0]["contract"]["inputs"]["properties"]["size"]["description"] = "one row of the sheet, given per run"
        self.assertEqual(card_mod.row_problems(c), [])

    def test_the_rows_named_are_read_at_any_depth(self):
        for kind in KINDS:
            got = card_mod.named_rows(intake(kind))
            self.assertEqual(sorted(r for _, r in got[KINDS[kind][0]]), sorted(self.both(kind)), kind)

    def test_a_named_row_must_be_one_the_bundle_will_carry(self):
        for kind in KINDS:
            row, nested = KINDS[kind][2], KINDS[kind][3]
            self.assertEqual(card_mod.row_problems(intake(kind, rows=self.both(kind))), [], kind)
            words = " ".join(card_mod.row_problems(intake(kind, rows=[row])))
            self.assertIn("the contracts name %s, which the intake's parameter_rows does not hold" % nested, words)
            words = " ".join(card_mod.row_problems(intake(kind), self.req(kind)))
            self.assertIn("neither the intake's parameter_rows nor a parameter sheet of the request gives", words)

    def test_without_parameter_rows_the_newest_sheet_is_read(self):
        for kind in KINDS:
            d = self.req(kind, sheets=[self.both(kind), [KINDS[kind][2]]])      # the newest lost a row
            words = " ".join(card_mod.row_problems(intake(kind), d))
            self.assertIn("the request's newest parameter sheet v2_parameter_sheet.json does not hold", words, kind)
            self.assertIn(KINDS[kind][3], words)
            d2 = self.req(kind + "-2", sheets=[[KINDS[kind][2]], self.both(kind)])
            self.assertEqual(card_mod.row_problems(intake(kind), d2), [], kind)


class TheDesigner(Fixture):
    def test_an_intake_without_rows_takes_the_newest_sheet(self):
        for kind in KINDS:
            d = self.req(kind, sheets=[[KINDS[kind][2]], self.both(kind) + ["extra"]])
            got = designer.with_parameter_rows(intake(kind), d)
            self.assertEqual([r["name"] for r in got["parameter_rows"]], self.both(kind) + ["extra"], kind)
            self.assertNotIn("parameter_rows", intake(kind))        # nothing is written back

    def test_an_intake_with_rows_keeps_its_own(self):
        for kind in KINDS:
            d = self.req(kind, sheets=[self.both(kind) + ["from_the_sheet"]])
            got = designer.with_parameter_rows(intake(kind, rows=self.both(kind)), d)
            self.assertEqual([r["name"] for r in got["parameter_rows"]], self.both(kind), kind)

    def test_a_row_neither_gives_stops_the_build(self):
        for kind in KINDS:
            with self.assertRaises(designer.Stopped) as cm:
                designer.with_parameter_rows(intake(kind), self.req(kind))
            self.assertIn(KINDS[kind][2], str(cm.exception))
            self.assertIn("neither the intake's parameter_rows nor a parameter sheet", str(cm.exception))
            with self.assertRaises(designer.Stopped) as cm:
                designer.with_parameter_rows(intake(kind), self.req(kind + "-old", sheets=[[KINDS[kind][2]]]))
            self.assertIn("%s, which the request's newest parameter sheet parameter_sheet.json does not hold" % KINDS[kind][3],
                          str(cm.exception))

    def test_contracts_that_name_no_row_need_none(self):
        for kind in KINDS:
            c = intake(kind, named=False)
            self.assertIs(designer.with_parameter_rows(c, self.req(kind)), c)


if __name__ == "__main__":
    unittest.main()
