#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/units.py -- the unit registry read as numbers (plan.md 6.3; meta_agent/tasks/031, failure dftmd-1).

  python contracts/tools/units.py check                                 every derived unit is what its parts give
  python contracts/tools/units.py derive NAME                           the factor and dimension NAME's parts give
  python contracts/tools/units.py factor FROM TO [--stands-for UNIT]    the factor that takes a value in FROM to TO
  python contracts/tools/units.py convert VALUE FROM TO [--stands-for UNIT]

A value goes from one registered unit to another only through contracts/units.json: the factor is
si_factor(FROM) / si_factor(TO), and only when the two have the same dimension. A unit with no si_factor (an
engine's own unit, engine_length, engine_energy, ...) has no factor until a scale says which registered unit
it stands for; that scale is a setting, confirmed by the person for the bundle that uses it (MP11), and is
passed here as --stands-for. Nothing here guesses a scale or converts between dimensions.

A derived unit (Ry/bohr^2) names its parts under derived_from ({"Ry": 1, "bohr": -2}); its si_factor and dim
are the product of its parts', and `check` recomputes both. The gate (check 25) reads this module; a bundle
converts through a library skill that reads the registry it carries. Standard library only.
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
UNITS = os.path.join(os.path.dirname(HERE), "units.json")
REL_TOL = 1e-12   # the round-off of a double over a product of a few factors; not a scientific threshold


def load(path=UNITS):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["units"]


def _dim_power(dim, p):
    return {k: v * p for k, v in dim.items()}


def _dim_add(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + v
    return {k: v for k, v in out.items() if v}


def same_dim(a, b):
    return {k: v for k, v in (a or {}).items() if v} == {k: v for k, v in (b or {}).items() if v}


def derive(units, name):
    """(si_factor, dim, None) from a unit's derived_from, or (None, None, reason)."""
    u = units.get(name)
    if not isinstance(u, dict):
        return None, None, "%r is not in contracts/units.json" % name
    parts = u.get("derived_from")
    if not isinstance(parts, dict) or not parts:
        return None, None, "%r has no derived_from" % name
    si, dim = 1.0, {}
    for part, p in sorted(parts.items()):
        pu = units.get(part)
        if not isinstance(pu, dict):
            return None, None, "%r: part %r is not registered" % (name, part)
        if pu.get("derived_from"):
            return None, None, "%r: part %r is itself derived; name base parts" % (name, part)
        if not isinstance(p, int) or isinstance(p, bool) or p == 0:
            return None, None, "%r: the power of %r is not a non-zero integer" % (name, part)
        if pu.get("si_factor") is None:
            si = None
        elif si is not None:
            si *= pu["si_factor"] ** p
        dim = _dim_add(dim, _dim_power(pu.get("dim") or {}, p))
    return si, dim, None


def check(units):
    """Problems with derived units: a stated si_factor or dim that is not what the parts give."""
    out = []
    for name in sorted(units):
        u = units[name]
        if not isinstance(u, dict) or "derived_from" not in u:
            continue
        si, dim, why = derive(units, name)
        if why:
            out.append(why)
            continue
        if not same_dim(dim, u.get("dim")):
            out.append("%r: dim %s stated, %s from its parts" % (name, u.get("dim"), dim))
        stated = u.get("si_factor")
        if (si is None) != (stated is None) or (si is not None and not math.isclose(si, stated, rel_tol=REL_TOL)):
            out.append("%r: si_factor %r stated, %r from its parts" % (name, stated, si))
    return out


def factor(units, from_unit, to_unit, stands_for=None):
    """(factor, None), or (None, reason): what a value in from_unit is multiplied by to be in to_unit.

    to_unit may be a unit with no si_factor only with stands_for, a registered unit of its dimension that
    has one; from_unit always needs its own si_factor (a value handed over is never in an engine's unit)."""
    fu, tu = units.get(from_unit), units.get(to_unit)
    if not isinstance(fu, dict):
        return None, "%r is not in contracts/units.json" % from_unit
    if not isinstance(tu, dict):
        return None, "%r is not in contracts/units.json" % to_unit
    if fu.get("si_factor") is None:
        return None, "%r has no si_factor: a value in it means nothing outside its engine" % from_unit
    target = tu
    if tu.get("si_factor") is None:
        if not stands_for:
            return None, "%r has no si_factor; a confirmed scale must say which unit it stands for" % to_unit
        su = units.get(stands_for)
        if not isinstance(su, dict) or su.get("si_factor") is None:
            return None, "the scale's unit %r is not registered with an si_factor" % stands_for
        if not same_dim(su.get("dim"), tu.get("dim")):
            return None, "the scale's unit %r is not of %r's dimension" % (stands_for, to_unit)
        target = su
    elif stands_for:
        return None, "%r has its own si_factor; it takes no scale" % to_unit
    if not same_dim(fu.get("dim"), target.get("dim")):
        return None, "%r and %r are not of one dimension (%s, %s)" % (from_unit, to_unit, fu.get("dim"), tu.get("dim"))
    return fu["si_factor"] / target["si_factor"], None


def factor_matches(stated, computed):
    return isinstance(stated, (int, float)) and not isinstance(stated, bool) and \
        math.isclose(stated, computed, rel_tol=REL_TOL)


def main(argv=None):
    ap = argparse.ArgumentParser(description="the unit registry read as numbers")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    d = sub.add_parser("derive")
    d.add_argument("name")
    for cmd in ("factor", "convert"):
        p = sub.add_parser(cmd)
        if cmd == "convert":
            p.add_argument("value", type=float)
        p.add_argument("from_unit")
        p.add_argument("to_unit")
        p.add_argument("--stands-for", default=None)
    a = ap.parse_args(argv)
    units = load()
    if a.cmd == "check":
        problems = check(units)
        for p in problems:
            print("unit    %s" % p)
        print("units: %d registered, %d derived, %d not what their parts give" % (
            len(units), sum(1 for u in units.values() if isinstance(u, dict) and "derived_from" in u), len(problems)))
        return 1 if problems else 0
    if a.cmd == "derive":
        si, dim, why = derive(units, a.name)
        if why:
            print("refused  %s" % why)
            return 1
        print(json.dumps({"si_factor": si, "dim": dim}))
        return 0
    f, why = factor(units, a.from_unit, a.to_unit, a.stands_for)
    if why:
        print("refused  %s" % why)
        return 1
    print(repr(f) if a.cmd == "factor" else repr(a.value * f))
    return 0


if __name__ == "__main__":
    sys.exit(main())
