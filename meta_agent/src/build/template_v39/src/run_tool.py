"""Call one tool of this bundle through its contract.

    python src/run_tool.py <tool> < input.json

Reads one JSON object from stdin, applies the gate, checks the input against
tools/<tool>/tool.json, calls tools/<tool>/adapter.py and checks the output
against the contract's outputs before it prints it (a field whose unit is
count is never below zero; a contract that needs a value for "none" declares
it; a field's enum or const holds for every type, so that a contract can say
that a call which answers ended well, and an output whose engine ended
otherwise comes back as an error, v36). Before the install the gate opens (a tool whose contract names
installs_from; a read of data from listed hosts needs no installer), it looks for the installer the
contract names on PATH, and returns an unavailable error that names it when
it is not there (putting it there is the person's step); then it points the
package caches of the installers it knows at runs/cache, so that the install
writes inside the bundle.
Prints the output object, or an error contract. The exit status is zero
whether the tool answered or reported an error (the error is in the output);
it is non-zero only when the tool does not exist in this bundle.
"""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gate  # noqa: E402

CACHE_VARIABLES = ("PIXI_CACHE_DIR", "RATTLER_CACHE_DIR", "PIP_CACHE_DIR", "UV_CACHE_DIR", "CONDA_PKGS_DIRS",
                   "XDG_CACHE_HOME")   # pixi, pip, uv and conda, and the cache root most others read
TYPES = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "array": list, "object": dict}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def of_type(value, name):
    """Whether a value is of a JSON Schema type the contracts use; a boolean is never a number."""
    py = TYPES.get(name)
    return py is not None and isinstance(value, py) and not (name in ("number", "integer") and isinstance(value, bool))


def same(a, b):
    """Equality as JSON means it: a boolean equals only a boolean, so true is not 1 and false is not 0."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def schema_errors(schema, value, where="input"):
    """A small, deterministic checker for the subset of JSON Schema the contracts use."""
    errs = []
    t = schema.get("type")
    if isinstance(t, list):
        # a list of types, as JSON Schema allows (["integer", "null"]): the value is one of them, and it is checked
        # further as the one it is (cfd-13, the clone's dolfinx-1 in run cfd/20261117-21)
        names = [n for n in t if isinstance(n, str)]
        if value is None and "null" in names:
            return []
        fits = [n for n in names if n in TYPES and of_type(value, n)]
        if not fits:
            return ["%s: expected one of %s" % (where, ", ".join(names))]
        t = fits[0]
        schema = dict(schema, type=t)
    elif t == "null":
        return [] if value is None else ["%s: expected null" % where]
    if t:
        py = TYPES.get(t)
        if py is not None:
            if not of_type(value, t):
                return ["%s: expected %s" % (where, t)]
    if t == "object" or "properties" in schema:
        if not isinstance(value, dict):
            return ["%s: expected object" % where]
        for req in schema.get("required", []):
            if req not in value:
                errs.append("%s.%s: required" % (where, req))
        for k, sub in (schema.get("properties") or {}).items():
            if k in value:
                errs.extend(schema_errors(sub, value[k], "%s.%s" % (where, k)))
    if t == "string" and isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append("%s: shorter than minLength" % where)
    # the values a field may take at all, for every type (v36; dft-13): under v35 an integer's or a boolean's enum was
    # not looked at, so a contract could not say that a call which answers ended well (an exit status of 0, a flag)
    if "enum" in schema and not any(same(value, e) for e in schema["enum"]):
        errs.append("%s: not one of %s" % (where, json.dumps(schema["enum"])))
    if "const" in schema and not same(value, schema["const"]):
        errs.append("%s: not %s, the one value the contract allows" % (where, json.dumps(schema["const"])))
    if t in ("number", "integer") and isinstance(value, (int, float)):
        if schema.get("unit") == "count" and value < 0:
            errs.append("%s: a count is never below zero" % where)
        if "minimum" in schema and value < schema["minimum"]:
            errs.append("%s: below minimum" % where)
        if "maximum" in schema and value > schema["maximum"]:
            errs.append("%s: above maximum" % where)
    return errs


def keep_caches_inside():
    """Point the installers' package caches at runs/cache for this process and what it starts."""
    root = os.path.join(BUNDLE, "runs", "cache")
    for name in CACHE_VARIABLES:
        path = os.path.join(root, name.lower())
        os.makedirs(path, exist_ok=True)
        os.environ[name] = path


