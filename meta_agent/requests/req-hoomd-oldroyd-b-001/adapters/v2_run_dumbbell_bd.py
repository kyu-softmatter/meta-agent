"""Run HOOMD-blue's Brownian dynamics on Hookean dumbbells in an implicit solvent, in a run folder of its own.

Each dumbbell is two beads of one type joined by hoomd.md.bond.Harmonic with r0 = 0, U(r) = k r^2 / 2, a Hookean spring
(mat-20261120-hoomd-7.2.2-bond-harmonic); there is no force between dumbbells. The dumbbells' centres are placed on a
simple cubic grid in a cubic box (box_side), each with its two beads initial_separation apart along x. The beads move by
hoomd.md.methods.Brownian at kT with the drag coefficient bead_drag (mat-20261121-hoomd-7.2.2-methods-brownian). After
equilibration_steps, the off-diagonal components xy, xz and yz of hoomd.md.compute.ThermodynamicQuantities.pressure_tensor
(mat-20261121-hoomd-7.2.2-compute-thermodynamicquantities) are logged every sample_every steps for steps steps, and
returned as three lists in the order xy, xz, yz, with
Simulation.always_compute_pressure set, without which HOOMD-blue computes the virial only on steps a GSD writer or an NPT
integrator needs it and the tensor read between them is not a number (mat-20261121-hoomd-7.2.2-simulation). Every
value is an input of the call and in HOOMD-blue's own units (mat-20261120-hoomd-7.2.2-units); the thermostat's kT and
the step are read back from HOOMD-blue, and the interval between two samples is the integrator's step times sample_every,
the call's own count. The call's inputs are returned under inputs, the conditions the run held under. This adapter chooses no
value and computes nothing from what it logs: the relaxation time and the polymer viscosity are the library skills'
(autocorrelation_of_series, shear_relaxation_modulus_green_kubo, exponential_decay_fit).

Each call makes runs/bd/<UTC stamp>/ and never writes into a folder that exists. It writes input.json and run.py there,
runs run.py with this agent's own interpreter through src/engine_wait.py (budget_s counts running time only), and
reads result.json, which run.py writes from what HOOMD-blue reports. A run that did not end, or wrote no result, is an
error and its folder stays.
"""
import datetime
import json
import os

import engine_wait

BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON = os.path.join(BUNDLE, "runs", "env", ".pixi", "envs", "default", "bin", "python")
KEYS = ("n_dumbbells", "box_side", "spring_k", "initial_separation", "bead_mass", "bead_drag", "kT", "dt",
        "equilibration_steps", "steps", "sample_every", "seed")
COUNTS = ("n_dumbbells", "equilibration_steps", "steps", "sample_every", "seed")

