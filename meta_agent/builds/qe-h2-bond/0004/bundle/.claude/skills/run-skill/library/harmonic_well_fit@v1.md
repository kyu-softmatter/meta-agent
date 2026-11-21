# `harmonic_well_fit@v1`

Rendered by the build from `skills/harmonic_well_fit@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** the potential constant, the rest position and the well's energy of a harmonic well fitted by least squares to energies at positions about a minimum.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** a well that is harmonic over the positions handed: the anharmonic terms of a real bond bend the fitted k and x0 as the span widens, and this skill does not say by how much; a span that does not hold the minimum gives an extrapolated x0, which minimum_inside_span marks.

## Inputs

- `points` (1): the energy curve: pairs of a position along one coordinate (a bond length, a displacement) and the energy computed or measured there, each part in one unit throughout, three distinct positions or more.

## Outputs

- `force_constant` (1): k of U = U0 + k (x - x0)^2 / 2: twice the fitted curvature, in the unit of the energies over the square of the unit of the positions; null when not fitted.
- `rest_position` (1): x0, the position of the fitted minimum, in the unit of the positions; null when the curvature is not positive.
- `well_energy` (1): U0, the fitted energy at x0, in the unit of the energies.
- `residual_standard_deviation` (1): the residual sum of squares over n - 3, rooted, in the unit of the energies; null with three points, where no degree of freedom is left.
- `minimum_inside_span` (1): true where x0 lies between the smallest and the largest position of the points; a minimum outside them is an extrapolation.
- `points` (count): how many points were handed.
- `state` (1): fitted | no_minimum | not_fitted.
- `why` (1): why nothing was fitted, or why there is no minimum; absent when fitted.

## Run

```
python src/run_skill.py harmonic_well_fit@v1 < inputs.json
```
