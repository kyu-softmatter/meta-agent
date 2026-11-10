"""The echo tool's adapter: the mock backend the Designer bundles for its first target.

run(payload) returns the output object of tests/fixtures/echo/README.md, or the
documented error contract when the message is missing, not a string or empty.
"""


def run(payload):
    message = payload.get("message") if isinstance(payload, dict) else None
    if not isinstance(message, str) or message == "":
        return {
            "artifact": "error_contract",
            "schema_version": "0.1",
            "code": "ECHO-INPUT-001",
            "category": "invalid_input",
            "message": "message is missing, not a string, or empty",
            "retryable": False,
            "remediation": {"action": "send a JSON object with a non-empty string field message"},
            "evidence": {"input": payload},
        }
    return {"message": message, "length": len(message)}
