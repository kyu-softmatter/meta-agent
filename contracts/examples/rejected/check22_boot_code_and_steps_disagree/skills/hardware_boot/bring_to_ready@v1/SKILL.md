---
name: bring_to_ready
description: The boot sequence of the instrument, from switched on to ready. Take it when read_status does not return ready and the instrument has just been switched on. It changes the device, so it is held until a person releases it.
---

# bring_to_ready

**The sequence:** two steps are a person's hands (the air supply, the transport lock) and are waited for, never assumed; then initialise and home, each verified by a reading; then `read_status@v1`, whose `ready` is the only thing that says the boot succeeded.

**It stops where it is** when a person's step is not confirmed, when a tool refuses or errors, or when a verification fails. It does not retry and it does not skip. What it returns says which step it stopped at and why.

**Reaches the device through:** the `initialise` and `home` tools, each behind the bundle's gate, and the `status` tool by way of `read_status@v1`.

**What it never holds:** a limit. It compares no reading against a number.
