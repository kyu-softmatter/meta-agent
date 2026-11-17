---
name: steps_for_diffusive_displacement
description: The time, and the number of steps, a run needs for a particle of a given diffusivity to move a stated multiple of a size by its root mean squared displacement. Take it to choose how long a run must last for its slowest particle to sample its surroundings, a colloid in a Brownian dynamics engine or a tracer molecule in a molecular dynamics engine alike.
---

# steps_for_diffusive_displacement

**Gives:** the run time and the number of steps.

**Needs:** `diffusivity`, of the slowest particle; `size`, the length the displacement is counted in; `multiple`, how many sizes it is to move; `dimensions`; `time_step`. Each is a row with its own source; the multiple is a choice, and a person's.

**When it applies:** a run whose length is set by how far its slowest particle must diffuse.

**What it does not say:** whether that displacement is enough for what the run measures, or how long the run takes on a computer.

Run it through the runner; never type its result.
