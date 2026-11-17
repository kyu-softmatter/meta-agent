---
name: box_length_for_volume_fraction
description: The side of a cubic box that holds a number of particles of a given volume at a given volume fraction. Any simulation set up by its volume fraction, whatever the particle's shape.
---

# box_length_for_volume_fraction

**Gives:** the side of the cubic box, and its volume.

**Needs:** `particle_count`, `particle_volume` (in the engine's own length units, cubed) and `volume_fraction`, each a row of the sheet with its own source. The particle's volume is its own row or another skill's output, so the shape does not enter this skill.

**When it applies:** a cubic box of identical particles that do not overlap, set up by its volume fraction; a box of another shape, or a mixture, is another relation.

**What it does not say:** whether that volume fraction can be reached, or how long the engine takes to reach it.

Run it through the runner; never type its result.
