"""Run this bundle's validation tasks: the interface gate and the scientific gate.

    python src/validate_tasks.py [--json]

validation/interface/<id>.json  a call with an expectation, judged like a replay item
validation/scientific/<id>.json a call whose measured output is compared with a
                                reference, and the agreement is judged against the
                                task's tolerance, which only a person chooses. No
                                tolerance: the verdict is undecided. The reference is
                                one of two:
                                  measure.reference_function  a function here computes
                                      it from the call's input, independently of the tool;
                                  measure.stated  the values a source states, a map from
                                      an output field to the value, beside the task's
                                      reference, which names the source. Nothing is
                                      computed: the output is compared with what is
                                      written. One tolerance has one unit, so it judges
                                      one stated field; several fields are judged
                                      together only by an exact tolerance, and a task
                                      per field is the way to give each its own.

A call that was not made measured nothing: when the gate refused it, a permission
was missing, or what the tool needs was not there, the task is not_run, with the
error's own words. That is not a pass and it is not a failure of the science.

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


# the categories of an error contract that say the call was not made
NOT_MADE = ("refused_by_safety", "permission_required", "unavailable")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def judged(r, item):
    """The verdict of an agreement against the task's tolerance. Without a person's tolerance it is undecided."""
    tol = item.get("tolerance")
    if not tol or tol.get("chosen_by") != "human" or "value" not in tol:
        r.update(verdict="undecided", reason="no tolerance chosen by a person")
        return r
    r["verdict"] = "pass" if r["agreement"] <= tol["value"] else "fail"
    return r


def against_stated(out, stated, item):
    """The call's output against the values a source states, field by field. No value is made here."""
    measured, differences, absent = {}, {}, []
    for field in sorted(stated):
        got = out.get(field) if isinstance(out, dict) else None
        if not is_number(got) or not is_number(stated[field]):
            absent.append(field)
            continue
        measured[field] = got
        differences[field] = abs(got - stated[field])
    if absent:
        return {"verdict": "fail", "measured": measured, "reference": dict(stated),
                "reason": "field(s) %s: not a number in the output or in the task" % ", ".join(absent)}
    r = {"measured": measured, "reference": dict(stated), "differences": differences, "agreement": max(differences.values())}
    tol = item.get("tolerance") or {}
    if len(stated) > 1 and tol.get("chosen_by") == "human" and tol.get("value"):
        # one tolerance has one unit: it cannot judge several quantities unless it asks them to be equal
        r.update(verdict="undecided", reason="one tolerance that is not exact cannot judge the %d stated fields %s together; "
                                             "a task states one field for each tolerance a person chooses" % (
                                                 len(stated), ", ".join(sorted(stated))))
        return r
    r = judged(r, item)
    if r["verdict"] == "fail":
        r["reason"] = "outside the tolerance: " + ", ".join(
            "%s (measured %r, stated %r)" % (f, measured[f], stated[f]) for f in sorted(differences) if differences[f] > tol["value"])
    return r


def scientific(item):
    call = item["call"]
    measure = item.get("measure") or {}
    stated = measure.get("stated") if isinstance(measure.get("stated"), dict) and measure.get("stated") else None
    ref_fn = REFERENCES.get(measure.get("reference_function"))
    if stated is None and ref_fn is None:
        return {"verdict": "not_run", "reason": "no reference function %r in this bundle" % measure.get("reference_function")}
    try:
        out = run_tool.run_call(call["tool"], call["input"])
    except FileNotFoundError as exc:
        return {"verdict": "fail", "reason": str(exc)}
    if isinstance(out, dict) and out.get("artifact") == "error_contract":
        said = "the call returned %s (%s): %s" % (out.get("code"), out.get("category"), out.get("message"))
        return {"verdict": "not_run" if out.get("category") in NOT_MADE else "fail", "reason": said}
    if stated is not None:
        return against_stated(out, stated, item)
    measured = out.get(measure.get("output_field"))
    reference = ref_fn(call["input"])
    if not is_number(measured):
        return {"verdict": "fail", "reason": "output field %r is not a number" % measure.get("output_field")}
    return judged({"measured": measured, "reference": reference, "agreement": abs(measured - reference)}, item)


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
