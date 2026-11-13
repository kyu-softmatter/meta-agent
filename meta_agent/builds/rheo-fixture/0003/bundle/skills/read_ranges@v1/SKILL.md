---
name: read_ranges
description: Reads what the instrument itself reports about its modes and the range of each quantity. Take it when a plan needs to know what the device says it can do, before choosing any interval.
---

# read_ranges

**Gives:** the modes the device lists and, per quantity, the lowest and highest value it reports with the unit, each row marked as reported by the device through the `ranges` tool.

**Needs:** `quantities`, the names wanted; an empty list means every quantity the device reports. A wanted quantity the device does not report is returned under `missing`, never filled in.

**Reaches the device through:** the `ranges` tool only, which reads and changes nothing.

**What it never does:** treat a reported range as a limit. What a device says about itself is the device's claim: it is not a safety value, it is not the operable range a scan finds, and nothing here compares a setting with it. A row whose ends are missing or reversed is returned under `inconsistent` and not as a range.
