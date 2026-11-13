# `read_status@v1`

Rendered by the build from `skills/read_status@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** reads the device's state and says ready, busy, fault or unknown.
- **Kind:** hardware_state. **Side effect:** read_device. **Status:** usable.
- **Calls tools:** `status`.
- **Uses skills:** none.
- **Valid for:** a device whose status tool returns state, initialised, homed and fault.

## Inputs

- none

## Outputs

- `verdict` (1): ready | busy | fault | unknown, by the rule in the skill.
- `readings` (1): what the status tool returned, unchanged.
- `value_kind` (1): measured: the readings are the device's own, taken in this call.
- `measured_at` (1): the device's time on the reading, or null when it gave none.
- `run_id` (1): the run the reading belongs to, or null outside a run.
- `why` (1): why the verdict is unknown, when the tool returned an error.
- `error` (1): the error contract the tool returned, unchanged.

## Run

```
python src/run_skill.py read_status@v1 < inputs.json
```
