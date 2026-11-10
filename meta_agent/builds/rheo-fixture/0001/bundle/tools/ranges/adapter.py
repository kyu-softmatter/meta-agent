"""A mock adapter of the fixture rheometer (meta_agent/tests/fixtures/rheometer/README.md).

It returns what that page says the tool returns and reaches nothing: no device, no file, no network.
"""

ADDRESS = "mock:rheo-1"
SESSION = "s-1"
UNAVAILABLE = {'artifact': 'error_contract', 'schema_version': '0.1', 'code': 'RHEO-UNAVAILABLE-001', 'category': 'unavailable', 'message': 'no reply from the instrument', 'retryable': True, 'remediation': {'action': 'check the connection'}}


def run(payload):
    return {"modes": ["steady_shear", "oscillation"],
            "ranges": [{"quantity": "torque", "min": 1e-08, "max": 0.2, "unit": "N.m"},
                       {"quantity": "angular_velocity", "min": 1e-06, "max": 300.0, "unit": "rad/s"},
                       {"quantity": "temperature", "min": 253.15, "max": 473.15, "unit": "K"}]}
