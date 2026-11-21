---
name: series_within_window
description: Whether the recent readings of a series lie inside a window, a lowest and a highest value it is handed, by the mean of its last readings. Any run or measurement that must keep a quantity in a band, an engine's acceptance ratio or an instrument's sample temperature alike.
---

# series_within_window

**Gives:** `within`, `below`, `above` or `undecided`, with the mean of the last readings.

**Needs:** `series`, the readings in the order they were taken; `window`, how many of the last readings the mean takes; `low` and `high`, the edges of the band, in the readings' unit. The window and the two edges are rows: a criterion is the person's, and this skill holds none of its own.

**When it applies:** a quantity read again and again that a run or a measurement must keep inside a band. Without either edge, or with fewer readings than the window, it says `undecided`.

**What it does not say:** what to change when the mean is outside the band; that is another skill's, or the person's.

Run it through the runner; never type its result.
