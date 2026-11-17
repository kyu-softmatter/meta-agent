"""Call one tool of this bundle through its contract.

    python src/run_tool.py <tool> < input.json

Reads one JSON object from stdin, applies the gate, checks the input against
tools/<tool>/tool.json, calls tools/<tool>/adapter.py and checks the output.
Prints the output object, or an error contract. The exit status is zero
whether the tool answered or reported an error (the error is in the output);
it is non-zero only when the tool does not exist in this bundle.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import gate  # noqa: E402

TYPES = {"string": str, "number": (int, float), "integer": int, "boolean": bool, "array": list, "object": dict}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def schema_errors(schema, value, where="input"):
    """A small, deterministic checker for the subset of JSON Schema the contracts use."""
    errs = []
    t = schema.get("type")
    if t:
        py = TYPES.get(t)
        if py is not None:
            ok = isinstance(value, py) and not (t in ("number", "integer") and isinstance(value, bool))
            if not ok:
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
        if "enum" in schema and value not in schema["enum"]:
            errs.append("%s: not one of %s" % (where, schema["enum"]))
    if t in ("number", "integer") and isinstance(value, (int, float)):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append("%s: below minimum" % where)
        if "maximum" in schema and value > schema["maximum"]:
            errs.append("%s: above maximum" % where)
    return errs


def error_template(tool, category):
    """The tool's own error contract for a category, if it ships one; else a generic one."""
    errors_dir = os.path.join(BUNDLE, "tools", tool, "errors")
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
