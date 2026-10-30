"""The deterministic gate of this bundle.

    python src/gate.py --self-check          every safety value is null, or set by a person
    python src/gate.py --before <tool>       refuse the call when the tool needs a gate and a value is missing

The gate reads envelope/safety.json and tools/<tool>/tool.json and nothing
else. It never writes. A refusal is printed as an error contract
(category refused_by_safety) and the exit status is non-zero.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safety_values():
    return load(os.path.join(BUNDLE, "envelope", "safety.json"))


def value_is_set_by_person(v):
    return isinstance(v, dict) and v.get("set_by") == "human" and "value" in v and v.get("date")


def self_check():
    """In a bundle every value is null. At a destination a person may have set
    values; those carry set_by: human and a date. Anything else is a defect."""
    bad = []
    for name, v in safety_values().items():
        if v is None or value_is_set_by_person(v):
            continue
        bad.append(name)
    if bad:
        print("gate: safety values not null and not set by a person: %s" % ", ".join(bad))
        return 2
    print("gate: self-check ok")
    return 0


def refusal(tool, missing):
    return {
        "artifact": "error_contract",
        "schema_version": "0.1",
        "code": "GATE-SAFETY-001",
        "category": "refused_by_safety",
        "message": "%s needs a safety gate and these values are not set: %s" % (tool, ", ".join(missing)),
        "retryable": False,
        "remediation": {"action": "a person sets the values in envelope/safety.json at the destination; the bundle ships them null"},
        "evidence": {"tool": tool, "missing": missing},
    }


def check_before(tool, contract=None):
    """Return None when the call may proceed, else the refusal error contract."""
    if contract is None:
        contract = load(os.path.join(BUNDLE, "tools", tool, "tool.json"))
    gate = contract.get("safety_gate") or {}
    if not gate.get("required"):
        return None
    values = safety_values()
    missing = [k for k, v in values.items() if not value_is_set_by_person(v)]
    if not values:
        missing = ["(no safety rows at all)"]
    if missing:
        return refusal(tool, missing)
    return None


def main(argv):
    if "--self-check" in argv:
        return self_check()
    if "--before" in argv:
        tool = argv[argv.index("--before") + 1]
        r = check_before(tool)
        if r is None:
            print("gate: %s may run" % tool)
            return 0
        print(json.dumps(r, indent=2))
        return 3
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
