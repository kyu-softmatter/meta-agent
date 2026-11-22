---
name: unit_convert
description: The factor between two registered units of one dimension and a value converted by it, read from the registry's entries its caller hands; into or out of an engine's own unit only through the registered unit a scale says it stands for, and nothing where the dimensions differ or no scale is handed. Take it whenever a value received from another agent, or read in one unit and wanted in another, changes unit.
---

# unit_convert

**Gives:** `factor`, `converted` (the value times the factor, in the unit wanted) and `state`: `converted`, or `not_convertible` with `why`.

**Needs:** `value`; `from_unit` and `to_unit`, each the registry's entry (name, si_factor, dim) as the bundle's copy of the registry holds it; `stands_for`, the entry of the registered unit a scale says the engine's own unit the value goes into stands for, or null; and `from_stands_for`, the same for the engine's own unit the value comes from (a value an engine computed), or null.

**When it applies:** multiplicative units of one dimension. An engine's own unit takes or gives a value only through a scale, and handing a scale is its caller's decision: in a bundle, a scale the person confirmed.

**What it does not say:** whether a scale was confirmed, or whether the value should be used. It never converts between dimensions and never guesses a scale.

Run it through the runner; never type its result.
