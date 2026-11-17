"""S6 Validate: run the bundle's own gates in a clean process and write the validation_report.

The bundle is run as it would be at its destination: a fresh interpreter,
the bundle directory as the working directory, no path to meta_agent/.
Verdicts are read off the bundle's printed JSON, never recomputed here.

A bundle that makes its own environment (a tool whose contract names
installs_from and whose gate opens by the execution permission) has no
environment in the builder's tree, and a task that needs it is not_run there.
in_its_environment() runs the gates again in an isolated copy of the bundle,
outside the repository, after the copy's own install tools have made its
environment through its own runner and gate; the copy is removed afterwards
(test run 20261116-7, where a session wrote that report by hand). The
builder installs nothing itself: the bundle's gate decides, from the lab's
permission the build copied, whether the install runs.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

from .. import cards

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
INSTALL = "network"
OPENS_AT = ("engine", "instrument")


def clean_env():
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH",)}
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def run_bundle(bundle_path, timeout=300):
    env = clean_env()
    out = {}
    for name, script in (("validate", "validate_tasks.py"), ("replay", "replay.py")):
        p = subprocess.run([sys.executable, "-I", os.path.join("src", script), "--json"], cwd=bundle_path,
                           capture_output=True, text=True, env=env, timeout=timeout)
        try:
            out[name] = json.loads(p.stdout)
        except ValueError:
            raise RuntimeError("%s printed no JSON (exit %s): %s %s" % (script, p.returncode, p.stdout[-800:], p.stderr[-800:]))
        out[name]["exit"] = p.returncode
    return out


def install_tools(bundle_path):
    """[(name, contract)] of the tools by which a bundle makes its own environment."""
    tools = os.path.join(bundle_path, "tools")
    out = []
    for name in sorted(os.listdir(tools)) if os.path.isdir(tools) else []:
        path = os.path.join(tools, name, "tool.json")
        if not os.path.isfile(path):
            continue
        c = cards.load_json(path)
        if c.get("side_effects") == INSTALL and isinstance(c.get("installs_from"), dict) \
                and (c.get("safety_gate") or {}).get("opens_by") == "execution_permission":
            out.append((name, c))
    return out


def outside(path, tree=REPO):
    path, tree = os.path.realpath(path), os.path.realpath(tree)
    return os.path.commonpath([path, tree]) != tree


def call_tool(bundle_path, tool, payload, timeout=None):
    p = subprocess.run([sys.executable, "-I", os.path.join("src", "run_tool.py"), tool], input=json.dumps(payload),
                       cwd=bundle_path, capture_output=True, text=True, env=clean_env(), timeout=timeout)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"artifact": "error_contract", "code": "S6-RUNNER", "category": "execution_failure",
                "message": "src/run_tool.py %s printed no JSON (exit %s): %s" % (tool, p.returncode, (p.stdout + p.stderr)[-400:])}


def in_its_environment(bundle_path):
    """(report, made, why). `report` is what the bundle's gates printed in an isolated copy whose environment its own
    install tools made, or None; `made` names the install tools that ran; `why` says why there is no such report, or
    is None when the bundle makes no environment of its own (its gates in the tree are then the whole of S6)."""
    tools = install_tools(bundle_path)
    if not tools:
        return None, [], None
    names = ", ".join(n for n, _ in tools)
    perm_path = os.path.join(bundle_path, "envelope", "execution_permission.json")
    perm = cards.load_json(perm_path) if os.path.isfile(perm_path) else None
    if not isinstance(perm, dict) or perm.get("confirmed_by") != "human" or perm.get("reaches") not in OPENS_AT:
        return None, [], ("its install tool %s was not called: the bundle carries no execution permission a person "
                          "confirmed that reaches an engine" % names)
    asks = ["%s (%s)" % (n, ", ".join((c.get("inputs") or {}).get("required") or [])) for n, c in tools
            if (c.get("inputs") or {}).get("required")]
    if asks:
        return None, [], "its install tool takes inputs that nothing in the bundle gives: %s" % "; ".join(asks)
    tmp = tempfile.mkdtemp(prefix="ma-s6-environment-")
    try:
        if not outside(tmp):
            return None, [], "the isolated copy would be inside the repository (%s), and is not made" % tmp
        copy = os.path.join(tmp, "bundle")
        top = os.path.abspath(bundle_path)
        shutil.copytree(bundle_path, copy, ignore=lambda d, names: [n for n in names if n in ("__pycache__",) or n.endswith(".pyc")
                                                                    or (os.path.abspath(d) == top and n == "runs")])
        made = []
        for name, c in tools:
            try:
                out = call_tool(copy, name, {}, timeout=c.get("timeout_s"))
            except subprocess.TimeoutExpired:
                return None, made, "%s did not end within its contract's timeout" % name
            if isinstance(out, dict) and out.get("artifact") == "error_contract":
                return None, made, "%s returned %s (%s): %s" % (name, out.get("code"), out.get("category"), out.get("message"))
            made.append({"tool": name, "installs_from": "%s/%s" % (c["installs_from"].get("installer"), c["installs_from"].get("channel"))})
        try:
            return run_bundle(copy, timeout=None), made, None
        except RuntimeError as e:
            return None, made, "the gates of the copy printed no verdict: %s" % e
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_validation_report(report, build_id, rid, bundle_rel, seat, now=None, environment="mock", not_made=None):
    vr = cards.skeleton("validation_report", "vr-" + build_id.replace("build-", ""), seat, cards.now_iso(now), rid=rid)
    v = report["validate"]
    vr["build_ref"] = build_id
    vr["environment"] = environment
    iface = []
    for t in v["interface"]["tasks"]:
        iface.append({"id": t["id"], "name": t.get("name") or t["id"], "verdict": t["verdict"],
                      "evidence": "%s/validation/interface/%s" % (bundle_rel, t["file"]),
                      **({"reason": t["detail"]} if t["verdict"] != "pass" else {})})
    sci = []
    for t in v["scientific"]["tasks"]:
        ref = t.get("reference_spec") or {"kind": "analytic", "ref": "the bundle's reference function"}
        item = {"id": t["id"], "name": t["name"], "verdict": t["verdict"] if t["verdict"] in ("pass", "fail") else "not_run",
                "reference": ref, "tolerance": t.get("tolerance"),
                "evidence": "%s/validation/scientific/%s" % (bundle_rel, t["file"])}
        if "agreement" in t:
            # the agreement is a difference of the measured quantity: it has the unit the person's tolerance has
            item["agreement"] = {"value": t["agreement"], "unit": (t.get("tolerance") or {}).get("unit") or "1"}
            names = ref.get("number_names") or []
            if len(names) >= 2 and isinstance(t.get("reference"), (int, float)) and not isinstance(t.get("reference"), bool):
                vr["numbers"].append({"name": names[0], "value": t["reference"], "unit": "1",
                                      "source": "computed:%s/validation/scientific/%s#reference" % (bundle_rel, t["file"]),
                                      "grade": "E4", "value_kind": "computed",
                                      "note": "the reference the runner computed independently of the tool"})
                vr["numbers"].append({"name": names[1], "value": t["agreement"], "unit": "1",
                                      "source": "computed:%s/validation/scientific/%s#agreement" % (bundle_rel, t["file"]),
                                      "grade": "E4", "value_kind": "computed",
                                      "note": "absolute difference between the measured output and the reference"})
        if t["verdict"] == "undecided":
            item["reason"] = "no tolerance chosen by a person yet: undecided"
        elif t["verdict"] == "not_run":
            item["reason"] = t.get("reason", "not run")
            if not_made:
                item["reason"] += "; the bundle's environment was not made: " + not_made
        elif t["verdict"] == "fail":
            item["reason"] = t.get("reason", "outside the tolerance")
        sci.append(item)
    vr["interface"] = {"tasks": iface}
    vr["scientific"] = {"tasks": sci}
    vr["overall"] = v["overall"]
    rp = report["replay"]
    vr["note"] = "gates read off the bundle's own runners: interface %s, scientific %s, replay %d item(s) %s" % (
        v["interface"]["verdict"], v["scientific"]["verdict"], len(rp["items"]), "ok" if rp["ok"] else "FAILED")
    vr["status"] = "validated" if v["overall"] == "pass" else "draft"
    return vr, v["interface"]["verdict"], v["scientific"]["verdict"]
