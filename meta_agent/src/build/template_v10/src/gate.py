"""The deterministic gate of this bundle.

    python src/gate.py --self-check          every safety value is null, or set by a person, and the
                                             execution permission, where there is one, is a person's
    python src/gate.py --before <tool>       refuse the call when the tool needs a gate and what opens it is missing

What opens the gate is said by the tool's contract (safety_gate.opens_by).
By safety values, the default: the call runs when every value in
envelope/safety.json is set by a person. By the execution permission: a tool
that starts a process or writes files, and touches no instrument, runs when
envelope/execution_permission.json, the lab's permission as a person
confirmed it, reaches an engine or further. The gate reads the level, a
value, and never the words beside it. A tool that changes an instrument opens
only by safety values.

The one network call this agent may make is an install of its own packages:
a tool whose contract names installs_from {installer, channel}, whose gate
opens by the execution permission, runs where the permission reaches an
engine and lists that same pair under package_sources. Every other tool that
reaches the network is refused, whatever its contract says.

The gate reads envelope/safety.json, envelope/execution_permission.json and
tools/<tool>/tool.json and nothing else. It never writes. A refusal is
printed as an error contract (category refused_by_safety) and the exit status
is non-zero.
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


LEVELS = ("none", "mock", "sandbox", "engine", "instrument")   # each includes the one before
PERMISSION_OPENS_AT = ("engine", "instrument")
PERMISSION_OPENS = ("runs_process", "writes_files")              # never an instrument
INSTALL = "network"                                              # only to install, from a listed source


def execution_permission():
    """The permission file, or None when the bundle carries none."""
    path = os.path.join(BUNDLE, "envelope", "execution_permission.json")
    return load(path) if os.path.isfile(path) else None


def permission_is_a_persons(p):
    return isinstance(p, dict) and p.get("confirmed_by") == "human" and p.get("reaches") in LEVELS and bool(p.get("date"))


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
    p = execution_permission()
    if p is not None and not permission_is_a_persons(p):
        print("gate: envelope/execution_permission.json is not a level a person confirmed")
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


def permission_refusal(tool, found, why):
    return {
        "artifact": "error_contract",
        "schema_version": "0.1",
        "code": "GATE-PERMISSION-001",
        "category": "refused_by_safety",
        "message": "%s opens by the execution permission and %s" % (tool, why),
        "retryable": False,
        "remediation": {"action": "the lab's execution permission is a person's to confirm, in the lab's profile; the builder "
                                  "copies it into envelope/execution_permission.json at a build, and no session writes that file"},
        "evidence": {"tool": tool, "reaches": found, "opens_at": list(PERMISSION_OPENS_AT)},
    }


def listed(p):
    return [(s.get("installer"), s.get("channel")) for s in (p or {}).get("package_sources") or [] if isinstance(s, dict)]


def network_refusal(tool, contract, why):
    src = contract.get("installs_from") if isinstance(contract.get("installs_from"), dict) else {}
    return {
        "artifact": "error_contract",
        "schema_version": "0.1",
        "code": "GATE-NETWORK-001",
        "category": "refused_by_safety",
        "message": "%s reaches the network and %s; the one network call this agent may make is an install from a source "
                   "the lab's permission lists" % (tool, why),
        "retryable": False,
        "remediation": {"action": "a package source is the person's to allow, in the lab's profile; the builder copies it "
                                  "into envelope/execution_permission.json at a build, and no session writes that file"},
        "evidence": {"tool": tool, "installs_from": src or None, "package_sources": ["%s/%s" % a for a in listed(execution_permission())]},
    }


def install_refused(tool, contract):
    """None when a network tool is the one install this agent may make, else the refusal."""
    if (contract.get("safety_gate") or {}).get("opens_by") != "execution_permission":
        return network_refusal(tool, contract, "its gate does not open by the execution permission")
    src = contract.get("installs_from")
    if not isinstance(src, dict):
        return network_refusal(tool, contract, "its contract names no installs_from")
    pair = (src.get("installer"), src.get("channel"))
    if pair not in listed(execution_permission()):
        return network_refusal(tool, contract, "installs from %s/%s, which the permission does not list" % pair)
    return None


def by_permission(tool, contract):
    """None when the lab's permission opens this tool, else the refusal naming the level found."""
    effects = contract.get("side_effects")
    if effects not in PERMISSION_OPENS + (INSTALL,):
        return permission_refusal(tool, None, "its side effects are %r; the permission opens only %s, and an install from a "
                                  "listed source; any other tool opens by safety values a person wrote" % (
                                      effects, " and ".join(PERMISSION_OPENS)))
    p = execution_permission()
    if p is None:
        return permission_refusal(tool, None, "this bundle carries no envelope/execution_permission.json")
    if not permission_is_a_persons(p):
        return permission_refusal(tool, p.get("reaches") if isinstance(p, dict) else None,
                                  "envelope/execution_permission.json is not a level a person confirmed")
    if p["reaches"] not in PERMISSION_OPENS_AT:
        return permission_refusal(tool, p["reaches"], "the lab's permission reaches %s, which opens no engine" % p["reaches"])
    return None


def check_before(tool, contract=None):
    """Return None when the call may proceed, else the refusal error contract."""
    if contract is None:
        contract = load(os.path.join(BUNDLE, "tools", tool, "tool.json"))
    gate = contract.get("safety_gate") or {}
    if contract.get("side_effects") == INSTALL:           # asked of every network tool, whether or not it asks for a gate
        return install_refused(tool, contract) or by_permission(tool, contract)
    if not gate.get("required"):
        return None
    if gate.get("opens_by") == "execution_permission":
        return by_permission(tool, contract)
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
