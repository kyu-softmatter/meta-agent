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

A reference the source gives as exact (an analytic value of the case's own settings, a
defined constant) is marked in measure.exact, a map from the stated field to true: the
rule's skill then takes no half of a printed digit for it, and the run's own error alone
gives its tolerance (v26).

The rule's branches are taken in their order (v28): the reference's stated
uncertainty (measure.stated_uncertainty); else the span [lowest, highest] of the
quantity across suitable materials, where the task carries them (measure.materials,
a map from the stated field to a list of entries, each naming its material, saying
how its system compares, and giving one value, with the uncertainty its material
states for it where it states one (v29: the entry then enters as the value less
and plus that uncertainty), or one range), computed by the
library skill TEMPLATE.json names under span_skill, through src/run_skill.py; else
the larger of half the last printed digit and the run's own error, for which alone
a refinement is run. A span is an acceptance interval, chosen_by rule, from
literature_span: the measured value passes when it lies within it, its edges as
the materials write them, and no difference from the reference is judged.

A task may measure through a library skill (analysis: {skill, data: {field, input},
rows, output}): the call's output field is handed to the skill's input, each other
input comes from its row in envelope/parameters.json, the skill runs through
src/run_skill.py, and its named output is what the reference judges. A row that
is not there, or whose value is null, leaves the task not_run: what the skill
needs was not there.

A comparison that cannot be judged yet stands as a held item (v34): validation/scientific/<id>.json carries held
{reason, needs}, is expected not_run and names no reference function; it is reported not_run with its reason and what
it needs, no call is made and no reference function is looked for. It is never a pass.

A reference printed in another unit than the measured quantity is compared in its printed unit (v34; the person,
2026-11-20, 'Compare in its printed unit'): the task's reference names the unit it is printed in (reference.unit) and
its measure names the measured quantity's (measure.unit); every value a call measures, the finer runs' included, is
converted into the reference's unit by the library skill TEMPLATE.json names under unit_skill, from the registry this
bundle carries (envelope/units.json), before anything is judged, so that the run's own error, a tolerance the rule
derives and the agreement are in it too. The reference stays as printed. The task's result records the value as
compared, the value and unit it was converted from and the skill that converted it (measured_converted), and a value
that does not convert leaves the task not_run with the skill's reason.

A call that was not made measured nothing: when the gate refused it, a permission
was missing, or what the tool needs was not there, the task is not_run, with the
error's own words. That is not a pass and it is not a failure of the science.

The agreement a tolerance judges is not computed here: the library skill
TEMPLATE.json names under agreement_skill, which the build puts into every
bundle with a scientific task, gives each measured value's error against its
reference and the error's magnitude, through src/run_skill.py, and the
magnitude is what the tolerance judges. Each run of it is printed with the
task, its inputs and every output it gave, whatever the verdict: a task that
is undecided because no tolerance was chosen, or because the person's rule
gave none, still has its agreement taken and printed (v30; under v29 a task the
rule left undecided took none, and a run's error and sign were in --json
alone). A bundle that does not carry the skill fails the task and says so.

Prints both sections and the overall verdict: pass only when every interface
task passes and every scientific task passes; not_run is never a pass. Under
each scientific task it prints the agreement where one was taken, the
tolerance that judged it (value or interval, unit, chosen_by, from) or that
there was none, the span of the task's materials where it carries any, with
how many values and stated ranges gave it and which material gave each edge,
and, where the task refines, the run's own error, how it was estimated and the
factor the rule weighed it by (v27, v28). --json prints the whole report.
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

