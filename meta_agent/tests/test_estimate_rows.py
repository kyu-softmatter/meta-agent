"""The sheet stage binds an estimate skill to the rows its entries name, once per row (2026-11-17, check 19).

A swept parameter is a row per point; a quantity that follows from it (a drag per diameter) is again a row per
point, each resting on the same estimate with its own basis, and on the output the basis names when the estimate
gives several. A bound keeps its old rule: listed once, written on the row named for its parameter.
"""
import unittest

from meta_agent.src.parameters import bounds

SEAT = "meta-fixture-20261117-1"
NOW = "2026-11-17T12:00:00Z"

PAIR = {"ref": "drag_and_diffusivity@v1", "kind": "estimate", "applies_to": {"parameters": []},
        "inputs": [{"name": "viscosity", "unit": "engine_viscosity"}, {"name": "diameter", "unit": "engine_length"}],
        "outputs": [{"name": "drag", "unit": "engine_drag"}, {"name": "twice_drag", "unit": "engine_drag"}]}
SINGLE = dict(PAIR, ref="drag_only@v1", outputs=[{"name": "drag", "unit": "engine_drag"}])
FLOOR = {"ref": "spacing_floor@v1", "kind": "bound", "parameter": "spacing", "side": "min",
         "applies_to": {"parameters": ["spacing"]}, "inputs": [{"name": "diameter", "unit": "engine_length"}],
         "outputs": [{"name": "spacing_min", "unit": "engine_length"}]}


def run(ref, inputs):
    drag = 3.0 * inputs.get("viscosity", 1.0) * inputs["diameter"]
    return {"verdict": "ran", "outputs": {"drag": drag, "twice_drag": 2 * drag, "spacing_min": inputs["diameter"]}}


def row(name, value, unit):
    return {"name": name, "value": value, "unit": unit, "source": "assumed:a_fixture_choice", "value_kind": "estimated",
            "uncertainty": None, "safety_relevant": False, "stage": "discovery"}


def empty(name, unit):
    return {"name": name, "value": None, "unit": unit, "source": None, "grade": None, "value_kind": None,
            "safety_relevant": False, "stage": "reasoning"}


def draft():
    return {"id": "ps-fixture-sweep-001", "rid": "req-fixture-sweep-001", "tool": "fixture_engine",
            "tool_ref": {"kind": "engine", "registry_id": None},
            "rows": [row("viscosity", 1.0, "engine_viscosity"), row("diameter_a", 0.5, "engine_length"),
                     row("diameter_b", 2.0, "engine_length"), row("spacing", 3.0, "engine_length"),
                     empty("drag_a", "engine_drag"), empty("drag_b", "engine_drag")]}


def entry(skill, target, diameter, output=None):
    e = {"skill": skill, "verdict": "used", "why": "the drag of each diameter", "target": target,
         "inputs": {"viscosity": "viscosity", "diameter": diameter}}
    if output:
        e["output"] = output
    return e


class EstimateRows(unittest.TestCase):
    def apply(self, entries, skills=(PAIR, SINGLE, FLOOR)):
        binding = {"skills": list(entries) + [{"skill": "spacing_floor@v1", "verdict": "used", "why": "floor",
                                               "inputs": {"diameter": "diameter_b"}}]}
        return bounds.apply(draft(), binding, list(skills), run, SEAT, NOW)

    def test_one_estimate_fills_a_row_per_point_at_the_output_it_names(self):
        sheet = self.apply([entry("drag_and_diffusivity@v1", "drag_a", "diameter_a", "drag"),
                            entry("drag_and_diffusivity@v1", "drag_b", "diameter_b", "drag")])
        rows = {r["name"]: r for r in sheet["rows"]}
        self.assertEqual((rows["drag_a"]["value"], rows["drag_b"]["value"]), (1.5, 6.0))
        self.assertEqual(rows["drag_a"]["basis"], {"skill": "drag_and_diffusivity@v1", "output": "drag",
                                                   "inputs": {"viscosity": "viscosity", "diameter": "diameter_a"}})
        self.assertEqual(rows["drag_b"]["source"], "computed:drag_and_diffusivity@v1")
        self.assertEqual([c["skill"] for c in sheet["skills_considered"]], ["drag_and_diffusivity@v1", "spacing_floor@v1"])

    def test_an_estimate_of_one_output_needs_no_output_and_its_basis_names_none(self):
        sheet = self.apply([entry("drag_only@v1", "drag_a", "diameter_a"), entry("drag_only@v1", "drag_b", "diameter_b")])
        rows = {r["name"]: r for r in sheet["rows"]}
        self.assertEqual(rows["drag_b"]["value"], 6.0)
        self.assertNotIn("output", rows["drag_b"]["basis"])

    def test_an_estimate_of_several_outputs_without_output_is_refused(self):
        with self.assertRaises(bounds.BindingError):
            self.apply([entry("drag_and_diffusivity@v1", "drag_a", "diameter_a")])

    def test_one_target_twice_is_refused(self):
        with self.assertRaises(bounds.BindingError):
            self.apply([entry("drag_only@v1", "drag_a", "diameter_a"), entry("drag_only@v1", "drag_a", "diameter_b")])

    def test_an_estimate_without_a_target_row_is_refused(self):
        with self.assertRaises(bounds.MissingRow):
            self.apply([entry("drag_only@v1", "drag_c", "diameter_a")])

    def test_a_bound_listed_twice_is_still_refused(self):
        binding = {"skills": [{"skill": "spacing_floor@v1", "verdict": "used", "why": "floor", "inputs": {"diameter": "diameter_a"}},
                              {"skill": "spacing_floor@v1", "verdict": "used", "why": "floor", "inputs": {"diameter": "diameter_b"}}]}
        with self.assertRaises(bounds.BindingError):
            bounds.apply(draft(), binding, [FLOOR], run, SEAT, NOW)


