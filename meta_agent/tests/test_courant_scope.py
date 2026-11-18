"""The Courant bound is offered by what a sheet steps in time, not by the program's name (failures.jsonl cfd-1, run
cfd/20261117-1, tasks/019): v1 named rheotool and openfoam alone, so a DOLFINx flow was offered no bound on its time
step; v2 names no engine. Shown on two unrelated kinds, a flow by finite elements and an electromagnetic wave by
finite differences in time, and run through the runner on each."""
import os
import unittest

from meta_agent.src.parameters import bounds
from meta_agent.src.skills import catalogue, runner

META = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY = os.path.join(META, "skills")
V1, V2 = "timestep_max_from_courant@v1", "timestep_max_from_courant@v2"
NOW = "2026-11-17T20:00:00Z"
FLOW = (["time_step", "final_time", "inflow_peak_velocity"], {"registry_id": "fenicsx"})
WAVE = (["time_step", "resolution", "cell_size"], {"registry_id": "meep"})
NO_STEP = (["volume_fraction", "steps"], {"registry_id": "hoomd_blue"})


def offered(names, tool_ref):
    skills = [r for r in catalogue.build_index(LIBRARY)["skills"] if r["kind"] == "bound"]
    return {r["ref"] for r in bounds.applicable(skills, names, tool_ref)}


class CourantScope(unittest.TestCase):
    def test_v1_is_not_offered_to_a_flow_or_a_wave_outside_two_engines(self):
        self.assertNotIn(V1, offered(*FLOW))
        self.assertNotIn(V1, offered(*WAVE))
        self.assertIn(V1, offered(["time_step"], {"registry_id": "openfoam"}))

    def test_v2_is_offered_to_a_flow_and_to_a_wave(self):
        self.assertIn(V2, offered(*FLOW))
        self.assertIn(V2, offered(*WAVE))

    def test_v2_is_not_offered_to_a_sheet_with_no_time_step(self):
        self.assertNotIn(V2, offered(*NO_STEP))

    def test_v2_runs_on_each_kind_and_a_faster_signal_gives_a_shorter_step(self):
        flow = runner.run(V2, {"courant_limit": 0.5, "cell_size": 0.001, "velocity": 2.0}, library=LIBRARY, now=NOW)
        wave = runner.run(V2, {"courant_limit": 0.5, "cell_size": 1e-08, "velocity": 299792458.0}, library=LIBRARY, now=NOW)
        self.assertEqual((flow["verdict"], wave["verdict"]), ("ran", "ran"))
        step = lambda r: r["outputs"]["time_step_max"]
        self.assertAlmostEqual(step(flow), 0.00025, places=12)
        self.assertAlmostEqual(step(wave) / 1.66782047599076e-17, 1.0, places=9)


if __name__ == "__main__":
    unittest.main()
