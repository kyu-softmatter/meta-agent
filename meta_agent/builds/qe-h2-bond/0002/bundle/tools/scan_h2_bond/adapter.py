"""Run one self-consistent pw.x calculation of one H2 molecule at each bond length a call names, and return the
energy curve, in a scan folder of its own.

The molecule sits at the centre of a cubic box (ibrav 1, celldm(1) the box side in bohr) along z, its two atoms
half the bond length on either side; the k-point is gamma and the Martyna-Tuckerman correction is on
(assume_isolated, INPUT_PW of Quantum ESPRESSO, mat-20261120-qe-7.5-input-pw). Every setting is an input of the
call; this adapter chooses none. The species mass is written as zero, which asks pw.x for its own value: an scf run
does not use it (INPUT_PW, ATOMIC_SPECIES, Mass_X), and the output's species table shows what pw.x took.

Each call makes runs/scan/<UTC stamp>/ and, in it, one folder r<bond length>/ per point, and never writes into a
folder that exists, so an earlier run is never overwritten (failure line dft-24 of the builder's tree). Each point
writes pw.in, runs pw.x directly, or on n_processes through the environment's mpirun where the call names a count (dft-23), and waits
through src/engine_wait.py, whose budget_s counts running time only (dft-17; a paused run is not taken for a hung
one), and keeps pw.out. The scan writes result.json: the energy curve, each pair a bond length as given and the total
energy pw.x printed for it (read, never computed), and the conditions the runs held under as pw.x printed them, which
must be the same for every point. A point that did not end with JOB DONE, or whose self-consistent loop did not
converge, ends the scan with an error, not an output (dft-13, dft-19): its folder stays and the error names it.
"""
import datetime
import json
import os
import re

import engine_wait

BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BIN = os.path.join(BUNDLE, "runs", "env", ".pixi", "envs", "default", "bin")
PW_X = os.path.join(BIN, "pw.x")
MPIRUN = os.path.join(BIN, "mpirun")
PSEUDO = "H.pbe-rrkjus_psl.1.0.0.UPF"
DEFAULT_PSEUDO_DIR = os.path.join("runs", "inputs", "pseudo")


def error(code, category, message, action, retryable=False, evidence=None):
    e = {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category, "message": message,
         "retryable": retryable, "remediation": {"action": action}}
    if evidence is not None:
        e["evidence"] = evidence
    return e


def absolute(path):
    return path if os.path.isabs(path) else os.path.join(BUNDLE, path)


def last(rx, text, cast=float):
    found = re.findall(rx, text, re.M)
    return cast(found[-1]) if found else None


def read_output(text):
    """What pw.x printed: read, never computed. A quantity it did not print is left out."""
    out = {"job_done": "JOB DONE." in text}
    v = re.search(r"Program PWSCF v\.(\S+)", text)
    out["program_version"] = v.group(1) if v else ""
    if "convergence has been achieved" in text:
        out["converged"] = True
    elif "convergence NOT achieved" in text:
        out["converged"] = False
    for name, rx, cast in (
            ("total_energy", r"^!\s+total energy\s+=\s+(-?\d+\.\d+)\s+Ry", float),
            ("iterations", r"convergence has been achieved in\s+(\d+)\s+iterations", int),
            ("total_force", r"Total force =\s+(-?\d+\.\d+)", float)):
        val = last(rx, text, cast)
        if val is not None:
            out[name] = val
    cond = {}
    for name, rx, cast in (
            ("ecutwfc", r"kinetic-energy cutoff\s+=\s+(\d+\.\d+)\s+Ry", float),
            ("ecutrho", r"charge density cutoff\s+=\s+(\d+\.\d+)\s+Ry", float),
            ("alat", r"lattice parameter \(alat\)\s+=\s+(\d+\.\d+)\s+a\.u\.", float),
            ("conv_thr", r"convergence threshold\s+=\s+(\S+)", float),
            ("mpi_processes", r"Number of MPI processes:\s+(\d+)", int)):
        val = last(rx, text, cast)
        if val is not None:
            cond[name] = val
    xc = re.search(r"Exchange-correlation=\s*(.+?)\s*$", text, re.M)
    if xc:
        cond["exchange_correlation"] = xc.group(1)
    pp = re.search(r"PseudoPot\. # 1 for H\s+read from file:\s*\n\s*(\S+)", text)
    if pp:
        cond["pseudopotential"] = os.path.basename(pp.group(1))
    m = re.search(r"atomic species\s+valence\s+mass\s+pseudopotential\s*\n\s*H\s+(\S+)\s+(\S+)", text)
    if m:
        cond["species_mass_used"] = float(m.group(2))
    if "Martyna-Tuckerman" in text or "martyna-tuckerman" in text.lower():
        cond["isolated_correction"] = "martyna-tuckerman"
    out["printed_conditions"] = cond
    return out


INPUT = """&CONTROL
  calculation = 'scf'
  prefix = 'h2'
  outdir = '{outdir}'
  pseudo_dir = '{pseudo_dir}'
  tprnfor = .true.
/
&SYSTEM
  ibrav = 1
  celldm(1) = {box_side!r}
  nat = 2
  ntyp = 1
  ecutwfc = {ecutwfc!r}
  ecutrho = {ecutrho!r}
  assume_isolated = 'martyna-tuckerman'
/
&ELECTRONS
  conv_thr = {conv_thr!r}
/
ATOMIC_SPECIES
  H 0.0 {pseudo}
ATOMIC_POSITIONS bohr
  H {c!r} {c!r} {z1!r}
  H {c!r} {c!r} {z2!r}
K_POINTS gamma
"""


