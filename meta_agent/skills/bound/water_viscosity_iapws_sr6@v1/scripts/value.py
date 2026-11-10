"""Viscosity of liquid water at 0.1 MPa: IAPWS SR6-08(2011), Eq. (7) with the coefficients of its Table 5."""

A = (280.68, 511.45, 61.131, 0.45903)     # Table 5, a_i
B = (-1.9, -7.7, -19.6, -40.0)            # Table 5, b_i
T_MIN, T_MAX = 253.15, 383.15             # Section 3.3: not to be extrapolated outside these limits


def value(inputs):
    temperature = inputs["temperature"]
    if not T_MIN <= temperature <= T_MAX:
        raise ValueError("the correlation holds from 253.15 K to 383.15 K and is not extrapolated; asked at %r K" % temperature)
    reduced = temperature / 300.0
    micro_pascal_seconds = sum(a * reduced ** b for a, b in zip(A, B))
    return {"water_viscosity_iapws_sr6": 1e-06 * micro_pascal_seconds}
