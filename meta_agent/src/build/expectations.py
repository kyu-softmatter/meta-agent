"""What an interface or replay item expects of a call's output, judged before a bundle is written (dft-13).

The bundle's judge (src/replay.py, which src/validate_tasks.py uses for the interface gate) compares only the output
fields an item names. An item that expects an output and names none passes whatever the call returns: a tool that
reports an engine's end in its output (an exit status, a converged flag, a state) passes its interface task with the
engine failed, and nothing in the verdicts shows it (dft-13: if-4 passed run_example's exit status 1). From the
template version FROM on, the builder refuses such an item: it names at least one field and the value it must have,
and each field it names is one the tool's contract declares under its outputs, so that a field the call never returns
is not expected by a typo.

The values an output field may take at all are the contract's: a field declared with `const` or `enum` is checked by
the bundle's runner for every type from that version on (src/run_tool.py), so a contract can say that a call that
answers ended well, and a call whose engine ended otherwise comes back as an error.

Nothing here makes a call or reads a value from a run.
"""

FROM = 36


def _version(template_meta):
    try:
        return int(str((template_meta or {}).get("version") or "v0")[1:])
    except ValueError:
        return 0


def problems(items, contracts, template_meta, what):
    """The reasons the items cannot be built under this template, or []. `items` are interface tasks or replay items,
    `contracts` the tools' contracts, `what` 'interface task' or 'replay item' for the message."""
    if _version(template_meta) < FROM:
        return []
    declared = {}
    for c in contracts or []:
        props = ((c.get("outputs") or {}).get("properties") or {}) if isinstance(c, dict) else {}
        declared[c.get("name")] = set(props)
    out = []
    for it in items or []:
        if not isinstance(it, dict):
            continue
        expected = it.get("expected") or {}
        if "error" in expected:
            continue
        iid = it.get("id")
        want = expected.get("output")
        if not isinstance(want, dict) or not want:
            out.append("%s %s expects an output and names no field of it, so it would pass whatever the call returns: "
                       "it names at least one output field and the value it must have, such as the exit status or the "
                       "state the call must end with (dft-13)" % (what, iid))
            continue
        tool = (it.get("call") or {}).get("tool")
        if tool in declared:
            unknown = sorted(k for k in want if k not in declared[tool])
            if unknown:
                out.append("%s %s expects output field(s) %s that the contract of %s does not declare under its outputs"
                           % (what, iid, ", ".join(unknown), tool))
    return out
