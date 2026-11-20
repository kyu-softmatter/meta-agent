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

A tool that reaches the network runs only where its gate opens by the
execution permission, the permission reaches an engine, and the tool is one
of two calls or both. An install of this agent's own packages: its contract
names installs_from {installer, channel} and the permission lists that same
pair under package_sources. A read of data: its contract names fetches_from,
a list of {host, access}, and the permission lists every one of those hosts
under data_sources with the same access; a host is matched by equality. Each
is judged against its own list: data_sources never opens an install and
package_sources never opens a read. A pair the permission allows for named
engines alone (its engines list) opens an install only in a bundle whose
CAPABILITIES.json names one of them as its engine (v27; the person,
2026-11-18, 'Yes, covered'), as the builder's bundle check B9 judges it; a
pair listed without engines opens it for any. Every other tool that reaches
the network is refused, whatever its contract says.

The gate reads envelope/safety.json, envelope/execution_permission.json,
CAPABILITIES.json and tools/<tool>/tool.json and nothing else. It never writes. A refusal is
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
INSTALL = "network"                                              # only to install or to read, from what is listed


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


def engines_of(p, pair):
    """The engines the permission allows a pair for, where every entry of that pair names them; None where an entry
    of it names none, and the pair is then allowed for any engine."""
    entries = [s for s in (p or {}).get("package_sources") or [] if isinstance(s, dict)
               and (s.get("installer"), s.get("channel")) == pair]
    if entries and all(isinstance(s.get("engines"), list) for s in entries):
        return sorted({e for s in entries for e in s["engines"]})
    return None


def this_engine():
    """The engine this bundle was built for, as its CAPABILITIES.json names it; None where it names none."""
    path = os.path.join(BUNDLE, "CAPABILITIES.json")
    cap = load(path) if os.path.isfile(path) else {}
    return cap.get("engine") if isinstance(cap, dict) else None


def hosts(p):
    return [(h.get("host"), h.get("access")) for h in (p or {}).get("data_sources") or [] if isinstance(h, dict)]


def network_refusal(tool, contract, why):
    src = contract.get("installs_from") if isinstance(contract.get("installs_from"), dict) else {}
    fetches = contract.get("fetches_from") if isinstance(contract.get("fetches_from"), list) else []
    p = execution_permission()
    return {
        "artifact": "error_contract",
        "schema_version": "0.1",
        "code": "GATE-NETWORK-001",
        "category": "refused_by_safety",
        "message": "%s reaches the network and %s; the network calls this agent may make are an install from a source "
                   "the lab's permission lists and a read of data from hosts it lists" % (tool, why),
        "retryable": False,
        "remediation": {"action": "a package source or a data host is the person's to allow, in the lab's profile; the builder "
                                  "copies it into envelope/execution_permission.json at a build, and no session writes that file"},
        "evidence": {"tool": tool, "installs_from": src or None, "package_sources": ["%s/%s" % a for a in listed(p)],
                     "fetches_from": fetches or None, "data_sources": ["%s (%s)" % h for h in hosts(p)]},
    }


def network_refused(tool, contract):
    """None when a network tool is an install from a listed source, a read from listed hosts, or both, else the
    refusal. Each is judged against its own list, and neither list opens the other."""
    if (contract.get("safety_gate") or {}).get("opens_by") != "execution_permission":
        return network_refusal(tool, contract, "its gate does not open by the execution permission")
    src = contract.get("installs_from")
    fetches = contract.get("fetches_from")
    if not isinstance(src, dict) and not (isinstance(fetches, list) and fetches):
        return network_refusal(tool, contract, "its contract names neither installs_from nor fetches_from")
    p = execution_permission()
    if isinstance(src, dict):
        pair = (src.get("installer"), src.get("channel"))
        if pair not in listed(p):
            return network_refusal(tool, contract, "installs from %s/%s, which the permission does not list under "
                                                   "package_sources" % pair)
        scope = engines_of(p, pair)
        if scope is not None and this_engine() not in scope:
            return network_refusal(tool, contract, "installs from %s/%s, which the permission allows only for the engines "
                                                   "%s; this bundle's CAPABILITIES.json names the engine %r" % (
                                                       pair + (", ".join(scope), this_engine())))
    if isinstance(fetches, list) and fetches:
        missing = [f for f in fetches if not isinstance(f, dict) or (f.get("host"), f.get("access")) not in hosts(p)]
        if missing:
            return network_refusal(tool, contract, "fetches from %s, which the permission does not list under data_sources" % (
                ", ".join("%s (%s)" % (f.get("host"), f.get("access")) if isinstance(f, dict) else repr(f) for f in missing)))
    return None


def by_permission(tool, contract):
    """None when the lab's permission opens this tool, else the refusal naming the level found."""
    effects = contract.get("side_effects")
    if effects not in PERMISSION_OPENS + (INSTALL,):
        return permission_refusal(tool, None, "its side effects are %r; the permission opens only %s, and an install or a "
                                  "read of data from what it lists; any other tool opens by safety values a person wrote" % (
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
        return network_refused(tool, contract) or by_permission(tool, contract)
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
