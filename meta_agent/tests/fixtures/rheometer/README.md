# The fixture rheometer

A rotational rheometer that does not exist. This page is its whole documentation: the profile the first
hardware skills of `meta_agent/skills/` were written against (plan.md 14-31(j)). Everything beside it in
this folder was written by hand from this page: the transcripts are the replies a device of this
description would give, the inputs are what a caller would hand a skill. Nothing here was read from a
device, and nothing here is a limit, a safety value or a threshold.

## Tools

Each tool takes one JSON object and returns one, or an error contract.

- `list_devices {}` returns `devices`, a list of `{address, answers}`.
- `open_session {address}` returns `{session}`; `close_session {session}` returns `{closed}`.
- `identify {session}` returns `manufacturer`, `model`, `serial`, `firmware`.
- `status {}` returns `state` (`idle`, `running`, `homing`, `initialising`, `equilibrating`), `initialised`,
  `homed`, `fault` (null or a sentence), `temperature` in kelvin, `gap` in metres, `time` and `run_id`.
  It reads and changes nothing.
- `ranges {}` returns `modes` and `ranges`, a list of `{quantity, min, max, unit}`: what the device says
  about itself. It reads and changes nothing.
- `initialise {}`, `home {}`, `set_shear_rate {shear_rate}`, `start {duration}`, `stop {}` change the
  device. `start` returns a `run_id`; the step ends by itself and the device returns to `idle`.
- `self_calibrate {quantity}` runs the device's own routine and returns `calibration_id`, `quantity`,
  `value`, `unit` and `valid_until`.

Every tool that changes the device is behind the bundle's gate. A gate that refuses returns the error
contract `GATE-SAFETY-001`, category `refused_by_safety`, and the call reaches no device.

## Start-up

In this order: a person opens the air supply to the bearing; a person removes the transport lock; the
motor and the electronics are initialised (`initialise`, read back as `initialised`); the home position is
found (`home`, read back as `homed`); the device is ready when `status` says `idle`, `initialised` and
`homed` with no fault.

## Steady shear

Set the shear rate, start a step of a given duration, read the state while it runs, stop.

## Calibration

`self_calibration.json` is this profile's `self_calibration` list (the shape of `tool_profile`):
the motor adjustment is mapped by the device's own routine (`self`); torque is checked against a
certified viscosity standard that a person loads (`assisted`); how the normal force is calibrated is not
stated here (`unknown`).
