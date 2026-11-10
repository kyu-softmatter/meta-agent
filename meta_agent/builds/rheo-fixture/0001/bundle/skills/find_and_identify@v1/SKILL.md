---
name: find_and_identify
description: Lists what answers, opens a session to one instrument, reads its identity and closes the session. Take it first, before any other hardware skill, and whenever it is not certain which instrument is on the other end.
---

# find_and_identify

**Gives:** the addresses that answered and, for the one opened, its identity as `observed` claims (manufacturer, model, serial, firmware), each naming the tool it was read through.

**Needs:** `address`, the one to open, or null to open the only instrument that answers. When several answer and none is named it opens nothing and returns the list: choosing is the caller's.

**Reaches the device through:** `list_devices`, `open_session`, `identify` and `close_session`. A session it opened is closed before it returns, whether or not the identity was read.

**What it never does:** write a setting, keep a session open, or decide that an identity is the right one. It compares the identity with nothing.
