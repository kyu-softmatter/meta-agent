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
        report, made, why = copy_and_run(bundle_path, tools, tmp)
    finally:
        left = remove_copy(tmp)
    if left:
        # never 'removed' unchecked (failure line dft-8): what is left is said where the report says where its gates ran
        if report is not None:
            report["copy_left"] = left
        else:
            why = "%s; %s" % (why, left) if why else left
    return report, made, why


def engine_tools(bundle_path):
    """[(name, contract)] of the tools that start an engine already on the computer: a contract that names the
    external program it calls (calls_external), whose gate opens by the execution permission, and that installs
    nothing. A call of one in the builder's tree would run the engine inside the repository, which the Meta-Agent
    never does (meta_agent/CLAUDE.md, Tier 0; request req-rheotool-001, the rheoTool engine in its Colima container)."""
    tools = os.path.join(bundle_path, "tools")
    out = []
    for name in sorted(os.listdir(tools)) if os.path.isdir(tools) else []:
        path = os.path.join(tools, name, "tool.json")
        if not os.path.isfile(path):
            continue
        c = cards.load_json(path)
        if isinstance(c.get("calls_external"), dict) and not isinstance(c.get("installs_from"), dict) \
                and (c.get("safety_gate") or {}).get("opens_by") == "execution_permission":
            out.append((name, c))
    return out


def in_a_copy(bundle_path):
    """(report, why, in_tree) for a bundle with a tool that starts an engine already on the computer (engine_tools).
    Where the bundle carries an execution permission a person confirmed that reaches an engine, its gates run in an
    isolated copy outside the repository, with no time limit, and the copy is removed: `report` is what they printed,
    or None where the copy gave none, `why` says why or names what the removal left, and in_tree is False: the gates
    are never run in the tree instead, since there the engine would run inside the repository. Where it carries no
    such permission, the gate refuses every such call, in_tree is True and `why` says so. A bundle with no such tool
    gives (None, None, True)."""
    tools = engine_tools(bundle_path)
    if not tools:
        return None, None, True
    perm_path = os.path.join(bundle_path, "envelope", "execution_permission.json")
    perm = cards.load_json(perm_path) if os.path.isfile(perm_path) else None
    if not isinstance(perm, dict) or perm.get("confirmed_by") != "human" or perm.get("reaches") not in OPENS_AT:
        return None, ("no execution permission a person confirmed that reaches an engine, so the gate refuses %s and "
                      "the gates ran in the tree" % ", ".join(n for n, _ in tools)), True
    tmp = tempfile.mkdtemp(prefix="ma-s6-engine-")
    report, why = None, None
    try:
        if not outside(tmp):
            why = "the isolated copy would be inside the repository (%s), and is not made" % tmp
        else:
            copy = os.path.join(tmp, "bundle")
            top = os.path.abspath(bundle_path)
            shutil.copytree(bundle_path, copy, ignore=lambda d, names: [
                n for n in names if n in ("__pycache__",) or n.endswith(".pyc") or (os.path.abspath(d) == top and n == "runs")])
            try:
                report = run_bundle(copy, timeout=None)
            except RuntimeError as e:
                why = "the gates of the copy printed no verdict: %s" % e
    finally:
        left = remove_copy(tmp)
    if left:
        why = "%s; %s" % (why, left) if why else left
    return report, why, False


def remove_copy(path):
    """Remove S6's isolated copy and look whether it is gone (failure line dft-8, test run dft/20261117-3). None when it
    is gone; otherwise a sentence naming what is left and the first errors the removal met, after a second try."""
    errors = []

    def met(func, p, exc):
        e = exc[1] if isinstance(exc, tuple) else exc
        errors.append("%s %s: %s" % (getattr(func, "__name__", func), os.path.relpath(p, path), type(e).__name__))
    for _ in range(2):
        if not os.path.lexists(path):
            return None
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=met)
        else:
            shutil.rmtree(path, onerror=met)
    if not os.path.lexists(path):
        return None
    return "the isolated copy %s was not removed (%d error(s), first: %s)" % (path, len(errors), "; ".join(errors[:3]) or "none")


def copy_and_run(bundle_path, tools, tmp):
    """The isolated copy in `tmp`, its own install tools called through its runner and gate, then its gates."""
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


