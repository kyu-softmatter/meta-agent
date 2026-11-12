---
name: estimate-parameter-ranges
description: Find the range each parameter of a request may take, with the limits considered together, by running library skills, and choose inside it with a stated reason. Use when a request needs parameter values or bounds for an instrument or an engine, after the physical system and the tool are analysed, and whenever a row of the sheet changes.
---

# Estimate the parameter ranges

Code computes; you choose and say why. A number you type enters nothing.

## Do this

1. **List the parameters** the request handles, each with the model, the instrument, the units and the valid range it was used in, from sources that were read.
2. **Consider the limits together,** not one parameter at a time: the scales of the system, the requirements that follow from them, the tool's discrete configurations listed in full by code, then the configurations that meet the requirements.
3. **Take every bound skill that applies.** `python -m meta_agent.src.skills list` shows them. Each one that applies to a row is on the sheet, as used or as not applied with a reason.
4. **Let code run them:**
   ```
   python -m meta_agent.src.designer --bounds meta_agent/requests/<rid>
   python -m meta_agent.src.designer --sheet meta_agent/requests/<rid> --seat <seat>
   ```
   The interval is the highest floor and the lowest ceiling, and names the skills they came from.
5. **Choose inside the interval and write the reason:** which skills apply, which quantity is fixed first, which rule or candidate is taken. The value is computed from that choice.
6. **An empty interval carries no point.** Say which bounds conflict and propose what would resolve it: another configuration, a measurement, a calibration, or the person's decision.
7. **Without grounds, propose the measurement** or the calibration that would give them, instead of a value.
8. **Check the sheet:** `python contracts/tools/sheets.py check <sheet>`.

## Safety rows

A safety-relevant row has no value but the person's, and no recommended point or candidate. Bounds may be attached to it as information.

## Never

Type a value, a bound or a default. Drop an applicable skill without a written reason. Optimise: code lists and filters, and no solver enters. Treat a missing bound as a bound that does not bind.

Reference: `plan.md 5.3`, `plan.md 14-30`, `plan.md 14-32`.
