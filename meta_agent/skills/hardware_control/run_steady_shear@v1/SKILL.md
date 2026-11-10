---
name: run_steady_shear
description: Runs one steady shear step at a shear rate and for a duration the plan gives, then stops the motor. Take it when the plan asks for a steady shear measurement and read_status returns ready. It changes the device, so it is held until a person releases it.
---

# run_steady_shear

**The procedure:** check the state with `read_status@v1` and go on only when it is `ready`; set the shear rate; start; poll the state until the device is no longer busy, at most as many times as the caller allows; stop. Once the motor was started, `stop` is always called, whatever the polls read.

**Needs:** `shear_rate` and `duration` from the plan, and `max_polls`, how many times the caller lets it read the state while the step runs.

**It stops where it is** when the device is not ready, when a tool or its gate refuses, or when a tool errors. After a refusal it calls nothing: a refused call reached no device, so there is nothing to stop. It does not retry.

**Reaches the device through:** `set_shear_rate`, `start` and `stop`, each behind the bundle's gate, and `status` by way of `read_status@v1`.

**What it never does:** hold a limit or choose a value. The rate and the duration are the plan's; whether they are allowed is the gate's question, asked on every call. It compares no reading and no input against a number.
