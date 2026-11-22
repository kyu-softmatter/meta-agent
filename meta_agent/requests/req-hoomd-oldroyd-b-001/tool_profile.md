# tool_profile tp-hoomd-oldroyd-b-001

Tool `HOOMD-blue` (engine), read from https://hoomd-blue.readthedocs.io/en/latest/ (units, md.bond.Harmonic, md.methods.Brownian, md.compute.ThermodynamicQuantities), read on the days their material cards name; the release they document is a row of values_read. Analysis permission: none; binaries and runtime were not analysed.

## Claims

- **observed** (documentation): HOOMD-blue adopts no system of units: it follows a self-consistent one on three base units, energy, length and mass, from which time, force and pressure are derived; at Units, sections Base Units and Unit Conversion (mat-20261120-hoomd-7.2.2-units)
- **observed** (documentation): md.bond.Harmonic gives each bond the energy U(r) = k (r - r0)^2 / 2, with k the potential constant in energy per length squared and r0 the rest length, set per bond type in params; at hoomd.md.bond.Harmonic, the formula and params (mat-20261120-hoomd-7.2.2-bond-harmonic)
- **observed** (documentation): md.methods.Brownian integrates the overdamped Langevin equation on a particle filter at a temperature kT (energy) with a translational drag coefficient gamma per particle type (mass per time), the random force sized by the fluctuation-dissipation theorem; its error is first order in the time step; at hoomd.md.methods.Brownian, the equations of motion, the parameters and the warning (mat-20261121-hoomd-7.2.2-methods-brownian)
- **observed** (documentation): md.compute.ThermodynamicQuantities reports pressure_tensor, six components xx, xy, xz, yy, yz, zz, each the kinetic sum plus the net virial of the integrator's forces over the volume, in pressure units; under Brownian the velocities are drawn each step at the set temperature; at hoomd.md.compute.ThermodynamicQuantities, property pressure_tensor (mat-20261121-hoomd-7.2.2-compute-thermodynamicquantities), hoomd.md.methods.Brownian, the paragraph on velocities (mat-20261121-hoomd-7.2.2-methods-brownian)
- **observed** (documentation): HOOMD-blue computes the virial and the pressure only on steps where a GSD writer or an NPT integrator needs them unless Simulation.always_compute_pressure is set; read between them, pressure_tensor is not a number; at hoomd.Simulation, property always_compute_pressure (mat-20261121-hoomd-7.2.2-simulation), the run adapter's first trial under TMPDIR, every logged component not a number, and its second, finite with the flag set (failure bd-1)
- **observed** (run_record): the run adapter, tried under TMPDIR with hoomd from conda-forge, ran Brownian dynamics of Hookean dumbbells and logged the xy, xz and yz components of the pressure tensor with the box volume; passed through autocorrelation_of_series, shear_relaxation_modulus_green_kubo and exponential_decay_fit they gave a relaxation time and a viscosity near the dumbbell relations' for the trial's settings (evidence for the adapter only; no value of it enters a card); at the adapter's third trial under TMPDIR, result.json and run.log of its run folder

## Gaps

- none

Parameter candidates: `bead_drag`, `bead_mass`, `box_side`, `budget_s`, `dt`, `equilibration_steps`, `initial_separation`, `kT`, `n_dumbbells`, `sample_every`, `seed`, `spring_k`, `steps`.
