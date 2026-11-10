"""What state is the device in? One read through the status tool, one verdict by a rule."""

BUSY = ("running", "homing", "initialising", "equilibrating")


def read_status(inputs, tools):
    tools.call("identify", {})
    reply = tools.call("status", {})
    if "error" in reply:
        return {"verdict": "unknown", "why": "the status tool returned an error", "error": reply["error"]}
    if reply.get("fault"):
        return {"verdict": "fault", "readings": reply}
    if reply.get("state") == "idle" and reply.get("initialised") is True and reply.get("homed") is True:
        return {"verdict": "ready", "readings": reply}
    if reply.get("state") in BUSY:
        return {"verdict": "busy", "readings": reply}
    return {"verdict": "unknown", "readings": reply}
