"""Density of liquid water at 0.1 MPa: IAPWS SR6-08(2011), Eq. (2) with Eq. (4) and the Eq. (2) rows of its Table 1."""

R = 461.51805            # J/(kg K), below Eq. (3)
T_R = 10.0               # K, below Eq. (3)
P_0 = 100000.0           # Pa: p0 = 0.1 MPa, Section 2.2
T_A, T_B = 593.0, 232.0  # K, below Eq. (4)
A_5 = 1.93763157e-2      # Table 1, i = 5
# Table 1, i = 6..10: (n_i, a_i)
A = ((4, 6.74458446e+3), (5, -2.22521604e+5), (7, 1.00231247e+8), (8, -1.63552118e+9), (9, 8.32299658e+9))
# Table 1, i = 5..10: (m_i, b_i)
B = ((1, 5.78545292e-3), (2, -1.53195665e-2), (3, 3.11337859e-2), (4, -4.23546241e-2), (5, 3.38713507e-2), (6, -1.19946761e-2))
T_MIN, T_MAX = 253.15, 383.15   # Eq. (5): not to be extrapolated outside these limits


def value(inputs):
    temperature = inputs["temperature"]
    if not T_MIN <= temperature <= T_MAX:
        raise ValueError("the correlation holds from 253.15 K to 383.15 K and is not extrapolated; asked at %r K" % temperature)
    alpha = T_R / (T_A - temperature)
    beta = T_R / (temperature - T_B)
    bracket = A_5 + sum(a * alpha ** n for n, a in A) + sum(b * beta ** m for m, b in B)
    specific_volume = R * T_R / P_0 * bracket
    return {"water_density_iapws_sr6": 1.0 / specific_volume}
