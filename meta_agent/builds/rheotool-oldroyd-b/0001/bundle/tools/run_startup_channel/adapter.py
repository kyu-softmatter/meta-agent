"""Run rheoTool's rheoFoam on the start-up of a planar channel flow of an Oldroyd-B fluid, in a run folder of its own.

The case is the planar channel of rheoTool's Oldroyd-BLog channel tutorial (mat-20261121-rheotool-6.0-user-guide,
section 5.1.3; mat-20261121-rheotool-of90-channel-oldroyd-b-constitutive), made periodic along the flow as OpenFOAM-9's
planarPoiseuille start-up tutorial is (mat-20261121-openfoam-9-planarpoiseuille-watersking): one cell along x with
cyclic ends, cells_across cells between two no-slip walls at y = -half_width and y = half_width, empty front and back.
The fluid starts at rest with no stress; from time zero a uniform momentum source, semiImplicitSource in fvModels,
drives it. rheoFoam's momentum equation is written per unit density (the guide, 4.7 and 5.1.1: the pressure and the
stress term are divided by the density), so the source the engine takes is driving / density, along x; this is the
engine's form of the input, and no other value is derived. constitutiveProperties takes type Oldroyd-BLog, rho, etaS,
etaP and lambda as given, with the tutorial's stabilization; the schemes and the linear solvers are the tutorial's
fvSchemes and fvSolution unchanged. The velocity is probed at the cell on the centreline (cells_across is odd) every
probe_every steps, and what the solver wrote there is read, never computed again.

Each call makes runs/cfd/<UTC stamp>/case/ and never writes into a folder that exists. The case goes into the image
rheotool:of90 of the Colima profile rheotool through stdin, blockMesh and rheoFoam run there, and the probe's file and
the logs come back through stdout between marker lines, so the bundle may sit anywhere on the computer. budget_s counts
running time only. A run that did not end, or wrote no probe, is an error and its folder stays.
"""
import base64
import datetime
import io
import json
import os
import re
import shutil
import subprocess
import tarfile

import engine_wait

BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONTEXT, IMAGE = "colima-rheotool", "rheotool:of90"
KEYS = ("half_width", "density", "solvent_viscosity", "polymer_viscosity", "relaxation_time", "driving",
        "cells_across", "dt", "end_time", "probe_every")
POSITIVE = ("half_width", "density", "polymer_viscosity", "relaxation_time", "dt", "end_time")
HEAD = "FoamFile\n{\n    format      ascii;\n    class       %s;\n    object      %s;\n}\n\n"

SCHEMES = """ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; grad(p) Gauss linear; grad(U) Gauss linear; linExtrapGrad Gauss linear; }
divSchemes
{
    default none;
    div(tau) Gauss linear;
    div(grad(U)) Gauss linear;
    div(phi,U) GaussDefCmpw none;
    div(phi,theta) GaussDefCmpw cubista;
    div(phi,tau) GaussDefCmpw cubista;
    div(phi,C) GaussDefCmpw cubista;
}
laplacianSchemes { default none; laplacian(eta,U) Gauss linear corrected; laplacian(p|(ap-H1)) Gauss linear corrected; laplacian(D,C) Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
fluxRequired { default no; p; }
"""
SOLUTION = """solvers
{
    "(p|U)" { solver PCG; preconditioner DIC; tolerance 1e-10; relTol 0.; minIter 0; maxIter 800; }
    "(theta|tau|C)" { solver PBiCG; preconditioner { preconditioner DILU; } tolerance 1e-10; relTol 0.; minIter 0; maxIter 1000; }
}
SIMPLE { nInIter 1; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; residualControl { } }
relaxationFactors { fields { p 1; } equations { U 1; tau 1; theta 1; C 1; } }
"""


def error(code, category, message, action, retryable=False, evidence=None):
    e = {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category, "message": message,
         "retryable": retryable, "remediation": {"action": action}}
    if evidence is not None:
        e["evidence"] = evidence
    return e


def fmt(x):
    return repr(float(x))


