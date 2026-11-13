"""What does the device say about its own ranges and modes? One read, returned row by row."""


def read_ranges(inputs, tools):
    reply = tools.call("ranges", {})
    if "error" in reply:
        return {"reported": False, "why": "the ranges tool returned an error", "error": reply["error"]}
    wanted = inputs.get("quantities") or []
    rows, inconsistent, seen = [], [], []
    for r in reply.get("ranges") or []:
        name = r.get("quantity")
        if wanted and name not in wanted:
            continue
        seen.append(name)
        low, high, unit = r.get("min"), r.get("max"), r.get("unit")
        if low is None or high is None or unit is None or low > high:
            inconsistent.append(name)
            continue
        rows.append({"quantity": name, "min": low, "max": high, "unit": unit, "reported_by": "device", "tool": "ranges"})
    return {"reported": True, "modes": reply.get("modes") or [], "ranges": rows,
            "missing": [q for q in wanted if q not in seen], "inconsistent": inconsistent}
