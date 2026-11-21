"""Run HOOMD-blue on H2 molecules held together by a harmonic bond, in a run folder of its own.

The molecules are placed on a simple cubic grid in a cubic box (box_side), each along x with its two atoms half the
rest length on either side of the grid point; there is no force between molecules, only each one's bond,
hoomd.md.bond.Harmonic with U(r) = k (r - r0)^2 / 2 (mat-20261120-hoomd-7.2.2-bond-harmonic). Momenta are drawn at kT,
and the run integrates at constant volume, hoomd.md.methods.ConstantVolume, with the Bussi thermostat at kT
(mat-20261120-hoomd-7.2.2-methods-constantvolume). Every value is an input of the call and in HOOMD-blue's own units
(mat-20261120-hoomd-7.2.2-units): bond_k and bond_r0 are the rows a received hand-over fills, and what those units
stand for is in envelope/handovers.json. This adapter chooses no value.

Each call makes runs/md/<UTC stamp>/ and never writes into a folder that exists. It writes input.json and run.py there,
runs run.py with this agent's own interpreter through src/engine_wait.py (budget_s counts running time only), and
reads result.json, which run.py writes from what HOOMD-blue reports: the bonds' energy, the potential energy and the
kinetic temperature at the end, and the kinetic temperature and potential energy logged along the run. Read, never
computed here. A run that did not end, or wrote no result, is an error and its folder stays.
"""
import datetime
import json
import os

import engine_wait

BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(BUNDLE, "runs", "env", ".pixi", "envs", "default", "bin", "python")
KEYS = ("bond_k", "bond_r0", "particle_mass", "n_molecules", "box_side", "kT", "dt", "steps", "log_every", "seed")

SCRIPT = r'''
import json, math, sys
import hoomd

p = json.load(open("input.json"))
n = p["n_molecules"]
m = 1
while m ** 3 < n:
    m += 1
L, r0 = p["box_side"], p["bond_r0"]
a = L / m
pos = []
for i in range(n):
    ix, iy, iz = i % m, (i // m) % m, i // (m * m)
    c = [-L / 2 + a * (ix + 0.5), -L / 2 + a * (iy + 0.5), -L / 2 + a * (iz + 0.5)]
    pos.append([c[0] - r0 / 2, c[1], c[2]])
    pos.append([c[0] + r0 / 2, c[1], c[2]])
snap = hoomd.Snapshot()
snap.configuration.box = [L, L, L, 0, 0, 0]
snap.particles.N = 2 * n
snap.particles.types = ["H"]
snap.particles.position[:] = pos
snap.particles.mass[:] = [p["particle_mass"]] * (2 * n)
snap.bonds.N = n
snap.bonds.types = ["H-H"]
snap.bonds.group[:] = [[2 * i, 2 * i + 1] for i in range(n)]
sim = hoomd.Simulation(device=hoomd.device.CPU(), seed=p["seed"])
sim.create_state_from_snapshot(snap)
harmonic = hoomd.md.bond.Harmonic()
harmonic.params["H-H"] = dict(k=p["bond_k"], r0=r0)
method = hoomd.md.methods.ConstantVolume(filter=hoomd.filter.All(),
                                         thermostat=hoomd.md.methods.thermostats.Bussi(kT=p["kT"]))
sim.operations.integrator = hoomd.md.Integrator(dt=p["dt"], methods=[method], forces=[harmonic])
thermo = hoomd.md.compute.ThermodynamicQuantities(filter=hoomd.filter.All())
sim.operations.computes.append(thermo)
sim.state.thermalize_particle_momenta(filter=hoomd.filter.All(), kT=p["kT"])
series = {"step": [], "kinetic_temperature": [], "potential_energy": []}
done = 0
while done < p["steps"]:
    k = min(p["log_every"], p["steps"] - done)
    sim.run(k)
    done += k
    series["step"].append(sim.timestep)
    series["kinetic_temperature"].append(thermo.kinetic_temperature)
    series["potential_energy"].append(thermo.potential_energy)
    print("step", sim.timestep, flush=True)
json.dump({"hoomd_version": hoomd.version.version, "steps_run": done, "bond_energy": harmonic.energy,
           "potential_energy": thermo.potential_energy, "kinetic_temperature": thermo.kinetic_temperature,
           "series": series}, open("result.json", "w"))
'''


def error(code, category, message, action, retryable=False, evidence=None):
    e = {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category, "message": message,
         "retryable": retryable, "remediation": {"action": action}}
    if evidence is not None:
        e["evidence"] = evidence
    return e


def run(payload):
    if not os.path.isfile(PYTHON):
        return error("HOOMD-ENV-001", "unavailable", "this agent's environment is not made: no %s" % os.path.relpath(PYTHON, BUNDLE),
                     "call install_environment first, then this call again", True)
    missing = [k for k in KEYS if payload.get(k) is None]
    if missing:
        return error("HOOMD-RUN-INPUT-001", "invalid_input", "no value for %s" % ", ".join(missing),
                     "give every value; bond_k and bond_r0 are what src/handover.py values prints for their rows, and a "
                     "row no hand-over filled is the person's to give")
    if not payload["bond_r0"] < payload["box_side"]:
        return error("HOOMD-RUN-INPUT-002", "invalid_input", "the rest length is not shorter than the box side",
                     "give a box side longer than the rest length")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = os.path.join(BUNDLE, "runs", "md", stamp)
    os.makedirs(work)
    rel = os.path.relpath(work, BUNDLE)
    with open(os.path.join(work, "input.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({k: payload[k] for k in KEYS}, f, indent=2)
    with open(os.path.join(work, "run.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(SCRIPT)
    log = os.path.join(work, "run.log")
    waited = engine_wait.run([PYTHON, "run.py"], cwd=work, budget_s=payload.get("budget_s"), progress=[log],
                             stdout_path=log, stderr_path=os.path.join(work, "run.err"))
    stop = engine_wait.stop_error("run_h2_md", waited)
    if stop is not None:
        stop.setdefault("evidence", {})["run_dir"] = rel
        return stop
    result = os.path.join(work, "result.json")
    if waited["returncode"] != 0 or not os.path.isfile(result):
        return error("HOOMD-RUN-002", "execution_failure",
                     "the run ended with exit status %s and %s" % (waited["returncode"],
                                                                   "a result" if os.path.isfile(result) else "no result"),
                     "read run.err in the run folder", False, {"run_dir": rel})
    with open(result, encoding="utf-8") as f:
        out = json.load(f)
    out.update({"run_dir": rel, "inputs": {k: payload[k] for k in KEYS}})
    return out