class RealEstimatesOnTwoKinds(unittest.TestCase):
    """The same binding on the library's own estimate skills, through the skill runner, on two unrelated kinds (landed from
    the clone of run 20261117-3, commit d9d3f98, with this class added): a simulation box swept over particle counts, and
    an instrument's acquisition swept over target signal-to-noise ratios. Each skill gives two outputs, so each entry names
    the output its row is."""

    def sheet(self, library, ref, rows, entries):
        from meta_agent.src.skills import catalogue, runner
        skills = catalogue.take([ref], library)
        d = {"id": "ps-fixture-%s" % ref.split("@")[0], "rid": "req-fixture", "tool": "fixture",
             "tool_ref": {"kind": "engine", "registry_id": None}, "rows": rows}
        out = bounds.apply(d, {"skills": entries}, skills, lambda r, i: runner.run(r, i, library=library, now=NOW), SEAT, NOW)
        return {r["name"]: r for r in out["rows"]}, (lambda inputs: runner.run(ref, inputs, library=library, now=NOW)["outputs"])

    def test_a_box_per_particle_count(self):
        from meta_agent.src.skills import LIBRARY
        ref = "box_length_for_volume_fraction@v1"
        rows = [row("count_small", 8, "count"), row("count_large", 1000, "count"), row("volume", 1.0, "engine_length^3"),
                row("fraction", 0.5, "1"), empty("box_small", "engine_length"), empty("box_large", "engine_length")]
        e = lambda target, count: {"skill": ref, "verdict": "used", "why": "the box of each count", "target": target,
                                   "output": "box_length", "inputs": {"particle_count": count, "particle_volume": "volume",
                                                                      "volume_fraction": "fraction"}}
        got, direct = self.sheet(LIBRARY, ref, rows, [e("box_small", "count_small"), e("box_large", "count_large")])
        for target, count in (("box_small", 8), ("box_large", 1000)):
            want = direct({"particle_count": count, "particle_volume": 1.0, "volume_fraction": 0.5})["box_length"]
            self.assertAlmostEqual(got[target]["value"], want)
            self.assertEqual(got[target]["basis"]["output"], "box_length")
        self.assertNotEqual(got["box_small"]["value"], got["box_large"]["value"])

    def test_an_acquisition_time_per_target(self):
        import os
        from meta_agent.src.skills import REPO
        library = os.path.join(REPO, "contracts", "examples", "skills")
        ref = "scans_for_signal_to_noise@v1"
        rows = [row("snr_one_scan", 2.0, "1"), row("scan_time", 10.0, "s"), row("target_low", 10.0, "1"),
                row("target_high", 20.0, "1"), empty("time_low", "s"), empty("time_high", "s")]
        e = lambda target, snr: {"skill": ref, "verdict": "used", "why": "the time of each target", "target": target,
                                 "output": "acquisition_time", "inputs": {"single_scan_snr": "snr_one_scan",
                                                                          "single_scan_time": "scan_time", "target_snr": snr}}
        got, direct = self.sheet(library, ref, rows, [e("time_low", "target_low"), e("time_high", "target_high")])
        for target, snr in (("time_low", 10.0), ("time_high", 20.0)):
            want = direct({"single_scan_snr": 2.0, "single_scan_time": 10.0, "target_snr": snr})["acquisition_time"]
            self.assertAlmostEqual(got[target]["value"], want)
            self.assertEqual(got[target]["basis"], {"skill": ref, "output": "acquisition_time", "inputs": {
                "single_scan_snr": "snr_one_scan", "single_scan_time": "scan_time",
                "target_snr": "target_low" if target == "time_low" else "target_high"}})
        self.assertLess(got["time_low"]["value"], got["time_high"]["value"])


if __name__ == "__main__":
    unittest.main()
