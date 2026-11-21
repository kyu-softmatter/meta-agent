"""Template v31 and the builder (meta_agent/failures.jsonl rheotool-27; the design role's manifest field unit_of,
7a4b9fc): a common skill's output in the unit of its readings names the input it takes it from, and the builder
follows that input through the task's analysis to the unit the tool's contract declares for the field it hands, so a
tolerance derived on such an output carries the quantity's unit. Under the previous versions of the skills it came out
'1'.

Two unrelated kinds, neither rheology: a heater's temperature trace in K, measured by its largest value, and a
spectrometer's settled line energy in eV, measured by the mean of its last window.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod

V30, V31 = template_mod.SOURCES["v30"], template_mod.SOURCES["v31"]
RULE = cards.load_json(os.path.join(V31, "TEMPLATE.json"))["tolerance_rule"]

# each kind: tool, its output field, the field's unit, the analysis skill (new and old), its data input, its output,
# the analysis's rows, the stated value as printed
KINDS = {
    "heater": ("heat_sample", "temperature_trace", "K", ("series_maximum@v3", "series_maximum@v2"), "series", "maximum",
               {}, "353.2"),
    "spectrometer": ("read_line", "energy_series", "eV", ("series_settled@v5", "series_settled@v4"), "series", "last_mean",
                     {"window": "settle_window", "tolerance": "settle_tolerance"}, "2.15"),
}


def tool(kind):
    name, field, unit = KINDS[kind][:3]
    return {"name": name, "contract": {"outputs": {"type": "object", "properties": {
        field: {"type": "array", "unit": unit, "description": "the readings, in %s" % unit}}}}}


def task(kind, skill):
    name, field, unit, _, data_input, output, rows, printed = KINDS[kind]
    return {"id": "sci-a", "call": {"tool": name, "input": {}},
            "analysis": {"skill": skill, "data": {"field": field, "input": data_input}, "rows": rows, "output": output},
            "measure": {"stated": {output: float(printed)}, "printed": {output: printed}},
            "reference": {"kind": "source", "ref": "a test's reference"}, "expected_verdict": "pass"}


class TheUnitIsFollowed(unittest.TestCase):
    def test_the_stated_unit_is_the_contract_s_unit_of_the_field_handed(self):
        for kind, k in KINDS.items():
            new = k[3][0]
            self.assertEqual(bundle_mod.stated_unit(task(kind, new), [tool(kind)], catalogue_mod.take([new])), k[2], kind)

    def test_under_the_previous_version_it_was_one(self):
        for kind, k in KINDS.items():
            old = k[3][1]
            self.assertEqual(bundle_mod.stated_unit(task(kind, old), [tool(kind)], catalogue_mod.take([old])), "1", kind)

    def test_a_tolerance_the_rule_derives_carries_the_unit(self):
        for kind, k in KINDS.items():
            new = k[3][0]
            t = bundle_mod.with_rule_tolerance(task(kind, new), RULE, [tool(kind)], catalogue_mod.take([new]))
            self.assertEqual((t["tolerance"]["from"], t["tolerance"]["unit"]), ("last_printed_digit", k[2]), kind)

    def test_the_independent_variable_s_unit_is_not_guessed(self):
        # series_maximum@v3's `at` takes the unit of the pairs' variable, which no contract names
        t = task("heater", "series_maximum@v3")
        t["analysis"]["output"], t["measure"] = "at", {"stated": {"at": 12.0}, "printed": {"at": "12.0"}}
        self.assertEqual(bundle_mod.stated_unit(t, [tool("heater")], catalogue_mod.take(["series_maximum@v3"])), "1")

    def test_the_agreement_skill_s_magnitude_takes_the_measured_unit(self):
        row = catalogue_mod.take(["measurement_error@v3"])[0]
        self.assertEqual({o["name"]: o.get("unit_of") for o in row["outputs"]}, {"error": "measured", "magnitude": "measured"})


class TheVersion(unittest.TestCase):
    def test_v31_is_the_latest_and_changes_its_card_alone(self):
        self.assertIn("v31", template_mod.SOURCES)                  # v32 is the latest since two agents hand values over
        changed = sorted(r for r in cards.tree_files(V30) if cards.sha256_file(os.path.join(V30, r)) != cards.sha256_file(os.path.join(V31, r)))
        self.assertEqual(changed, ["TEMPLATE.json"])
        m = cards.load_json(os.path.join(V31, "TEMPLATE.json"))
        self.assertEqual(m["agreement_skill"], "measurement_error@v3")
        for ref in ("measurement_error@v3", "series_maximum@v3", "series_settled@v5"):
            self.assertIn(ref, m["common_skills"])
        for ref in ("measurement_error@v2", "series_maximum@v2", "series_settled@v4"):
            self.assertNotIn(ref, m["common_skills"])


if __name__ == "__main__":
    unittest.main()
