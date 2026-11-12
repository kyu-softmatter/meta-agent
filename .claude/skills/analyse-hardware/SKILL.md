---
name: analyse-hardware
description: Work out what an instrument can do and what limits it, from its manuals, specifications and control interface, as claims with evidence, and prove the hardware skills on a mock. Use when a request names an instrument, when a manual, a specification sheet or an interface guide for one arrives, and when the discrete configurations or the operable range of a device are needed. The Meta-Agent never reaches the instrument itself.
---

# Analyse the hardware

You build and propose; you never operate. There is no instrument, no engine process and no network path to an instrument computer here. Hardware is a mock.

## Do this

1. **Read what describes the instrument:** manuals, vendor specifications, interface guides, existing scripts, run records. Take them in with `research-materials` first.
2. **Write each capability as a claim** in the `tool_profile` (`contracts/schemas/tool_profile.schema.json`): what it offers, the commands that really run, input and output formats, required parameters with units, valid ranges, hardware constraints, what it can observe, and what is unverified.
3. **Keep the kinds apart.** A vendor's figure is a specification, not a measurement of this instrument. A claim is `observed`, `derived`, `inferred` or `unknown`; an `unknown` says what would resolve it.
4. **List the discrete configurations in full,** each axis with its options and its evidence: objectives, geometries, modes, binning. An axis that is only inferred is listed as inferred.
5. **Say how the device calibrates each quantity:** by itself, with a person's help, or unknown.
6. **Take the hardware skills from the library** and prove them on recorded replies:
   ```
   python -m meta_agent.src.skills list
   python -m meta_agent.src.skills run <id@vN> --inputs <file> --transcript <file>
   ```
   Connection and identity, state, boot, control, calibration, and the ranges the device reports about itself.
7. **The operable range is read by the built agent at its destination,** by read-only queries of what the device reports. It is never found by driving the instrument until it stops.

## What goes to `held`

A skill that changes a device's state is `held` until the person releases it. A capability whose scope, permission, side effect or validation is unresolved stays out of the bundle.

## Never

Open a path to a real device. Run a hardware skill against anything but a mock. Write a safety value, or let a specification or a model's figure stand as a limit. Reach a device from a skill's own code: it goes through the tools the skill names.

Reference: `plan.md 5.1` (tool understanding), `plan.md 14-31`, `plan.md 14-36`.
