"""One steady shear step: check the state, set, start, poll, stop. Every device call is a tool call."""


def _stop(step, why, **more):
    out = {"completed": False, "stopped_at": step, "why": why}
    out.update(more)
    return out


def _refused(error):
    return "refused_by_safety" in (error.get("code"), error.get("category"))


def run_steady_shear(inputs, tools, skills):
    before = skills.run("read_status@v1", {})
    if before.get("verdict") != "ready":
        return _stop("check_state", "the device is not ready", verdict=before.get("verdict"))

    reply = tools.call("set_shear_rate", {"shear_rate": inputs["shear_rate"]})
    if "error" in reply:
        return _stop("set", "the tool refused or failed", refused=_refused(reply["error"]), error=reply["error"])

    started = tools.call("start", {"duration": inputs["duration"]})
    if "error" in started:
        if _refused(started["error"]):
            return _stop("start", "the gate refused the start", refused=True, error=started["error"])
        halted = tools.call("stop", {})
        return _stop("start", "the start failed; stop was called", refused=False, error=started["error"],
                     stop_confirmed="error" not in halted)

    polls, last = 0, {}
    for _ in range(inputs["max_polls"]):
        last = skills.run("read_status@v1", {})
        polls += 1
        if last.get("verdict") != "busy":
            break
    halted = tools.call("stop", {})
    out = {"run_id": started.get("run_id"), "polls": polls, "verdict": last.get("verdict"),
           "stop_confirmed": "error" not in halted}
    if last.get("verdict") == "ready":
        out.update(completed=True, stopped_at=None)
    elif last.get("verdict") == "busy":
        out.update(completed=False, stopped_at="poll", why="still running after the polls the caller allowed; stop was called")
    else:
        out.update(completed=False, stopped_at="poll", why="the device left the run without returning to ready; stop was called")
    return out
