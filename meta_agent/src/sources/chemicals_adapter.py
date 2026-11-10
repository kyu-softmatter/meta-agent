"""Water properties from the `chemicals` package (MIT, pure Python; https://github.com/CalebBell/chemicals).

    water(temperature, pressure=101325.0)   ->  {rows, degraded, gaps}
    glycerol_water(temperature, mass_fraction)  ->  {rows, degraded, gaps}   (a gap: see below)

This is the only module that imports `chemicals`. The package is not in this repository and is never
vendored; its pin belongs in tools.lock.json, which is the person's to change, and fetching it is the
person's step. Until then, and wherever the package is absent, every call returns no rows, a `degraded`
line and a gap naming what would settle it, and the Designer goes on with the rows the draft has.

What is called, as the package's documentation states it (read 2026-11-09; the viscosity signature from
the page's summary, the density one verbatim):
    chemicals.iapws.iapws95_rho(T, P)          T in K, P in Pa  ->  kg/m^3   (IAPWS-95)
    chemicals.viscosity.mu_IAPWS(T, rho)       T in K, rho in kg/m^3  ->  Pa*s   (IAPWS 2008)
A row is `database:chemicals@<version>`, value_kind `correlation`, so its grade derives as E4. The
conditions the value holds at go on the row. No uncertainty is stated: the documentation pages read give
none for either function, and one is not made up here.

Glycerol-water: the documentation pages read name no function for the viscosity or the density of the
mixture, so glycerol_water() returns a gap whether the package is present or not.
"""
import importlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
LOCK = os.path.join(REPO, "tools.lock.json")
ATMOSPHERE = 101325.0


def pinned_version(lock_path=LOCK):
    """The version tools.lock.json pins, or None when the file has no chemicals entry."""
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            return (json.load(f).get("chemicals") or {}).get("version")
    except (OSError, ValueError):
        return None


def load():
    """(module, version) when the package can be imported, else (None, None)."""
    try:
        mod = importlib.import_module("chemicals")
    except ImportError:
        return None, None
    return mod, getattr(mod, "__version__", None)


def status(lock_path=LOCK):
    """{present, version, pinned, ok, says}: ok only when the installed version is the pinned one."""
    mod, version = load()
    pin = pinned_version(lock_path)
    if mod is None:
        says = "chemicals is not installed" + ("" if pin else " and tools.lock.json does not pin it")
    elif pin is None:
        says = "chemicals %s is installed and tools.lock.json does not pin it" % version
    elif pin != version:
        says = "chemicals %s is installed and tools.lock.json pins %s" % (version, pin)
    else:
        says = "chemicals %s, as pinned" % version
    return {"present": mod is not None, "version": version, "pinned": pin, "ok": mod is not None and pin == version, "says": says}


def _absent(what, st):
    return {"rows": [], "degraded": ["chemicals_adapter: %s; %s was not looked up" % (st["says"], what)],
            "gaps": [{"what": what, "searched": ["database:chemicals"], "reason": st["says"],
                      "requires": "the person pins chemicals in tools.lock.json and installs it (python bootstrap.py check)"}]}


def water(temperature, pressure=ATMOSPHERE, lock_path=LOCK):
    """Density and viscosity of liquid water at a temperature (K) and a pressure (Pa), as two rows."""
    what = "the density and the viscosity of water at %r K and %r Pa" % (temperature, pressure)
    st = status(lock_path)
    if not st["present"]:
        return _absent(what, st)
    rho_fn = importlib.import_module("chemicals.iapws").iapws95_rho
    mu_fn = importlib.import_module("chemicals.viscosity").mu_IAPWS
    rho = float(rho_fn(temperature, pressure))
    mu = float(mu_fn(temperature, rho))
    source = "database:chemicals@%s" % st["version"]
    conditions = {"temperature": {"value": temperature, "unit": "K"}, "pressure": {"value": pressure, "unit": "Pa"}}
    rows = [
        {"name": "water_density", "value": rho, "unit": "kg/m^3", "source": source, "value_kind": "correlation",
         "uncertainty": None, "conditions": conditions, "note": "chemicals.iapws.iapws95_rho(T, P), the IAPWS-95 formulation"},
        {"name": "water_viscosity", "value": mu, "unit": "Pa.s", "source": source, "value_kind": "correlation",
         "uncertainty": None, "conditions": conditions,
         "note": "chemicals.viscosity.mu_IAPWS(T, rho), the IAPWS 2008 release, at the density above"},
    ]
    degraded = [] if st["ok"] else ["chemicals_adapter: %s; the rows say which version gave them" % st["says"]]
    return {"rows": rows, "degraded": degraded, "gaps": []}


def glycerol_water(temperature, mass_fraction, lock_path=LOCK):
    """A gap: the package's documentation names no glycerol-water mixture function."""
    what = "the viscosity and the density of glycerol-water at %r K and a glycerol mass fraction of %r" % (temperature, mass_fraction)
    return {"rows": [], "degraded": [],
            "gaps": [{"what": what, "searched": ["database:chemicals"],
                      "reason": "the chemicals documentation pages read on 2026-11-09 (viscosity, iapws) name no function for the mixture",
                      "requires": "a mixture correlation from a registered source, written as a skill with its own worked case"}]}


def lookup(request, lock_path=LOCK):
    """One row for a draft's lookup {substance, quantity, temperature, pressure?}: (row or None, degraded, gaps)."""
    substance, quantity = request.get("substance"), request.get("quantity")
    if substance == "water" and quantity in ("density", "viscosity"):
        got = water(request["temperature"], request.get("pressure", ATMOSPHERE), lock_path)
        row = next((r for r in got["rows"] if r["name"] == "water_" + quantity), None)
        return row, got["degraded"], got["gaps"]
    if substance == "glycerol_water":
        got = glycerol_water(request["temperature"], request.get("mass_fraction"), lock_path)
        return None, got["degraded"], got["gaps"]
    return None, [], [{"what": "%s of %s" % (quantity, substance), "searched": ["database:chemicals"],
                       "reason": "this adapter looks up the density and the viscosity of water only",
                       "requires": "another source or another adapter"}]
