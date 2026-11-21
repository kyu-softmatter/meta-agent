# tool_profile tp-hoomd-h2-bond-001

Tool `HOOMD-blue` (engine), read from https://hoomd-blue.readthedocs.io/en/latest/ (units, md.bond.Harmonic, md.methods.ConstantVolume), read on the day their material cards name; the release they document is a row of values_read. Analysis permission: none; binaries and runtime were not analysed.

## Claims

- **observed** (documentation): HOOMD-blue adopts no system of units: it follows a self-consistent one on three base units, energy, length and mass, from which time, force and pressure are derived; at Units, sections Base Units and Unit Conversion (mat-20261120-hoomd-7.2.2-units)
- **observed** (documentation): md.bond.Harmonic gives each bond the energy U(r) = k (r - r0)^2 / 2, with k the potential constant in energy per length squared and r0 the rest length, set per bond type in params; at hoomd.md.bond.Harmonic, the formula and params (mat-20261120-hoomd-7.2.2-bond-harmonic)
- **observed** (documentation): md.methods.ConstantVolume integrates by velocity Verlet and, with a thermostat, samples a canonical ensemble; with none, constant energy; at hoomd.md.methods.ConstantVolume (mat-20261120-hoomd-7.2.2-methods-constantvolume)
- **observed** (run_record): hoomd from conda-forge, at the version values_read names, ran the adapter's script on molecules with a harmonic bond and reported the bonds' energy, the potential energy and the kinetic temperature; at the adapter's trial under TMPDIR, result.json and run.log of a run (evidence for the adapter only; no value of it enters a card)

## Gaps

- none

Parameter candidates: `bond_k`, `bond_r0`, `box_side`, `budget_s`, `dt`, `kT`, `log_every`, `n_molecules`, `particle_mass`, `seed`, `steps`.
