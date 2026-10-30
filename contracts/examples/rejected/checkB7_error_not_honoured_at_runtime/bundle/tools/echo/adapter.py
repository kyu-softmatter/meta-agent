"""Fixture adapter: on the word boom it returns a malformed error (no category, message or remediation)."""


def run(payload):
    message = payload.get("message")
    if message == "boom":
        return {"artifact": "error_contract", "code": "ECHO-BOOM"}
    return {"message": message, "length": len(message)}
