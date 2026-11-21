---
name: timestep_max_from_period
description: The largest time step that still resolves a period, such as a bond's vibration, into a stated number of steps. Take it when a run's time step is chosen against the fastest motion it must follow.
---

# timestep_max_from_period

**Gives:** `time_step_max`, the period divided by the steps it is to span.

**Needs:** `period`, in the engine's own time unit, and `steps_per_period`, a judgement bound to a row.

**When it applies:** a run whose fastest motion has the period handed.

**What it does not say:** how many steps a period needs. That depends on the integrator and is a person's judgement.

Run it through the runner; never type its result.
