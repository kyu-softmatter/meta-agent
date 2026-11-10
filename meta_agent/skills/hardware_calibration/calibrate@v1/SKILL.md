---
name: calibrate
description: Calibrates one quantity the way the tool profile says the device allows. Take it when a reading rests on a calibration that is absent or expired. It reads the profile's self_calibration claim first and takes one of three ways; one of them changes the device, so the skill is held until a person releases it.
---

# calibrate

**First it reads the claim.** `self_calibration` is the tool profile's list, handed in; the row for `quantity` says `self`, `assisted` or `unknown`. Whether a device calibrates a quantity itself is checked at S2 and never assumed here: no row, or a row resting on an unknown claim, is `unknown`.

**self:** the device's own routine, one gated call to `self_calibrate`. It returns a `calibration:<id>` number with its expiry, as the device gave them. A routine that returns no expiry gives no number: a calibration without one enters nothing.

**assisted:** no tool call. It returns a `calibration_design` draft (the quantity, who does which step, what is read and how it is recorded) with the questions for the person left open in it: which reference, what difference is accepted, how often. The draft is a draft until the person confirms it.

**unknown:** no tool call. It returns a gap naming what would settle it.

**What it never does:** assume `self`, write an acceptance limit, confirm a design, state a grade, or go on after a refusal.
