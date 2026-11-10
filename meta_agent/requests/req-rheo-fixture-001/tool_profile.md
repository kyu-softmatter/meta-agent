# tool_profile tp-rheo-fixture-001

Tool `fixture_rheometer` (instrument), read from meta_agent/tests/fixtures/rheometer/README.md. Analysis permission: none; binaries and runtime were not analysed.

## Claims

- **observed** (documentation): each tool takes one JSON object and returns one, or an error contract; at ## Tools
- **observed** (documentation): list_devices, open_session, identify and close_session find the instrument and read its identity; none writes a setting; at ## Tools
- **observed** (documentation): status returns the state, whether the device is initialised and homed, a fault if there is one, the temperature, the gap, the time and the run id, and changes nothing; at ## Tools
- **observed** (documentation): ranges returns the modes and, per quantity, the lowest and highest value and the unit, as the device reports them about itself, and changes nothing; at ## Tools
- **observed** (documentation): initialise, home, set_shear_rate, start, stop and self_calibrate change the device, and every one of them is behind the bundle's gate; at ## Tools
- **observed** (documentation): the start-up order is the air supply and the transport lock by a person, then initialise, then home, and the device is ready when status says idle, initialised and homed with no fault; at ## Start-up
- **observed** (documentation): the motor adjustment is calibrated by the device's own routine and torque against a standard a person loads; at ## Calibration
- **unknown** (documentation): how the normal force is calibrated; at no locus; requires: the section of a manual on the normal force transducer

## Gaps

- how the normal force is calibrated (no_material); requires: the section of a manual on the normal force transducer
- a real instrument behaves as the mock adapters do (permission_required); requires: analysis_permission confirmed by a person (granted_by, scope, basis, date)

Parameter candidates: `address`, `session`.
