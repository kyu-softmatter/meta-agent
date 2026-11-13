# `find_and_identify@v1`

Rendered by the build from `skills/find_and_identify@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** lists what answers, opens one session, reads the instrument's identity and closes the session.
- **Kind:** hardware_connection. **Side effect:** read_device. **Status:** usable.
- **Calls tools:** `list_devices`, `open_session`, `identify`, `close_session`.
- **Uses skills:** none.
- **Valid for:** an instrument whose tools list what answers and identify one session at a time.

## Inputs

- `address` (1): the address to open, or null to open the only instrument that answers.

## Outputs

- `identified` (1): true when an identity was read.
- `found` (1): the addresses that answered.
- `address` (1): the address that was opened.
- `identity` (1): observed claims, one per field read: field, value, kind, tool.
- `session_closed` (1): true when the session it opened was closed again.
- `why` (1): why no identity was read.
- `error` (1): the error contract a tool returned, unchanged.

## Run

```
python src/run_skill.py find_and_identify@v1 < inputs.json
```
