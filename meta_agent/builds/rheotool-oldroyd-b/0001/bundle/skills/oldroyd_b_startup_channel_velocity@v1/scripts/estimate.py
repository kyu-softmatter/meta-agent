"""Waters and King's start-up velocity of an Oldroyd-B fluid in a planar channel, as Amoreira and Oliveira (2010) write it,
equations (2.5)-(2.9), and as OpenFOAM-9's WatersKing.C computes it: with h the half-width, eta0 = eta_s + eta_p,
E = lambda eta0/(rho h^2), beta = eta_s/eta0, u_mean = K h^2/(3 eta0), T = t/lambda and Y = y/h,
u = u_mean [ (3/2)(1 - Y^2) + sum_k A_k(T) B_k(Y) ]. The number of terms is the caller's."""
import math


def _a(k_ak, bk, ck, t):
    if bk >= k_ak:
        # exp(-b t) [ ((b - a^2)/c) sinh(c t) + cosh(c t) ], written without forming sinh or cosh of a large argument
        ep, em = math.exp((ck - bk) * t), math.exp(-(ck + bk) * t)
        if ck == 0.0:
            return math.exp(-bk * t) * ((bk - k_ak * k_ak) * t + 1.0)
        return (bk - k_ak * k_ak) / ck * (ep - em) / 2.0 + (ep + em) / 2.0
    return math.exp(-bk * t) * ((bk - k_ak * k_ak) / ck * math.sin(ck * t) + math.cos(ck * t))


def estimate(inputs):
    h, rho = inputs["half_width"], inputs["density"]
    es, ep, lam, kd = inputs["solvent_viscosity"], inputs["polymer_viscosity"], inputs["relaxation_time"], inputs["driving"]
    y, times, n = inputs["position"], inputs["times"], inputs["terms"]
    if not (h > 0 and rho > 0 and es >= 0 and ep > 0 and lam > 0):
        raise ValueError("the half-width, density, polymer viscosity and relaxation time must be positive, the solvent viscosity not negative")
    if not (isinstance(n, int) and n >= 1):
        raise ValueError("terms is a count, one or more")
    if abs(y) > h:
        raise ValueError("the position lies outside the channel")
    if any(t < 0 for t in times):
        raise ValueError("a time before start-up")
    eta0 = es + ep
    e = lam * eta0 / (rho * h * h)
    beta = es / eta0
    um = kd * h * h / (3.0 * eta0)
    yy = y / h
    ks = []
    for k in range(1, n + 1):
        m = 2 * k - 1
        ak = m * math.pi * math.sqrt(e) / 2.0
        bk = (1.0 + beta * ak * ak) / 2.0
        ck = math.sqrt(abs(bk * bk - ak * ak))
        bkk = 48.0 * (-1) ** k / (m ** 3 * math.pi ** 3) * math.cos(m * math.pi * yy / 2.0)
        ks.append((ak, bk, ck, bkk))
    vel = []
    for t in times:
        tt = t / lam
        s = math.fsum(_a(ak, bk, ck, tt) * bkk for ak, bk, ck, bkk in ks)
        vel.append([t, um * (1.5 * (1.0 - yy * yy) + s)])
    return {"velocity": vel, "elasticity_number": e, "solvent_fraction": beta, "steady_mean_velocity": um}
