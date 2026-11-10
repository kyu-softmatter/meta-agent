"""Viscosity of liquid water: Kestin, Sokolov and Wakeham (1978), Eq. (15) from 0 to 40 degrees Celsius and Eq. (16)
elsewhere between -8 and 150 degrees Celsius, on the viscosity at 20 degrees Celsius the paper adopts."""

MU_20 = 1002.0e-06          # Pa.s: 1002.0 micro Pa.s at 20 degrees Celsius, the standard datum of Sections 1 and 4
ZERO_CELSIUS = 273.15       # K: the definition of the Celsius scale
T_MIN, T_MAX = -8.0, 150.0  # degrees Celsius: the range of Eq. (16)


def _eq15(t):
    d = 20.0 - t
    return d / (t + 96.0) * (1.2364 - 1.37e-3 * d + 5.7e-6 * d ** 2)


def _eq16(t):
    d = 20.0 - t
    return d / (t + 96.0) * (1.2378 - 1.303e-3 * d + 3.06e-6 * d ** 2 + 2.55e-8 * d ** 3)


def value(inputs):
    t = inputs["temperature"] - ZERO_CELSIUS
    if not T_MIN <= t <= T_MAX:
        raise ValueError("the correlation holds from -8 to 150 degrees Celsius; asked at %r degrees Celsius" % t)
    log_ratio = _eq15(t) if 0.0 <= t <= 40.0 else _eq16(t)     # the paper tabulates with Eq. (15) where it holds
    return {"water_viscosity_kestin_1978": MU_20 * 10.0 ** log_ratio}
