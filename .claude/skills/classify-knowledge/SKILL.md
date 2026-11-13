---
name: classify-knowledge
description: Settle three things about a piece of knowledge before it is used, namely what kind of knowledge it is, what type of data it is, and what it means. Use whenever a value, a statement, a table, a curve or a data file is about to enter a card, a sheet, a skill's inputs or a report, when a source is read, when two values are to be compared, and when a file's format or a quantity's definition is not certain.
---

# Classify a piece of knowledge: its kind, its data type, its meaning

A value with the wrong kind gets the wrong grade. A wrong type breaks the code that reads it. A wrong meaning gives a right number for another quantity. Settle all three before the value is written anywhere, and write `unknown` where one cannot be settled.

## Its kind: how it is known

1. **A statement** is `observed`, `derived`, `inferred` or `unknown`; a **setting** is `confirmed`, `inferred` or `unknown`. The meanings are in `contracts/claim_kinds.json`. An inference is never written as an observation, and only the person makes a setting `confirmed`.
2. **Where a number comes from** is the part of its `source` before the colon: `measured` (a run of this system), `calibration`, `literature`, `database`, `spec` (a vendor's specification), `prior_run` (a run somewhere else), `operator_read`, `computed`, `correlation`, `predicted`, `assumed`, `operator_recall`.
3. **What kind of value it is:** `measured`, `correlation`, `computed`, `predicted`, `literature` or `estimated`.
4. **The grade is derived, never stated:** it is looked up from the two above in `contracts/grades.json`. A computed value is no better than its worst input.

Where the kinds are most often confused:

- A vendor's specification is not a measurement of this instrument.
- A run somewhere else is not a run here.
- A fitted or empirical relation gives a `correlation`, not an exact `computed` value.
- A value in a paper may be measured there, computed there, or quoted from another paper: follow it to where it was obtained, or say that you could not.
- A value you remember or work out yourself is none of these. It is a model's number, and it enters nothing.

## Its data type: what shape it has

Say which it is, read off the source and not assumed:

- **a number with a unit**, and its uncertainty, or that none is given;
- **a range:** two rows, a minimum and a maximum;
- **one of a listed set of options:** a mode, a geometry, an objective; the whole set is listed, with its evidence;
- **a series or a curve:** values against an independent variable, with both units, the sampling and the length;
- **a table**, with what each column is and its unit;
- **a count, or a yes or no;**
- **a statement in words**, kept as words: do not turn it into a number;
- **a file:** its format, what is header and what is data, the columns and their units, the time base, how missing values are written.

Units are those of `contracts/units.json`. Convert only through the registry, and check the dimension. A unit that is not registered is asked of the design role, not converted by hand. Temperature is carried in kelvin, and a reading given in Celsius is noted on the number. Significant figures follow the worst input.

For a data file, what you read about its layout is itself a claim: `observed` when you read it in the file, with the place; `inferred` when you guessed it from a name or a habit.

## Its meaning: what it is a value of

1. **Which quantity, by its definition.** The name and the symbol the source uses, and the convention behind it. One word often covers several quantities: a viscosity that is dynamic or kinematic, a height measured to a centre or to a surface, a rate or an angular frequency, a peak or a root mean square, an amount per particle or per mole.
2. **Of what.** The sample, the model or the instrument it belongs to.
3. **Under what conditions.** Temperature, concentration, geometry, the range over which it holds.
4. **Relative to what.** The reference of a ratio and the zero of a scale.
5. **How it was obtained.** The method decides what it may be compared with.
6. **What it is for here.** The row, the parameter or the claim of this request that it supports. A value nothing here needs is not carried.

Name the number so that its meaning cannot be mistaken, and carry its conditions as condition tags. Two values that mean different things do not conflict. Two that mean the same thing and differ are a conflict, and both stay.

## When it cannot be settled

Write it as `unknown` and say what would settle it: a source, a measurement, the person. Ask one question when two readings would lead to different work. Do not pick the likelier reading and go on.

## Never

State a grade by hand. Give a model's number any kind. Convert a unit by hand. Put two definitions under one name. Compare two values before their meanings are shown to be the same.
