"""The Green-Kubo shear viscosity eta = V/(kB T) x integral of <pxy(0) pxy(t)> dt (Kim et al. 2018, equations (1) and (24)),
by the trapezoidal rule (their section III), and the relaxation modulus G(t) = V C(t)/(kB T) whose integral it is (the memory
of the Maxwell stress, Morozov and Spagnolie 2015, equation (1.51)). The end of the integral is the caller's."""
import math


def analysis(inputs):
    corr = inputs.get("correlation") or []
    v, kt, end = inputs.get("volume"), inputs.get("thermal_energy"), inputs.get("end")
    out = {"modulus": None, "viscosity": None, "samples_integrated": None, "state": "not_computed"}
    if not (isinstance(v, (int, float)) and v > 0 and isinstance(kt, (int, float)) and kt > 0):
        out["why"] = "the volume and kT must be positive"
        return out
    if len(corr) < 2 or any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in corr):
        out["why"] = "correlation is two or more pairs of a lag time and a value"
        return out
    ts = [float(p[0]) for p in corr]
    if ts[0] != 0.0 or any(b <= a for a, b in zip(ts, ts[1:])):
        out["why"] = "the lag times must start at zero and increase"
        return out
    if end not in ts:
        out["why"] = "end %r is not one of the correlation's lag times" % (end,)
        return out
    a = v / kt
    g = [[t, a * float(c)] for t, c in corr]
    j = ts.index(end)
    eta = math.fsum((g[i + 1][0] - g[i][0]) * (g[i][1] + g[i + 1][1]) / 2.0 for i in range(j))
    out.update({"modulus": g, "viscosity": eta, "samples_integrated": j + 1, "state": "computed"})
    return out