def task_verdicts():
    """The verdicts the validation report's schema allows a scientific task."""
    schemas = os.path.join(REPO, "contracts", "schemas")
    v = cards.load_json(os.path.join(schemas, "validation_report.schema.json"))["properties"]["scientific"]["properties"]["tasks"]["items"]["properties"]["verdict"]
    if "$ref" in v:
        name, _, pointer = v["$ref"].partition("#")
        v = cards.load_json(os.path.join(schemas, name))
        for part in pointer.strip("/").split("/"):
            v = v[part]
    return list(v.get("enum") or [])


def agreement_runs(t):
    """[(field, run)] of the agreement skill's runs a task printed (template v16 on), each one that ran with an error
    and a magnitude; [] for a bundle of an earlier template, whose agreement its own script computed."""
    out = []
    for field, run in sorted((t.get("agreement_runs") or {}).items()):
        outputs = (run or {}).get("outputs") or {}
        if (run or {}).get("verdict") == "ran" and all(isinstance(outputs.get(k), (int, float)) and not isinstance(outputs.get(k), bool)
                                                       for k in ("error", "magnitude")):
            out.append((field, run))
    return out


def measured_words(t):
    if "measured" not in t:
        return ""
    words = "; it ran and measured %s against the reference %s, agreement %s" % (t.get("measured"), t.get("reference"), t.get("agreement"))
    skills = sorted({run["skill"] for _, run in agreement_runs(t)})
    if skills:
        words += ", given by %s" % ", ".join(skills)
    return words


def measured_unit(bundle_path, task_file):
    """The unit of the quantity a scientific task measures, as the contract of the tool it calls declares it for that
    output; None where the contract declares none, where the task's fields have different units, or where the task or
    the contract cannot be read (failure line chem-1, test run chemical-kinetics/20261117-1)."""
    if not bundle_path or not task_file:
        return None
    try:
        item = cards.load_json(os.path.join(bundle_path, "validation", "scientific", task_file))
        tool = (item.get("call") or {}).get("tool")
        contract = cards.load_json(os.path.join(bundle_path, "tools", tool, "tool.json"))
    except (OSError, ValueError, TypeError, AttributeError):
        return None
    measure = item.get("measure") or {}
    stated = measure.get("stated")
    fields = sorted(stated) if isinstance(stated, dict) and stated else [measure.get("output_field")]
    props = ((contract.get("outputs") or {}).get("properties") or {})
    units = {(props.get(f) or {}).get("unit") for f in fields if f}
    unit = units.pop() if len(units) == 1 and None not in units else None
    # a unit the registry does not hold enters no card (check 2): the report keeps its earlier unit then
    return unit if unit in registered_units() else None


def registered_units():
    try:
        return set((cards.load_json(os.path.join(REPO, "contracts", "units.json")).get("units") or {}).keys())
    except (OSError, ValueError, AttributeError):
        return set()