def case_files(p):
    h, n = p["half_width"], p["cells_across"]
    dx = 2.0 * h / n                                   # one square cell along x and z: the flow does not vary there
    files = {}
    files["system/blockMeshDict"] = HEAD % ("dictionary", "blockMeshDict") + (
        "convertToMeters 1;\nvertices\n(\n"
        "    (%(a)s %(b)s %(a)s) (%(c)s %(b)s %(a)s) (%(c)s %(d)s %(a)s) (%(a)s %(d)s %(a)s)\n"
        "    (%(a)s %(b)s %(c)s) (%(c)s %(b)s %(c)s) (%(c)s %(d)s %(c)s) (%(a)s %(d)s %(c)s)\n);\n"
        "blocks ( hex (0 1 2 3 4 5 6 7) (1 %(n)d 1) simpleGrading (1 1 1) );\nedges ();\nboundary\n(\n"
        "    left { type cyclic; neighbourPatch right; faces ((0 3 7 4)); }\n"
        "    right { type cyclic; neighbourPatch left; faces ((1 2 6 5)); }\n"
        "    walls { type wall; faces ((0 1 5 4) (3 7 6 2)); }\n"
        "    frontAndBack { type empty; faces ((0 1 2 3) (4 7 6 5)); }\n);\n"
        % {"a": fmt(-dx / 2), "c": fmt(dx / 2), "b": fmt(-h), "d": fmt(h), "n": n})
    files["system/controlDict"] = HEAD % ("dictionary", "controlDict") + (
        "application rheoFoam;\nstartFrom startTime;\nstartTime 0;\nstopAt endTime;\nendTime %s;\ndeltaT %s;\n"
        "writeControl runTime;\nwriteInterval %s;\npurgeWrite 0;\nwriteFormat ascii;\nwritePrecision 12;\n"
        "writeCompression off;\ntimeFormat general;\ntimePrecision 12;\nrunTimeModifiable no;\nadjustTimeStep off;\n"
        "functions\n{\n    probes\n    {\n        functionObjectLibs (\"libsampling.so\");\n        type probes;\n"
        "        name probes;\n        writeControl timeStep;\n        writeInterval %d;\n        fields (U);\n"
        "        probeLocations ((0 0 0));\n    }\n}\n" % (fmt(p["end_time"]), fmt(p["dt"]), fmt(p["end_time"]), p["probe_every"]))
    files["system/fvSchemes"] = HEAD % ("dictionary", "fvSchemes") + SCHEMES
    files["system/fvSolution"] = HEAD % ("dictionary", "fvSolution") + SOLUTION
    files["constant/constitutiveProperties"] = HEAD % ("dictionary", "constitutiveProperties") + (
        "parameters\n{\n    type Oldroyd-BLog;\n    rho rho [1 -3 0 0 0 0 0] %s;\n    etaS etaS [1 -1 -1 0 0 0 0] %s;\n"
        "    etaP etaP [1 -1 -1 0 0 0 0] %s;\n    lambda lambda [0 0 1 0 0 0 0] %s;\n    stabilization coupling;\n}\n"
        "passiveScalarProperties { solvePassiveScalar no; D D [0 2 -1 0 0 0 0] 1e-9; }\n"
        % (fmt(p["density"]), fmt(p["solvent_viscosity"]), fmt(p["polymer_viscosity"]), fmt(p["relaxation_time"])))
    files["constant/fvModels"] = HEAD % ("dictionary", "fvModels") + (
        "momentumSource\n{\n    type semiImplicitSource;\n    selectionMode all;\n    volumeMode specific;\n"
        "    sources { U { explicit (%s 0 0); implicit 0; } }\n}\n" % fmt(p["driving"] / p["density"]))
    cyc = "    left { type cyclic; }\n    right { type cyclic; }\n    frontAndBack { type empty; }\n"
    files["0/U"] = HEAD % ("volVectorField", "U") + (
        "dimensions [0 1 -1 0 0 0 0];\ninternalField uniform (0 0 0);\nboundaryField\n{\n"
        "    walls { type fixedValue; value uniform (0 0 0); }\n" + cyc + "}\n")
    files["0/p"] = HEAD % ("volScalarField", "p") + (
        "dimensions [0 2 -2 0 0 0 0];\ninternalField uniform 0;\nboundaryField\n{\n    walls { type zeroGradient; }\n" + cyc + "}\n")
    files["0/tau"] = HEAD % ("volSymmTensorField", "tau") + (
        "dimensions [1 -1 -2 0 0 0 0];\ninternalField uniform (0 0 0 0 0 0);\nboundaryField\n{\n"
        "    walls { type linearExtrapolation; value uniform (0 0 0 0 0 0); }\n" + cyc + "}\n")
    files["0/theta"] = HEAD % ("volSymmTensorField", "theta") + (
        "dimensions [0 0 0 0 0 0 0];\ninternalField uniform (0 0 0 0 0 0);\nboundaryField\n{\n"
        "    walls { type zeroGradient; }\n" + cyc + "}\n")
    return files


def read_probe(text):
    """Rows 'time (ux uy uz)' of the probe file written by OpenFOAM's probes function: [[t, ux], ...]."""
    rows = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        t, rest = s.split(None, 1)
        ux = rest.strip().strip("()").split()[0]
        rows.append([float(t), float(ux)])
    return rows


def read_banner(head):
    """The Version and Build fields of the banner OpenFOAM prints at the head of a solver's log, as printed."""
    v = re.search(r"Version:\s*(\S+)", head)
    b = re.search(r"^Build\s*:\s*(\S+)", head, re.M)
    return (v.group(1) if v else None), (b.group(1) if b else None)


