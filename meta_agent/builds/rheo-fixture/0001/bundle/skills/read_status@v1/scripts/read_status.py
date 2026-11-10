"""What state is the device in? One read through the status tool, one verdict by a rule."""

BUSY = ("running", "homing", "initialising", "equilibrating")


def _verdict(reply):
    if reply.get("fault"):
        return "fault"
    if reply.get("state") == "idle" and reply.get("initialised") is True and reply.get("homed") is True:
        return "ready"
    if reply.get("state") in BUSY:
        return "busy"
    return "unknown"


def read_status(inputs, tools):
    reply = tools.call("status", {})
    if "error" in reply:
        return {"verdict": "unknown", "why": "the status tool returned an error", "error": reply["error"]}
    return {"verdict": _verdict(reply), "readings": reply, "value_kind": "measured",
            "measured_at": reply.get("time"), "run_id": reply.get("run_id")}
