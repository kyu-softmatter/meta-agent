# tool_profile tp-qe-h2-bond-001

Tool `Quantum ESPRESSO pw.x (PWscf)` (engine), read from https://www.quantum-espresso.org/Doc/INPUT_PW.html, read on the day its material card names; the release it documents is a row of values_read. Analysis permission: none; binaries and runtime were not analysed.

## Claims

- **observed** (documentation): pw.x reads namelists &CONTROL, &SYSTEM and &ELECTRONS and the cards ATOMIC_SPECIES, ATOMIC_POSITIONS and K_POINTS; quantities whose dimensions are not stated are in Rydberg atomic units; at INPUT_PW.html, INTRODUCTION: 'All quantities whose dimensions are not explicitly specified are in RYDBERG ATOMIC UNITS'
- **observed** (documentation): ecutwfc and ecutrho are the kinetic energy cutoffs in Ry for wavefunctions and for charge density; with ultrasoft pseudopotentials an ecutrho larger than four times ecutwfc is often desirable; at INPUT_PW.html, &SYSTEM, ecutwfc and ecutrho
- **observed** (documentation): celldm(1) is the lattice parameter in bohr; with ibrav 1 the cell is simple cubic; at INPUT_PW.html, &SYSTEM, celldm(i)
- **observed** (documentation): assume_isolated 'martyna-tuckerman' corrects the total energy and the self-consistent potential of a molecule in a 3D supercell; at INPUT_PW.html, &SYSTEM, assume_isolated
- **observed** (documentation): the species mass in ATOMIC_SPECIES is used only for molecular dynamics or damped dynamics, not in an scf run; at INPUT_PW.html, ATOMIC_SPECIES, Mass_X
- **observed** (documentation): the pseudopotential H.pbe-rrkjus_psl.1.0.0.UPF is ultrasoft, for the PBE functional, and states suggested minimum cutoffs for wavefunctions and charge density; at H.pbe-rrkjus_psl.1.0.0.UPF, PP_INFO lines 6 to 10
- **observed** (run_record): pw.x from conda-forge, at the version values_read names, ran an scf of one H2 molecule from the adapter's input, printed the total energy on its line starting with an exclamation mark, the convergence line and JOB DONE, and, given a species mass of zero, printed the mass it took from its own table; at the adapter's trial under TMPDIR, pw.out of each point of a scan (evidence for the adapter only; no value of it enters a card)
- **observed** (run_record): with n_processes two, pw.x ran through the environment's mpirun and printed the number of MPI processes; at the adapter's trial under TMPDIR, pw.out

## Gaps

- none

Parameter candidates: `bond_lengths`, `box_side`, `budget_s`, `conv_thr`, `ecutrho`, `ecutwfc`, `n_processes`, `pseudo_dir`.
