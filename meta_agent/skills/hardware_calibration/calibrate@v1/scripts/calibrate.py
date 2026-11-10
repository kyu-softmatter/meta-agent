"""Calibrate one quantity the way the profile says the device allows: self, assisted or unknown."""

SETTLED = ("observed", "derived", "inferred")


def _refused(error):
    return "refused_by_safety" in (error.get("code"), error.get("category"))


def _gap(quantity, requires):
    return {"mode": "unknown", "calibrated": False,
            "gap": {"what": "whether the device calibrates %s itself" % quantity,
                    "searched": ["tool_profile.self_calibration"], "requires": requires}}


def _design(quantity, instrument, claim):
    questions = [
        "Which reference for %s is in the laboratory, and what does its certificate say (lot, value, valid until)?" % quantity,
        "What difference between the reference and the reading do you accept?",
        "How often should this be repeated?",
    ]
    return {
        "card": "calibration_design", "status": "draft", "instrument": instrument, "quantity": quantity, "mode": "assisted",
        "profile_claim": "self_calibration[quantity = %s] says assisted: %s" % (quantity, claim.get("claim")),
        "reference": {"what": None, "traceability": None, "provided_by": "the person"},
        "steps": [
            {"n": 1, "actor": "person", "action": "bring the reference for %s to the instrument and state what its certificate says" % quantity,
             "reading": "the certificate's lot, value and validity", "recorded_as": "operator_read"},
            {"n": 2, "actor": "device", "action": "measure %s on the reference" % quantity,
             "reading": quantity, "recorded_as": "measured"},
            {"n": 3, "actor": "person", "action": "read the certificate value beside the measured one and decide",
             "reading": "the difference between the two", "recorded_as": "operator_read"},
        ],
        "interval": None,
        "acceptance": {"criterion": "the reading agrees with the reference within a limit the person chooses",
                       "limit": None, "author": None},
        "open_questions": questions, "confirmed_by": None,
    }


def calibrate(inputs, tools):
    quantity = inputs["quantity"]
    rows = [r for r in inputs.get("self_calibration") or [] if r.get("quantity") == quantity]
    if not rows:
        return _gap(quantity, "a self_calibration claim for %s in the tool profile (S2)" % quantity)
    mode, claim = rows[0].get("mode"), rows[0].get("claim") or {}
    if mode not in ("self", "assisted") or claim.get("kind") not in SETTLED:
        return _gap(quantity, claim.get("requires") or "evidence of how %s is calibrated on this device" % quantity)

    if mode == "assisted":
        design = _design(quantity, inputs.get("instrument"), claim)
        return {"mode": "assisted", "calibrated": False, "calibration_design": design,
                "open_questions": design["open_questions"]}

    reply = tools.call("self_calibrate", {"quantity": quantity})
    if "error" in reply:
        return {"mode": "self", "calibrated": False, "refused": _refused(reply["error"]), "error": reply["error"],
                "why": "the routine was refused or failed"}
    if not reply.get("calibration_id") or not reply.get("valid_until"):
        return {"mode": "self", "calibrated": False,
                "why": "the routine returned no id or no expiry; a calibration without them enters nothing"}
    return {"mode": "self", "calibrated": True,
            "calibration": {"name": "%s_calibration" % quantity, "value": reply.get("value"), "unit": reply.get("unit"),
                            "source": "calibration:%s" % reply["calibration_id"], "value_kind": "measured",
                            "expires": reply["valid_until"]}}
