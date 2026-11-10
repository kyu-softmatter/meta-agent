---
name: read_status
description: Reads what state the instrument is in through its status tool and returns ready, busy, fault or unknown with the readings. Take it before any step that changes the device and to verify a step that did.
---

# read_status

**Gives:** one verdict and the readings it rests on. `ready` means idle, initialised and homed; `fault` means the device reports a fault; `busy` means it is doing something; anything else, and any error from the tool, is `unknown`. The readings are what the status tool returned, unchanged, as `measured` values with the device's time and run id beside them.

**Needs:** nothing.

**Reaches the device through:** the `status` tool only, which reads and changes nothing.

**What it never does:** decide that a value is too high or too low. It compares no reading against a number; a limit is a safety value, and the gate holds those.
