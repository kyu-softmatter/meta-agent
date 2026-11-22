# tool_profile tp-rheotool-oldroyd-b-001

Tool `rheoTool on OpenFOAM (rheoFoam)` (engine), read from rheoTool's user guide (mat-20261121-rheotool-6.0-user-guide), its of90 tutorials and OpenFOAM's own planarPoiseuille tutorial, read on the day their material cards name. Analysis permission: none; binaries and runtime were not analysed.

## Claims

- **observed** (documentation): rheoTool's Oldroyd-B model (TypeName Oldroyd-B, or Oldroyd-BLog for the log-conformation approach) takes the constants etaS, etaP and lambda in constitutiveProperties, with rho, each a dimensioned value in OpenFOAM's SI dimension set (dynamic viscosity, time, density); at the user guide, Table 4.1 (mat-20261121-rheotool-6.0-user-guide), of90 tutorial rheoFoam/Channel/Oldroyd-BLog, constant/constitutiveProperties (mat-20261121-rheotool-of90-channel-oldroyd-b-constitutive)
- **observed** (documentation): rheoFoam is a transient solver whose momentum equation takes fvOptions, and rheoTool supports cyclic patches, so a channel may be driven by a momentum source with periodic ends; at the user guide, section 4.7.1, the listing of rheoFoam's momentum equation, and the changelog on cyclicAMI (mat-20261121-rheotool-6.0-user-guide)
- **observed** (documentation): the analytical velocity of the start-up planar Poiseuille flow of an Oldroyd-B fluid is Waters and King's series in the elasticity number lambda eta0/(rho h^2) and the solvent's share beta, h the half-width and time scaled by lambda; at Amoreira and Oliveira (2010), equations (2.6)-(2.9) (mat-20261121-amoreira-oliveira-2010-startup), OpenFOAM-9 validation/WatersKing/WatersKing.C (mat-20261121-openfoam-9-planarpoiseuille-watersking)
- **observed** (run_record): the image rheotool:of90 is in the Colima profile rheotool, which `colima list` showed stopped on 2026-11-21; at `colima list` on this computer, 2026-11-21
- **observed** (documentation): rheoFoam's momentum equation is written per unit density: the pressure it solves for and the stress term are divided by the density, so a momentum source given to it in fvModels (semiImplicitSource, volumeMode specific) is a force per unit mass, the pressure gradient over the density; at the user guide, section 4.7 on divTau, 'divided by the density to be compliant with the usual strategy of OpenFOAM', and section 5.1.1 on the pressure (mat-20261121-rheotool-6.0-user-guide), OpenFOAM-9's planarPoiseuille tutorial, constant/fvModels, a semiImplicitSource of volumeMode specific on U (mat-20261121-openfoam-9-planarpoiseuille-watersking, the same tutorial folder)
- **observed** (run_record): the run adapter, tried under TMPDIR, sent a periodic planar channel case into rheotool:of90 through stdin, ran blockMesh and rheoFoam there and read back OpenFOAM's probe of the centreline velocity; the series followed oldroyd_b_startup_channel_velocity for the trial's settings, its overshoot and its oscillation included (evidence for the adapter only; no value of it enters a card); at the adapter's trial under TMPDIR, back/log.rheoFoam and back/postProcessing/probes/0/U of its run folder

## Gaps

- none

Parameter candidates: `budget_s`, `cells_across`, `density`, `driving`, `dt`, `end_time`, `half_width`, `polymer_viscosity`, `probe_every`, `relaxation_time`, `solvent_viscosity`.