SCRIPT = r'''
import json
import hoomd

p = json.load(open("input.json"))
n, L, s = p["n_dumbbells"], p["box_side"], p["initial_separation"]
m = 1
while m ** 3 < n:
    m += 1
a = L / m
pos = []
for i in range(n):
    ix, iy, iz = i % m, (i // m) % m, i // (m * m)
    c = [-L / 2 + a * (ix + 0.5), -L / 2 + a * (iy + 0.5), -L / 2 + a * (iz + 0.5)]
    pos.append([c[0] - s / 2, c[1], c[2]])
    pos.append([c[0] + s / 2, c[1], c[2]])
snap = hoomd.Snapshot()
snap.configuration.box = [L, L, L, 0, 0, 0]
snap.particles.N = 2 * n
snap.particles.types = ["B"]
snap.particles.position[:] = pos
snap.particles.mass[:] = [p["bead_mass"]] * (2 * n)
snap.bonds.N = n
snap.bonds.types = ["spring"]
snap.bonds.group[:] = [[2 * i, 2 * i + 1] for i in range(n)]
sim = hoomd.Simulation(device=hoomd.device.CPU(), seed=p["seed"])
sim.create_state_from_snapshot(snap)
sim.always_compute_pressure = True
spring = hoomd.md.bond.Harmonic()
spring.params["spring"] = dict(k=p["spring_k"], r0=0.0)
bd = hoomd.md.methods.Brownian(filter=hoomd.filter.All(), kT=p["kT"])
bd.gamma["B"] = p["bead_drag"]
sim.operations.integrator = hoomd.md.Integrator(dt=p["dt"], methods=[bd], forces=[spring])
thermo = hoomd.md.compute.ThermodynamicQuantities(filter=hoomd.filter.All())
sim.operations.computes.append(thermo)
sim.run(p["equilibration_steps"])
print("equilibrated", sim.timestep, flush=True)
xy, xz, yz = [], [], []
done = 0
while done < p["steps"]:
    sim.run(p["sample_every"])
    done += p["sample_every"]
    t = thermo.pressure_tensor
    xy.append(t[1]); xz.append(t[2]); yz.append(t[4])
    if len(xy) % 1000 == 0:
        print("step", sim.timestep, flush=True)
json.dump({"hoomd_version": hoomd.version.version, "steps_run": done, "volume": sim.state.box.volume,
           "kinetic_temperature": thermo.kinetic_temperature, "bond_energy": spring.energy,
           "thermostat_kT": bd.kT(sim.timestep), "integrator_dt": sim.operations.integrator.dt,
           "sample_interval": sim.operations.integrator.dt * p["sample_every"],
           "pressure_tensor_offdiagonal": [xy, xz, yz]}, open("result.json", "w"))
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
        return error("HOOMD-BD-INPUT-001", "invalid_input", "no value for %s" % ", ".join(missing),
                     "give every value; none of them is chosen by this agent")
    bad = [k for k in COUNTS if not isinstance(payload[k], int) or isinstance(payload[k], bool) or payload[k] < (0 if k in ("equilibration_steps", "seed") else 1)]
    if bad:
        return error("HOOMD-BD-INPUT-002", "invalid_input", "%s must be whole numbers" % ", ".join(bad),
                     "give counts as whole numbers, steps and sample_every at least one")
    if payload["steps"] % payload["sample_every"]:
        return error("HOOMD-BD-INPUT-003", "invalid_input", "steps is not a multiple of sample_every",
                     "give steps as a whole number of samples")
    if not (0 < payload["initial_separation"] < payload["box_side"]):
        return error("HOOMD-BD-INPUT-004", "invalid_input", "the initial separation is not between zero and the box side",
                     "give a positive initial separation shorter than the box side")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = os.path.join(BUNDLE, "runs", "bd", stamp)
    os.makedirs(work)
    rel = os.path.relpath(work, BUNDLE)
    with open(os.path.join(work, "input.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({k: payload[k] for k in KEYS}, f, indent=2)
    with open(os.path.join(work, "run.py"), "w", encoding="utf-8", newline="\n") as f:
        f.write(SCRIPT)
    log = os.path.join(work, "run.log")
    waited = engine_wait.run([PYTHON, "run.py"], cwd=work, budget_s=payload.get("budget_s"), progress=[log],
                             stdout_path=log, stderr_path=os.path.join(work, "run.err"))
    stop = engine_wait.stop_error("run_dumbbell_bd", waited)
    if stop is not None:
        stop.setdefault("evidence", {})["run_dir"] = rel
        return stop
    result = os.path.join(work, "result.json")
    if waited["returncode"] != 0 or not os.path.isfile(result):
        return error("HOOMD-BD-002", "execution_failure",
                     "the run ended with exit status %s and %s" % (waited["returncode"],
                                                                   "a result" if os.path.isfile(result) else "no result"),
                     "read run.err in the run folder", False, {"run_dir": rel})
    with open(result, encoding="utf-8") as f:
        out = json.load(f)
    out.update({"run_dir": rel, "inputs": {k: payload[k] for k in KEYS}})
    return out