def installer_missing(tool, contract):
    """An unavailable error when the installer the contract names is not on this computer, else None. The install
    uses an installer that is there and never installs it: putting it there is the person's step."""
    installer = str((contract.get("installs_from") or {}).get("installer") or "")
    if installer and shutil.which(installer):
        return None
    e = error_template(tool, "unavailable")
    e["code"] = "%s-INSTALLER-MISSING" % tool.upper()
    e["category"] = "unavailable"
    e["message"] = ("the installer %s that this tool's contract names is not on this computer (it was looked for on PATH); "
                    "this agent installs its packages with it and never installs the installer" % (installer or "(none named)"))
    e["retryable"] = True
    e["remediation"] = {"action": "a person puts %s on this computer; then the call is made again" % (installer or "the installer"),
                        "note": "putting the installer on the computer is the person's step, not this agent's"}
    e["evidence"] = {"installer": installer or None, "looked_on": "PATH"}
    return e


def error_template(tool, category):
    """The tool's own error contract for a category, if it ships one; else a generic one. A tool may ship several
    contracts of one category: the first its contract declared is errors/<category>.json and is the one the runner
    returns itself; each other is errors/<category>.<code>.json, returned by the adapter that raises it."""
    errors_dir = os.path.join(BUNDLE, "tools", tool, "errors")
    first = os.path.join(errors_dir, category + ".json")
    if os.path.isfile(first):
        e = load(first)
        if e.get("category") == category:
            return dict(e)
    if os.path.isdir(errors_dir):
        for fn in sorted(os.listdir(errors_dir)):
            if fn.endswith(".json"):
                e = load(os.path.join(errors_dir, fn))
                if e.get("category") == category:
                    return dict(e)
    return {
        "artifact": "error_contract",
        "schema_version": "0.1",
        "code": "%s-%s-000" % (tool.upper(), category.upper().replace("_", "-")[:12]),
        "category": category,
        "message": category.replace("_", " "),
        "retryable": False,
        "remediation": {"action": "see the tool contract"},
    }


def run_call(tool, payload):
    tool_dir = os.path.join(BUNDLE, "tools", tool)
    contract_path = os.path.join(tool_dir, "tool.json")
    if not os.path.exists(contract_path):
        raise FileNotFoundError("no tool %r in this bundle" % tool)
    contract = load(contract_path)
    refused = gate.check_before(tool, contract)
    if refused is not None:
        return refused
    errs = schema_errors(contract.get("inputs") or {}, payload, "input")
    if errs:
        e = error_template(tool, "invalid_input")
        e["message"] = "; ".join(errs)
        e["evidence"] = {"input": payload}
        return e
    if contract.get("side_effects") == gate.INSTALL and isinstance(contract.get("installs_from"), dict):
        # the gate opened it as the install, from a listed source; a read of data from listed hosts alone needs no installer
        missing = installer_missing(tool, contract)
        if missing is not None:
            return missing
        keep_caches_inside()
    spec = importlib.util.spec_from_file_location("adapter_" + tool, os.path.join(tool_dir, "adapter.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.run(payload)
    if isinstance(result, dict) and result.get("artifact") == "error_contract":
        return result
    errs = schema_errors(contract.get("outputs") or {}, result, "output")
    if errs:
        cat = "integrity_mismatch" if "integrity_mismatch" in contract.get("errors", []) else "execution_failure"
        e = error_template(tool, cat)
        e["message"] = "the adapter's output does not match the contract: " + "; ".join(errs)
        e["evidence"] = {"output": result}
        return e
    return result


def main(argv):
    if len(argv) != 1:
        print(__doc__)
        return 1
    payload = json.load(sys.stdin)
    try:
        out = run_call(argv[0], payload)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
