"""Run this bundle's validation tasks: the interface gate and the scientific gate.

    python src/validate_tasks.py [--json]

validation/interface/<id>.json  a call with an expectation, judged like a replay item
validation/scientific/<id>.json a call whose measured output is compared with a
                                reference, and the agreement is judged against the
                                task's tolerance, which a person chooses or the
                                person's standing rule gives (chosen_by rule, naming
                                the rule and the skill that derived it). No such
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

A task may measure through a library skill (analysis: {skill, data: {field, input},
rows, output}): the call's output field is handed to the skill's input, each other
input comes from its row in envelope/parameters.json, the skill runs through
src/run_skill.py, and its named output is what the reference judges. A row that
is not there, or whose value is null, leaves the task not_run: what the skill
needs was not there.

A call that was not made measured nothing: when the gate refused it, a permission
was missing, or what the tool needs was not there, the task is not_run, with the
error's own words. That is not a pass and it is not a failure of the science.

The agreement a tolerance judges is not computed here: the library skill
measurement_error@v1, which the build puts into every bundle with a scientific
task, gives each measured value's error against its reference and the error's
magnitude, through src/run_skill.py, and the magnitude is what the tolerance
judges. Each run of it is printed with the task. A bundle that does not carry
the skill fails the task and says so.

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
import run_skill  # noqa: E402
import run_tool  # noqa: E402

# reference functions: analytic references a task may name; each takes the call input
REFERENCES = {
    "len_message": lambda inp: len(inp.get("message", "")),
}


# the categories of an error contract that say the call was not made
NOT_MADE = ("refused_by_safety", "permission_required", "unavailable")

# the library skill that gives a measured value's error against its reference (JCGM 200:2012, 2.16)
AGREEMENT = "measurement_error@v1"


class NoAgreement(Exception):
    """The agreement skill did not give an error: the bundle lacks it, or it was refused or failed."""


def agreement(measured, reference):
    """(magnitude, the skill's run) for one measured value against its reference, through src/run_skill.py."""
    try:
        record = run_skill.run(AGREEMENT, {"measured": measured, "reference": reference})
    except FileNotFoundError:
        raise NoAgreement("this bundle does not carry %s, the skill that gives the agreement; the build puts it into "
                          "every bundle with a scientific task" % AGREEMENT)
    run = {"skill": AGREEMENT, "inputs": {"measured": measured, "reference": reference},
           "verdict": record.get("verdict"), "outputs": record.get("outputs")}
    outputs = record.get("outputs") or {}
    if record.get("verdict") != "ran" or not is_number(outputs.get("magnitude")):
        raise NoAgreement("%s %s: %s" % (AGREEMENT, record.get("verdict"), record.get("why")))
    return outputs["magnitude"], run


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def tolerance_of(item):
    """The task's tolerance where it is one a verdict may rest on: chosen by a person, or derived by the person's
    standing rule (chosen_by rule), which names the rule, the skill that derived it and which way it came; else None."""
    tol = item.get("tolerance")
    if not isinstance(tol, dict) or not is_number(tol.get("value")):
        return None
    if tol.get("chosen_by") == "human":
        return tol
    if tol.get("chosen_by") == "rule" and tol.get("rule") and tol.get("derived_by") and tol.get("from"):
        return tol
    return None


def judged(r, item):
    """The verdict of an agreement against the task's tolerance. Without a tolerance a person chose, or one the
    person's standing rule gave, it is undecided."""
    tol = tolerance_of(item)
    if tol is None:
        r.update(verdict="undecided", reason="no tolerance chosen by a person or given by the person's rule")
        return r
    r["verdict"] = "pass" if r["agreement"] <= tol["value"] else "fail"
    return r


def against_stated(out, stated, item):
    """The call's output against the values a source states, field by field. No value is made here."""
    measured, differences, absent, runs = {}, {}, [], {}
    for field in sorted(stated):
        got = out.get(field) if isinstance(out, dict) else None
        if not is_number(got) or not is_number(stated[field]):
            absent.append(field)
            continue
        measured[field] = got
    if absent:
        return {"verdict": "fail", "measured": measured, "reference": dict(stated),
                "reason": "field(s) %s: not a number in the output or in the task" % ", ".join(absent)}
    try:
        for field in sorted(measured):
            differences[field], runs[field] = agreement(measured[field], stated[field])
    except NoAgreement as exc:
        return {"verdict": "fail", "measured": measured, "reference": dict(stated), "agreement_runs": runs, "reason": str(exc)}
    r = {"measured": measured, "reference": dict(stated), "differences": differences, "agreement": max(differences.values()),
         "agreement_runs": runs}
    tol = tolerance_of(item) or {}
    if len(stated) > 1 and tol.get("value"):
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


def parameter_rows():
    path = os.path.join(BUNDLE, "envelope", "parameters.json")
    rows = load(path).get("rows") if os.path.isfile(path) else []
    return {r.get("name"): r for r in rows or [] if isinstance(r, dict)}


def analysed(out, analysis):
    """(the skill's run, None), or (None, the task's result) where the analysis could not give its output."""
    data = analysis.get("data") or {}
    if not isinstance(out, dict) or data.get("field") not in out:
        return None, {"verdict": "fail", "reason": "the call's output has no field %r for the analysis" % data.get("field")}
    rows, inputs = parameter_rows(), {data.get("input"): out[data.get("field")]}
    for name, row in sorted((analysis.get("rows") or {}).items()):
        if row not in rows:
            return None, {"verdict": "not_run", "reason": "the analysis needs the row %s, which envelope/parameters.json does not hold" % row}
        if rows[row].get("value") is None:
            return None, {"verdict": "not_run", "reason": "the row %s, which hands %s its %s, has no value yet" % (row, analysis.get("skill"), name)}
        inputs[name] = rows[row]["value"]
    try:
        record = run_skill.run(analysis.get("skill"), inputs)
    except FileNotFoundError as exc:
        return None, {"verdict": "fail", "reason": str(exc)}
    run = {"skill": analysis.get("skill"), "inputs": inputs, "verdict": record.get("verdict"), "outputs": record.get("outputs")}
    if record.get("verdict") != "ran":
        return None, {"verdict": "not_run" if record.get("verdict") == "refused" else "fail", "analysis": run,
                      "reason": "the analysis %s %s: %s" % (analysis.get("skill"), record.get("verdict"), record.get("why"))}
    if analysis.get("output") not in (record.get("outputs") or {}):
        return None, {"verdict": "fail", "analysis": run,
                      "reason": "the analysis %s gave no output %r" % (analysis.get("skill"), analysis.get("output"))}
    return run, None


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
    analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else None
    run = None
    if analysis is not None:
        run, result = analysed(out, analysis)
        if result is not None:
            return result
        out = run["outputs"]
    r = against_stated(out, stated, item) if stated is not None else None
    if r is None:
        field = measure.get("output_field") or (analysis or {}).get("output")
        measured = out.get(field)
        reference = ref_fn(call["input"])
        if not is_number(measured):
            r = {"verdict": "fail", "reason": "output field %r is not a number" % field}
        else:
            try:
                magnitude, agreed = agreement(measured, reference)
            except NoAgreement as exc:
                r = {"verdict": "fail", "measured": measured, "reference": reference, "reason": str(exc)}
            else:
                r = judged({"measured": measured, "reference": reference, "agreement": magnitude,
                            "agreement_runs": {field: agreed}}, item)
    if run is not None:
        r["analysis"] = run
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
