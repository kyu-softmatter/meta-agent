"""The boot sequence: the person's steps, initialise, home, a last check. It stops where it is and never skips."""

PERSON_STEPS = (1, 2)


def _stop(n, why, **more):
    out = {"ready": False, "stopped_at": n, "why": why}
    out.update(more)
    return out


def _refused(error):
    return "refused_by_safety" in (error.get("code"), error.get("category"))


def _readings(skills):
    status = skills.run("read_status@v1", {})
    return status, status.get("readings") or {}


def bring_to_ready(inputs, tools, skills):
    confirmed = inputs.get("person_confirmed") or []
    for n in PERSON_STEPS:
        if n not in confirmed:
            return _stop(n, "the person has not said this step is done", waiting_for="person")

    reply = tools.call("initialise", {})
    if "error" in reply:
        return _stop(3, "the tool refused or failed", refused=_refused(reply["error"]), error=reply["error"])
    status, readings = _readings(skills)
    if readings.get("initialised") is not True:
        return _stop(3, "initialised was not read back as true", verdict=status.get("verdict"))

    reply = tools.call("home", {})
    if "error" in reply:
        return _stop(4, "the tool refused or failed", refused=_refused(reply["error"]), error=reply["error"])
    status, readings = _readings(skills)
    if readings.get("homed") is not True:
        return _stop(4, "homed was not read back as true", verdict=status.get("verdict"))

    status, readings = _readings(skills)
    if status.get("verdict") != "ready":
        return _stop(5, "the last check did not return ready", verdict=status.get("verdict"))
    return {"ready": True, "stopped_at": None, "verdict": "ready"}
