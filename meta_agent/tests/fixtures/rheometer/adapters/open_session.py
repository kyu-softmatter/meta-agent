"""A mock adapter of the fixture rheometer (meta_agent/tests/fixtures/rheometer/README.md).

It returns what that page says the tool returns and reaches nothing: no device, no file, no network.
"""

ADDRESS = "mock:rheo-1"
SESSION = "s-1"
UNAVAILABLE = {'artifact': 'error_contract', 'schema_version': '0.1', 'code': 'RHEO-UNAVAILABLE-001', 'category': 'unavailable', 'message': 'no reply from the instrument', 'retryable': True, 'remediation': {'action': 'check the connection'}}


def run(payload):
    if payload.get("address") != ADDRESS:
        return dict(UNAVAILABLE, evidence={"address": payload.get("address")})
    return {"session": SESSION}
