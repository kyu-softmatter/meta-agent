"""The scans an averaged measurement needs to reach a signal-to-noise ratio."""
import math


def estimate(inputs):
    one = inputs["single_scan_snr"]
    if one <= 0:
        raise ValueError("single_scan_snr must be above zero")
    n = max(1, math.ceil((inputs["target_snr"] / one) ** 2 - 1e-12))
    return {"scan_count": n, "acquisition_time": n * inputs["single_scan_time"]}