def one_point(d, side, payload, pseudo_dir, n, scan, env):
    """(the point's record, None) or (None, an error)."""
    work = os.path.join(scan, "r%s" % repr(d))
    os.makedirs(work)
    c = side / 2.0
    text = INPUT.format(outdir=os.path.join(work, "tmp"), pseudo_dir=pseudo_dir, box_side=float(side),
                        ecutwfc=float(payload["ecutwfc"]), ecutrho=float(payload["ecutrho"]),
                        conv_thr=float(payload["conv_thr"]), pseudo=PSEUDO, c=c, z1=c - d / 2.0, z2=c + d / 2.0)
    with open(os.path.join(work, "pw.in"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    cmd = [PW_X, "-in", "pw.in"] if n is None else [MPIRUN, "-np", str(n), PW_X, "-in", "pw.in"]
    rel = os.path.relpath(work, BUNDLE)
    waited = engine_wait.run(cmd, cwd=work, env=env, budget_s=payload.get("budget_s"),
                             progress=[os.path.join(work, "pw.out")], stdout_path=os.path.join(work, "pw.out"),
                             stderr_path=os.path.join(work, "pw.err"))
    stop = engine_wait.stop_error("scan_h2_bond", waited)
    if stop is not None:
        stop.setdefault("evidence", {})["run_dir"] = rel
        return None, stop
    with open(os.path.join(work, "pw.out"), encoding="utf-8", errors="replace") as f:
        printed = read_output(f.read())
    point = {"bond_length": d, "run_dir": rel, "exit_status": waited["returncode"]}
    point.update(printed)
    if waited["returncode"] != 0 or not printed["job_done"] or printed.get("converged") is not True:
        return None, error("QE-RUN-002", "execution_failure",
                           "pw.x at bond length %r ended with exit status %s, JOB DONE %s, converged %s" % (
                               d, waited["returncode"], "printed" if printed["job_done"] else "not printed",
                               printed.get("converged")),
                           "read pw.out in the run folder; no energy of this scan is used", False, {"run_dir": rel})
    return point, None


def run(payload):
    if not os.path.isfile(PW_X):
        return error("QE-ENV-001", "unavailable", "this agent's environment is not made: no %s" % os.path.relpath(PW_X, BUNDLE),
                     "call install_environment first, then this call again", True)
    pseudo_dir = absolute(payload.get("pseudo_dir") or DEFAULT_PSEUDO_DIR)
    if not os.path.isfile(os.path.join(pseudo_dir, PSEUDO)):
        return error("QE-PSEUDO-001", "unavailable", "no %s in %s" % (PSEUDO, os.path.relpath(pseudo_dir, BUNDLE)),
                     "call fetch_pseudopotential first, then this call again", True)
    lengths, side = list(payload["bond_lengths"]), payload["box_side"]
    n = payload.get("n_processes")         # null: pw.x is started directly, without mpirun
    if len(set(lengths)) != len(lengths):
        return error("QE-RUN-INPUT-001", "invalid_input", "a bond length is named twice", "name each bond length once")
    if not all(d < side for d in lengths):
        return error("QE-RUN-INPUT-001", "invalid_input", "a bond length is not shorter than the box side",
                     "give bond lengths shorter than the box side")
    if n is not None and n < 1:
        return error("QE-RUN-INPUT-001", "invalid_input", "a count of processes that is not positive",
                     "name a positive count, or null to start pw.x directly")
    if n is not None and not os.path.isfile(MPIRUN):
        return error("QE-ENV-002", "unavailable", "processes asked for and no mpirun in this agent's environment",
                     "call with n_processes null, or remake the environment")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    scan = os.path.join(BUNDLE, "runs", "scan", stamp)
    os.makedirs(scan)       # refuses a folder that exists: a run is never written over
    env = dict(os.environ, OMP_NUM_THREADS="1", PATH=BIN + os.pathsep + os.environ.get("PATH", ""))
    points = []
    for d in lengths:
        point, err = one_point(d, side, payload, pseudo_dir, n, scan, env)
        if err is not None:
            return err
        points.append(point)
    rel = os.path.relpath(scan, BUNDLE)
    conditions = [p["printed_conditions"] for p in points]
    result = {"run_dir": rel, "energy_curve": [[p["bond_length"], p["total_energy"]] for p in points],
              "printed_conditions": conditions[0], "program_version": points[0]["program_version"],
              "points": [{k: p[k] for k in ("bond_length", "run_dir", "total_energy", "iterations", "converged")
                          if k in p} for p in points],
              "box_side": side, "n_processes": n, "inputs": {k: payload[k] for k in sorted(payload)}}
    with open(os.path.join(scan, "result.json"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(result, indent=2) + "\n")
    if any(c != conditions[0] for c in conditions[1:]):
        return error("QE-RUN-003", "execution_failure", "pw.x printed different conditions for the points of one scan",
                     "read result.json in the scan folder; no energy curve is handed on from runs under different conditions",
                     False, {"run_dir": rel})
    return result
