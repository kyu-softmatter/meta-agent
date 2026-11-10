---
name: gap_min_from_particle_size
description: Lower bound on the measuring gap from the size of the largest particle in the sample. Take it when gap is a parameter and the sample is a suspension, an emulsion or anything with a largest structure.
---

# gap_min_from_particle_size

**Gives:** the smallest gap that still holds the stated number of particle diameters.

**Needs:** two rows of the sheet. `gap_to_particle_ratio` is a judgement and is a row with its own source.

**When it applies:** a sample with a largest particle or structure, in any geometry whose gap is set.

**What it never does:** hold the multiple, or say a geometry is unsuitable: it gives the floor.

Run it through the runner; never type its result.
