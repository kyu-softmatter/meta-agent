"""Call one tool of this bundle through its contract.

    python src/run_tool.py <tool> [--out runs/<file>.json] < input.json

Reads one JSON object from stdin, applies the gate, checks the input against
tools/<tool>/tool.json, calls tools/<tool>/adapter.py and checks the output
against the contract's outputs before it prints it (a field whose unit is
count is never below zero; a contract that needs a value for "none" declares
it). Before the install the gate opens (a tool whose contract names
installs_from; a read of data from listed hosts needs no installer), it looks for the installer the
contract names on PATH, and returns an unavailable error that names it when
it is not there (putting it there is the person's step); then it points the
package caches of the installers it knows at runs/cache, so that the install
writes inside the bundle.
Prints the output object, or an error contract. With --out it also writes what
it printed to that file (template v37, bd-3): a file in the folder named runs,
ending in .json, that must not exist yet, written whole only once the call has
returned, through a file beside it that is renamed into place, so that a call
cut short leaves no empty or partial file there. The exit status is zero
whether the tool answered or reported an error (the error is in the output);
it is non-zero only when the tool does not exist in this bundle (2), or the
command was not understood or the file named with --out cannot be written (1).
An output field whose contract is an array is checked item by item against the
contract's items and prefixItems, so a series the contract declares with a unit
for each part is a series of numbers when it is kept (v37).
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
    if t == "array" and isinstance(value, list):
        # a series is checked point by point against what the contract declares of its items (v37, rheo-4)
        items, prefix = schema.get("items"), schema.get("prefixItems")
        for i, v in enumerate(value):
            if isinstance(items, dict):
                errs.extend(schema_errors(items, v, "%s[%d]" % (where, i)))
        if isinstance(items, dict) and isinstance(items.get("prefixItems"), list) and items.get("items") is False:
            n = len(items["prefixItems"])
            for i, v in enumerate(value):
                if isinstance(v, list) and len(v) != n:
                    errs.append("%s[%d]: expected %d item(s)" % (where, i, n))
        if isinstance(prefix, list):
            for i, (sub, v) in enumerate(zip(prefix, value)):
                errs.extend(schema_errors(sub, v, "%s[%d]" % (where, i)))
            if schema.get("items") is False and len(value) > len(prefix):
                errs.append("%s: more than %d item(s)" % (where, len(prefix)))
    if t == "string" and isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append("%s: shorter than minLength" % where)
        if "enum" in schema and value not in schema["enum"]:
            errs.append("%s: not one of %s" % (where, schema["enum"]))
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


def out_path(rel):
    """The absolute path --out names, or a reason it may not be written (v37, bd-3)."""
    norm = os.path.normpath(rel).replace(os.sep, "/")
    if os.path.isabs(rel) or not norm.startswith("runs/") or not norm.endswith(".json"):
        return None, "--out names a file ending in .json in the folder named runs, not %r" % rel
    p = os.path.join(BUNDLE, *norm.split("/"))
    if os.path.exists(p):
        return None, "%s exists already; --out writes a new file" % norm
    return p, None


def keep(p, text):
    """Write the whole output beside the file and rename it into place: no empty or partial file is left (bd-3)."""
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".part"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
        f.flush()
        os.fsync(f.fileno())
    with open(tmp, encoding="utf-8") as f:
        json.load(f)
    if os.path.exists(p):
        os.remove(tmp)
        raise FileExistsError("%s appeared while the call ran; the output was not written over it" % p)
    os.replace(tmp, p)


def main(argv):
    out_rel = None
    if "--out" in argv:
        i = argv.index("--out")
        if i + 1 >= len(argv):
            print(__doc__)
            return 1
        out_rel = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 1:
        print(__doc__)
        return 1
    target = None
    if out_rel is not None:
        target, why = out_path(out_rel)
        if why:
            print(why, file=sys.stderr)
            return 1
    payload = json.load(sys.stdin)
    try:
        out = run_call(argv[0], payload)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    text = json.dumps(out, indent=2, ensure_ascii=False)
    print(text)
    if target is not None:
        try:
            keep(target, text + "\n")
        except (OSError, ValueError) as exc:
            print("the output was printed and not kept: %s" % exc, file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
