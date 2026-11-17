---
name: scans_for_signal_to_noise
description: How many scans, and how long, an averaged measurement needs to reach a signal-to-noise ratio, from the ratio and the time of one scan. Any instrument whose noise falls as the square root of the scans averaged.
---

# scans_for_signal_to_noise

**Gives:** the number of scans to average, and the time they take.

**Needs:** `single_scan_snr` and `single_scan_time`, read off one scan of the instrument, and `target_snr`, a row the person or the request gives.

**When it applies:** noise that is random and independent from scan to scan, so that averaging n scans raises the ratio by the square root of n; drift or a fixed pattern in the noise is another matter.

**What it does not say:** whether the target ratio is the right one; that is the request's.

Run it through the runner; never type its result.
