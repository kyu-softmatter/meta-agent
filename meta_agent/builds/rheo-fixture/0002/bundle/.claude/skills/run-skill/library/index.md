# Library skills of this agent

Rendered by the build from the manifests under `skills/`; never edited by hand. Each skill has a page beside this file, named after it.

- `find_and_identify@v1` (hardware_connection, read_device, usable): lists what answers, opens one session, reads the instrument's identity and closes the session. Page: `find_and_identify@v1.md`.
- `read_status@v1` (hardware_state, read_device, usable): reads the device's state and says ready, busy, fault or unknown. Page: `read_status@v1.md`.
- `read_ranges@v1` (hardware_range, read_device, usable): reads the modes and the range of each quantity as the device itself reports them. Page: `read_ranges@v1.md`.
- `shear_rate_max_from_max_speed@v1` (bound, none, usable): the highest shear rate a cone-and-plate geometry reaches at the instrument's top angular velocity. Page: `shear_rate_max_from_max_speed@v1.md`.
- `flow_curve_fit@v1` (data_analysis, none, usable): fits stress = consistency * rate ^ flow_index to a flow curve and returns both with the residual. Page: `flow_curve_fit@v1.md`.