# the library skill that gives a measured value's error against its reference (JCGM 200:2012, 2.16): the one this
# bundle's TEMPLATE.json names under agreement_skill
def _agreement_skill():
    try:
        with open(os.path.join(BUNDLE, "TEMPLATE.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("agreement_skill") or "measurement_error@v2"
    except (OSError, ValueError):
        return "measurement_error@v2"


AGREEMENT = _agreement_skill()


def _interval_skill():
    try:
        with open(os.path.join(BUNDLE, "TEMPLATE.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("interval_skill") or "series_within_window@v3"
    except (OSError, ValueError):
        return "series_within_window@v3"


# the diagnostic library skill that says whether a value lies within an interval the person gave (cfd-19): handed a
# series of the one measured value, a window of one, and the interval's edges as written; its edges belong to it
INTERVAL = _interval_skill()


def interval_of(tol):
    """(low, high) of an acceptance interval a person gave, or of one the person's standing rule gave as the span of the
    quantity across suitable materials (chosen_by rule, from literature_span, naming the rule and the skill); or None."""
    iv = tol.get("interval") if isinstance(tol, dict) else None
    if not isinstance(iv, dict):
        return None
    by_rule = (tol.get("chosen_by") == "rule" and tol.get("rule") and tol.get("derived_by")
               and tol.get("from") == "literature_span")
    if tol.get("chosen_by") != "human" and not by_rule:
        return None
    low, high = iv.get("low"), iv.get("high")
    if not (is_number(low) and is_number(high)) or low > high:
        return None
    return low, high


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
    if isinstance(tol, dict) and interval_of(tol) is not None:
        return tol
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
    iv = interval_of(tol)
    if iv is not None:
        measured = r.get("measured")
        if isinstance(measured, dict):
            measured = next(iter(measured.values())) if len(measured) == 1 else None
        if not is_number(measured):
            r.update(verdict="undecided", reason="an interval judges one measured value; the task measures %r" % (r.get("measured"),))
            return r
        try:
            record = run_skill.run(INTERVAL, {"series": [measured], "window": 1, "low": iv[0], "high": iv[1]})
        except FileNotFoundError:
            r.update(verdict="fail", reason="this bundle does not carry %s, the skill that judges an interval" % INTERVAL)
            return r
        state = (record.get("outputs") or {}).get("state")
        r["interval_run"] = {"skill": INTERVAL, "inputs": {"series": [measured], "window": 1, "low": iv[0], "high": iv[1]},
                             "verdict": record.get("verdict"), "outputs": record.get("outputs")}
        if record.get("verdict") != "ran" or state not in ("within", "below", "above"):
            r.update(verdict="undecided", reason="%s gave no state for the interval: %s" % (INTERVAL, record.get("why")))
            return r
        r["verdict"] = "pass" if state == "within" else "fail"
        if r["verdict"] == "fail":
            r["reason"] = "%s the interval [%r, %r] %s, as %s says" % (
                state, iv[0], iv[1], "the person gave" if tol.get("chosen_by") == "human" else
                "the person's rule gave as the span of the materials", INTERVAL)
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
    printed = (item.get("measure") or {}).get("printed") or {}
    try:
        for field in sorted(measured):
            # the reference as its source prints it, where the task carries the text, so that the agreement skill keeps
            # its last digit (v37, dft-20); else the stated number
            ref = printed.get(field) if isinstance(printed, dict) and isinstance(printed.get(field), str) else stated[field]
            differences[field], runs[field] = agreement(measured[field], ref)
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
    if r["verdict"] == "fail" and "value" in tol:
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


def _units():
    with open(os.path.join(BUNDLE, "envelope", "units.json"), "r", encoding="utf-8") as f:
        return json.load(f)["units"]


def _entry(units, name):
    u = units.get(name)
    return {"name": name, "si_factor": u.get("si_factor"), "dim": u.get("dim") or {}} if isinstance(u, dict) else None


def printed_unit_of(item):
    """(the measured unit, the reference's printed unit) of a task compared in its reference's printed unit, or None."""
    ref_unit = (item.get("reference") or {}).get("unit") if isinstance(item.get("reference"), dict) else None
    measured_unit = (item.get("measure") or {}).get("unit")
    if ref_unit and measured_unit and ref_unit != measured_unit:
        return measured_unit, ref_unit
    return None


def in_reference_unit(item, out):
    """(out with the stated field in the reference's printed unit, the conversion record) or (None, the task's result).
    Unchanged, with no record, for a task compared in the unit it is measured in."""
    units_pair = printed_unit_of(item)
    stated = (item.get("measure") or {}).get("stated") or {}
    if units_pair is None or not isinstance(out, dict) or len(stated) != 1:
        return out, None
    field = next(iter(stated))
    value = out.get(field)
    if not is_number(value):
        return out, None
    from_unit, to_unit = units_pair
    skill = _template().get("unit_skill") or "unit_convert@v2"
    try:
        units = _units()
    except (OSError, ValueError, KeyError):
        return None, {"verdict": "not_run", "reason": "the reference is printed in %s and the measured value is in %s, and "
                                                      "this bundle carries no unit registry to convert by" % (to_unit, from_unit)}
    fu, tu = _entry(units, from_unit), _entry(units, to_unit)
    if fu is None or tu is None:
        return None, {"verdict": "not_run", "reason": "%s or %s is not in this bundle's unit registry" % (from_unit, to_unit)}
    try:
        rec = run_skill.run(skill, {"value": value, "from_unit": fu, "to_unit": tu, "stands_for": None,
                                         "from_stands_for": None})
    except FileNotFoundError:
        return None, {"verdict": "fail", "reason": "this bundle does not carry %s, the unit skill" % skill}
    o = rec.get("outputs") or {}
    if rec.get("verdict") != "ran" or o.get("state") != "converted":
        return None, {"verdict": "not_run", "reason": "the measured value in %s does not convert into %s, the reference's "
                                                      "printed unit: %s" % (from_unit, to_unit, o.get("why") or rec.get("why"))}
    conversion = {"value": o["converted"], "unit": to_unit, "converted_from": {"value": value, "unit": from_unit},
                  "converted_by": "computed:%s" % skill, "factor": o["factor"]}
    return dict(out, **{field: o["converted"]}), conversion


def measured_once(item, call_input):
    """(the measured output, the analysis run or None, None), or (None, None, the task's result) where the call or its
    analysis gave nothing to judge."""
    call = item["call"]
    try:
        out = run_tool.run_call(call["tool"], call_input)
    except FileNotFoundError as exc:
        return None, None, {"verdict": "fail", "reason": str(exc)}
    if isinstance(out, dict) and out.get("artifact") == "error_contract":
        said = "the call returned %s (%s): %s" % (out.get("code"), out.get("category"), out.get("message"))
        return None, None, {"verdict": "not_run" if out.get("category") in NOT_MADE else "fail", "reason": said}
    analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else None
    run = None
    if analysis is not None:
        run, result = analysed(out, analysis)
        if result is not None:
            return None, None, result
        out = run["outputs"]
    out, conversion = in_reference_unit(item, out)
    if out is None:
        return None, None, conversion
    if conversion is not None:
        run = dict(run or {}, conversion=conversion) if run is not None else {"conversion": conversion}
    return out, run, None


def _template():
    try:
        with open(os.path.join(BUNDLE, "TEMPLATE.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _takes(ref, name):
    """Whether the library skill this bundle carries under ref names the input: a rule's skill of an earlier version takes
    no span, and is handed none."""
    try:
        manifest = load(os.path.join(BUNDLE, "skills", ref or "", "skill.json"))
    except (OSError, ValueError):
        return False
    return name in {i.get("name") for i in manifest.get("inputs") or [] if isinstance(i, dict)}


def span_of(item, field):
    """(low, high, the span skill's run) for the materials a task carries for its stated field, or (None, None, the run or
    None): the span [lowest, highest] of branch 3 of the person's standing rule (2026-11-18, 'Yes, add literature span',
    'Min-max of values'; 2026-11-19, 'Yes, widen it'), computed by the library skill TEMPLATE.json names under span_skill
    through src/run_skill.py. Nothing is computed here and no entry is chosen here. Raises FileNotFoundError where the
    bundle does not carry the skill."""
    entries = ((item.get("measure") or {}).get("materials") or {}).get(field)
    if not isinstance(entries, list):
        return None, None, None
    skill = _template().get("span_skill")
    if not skill:
        return None, None, {"skill": None, "verdict": "refused", "outputs": None,
                            "why": "TEMPLATE.json names no span_skill, so the task's materials give no span"}
    record = run_skill.run(skill, {"entries": entries})
    o = record.get("outputs") or {}
    run = {"skill": skill, "inputs": {"entries": entries}, "verdict": record.get("verdict"), "outputs": record.get("outputs"),
           "why": record.get("why")}
    if record.get("verdict") != "ran" or not (is_number(o.get("low")) and is_number(o.get("high"))):
        return None, None, run
    return o["low"], o["high"], run


def ruled(item, out):
    """The task with the tolerance the person's standing rule gives it, its branches in their order (v28), and the record
    of how. The stated uncertainty and the span of the task's materials need no run: where either gives the tolerance, no
    finer run is made and the result as built is judged. Otherwise, where the task names a refinement (2026-11-18, 'Yes,
    run's own error'; 'Yes, factor 3'; 'Yes, refine and derive'), the call is made again with the finer inputs the
    refinement's rows hand it, the refinement's skill estimates the finer result's error from the two, and the rule's
    skill turns it into the tolerance, all through src/run_skill.py. Where the finer run or the estimate cannot be made,
    the half-digit branch alone applies and the record says the run's error was not estimated. Returns (item, out to
    judge, record), out being the finer run's where it was made; or (None, None, the task's result)."""
    ref = item.get("refinement") if isinstance(item.get("refinement"), dict) else {}
    stated = (item.get("measure") or {}).get("stated") or {}
    field, reference = next(iter(stated.items()))
    rows = parameter_rows()
    record = {"skill": ref.get("skill"), "refines": sorted((ref.get("inputs") or {}).keys()), "as_built": out.get(field)}
    error, why = None, None
    try:
        span_low, span_high, span_run = span_of(item, field)
    except FileNotFoundError:
        return None, None, {"verdict": "fail", "reason": "this bundle does not carry %s, the span's skill" % _template().get("span_skill")}
    if span_run is not None:
        record["span_run"] = span_run
    uncertainty = ((item.get("measure") or {}).get("stated_uncertainty") or {}).get(field)
    if uncertainty is not None or span_low is not None:
        # an earlier branch of the rule gives the tolerance, so the run's own error is not weighed and no finer run is made
        why = "an earlier branch of the rule gives the tolerance: %s" % (
            "the reference's stated uncertainty" if uncertainty is not None else "the span of the task's materials")
    elif not ref:
        why = "the task names no refinement"
    fine_input = dict(item["call"]["input"])
    for name, row in sorted((ref.get("inputs") or {}).items()) if why is None else []:
        value = (rows.get(row) or {}).get("value")
        if value is None:
            why = "the row %s, which hands the finer run its %s, has no value" % (row, name)
            break
        fine_input[name] = value
    third = ref.get("third_inputs") if isinstance(ref.get("third_inputs"), dict) else None
    third_input = dict(item["call"]["input"])
    if third is not None and why is None:
        for name, row in sorted(third.items()):
            value = (rows.get(row) or {}).get("value")
            if value is None and why is None:
                why = "the row %s, which hands the third run its %s, has no value" % (row, name)
            third_input[name] = value
    ratio = (rows.get(ref.get("ratio_row")) or {}).get("value")
    order = None if third is not None else (rows.get(ref.get("order_row")) or {}).get("value")
    if why is None and ratio is None:
        why = "the refinement's ratio row %s has no value" % ref.get("ratio_row")
    if why is None and third is None and order is None:
        why = "the refinement's order row %s has no value" % ref.get("order_row")
    judged_out = out
    observed = False
    if why is None:
        fine_out, fine_run, result = measured_once(item, fine_input)     # in the reference's printed unit where it has one
        if result is not None:
            why = "the finer run gave nothing to judge: %s" % result.get("reason")
        elif not is_number(fine_out.get(field)) or not is_number(out.get(field)):
            why = "the field %s is not a number in both runs" % field
        else:
            record.update(finer_input={k: fine_input[k] for k in record["refines"]}, finer=fine_out[field])
            coarse_v, fine_v = out[field], fine_out[field]
            if third is not None:
                # three runs, each finer by the same ratio: the order is observed from them (cfd-25), and the error is the
                # finest result's, from the two finest at that order
                third_out, third_run, result = measured_once(item, third_input)
                if result is not None or not is_number((third_out or {}).get(field)):
                    why = "the third run gave nothing to judge: %s" % ((result or {}).get("reason") or "field %s is not a number" % field)
                else:
                    record.update(third_input={k: third_input[k] for k in sorted(third)}, third=third_out[field])
                    order_skill = _template().get("order_skill") or "observed_order_of_convergence@v1"
                    try:
                        o = run_skill.run(order_skill, {"coarse": out[field], "medium": fine_out[field], "fine": third_out[field],
                                                        "refinement_ratio": ratio})
                    except FileNotFoundError:
                        return None, None, {"verdict": "fail", "reason": "this bundle does not carry %s, the order's skill" % order_skill}
                    record["order_run"] = {"skill": order_skill, "verdict": o.get("verdict"), "outputs": o.get("outputs")}
                    if o.get("verdict") == "ran" and (o.get("outputs") or {}).get("observed"):
                        order, coarse_v, fine_v, fine_out, observed = o["outputs"]["order"], fine_out[field], third_out[field], third_out, True
                        fine_run = third_run
                    else:
                        why = "%s read no order: %s" % (order_skill, (o.get("outputs") or {}).get("why") or o.get("why"))
        if why is None:
            try:
                e = run_skill.run(ref["skill"], {"fine": fine_v, "coarse": coarse_v, "refinement_ratio": ratio, "order": order})
            except FileNotFoundError:
                return None, None, {"verdict": "fail", "reason": "this bundle does not carry %s, the refinement's skill" % ref["skill"]}
            record["error_run"] = {"verdict": e.get("verdict"), "outputs": e.get("outputs")}
            if e.get("verdict") == "ran" and (e.get("outputs") or {}).get("estimated"):
                error, judged_out = e["outputs"]["error"], fine_out
                if isinstance(fine_run, dict) and fine_run.get("conversion"):
                    # the value judged is the finer run's: its conversion into the reference's printed unit is the one
                    # the task records (v34)
                    record["judged_conversion"] = fine_run["conversion"]
            else:
                why = "%s estimated no error: %s" % (ref["skill"], (e.get("outputs") or {}).get("why") or e.get("why"))
    rule = _template().get("tolerance_rule") or {}
    printed = ((item.get("measure") or {}).get("printed") or {}).get(field)
    try:
        # how the refinement's skill estimates the run's error, which the rule's factor depends on: a two-grid estimate
        # enters three times over (the person, 2026-11-18, 'Yes, factor 3'; TEMPLATE.json run_error_from)
        how = (_template().get("run_error_from") or {}).get(ref.get("skill")) if error is not None else None
        if error is not None and observed:
            how = "three_or_more_grids"   # the order was observed from three runs: no factor (the person, 2026-11-18)
        record["run_error_from"] = how
        inputs = {"printed": printed if isinstance(printed, str) else repr(reference),
                  "stated_uncertainty": ((item.get("measure") or {}).get("stated_uncertainty") or {}).get(field),
                  "run_numerical_error": error, "run_error_from": how}
        # a reference the source gives as exact has no printed digit to be uncertain in: the rule's skill takes the run's
        # own error alone for it (template v26; tolerance_from_reference@v4); null where the task marks nothing
        inputs["exact"] = ((item.get("measure") or {}).get("exact") or {}).get(field)
        if _takes(rule.get("skill"), "span_low"):
            # the span of the task's materials, branch 3 of the rule, as the span's skill gave it; null where it gave none
            inputs["span_low"], inputs["span_high"] = span_low, span_high
        t = run_skill.run(rule.get("skill"), inputs)
    except FileNotFoundError:
        return None, None, {"verdict": "fail", "reason": "this bundle does not carry %s, the rule's skill" % rule.get("skill")}
    o = t.get("outputs") or {}
    record["tolerance_run"] = {"skill": rule.get("skill"), "verdict": t.get("verdict"), "outputs": o}
    if why:
        record["run_error_not_estimated"] = why
    if t.get("verdict") == "ran" and o.get("from") == "literature_span" and is_number(o.get("interval_low")) and is_number(o.get("interval_high")):
        # the span is an acceptance interval, derived by the span's skill: its edges as the materials write them
        tol = {"interval": {"low": o["interval_low"], "high": o["interval_high"]}, "unit": item.get("tolerance_unit") or "1",
               "chosen_by": "rule", "rule": rule.get("rule"), "derived_by": "computed:%s" % span_run["skill"],
               "from": "literature_span"}
        return dict(item, tolerance=tol), judged_out, record
    if t.get("verdict") != "ran" or o.get("tolerance") is None:
        return None, None, {"verdict": "undecided", "refinement": record,
                            "reason": "the rule gave no tolerance: %s" % (o.get("why") or t.get("why"))}
    tol = {"value": o["tolerance"], "unit": item.get("tolerance_unit") or "1", "chosen_by": "rule", "rule": rule.get("rule"),
           "derived_by": "computed:%s" % rule.get("skill"), "from": o["from"]}
    return dict(item, tolerance=tol), judged_out, record


def scientific(item):
    if isinstance(item.get("held"), dict):
        # a comparison that cannot be judged yet (v34; the person, 2026-11-20, 'Held item, shown pending'): no call is
        # made and no reference function is looked for
        h = item["held"]
        return {"verdict": "not_run", "held": dict(h), "reason": "held: %s; it needs %s" % (h.get("reason"), h.get("needs"))}
    call = item["call"]
    measure = item.get("measure") or {}
    stated = measure.get("stated") if isinstance(measure.get("stated"), dict) and measure.get("stated") else None
    ref_fn = REFERENCES.get(measure.get("reference_function"))
    if stated is None and ref_fn is None:
        return {"verdict": "not_run", "reason": "no reference function %r in this bundle" % measure.get("reference_function")}
    analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else None
    out, run, result = measured_once(item, call["input"])
    if result is not None:
        return result
    record = None
    carries = isinstance(((measure.get("materials") or {}) if isinstance(measure.get("materials"), dict) else {}).get(
        next(iter(stated)) if stated else None), list)
    if stated is not None and len(stated) == 1 and (
            (isinstance(item.get("refinement"), dict) and not (
                isinstance(item.get("tolerance"), dict) and item["tolerance"].get("chosen_by") == "human"))
            or (carries and tolerance_of(item) is None)):
        # the rule's branches in order: a task that refines, as before, and a task that carries materials and has no
        # tolerance yet, whose span is derived here (v28)
        ruled_item, ruled_out, record = ruled(item, out)
        if ruled_item is None:
            if record.get("verdict") == "undecided":
                # the rule gave no tolerance: the agreement is still taken, so that the task prints what a tolerance
                # would judge (v30; gmx-27, where a session ran the agreement skill itself for the undecided tasks)
                taken = against_stated(out, stated, dict(item, tolerance=None))
                for k in ("measured", "reference", "differences", "agreement", "agreement_runs"):
                    if k in taken:
                        record[k] = taken[k]
                if "agreement" not in taken:
                    record["agreement_not_taken"] = taken.get("reason")
                if isinstance(run, dict) and run.get("conversion"):
                    record["measured_converted"] = run["conversion"]
            return record
        item, out = ruled_item, ruled_out
    r = against_stated(out, stated, item) if stated is not None else None
    if record is not None:
        r["refinement"] = record
        r["derived_tolerance"] = item["tolerance"]
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
        conversion = run.pop("conversion", None) if isinstance(run, dict) else None
        if record is not None and record.get("judged_conversion"):
            conversion = record.pop("judged_conversion")
        if conversion is not None:
            r["measured_converted"] = conversion
        if run:
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
        derived = r.pop("derived_tolerance", None)
        r.update({"id": item.get("id", fn), "name": item.get("name", fn), "file": fn,
                  "reference_spec": item.get("reference"), "tolerance": derived or item.get("tolerance"),
                  "expected_verdict": item.get("expected_verdict")})
        results.append(r)
    return results


def judged_by(r):
    """The lines printed under a scientific task: the agreement where the verdict line gave a reason in its place, the
    tolerance that judged it or that there was none, and the run's own error where the task refines (v27; the
    tolerance and the error were in --json alone before, so a pass printed rested on numbers a reader did not see)."""
    lines = []
    conv = r.get("measured_converted")
    if isinstance(conv, dict):
        src = conv.get("converted_from") or {}
        lines.append("compared in the reference's printed unit %s: measured %r %s, converted to %r %s by %s (factor %r)" % (
            conv.get("unit"), src.get("value"), src.get("unit"), conv.get("value"), conv.get("unit"),
            conv.get("converted_by"), conv.get("factor")))
    if r.get("reason") and r.get("agreement") is not None:
        lines.append("measured %s, reference %s, agreement %s" % (r.get("measured"), r.get("reference"), r.get("agreement")))
    for field, run in sorted((r.get("agreement_runs") or {}).items()):
        # each run of the agreement skill, whatever the verdict (v30): its inputs and every output it gave
        if not isinstance(run, dict):
            continue
        given, o = run.get("inputs") or {}, run.get("outputs") or {}
        lines.append("agreement by %s, field %s: measured %r, reference %r -> %s" % (
            run.get("skill"), field, given.get("measured"), given.get("reference"),
            ", ".join("%s %r" % (k, o[k]) for k in sorted(o)) if run.get("verdict") == "ran" and o else run.get("verdict")))
    if r.get("agreement_not_taken"):
        lines.append("agreement: not taken: %s" % r["agreement_not_taken"])
    tol = r.get("tolerance")
    if isinstance(tol, dict) and interval_of(tol) is not None:
        lo, hi = interval_of(tol)
        lines.append("tolerance: the interval [%r, %r] %s, chosen_by %s%s" % (
            lo, hi, tol.get("unit") or "", tol.get("chosen_by"), ", from %s" % tol["from"] if tol.get("from") else ""))
    elif isinstance(tol, dict) and tol.get("value") is not None:
        lines.append("tolerance: %r %s, chosen_by %s%s" % (tol["value"], tol.get("unit") or "", tol.get("chosen_by"),
                                                           ", from %s" % tol["from"] if tol.get("from") else ""))
    elif r.get("verdict") in ("pass", "fail", "undecided"):
        lines.append("tolerance: none")
    ref = r.get("refinement")
    if isinstance(ref, dict) and isinstance(ref.get("span_run"), dict):
        so = ref["span_run"].get("outputs") or {}
        if is_number(so.get("low")) and is_number(so.get("high")):
            lines.append("span of the materials: [%r, %r] from %s value(s) and %s stated range(s), by %s; lowest from %s, highest from %s" % (
                so["low"], so["high"], so.get("values"), so.get("ranges"), ref["span_run"].get("skill"),
                so.get("lowest_from"), so.get("highest_from")))
        else:
            lines.append("span of the materials: none: %s" % (so.get("why") or ref["span_run"].get("why") or "no reason given"))
    if isinstance(ref, dict):
        error = ((ref.get("error_run") or {}).get("outputs") or {}).get("error")
        factor = ((ref.get("tolerance_run") or {}).get("outputs") or {}).get("factor")
        if error is not None:
            lines.append("run's own error: %r (%s, factor %s), as built %r, finer %r" % (
                error, ref.get("run_error_from"), factor, ref.get("as_built"), ref.get("finer")))
        else:
            lines.append("run's own error: not estimated: %s" % (ref.get("run_error_not_estimated") or "no reason given"))
    return lines


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
            for line in judged_by(r):
                print("  %-9s %-8s %s" % ("", "", line))
        print("gates: interface %s, scientific %s; overall %s" % (iface_verdict, sci_verdict, overall))
    return 0 if overall == "pass" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
