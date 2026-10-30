"""S6 Validate: run the bundle's own gates in a clean process and write the validation_report.

The bundle is run as it would be at its destination: a fresh interpreter,
the bundle directory as the working directory, no path to meta_agent/.
Verdicts are read off the bundle's printed JSON, never recomputed here.
"""
import json
import os
import subprocess
import sys

from .. import cards


def run_bundle(bundle_path):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH",)}
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    out = {}
    for name, script in (("validate", "validate_tasks.py"), ("replay", "replay.py")):
        p = subprocess.run([sys.executable, "-I", os.path.join("src", script), "--json"], cwd=bundle_path,
                           capture_output=True, text=True, env=env, timeout=300)
        try:
            out[name] = json.loads(p.stdout)
        except ValueError:
            raise RuntimeError("%s printed no JSON (exit %s): %s %s" % (script, p.returncode, p.stdout[-800:], p.stderr[-800:]))
        out[name]["exit"] = p.returncode
    return out


def make_validation_report(report, build_id, rid, bundle_rel, seat, now=None, environment="mock"):
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
            item["agreement"] = {"value": t["agreement"], "unit": "1"}
            names = ref.get("number_names") or []
            if len(names) >= 2:
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
