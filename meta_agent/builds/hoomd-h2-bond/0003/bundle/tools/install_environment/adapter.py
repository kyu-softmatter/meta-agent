"""Make this agent's own environment: HOOMD-blue's package hoomd from conda-forge, with pixi, under runs/env.

The version is the one conda-forge offered for this computer when the agent was built and the one its adapter was
tried on (the builder's intake, environment_read); a change of it is a new build. The runner points pixi's caches at
runs/cache before this call, so nothing is installed outside this directory. pixi itself is the person's to put on the
computer; the runner says so when it is not there.
"""
import json
import os
import platform
import shutil
import subprocess
import sys

BUNDLE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV = os.path.join(BUNDLE, "runs", "env")
PACKAGE, VERSION = "hoomd", "7.2.2"
PYTHON = "3.12.*"     # the interpreter the adapter was tried with; hoomd is a Python package
PLATFORMS = {("darwin", "arm64"): "osx-arm64", ("darwin", "x86_64"): "osx-64",
             ("linux", "x86_64"): "linux-64", ("linux", "aarch64"): "linux-aarch64"}


def error(code, category, message, action, retryable=False, evidence=None):
    e = {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category, "message": message,
         "retryable": retryable, "remediation": {"action": action}}
    if evidence is not None:
        e["evidence"] = evidence
    return e


def prefix():
    return os.path.join(ENV, ".pixi", "envs", "default")


def installed_version():
    meta = os.path.join(prefix(), "conda-meta")
    if not os.path.isdir(meta):
        return None
    for fn in sorted(os.listdir(meta)):
        if fn.startswith(PACKAGE + "-") and fn.endswith(".json"):
            with open(os.path.join(meta, fn), encoding="utf-8") as f:
                d = json.load(f)
            if d.get("name") == PACKAGE:
                return d.get("version")
    return None


def run(payload):
    subdir = PLATFORMS.get((sys.platform, platform.machine().lower()))
    if subdir is None:
        return error("HOOMD-INSTALL-002", "unsupported_target",
                     "conda-forge's hoomd is offered for osx-arm64, osx-64, linux-64 and linux-aarch64; this computer is %s %s"
                     % (sys.platform, platform.machine()), "run this agent on one of those platforms")
    pixi = shutil.which("pixi")
    os.makedirs(ENV, exist_ok=True)
    manifest = os.path.join(ENV, "pixi.toml")
    with open(manifest, "w", encoding="utf-8", newline="\n") as f:
        f.write('[workspace]\nname = "hoomd-h2-bond-env"\nchannels = ["conda-forge"]\nplatforms = ["%s"]\n\n'
                '[dependencies]\n%s = "==%s"\npython = "%s"\n' % (subdir, PACKAGE, VERSION, PYTHON))
    p = subprocess.run([pixi, "install", "--manifest-path", manifest], capture_output=True, text=True)
    py = os.path.join(prefix(), "bin", "python")
    if p.returncode != 0 or not os.path.isfile(py):
        return error("HOOMD-INSTALL-001", "execution_failure",
                     "pixi install of %s==%s from conda-forge did not give its interpreter (exit status %d)" % (PACKAGE, VERSION, p.returncode),
                     "read the evidence; a network or channel problem may pass on a retry", True,
                     {"stderr_tail": p.stderr[-2000:], "manifest": os.path.relpath(manifest, BUNDLE)})
    return {"installed": True, "python": os.path.relpath(py, BUNDLE), "package": PACKAGE,
            "version": installed_version() or "", "platform": subdir}
