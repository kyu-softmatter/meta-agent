"""Who is there? List what answers, open one session, read the identity, close the session."""

FIELDS = ("manufacturer", "model", "serial", "firmware")


def _no(why, found, **more):
    out = {"identified": False, "found": found, "why": why}
    out.update(more)
    return out


def find_and_identify(inputs, tools):
    listed = tools.call("list_devices", {})
    if "error" in listed:
        return _no("the list of devices could not be read", [], error=listed["error"])
    found = [d.get("address") for d in listed.get("devices") or [] if d.get("answers") is True]
    address = inputs.get("address")
    if address is None:
        if not found:
            return _no("nothing answered", found)
        if found[1:]:
            return _no("several instruments answer and none was named; the caller names one", found)
        address = found[0]
    elif address not in found:
        return _no("the named address did not answer", found, address=address)

    opened = tools.call("open_session", {"address": address})
    if "error" in opened:
        return _no("the session could not be opened", found, address=address, error=opened["error"])
    session = opened.get("session")
    identity = tools.call("identify", {"session": session})
    closed = tools.call("close_session", {"session": session})
    session_closed = "error" not in closed and closed.get("closed") is True
    if "error" in identity:
        return _no("the identity could not be read", found, address=address, session_closed=session_closed,
                   error=identity["error"])
    claims = [{"field": k, "value": identity[k], "kind": "observed", "tool": "identify"} for k in FIELDS if k in identity]
    return {"identified": True, "found": found, "address": address, "identity": claims, "session_closed": session_closed}
