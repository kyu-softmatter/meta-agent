"""Run this bundle's validation tasks: the interface gate and the scientific gate.

    python src/validate_tasks.py [--json]

validation/interface/<id>.json  a call with an expectation, judged like a replay item
validation/scientific/<id>.json a call whose measured output is compared with a
                                reference computed independently here; the agreement
                                is judged against the task's tolerance, which only a
                                person chooses. No tolerance: the verdict is undecided.

Prints both sections and the overall verdict: pass only when every interface
task passes and every scientific task passes; not_run is never a pass.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import replay  # noqa: E402
import run_tool  # noqa: E402

# reference functions: analytic references a task may name; each takes the call input
REFERENCES = {
    "len_message": lambda inp: len(inp.get("message", "")),
}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scientific(item):
    call = item["call"]
    measure = item.get("measure") or {}
    ref_fn = REFERENCES.get(measure.get("reference_function"))
    if ref_fn is None:
        return {"verdict": "not_run", "reason": "no reference function %r in this bundle" % measure.get("reference_function")}
    try:
        out = run_tool.run_call(call["tool"], call["input"])
    except FileNotFoundError as exc:
        return {"verdict": "fail", "reason": str(exc)}
    if isinstance(out, dict) and out.get("artifact") == "error_contract":
        return {"verdict": "fail", "reason": "the call returned %s" % out.get("code")}
    measured = out.get(measure.get("output_field"))
    reference = ref_fn(call["input"])
    if not isinstance(measured, (int, float)) or isinstance(measured, bool):
        return {"verdict": "fail", "reason": "output field %r is not a number" % measure.get("output_field")}
    agreement = abs(measured - reference)
    r = {"measured": measured, "reference": reference, "agreement": agreement}
    tol = item.get("tolerance")
    if not tol or tol.get("chosen_by") != "human" or "value" not in tol:
        r.update(verdict="undecided", reason="no tolerance chosen by a person")
        return r
    r["verdict"] = "pass" if agreement <= tol["value"] else "fail"
    return r


def run_scientific(d):
    results = []
    if not os.path.isdir(d):
        return results
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        item = load(os.path.join(d, fn))
        r = scientific(item)
        r.update({"id": item.get("id", fn), "name": item.get("name", fn), "file": fn,
                  "reference_spec": item.get("reference"), "tolerance": item.get("tolerance"),
                  "expected_verdict": item.get("expected_verdict")})
        results.append(r)
    return results


def main(argv):
    iface = replay.run_dir(os.path.join(BUNDLE, "validation", "interface"))
    sci = run_scientific(os.path.join(BUNDLE, "validation", "scientific"))
    iface_ok = bool(iface) and all(r["verdict"] == "pass" for r in iface)
    if not sci:
        sci_verdict = "not_run"
    elif any(r["verdict"] == "fail" for r in sci):
        sci_verdict = "fail"
    elif any(r["verdict"] in ("undecided", "not_run") for r in sci):
        sci_verdict = "undecided" if any(r["verdict"] == "undecided" for r in sci) else "not_run"
    else:
        sci_verdict = "pass"
    iface_verdict = "pass" if iface_ok else ("fail" if iface else "not_run")
    overall = "pass" if (iface_verdict == "pass" and sci_verdict == "pass") else (
        "fail" if "fail" in (iface_verdict, sci_verdict) else ("undecided" if "undecided" in (iface_verdict, sci_verdict) else "not_run"))
    report = {"interface": {"verdict": iface_verdict, "tasks": iface},
              "scientific": {"verdict": sci_verdict, "tasks": sci}, "overall": overall}
    if "--json" in argv:
        print(json.dumps(report, indent=2))
    else:
        print("interface:")
        for r in iface:
            print("  %-6s %-8s %s" % (r["verdict"], r["id"], r["detail"]))
        print("scientific:")
        for r in sci:
            print("  %-9s %-8s %s" % (r["verdict"], r["id"], r.get("reason") or
                                      "measured %s, reference %s, agreement %s" % (r.get("measured"), r.get("reference"), r.get("agreement"))))
        print("gates: interface %s, scientific %s; overall %s" % (iface_verdict, sci_verdict, overall))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
