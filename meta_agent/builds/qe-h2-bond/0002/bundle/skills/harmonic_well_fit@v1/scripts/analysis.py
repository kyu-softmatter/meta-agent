"""The harmonic well U(x) = U0 + k (x - x0)^2 / 2 fitted by least squares to energies at positions near a minimum.

The model is the form an MD engine's harmonic bond takes (HOOMD-blue's md.bond.Harmonic: U(r) = k (r - r0)^2 / 2), so
that k and x0 mean on both sides what the engine means by its potential constant and its rest length. The fit is the
linear least-squares fit of a quadratic in the centred position u = x - xbar, U = a + b u + c u^2 (NIST/SEMATECH
e-Handbook 4.4.3.1: the model is linear in its parameters), solved from its normal equations; then k = 2c,
x0 = xbar - b / (2c) and U0 = a - b^2 / (4c). The residual standard deviation is the residual sum over n - p, p = 3,
rooted. Nothing here chooses which points to fit or judges whether the fit is good enough: both are the caller's.
"""
import math


def _solve3(m, v):
    """Gaussian elimination with partial pivoting on a 3x3 system."""
    a = [list(m[i]) + [v[i]] for i in range(3)]
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if a[piv][col] == 0.0:
            return None
        a[col], a[piv] = a[piv], a[col]
        for r in range(3):
            if r != col:
                f = a[r][col] / a[col][col]
                a[r] = [x - f * y for x, y in zip(a[r], a[col])]
    return [a[i][3] / a[i][i] for i in range(3)]


def analysis(inputs):
    pts = list(inputs["points"])
    n = len(pts)
    out = {"points": n, "force_constant": None, "rest_position": None, "well_energy": None,
           "residual_standard_deviation": None, "minimum_inside_span": None, "state": "not_fitted"}
    if any(not isinstance(p, (list, tuple)) or len(p) != 2 for p in pts):
        out["why"] = "each point is a pair: a position and the energy there"
        return out
    xs, ys = [float(p[0]) for p in pts], [float(p[1]) for p in pts]
    if n < 3 or len(set(xs)) < 3:
        out["why"] = "a quadratic needs three distinct positions or more"
        return out
    xbar = math.fsum(xs) / n
    us = [x - xbar for x in xs]
    s = [math.fsum(u ** p for u in us) for p in range(5)]
    t = [math.fsum(y * u ** p for u, y in zip(us, ys)) for p in range(3)]
    sol = _solve3([[s[0], s[1], s[2]], [s[1], s[2], s[3]], [s[2], s[3], s[4]]], t)
    if sol is None:
        out["why"] = "the normal equations are singular"
        return out
    a, b, c = sol
    if not c > 0.0:
        out["state"] = "no_minimum"
        out["why"] = "the fitted curvature is not positive: the points do not lie about a minimum"
        out["force_constant"] = 2.0 * c
        return out
    x0 = xbar - b / (2.0 * c)
    resid = [y - (a + b * u + c * u * u) for u, y in zip(us, ys)]
    out.update({"force_constant": 2.0 * c, "rest_position": x0, "well_energy": a - b * b / (4.0 * c),
                "minimum_inside_span": min(xs) <= x0 <= max(xs), "state": "fitted"})
    if n > 3:
        out["residual_standard_deviation"] = math.sqrt(math.fsum(r * r for r in resid) / (n - 3))
    return out
