# `flow_curve_fit@v1`

Rendered by the build from `skills/flow_curve_fit@v1/skill.json`; never edited by hand. This page is reference and not a trigger: the sentence that says when to take the skill is in `CLAUDE.md`, and the skill's own `SKILL.md` is beside its manifest.

- **Gives:** fits stress = consistency * rate ^ flow_index to a flow curve and returns both with the residual.
- **Kind:** data_analysis. **Side effect:** none. **Status:** usable.
- **Calls tools:** none.
- **Uses skills:** none.
- **Valid for:** a power-law fluid over the range of the points; a yield stress or a Newtonian plateau is another model and another skill.

## Inputs

- `shear_rate` (1/s): the shear rates of the flow curve, a list.
- `shear_stress` (Pa): the shear stress at each rate, a list of the same length.

## Outputs

- `fitted` (1): true when a fit was made.
- `flow_index` (1): the exponent of the power law.
- `consistency` (Pa.s^n): the stress at a shear rate of one reciprocal second; its unit carries the flow index.
- `residual_rms_log` (1): root mean square of the residuals of ln(stress).
- `points` (count): how many points were fitted.
- `value_kind` (1): computed.
- `basis` (1): how the numbers were computed, naming this skill and its version.
- `why` (1): why no fit was made.

## Run

```
python src/run_skill.py flow_curve_fit@v1 < inputs.json
```