def make_validation_report(report, build_id, rid, bundle_rel, seat, now=None, environment="mock", not_made=None,
                           bundle_path=None):
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
    allowed = task_verdicts()
    for t in v["scientific"]["tasks"]:
        ref = t.get("reference_spec") or {"kind": "analytic", "ref": "the bundle's reference function"}
        # the bundle's verdict, where the report's schema has the word for it: a task that ran and measured and has no
        # person's tolerance is undecided, never not_run (test run 20261117-1)
        said = t["verdict"] if t["verdict"] in ("pass", "fail") or t["verdict"] in allowed else "not_run"
        item = {"id": t["id"], "name": t["name"], "verdict": said,
                "reference": ref, "tolerance": t.get("tolerance"),
                "evidence": "%s/validation/scientific/%s" % (bundle_rel, t["file"])}
        printed = (ref.get("unit") if isinstance(ref, dict) else None) or None
        conv = t.get("measured_converted") if isinstance(t.get("measured_converted"), dict) else None
        if conv is not None:
            # compared in the reference's printed unit (template v34; check 12): the value as compared, the value and unit
            # it was converted from and the skill that converted it, whose factor check 12 recomputes
            item["measured"] = {"value": conv["value"], "unit": conv["unit"], "converted_from": dict(conv["converted_from"]),
                                "converted_by": conv["converted_by"]}
        if "agreement" in t:
            # the agreement is a difference of the measured quantity: it has the unit the tool's contract declares for
            # that output; where the contract declares none, the unit the person's tolerance has, otherwise '1'; and
            # where the reference states the unit it is printed in, that unit, the comparison being made in it (v34)
            unit = printed or measured_unit(bundle_path, t.get("file")) or (t.get("tolerance") or {}).get("unit") or "1"
            item["agreement"] = {"value": t["agreement"], "unit": unit}
            names = ref.get("number_names") or []
            if len(names) >= 2 and isinstance(t.get("reference"), (int, float)) and not isinstance(t.get("reference"), bool):
                vr["numbers"].append({"name": names[0], "value": t["reference"], "unit": unit,
                                      "source": "computed:%s/validation/scientific/%s#reference" % (bundle_rel, t["file"]),
                                      "grade": "E4", "value_kind": "computed",
                                      "note": "the reference the runner computed independently of the tool"})
                vr["numbers"].append({"name": names[1], "value": t["agreement"], "unit": unit,
                                      "source": "computed:%s/validation/scientific/%s#agreement" % (bundle_rel, t["file"]),
                                      "grade": "E4", "value_kind": "computed",
                                      "note": "absolute difference between the measured output and the reference"})
        refinement = t.get("refinement") or {}
        error = ((refinement.get("error_run") or {}).get("outputs") or {})
        if (refinement.get("error_run") or {}).get("verdict") == "ran" and error.get("estimated"):
            # the run's own numerical error a refinement measured (template v23), from which the rule derived the tolerance
            field = next(iter(((t.get("reference") if isinstance(t.get("reference"), dict) else None) or {"value": 0}).keys()))
            vr["numbers"].append({"name": "%s.%s.run_numerical_error" % (t["id"], field), "value": error["error"],
                                  "unit": (t.get("tolerance") or {}).get("unit") or "1",
                                  "source": "computed:%s@%s/validation/scientific/%s#%s" % (refinement.get("skill"), bundle_rel, t["file"], field),
                                  "grade": "E4", "value_kind": "computed",
                                  "note": "the finer run's discretization error, from the run as built and a finer run refining %s; "
                                          "the tolerance the person's rule derived from it is the task's" % ", ".join(refinement.get("refines") or [])})
        runs = agreement_runs(t)
        for field, run in runs:
            # the skill that gave the agreement, kept on the record (cfd-14, run cfd/20261117-21): each run's error is
            # a number whose source names the skill and the task, its magnitude being the task's agreement
            unit = printed or measured_unit(bundle_path, t.get("file")) or (t.get("tolerance") or {}).get("unit") or "1"
            vr["numbers"].append({"name": "%s.%s.error" % (t["id"], field), "value": run["outputs"]["error"], "unit": unit,
                                  "source": "computed:%s@%s/validation/scientific/%s#%s" % (run["skill"], bundle_rel, t["file"], field),
                                  "grade": "E4", "value_kind": "computed",
                                  "note": "the measured value less the reference, given by %s through the bundle's runner; "
                                          "its magnitude, %r, is the task's agreement" % (run["skill"], run["outputs"]["magnitude"])})
        if t["verdict"] == "undecided":
            item["reason"] = "no tolerance chosen by a person yet: undecided" + measured_words(t)
            if said != "undecided":
                item["reason"] += "; the report's schema has no word undecided for a task, so it is written not_run"
        elif t["verdict"] == "not_run":
            item["reason"] = t.get("reason", "not run")
            if not_made:
                item["reason"] += "; the bundle's environment was not made: " + not_made
        elif t["verdict"] == "fail":
            item["reason"] = t.get("reason", "outside the tolerance")
        elif t["verdict"] == "pass" and "measured" in t:
            # a passing task keeps what it measured, as a failing one does in its reason (cfd-r3-3, run cfd/20261118-2)
            item["reason"] = "within the tolerance" + measured_words(t)
        sci.append(item)
    vr["interface"] = {"tasks": iface}
    vr["scientific"] = {"tasks": sci}
    vr["overall"] = v["overall"]
    rp = report["replay"]
    vr["note"] = "gates read off the bundle's own runners: interface %s, scientific %s, replay %d item(s) %s" % (
        v["interface"]["verdict"], v["scientific"]["verdict"], len(rp["items"]), "ok" if rp["ok"] else "FAILED")
    vr["status"] = "validated" if v["overall"] == "pass" else "draft"
    return vr, v["interface"]["verdict"], v["scientific"]["verdict"]
