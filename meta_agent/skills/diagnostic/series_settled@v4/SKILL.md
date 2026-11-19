---
name: series_settled
description: Whether a series of readings has settled, by comparing the means of its last two windows against a relative tolerance it is handed. Any run or measurement that reports a quantity over time, an engine's acceptance ratio or an instrument's sample temperature alike.
---

# series_settled

**Gives:** `settled`, `not_settled` or `undecided`, with the two means and their relative change.

**Needs:** `series`, the readings in the order they were taken; `window`, how many readings each mean takes; `tolerance`, the largest relative change between the last two windows that counts as settled. The window and the tolerance are rows: a criterion is the person's, and this skill holds none of its own.

**When it applies:** a quantity read again and again under conditions held fixed. Without a tolerance, without a window, or with fewer than two windows of readings, it says `undecided`.

**What it does not say:** whether the state it settled in is the one wanted; that is for the person, or for another skill on a criterion the person gave.

Run it through the runner; never type its result.