def run(payload):
    if shutil.which("docker") is None:
        return error("RHEO-ENV-001", "unavailable", "the docker command is not on this computer",
                     "the person installs Colima and the docker CLI as the lab's README for rheotool:of90 says")
    missing = [k for k in KEYS if payload.get(k) is None]
    if missing:
        return error("RHEO-RUN-INPUT-001", "invalid_input", "no value for %s" % ", ".join(missing),
                     "give every value; none of them is chosen by this agent")
    bad = [k for k in POSITIVE if not (isinstance(payload[k], (int, float)) and payload[k] > 0)]
    if bad or payload["solvent_viscosity"] < 0:
        return error("RHEO-RUN-INPUT-002", "invalid_input", "%s must be positive and solvent_viscosity not negative" % ", ".join(bad or ["-"]),
                     "give positive values")
    for k in ("cells_across", "probe_every"):
        if not isinstance(payload[k], int) or isinstance(payload[k], bool) or payload[k] < 1:
            return error("RHEO-RUN-INPUT-003", "invalid_input", "%s must be a whole number, one or more" % k, "give a count")
    if payload["cells_across"] % 2 == 0:
        return error("RHEO-RUN-INPUT-004", "invalid_input", "cells_across is even, so no cell centre lies on the centreline",
                     "give an odd number of cells across the channel")
    ping = subprocess.run(["docker", "--context", CONTEXT, "image", "inspect", IMAGE], capture_output=True, text=True)
    if ping.returncode != 0:
        return error("RHEO-ENV-002", "unavailable", "the image %s is not reachable in the docker context %s" % (IMAGE, CONTEXT),
                     "the person starts the Colima profile rheotool (colima start -p rheotool, which also makes colima-rheotool the "
                     "docker command's current context; docker context use default sets it back), then this call again", True,
                     {"stderr_tail": ping.stderr[-1000:]})
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    work = os.path.join(BUNDLE, "runs", "cfd", stamp)
    case = os.path.join(work, "case")
    os.makedirs(case)
    rel = os.path.relpath(work, BUNDLE)
    with open(os.path.join(work, "input.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({k: payload[k] for k in KEYS}, f, indent=2)
    for name, text in case_files(payload).items():
        os.makedirs(os.path.join(case, os.path.dirname(name)), exist_ok=True)
        with open(os.path.join(case, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        t.add(case, arcname="case")
    with open(os.path.join(work, "case.tar"), "wb") as f:
        f.write(buf.getvalue())
    inner = ("mkdir -p run && cd run && tar xf - && cd case && (blockMesh > log.blockMesh 2>&1 && rheoFoam > log.rheoFoam 2>&1); "
             "echo @@BEGIN@@; tar cf - log.* postProcessing 2>/dev/null | base64; echo @@END@@")
    out_path, err_path = os.path.join(work, "container.out"), os.path.join(work, "container.err")
    # engine_wait gives the process no stdin, so a shell redirects the case's archive into docker; the inner command
    # is the shell's first argument, never spliced into its text
    argv = ["/bin/sh", "-c", 'exec docker --context "$1" run -i --rm "$2" "$3" < case.tar', "sh", CONTEXT, IMAGE, inner]
    waited = engine_wait.run(argv, cwd=work, budget_s=payload.get("budget_s"), progress=[out_path],
                             stdout_path=out_path, stderr_path=err_path)
    stop = engine_wait.stop_error("run_startup_channel", waited)
    if stop is not None:
        stop.setdefault("evidence", {})["run_dir"] = rel
        return stop
    with open(out_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    if "@@BEGIN@@" not in text or "@@END@@" not in text:
        return error("RHEO-RUN-002", "execution_failure", "the container returned no results", "read container.err in the run folder",
                     False, {"run_dir": rel})
    blob = text.split("@@BEGIN@@", 1)[1].split("@@END@@", 1)[0]
    back = os.path.join(work, "back")
    with tarfile.open(fileobj=io.BytesIO(base64.b64decode("".join(blob.split()))), mode="r") as t:
        t.extractall(back, filter="data")
    probe = os.path.join(back, "postProcessing", "probes", "0", "U")
    log = os.path.join(back, "log.rheoFoam")
    ended = os.path.isfile(log) and "\nEnd" in open(log, encoding="utf-8", errors="replace").read()
    if not os.path.isfile(probe) or not ended:
        return error("RHEO-RUN-003", "execution_failure", "rheoFoam %s and %s" % ("ended" if ended else "did not reach End",
                     "wrote a probe" if os.path.isfile(probe) else "wrote no probe"),
                     "read back/log.blockMesh and back/log.rheoFoam in the run folder", False, {"run_dir": rel})
    with open(probe, encoding="utf-8") as f:
        series = read_probe(f.read())
    version, build = read_banner(open(log, encoding="utf-8", errors="replace").read(4000))
    return {"openfoam_version": version, "openfoam_build": build, "probe_location": [0.0, 0.0, 0.0], "centreline_velocity": series,
            "run_dir": rel, "inputs": {k: payload[k] for k in KEYS}}
