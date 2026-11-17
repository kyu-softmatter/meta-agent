#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/tool_contracts.py -- what a tool contract may ask for and promise
(plan.md 8, B16; meta_agent/tasks/015).

  python contracts/tools/tool_contracts.py check TOOL_JSON     every problem bundle check B16 would name, for one contract

A tool contract (`tools/<name>/tool.json` of a bundle, schema `tool_contract`) carries a JSON Schema for
the tool's input and one for its output. The schema of the card says only that each is an object, so a
contract can name a field under `required` that it declares nowhere: a caller is then asked for, or
promised, a field whose type nothing states. This file reads that off the contract, and the gate's bundle
check B16 calls it, so that the tool and the gate are one rule.

What B16 asks of a bundle built from the template version after v5 or later: in every tool contract,
at every depth of `inputs` and of `outputs`, each name under `required` is a key of the `properties`
beside it. A bundle of an earlier template is not judged by it, since a build is a record and one of
them carries such a contract (meta_agent/builds/rheo-fixture/0003).

It reads the contract and nothing else. It cannot see what an adapter returns, so a field that is
returned and not declared is not its to find; that is the runner's to refuse, at run time.

Standard library only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import session_skills  # noqa: E402  (template_version: the version a bundle's TEMPLATE.json states)

B16_FROM = 6
SIDES = ("inputs", "outputs")
SUBSCHEMA_KEYS = ("items", "additionalProperties", "contains", "not", "if", "then", "else")
SUBSCHEMA_LIST_KEYS = ("allOf", "anyOf", "oneOf", "prefixItems")
SUBSCHEMA_MAP_KEYS = ("properties", "patternProperties", "$defs", "definitions", "dependentSchemas")


def undeclared(schema, where):
    """(where, name) for each name under a `required` that the `properties` beside it does not declare."""
    out = []
    if not isinstance(schema, dict):
        return out
    props = schema.get("properties")
    props = props if isinstance(props, dict) else {}
    required = schema.get("required")
    if isinstance(required, list):
        for name in required:
            if isinstance(name, str) and name not in props:
                out.append((where, name))
    for key in SUBSCHEMA_MAP_KEYS:
        sub = schema.get(key)
        if isinstance(sub, dict):
            for name in sorted(sub):
                out.extend(undeclared(sub[name], "%s.%s.%s" % (where, key, name)))
    for key in SUBSCHEMA_KEYS:
        out.extend(undeclared(schema.get(key), "%s.%s" % (where, key)))
    for key in SUBSCHEMA_LIST_KEYS:
        sub = schema.get(key)
        if isinstance(sub, list):
            for i, item in enumerate(sub):
                out.extend(undeclared(item, "%s.%s[%d]" % (where, key, i)))
    return out


def problems(contract):
    """B16 over one contract: a message per name that is required and not declared."""
    if not isinstance(contract, dict):
        return ["the contract is not an object"]
    out = []
    for side in SIDES:
        for where, name in undeclared(contract.get(side), side):
            out.append("%s: `%s` is under required and is not declared under properties" % (where, name))
    return out


def tool_names(bundle):
    tdir = os.path.join(bundle, "tools")
    if not os.path.isdir(tdir):
        return []
    return sorted(n for n in os.listdir(tdir) if os.path.isfile(os.path.join(tdir, n, "tool.json")))


def bundle_problems(bundle):
    """B16 over one bundle: (relative path, message) per problem. Empty for a bundle of an earlier template."""
    version = session_skills.template_version(bundle)
    if version is None or version < B16_FROM:
        return []
    out = []
    for name in tool_names(bundle):
        relpath = "tools/%s/tool.json" % name
        try:
            with open(os.path.join(bundle, "tools", name, "tool.json"), encoding="utf-8") as f:
                contract = json.load(f)
        except (OSError, ValueError):
            continue  # a contract that cannot be read is B7's to name
        for msg in problems(contract):
            out.append((relpath, msg))
    return out


def named_rows(schema, at="inputs"):
    """(place, row name) for every property of a contract's input schema, at any depth, that names under
    `row` the parameter row that gives it (B17; tasks/016, run 20261117-3)."""
    out = []
    if isinstance(schema, dict):
        for key, prop in sorted((schema.get("properties") or {}).items()):
            if isinstance(prop, dict):
                here = "%s.%s" % (at, key)
                if isinstance(prop.get("row"), str):
                    out.append((here, prop["row"]))
                for name in prop.get("rows") or []:          # an input that takes a swept parameter, a row per point
                    if isinstance(name, str):
                        out.append((here, name))
                out.extend(named_rows(prop, here))
        if isinstance(schema.get("items"), dict):
            out.extend(named_rows(schema["items"], at + "[]"))
    return out


def row_problems(bundle):
    """B17 over one bundle: every row a tool contract's input names is a row of envelope/parameters.json."""
    try:
        with open(os.path.join(bundle, "envelope", "parameters.json"), encoding="utf-8") as f:
            rows = json.load(f).get("rows") or []
    except (OSError, ValueError, AttributeError):
        rows = []
    have = {r.get("name") for r in rows if isinstance(r, dict)}
    out = []
    for name in tool_names(bundle):
        relpath = "tools/%s/tool.json" % name
        try:
            with open(os.path.join(bundle, "tools", name, "tool.json"), encoding="utf-8") as f:
                contract = json.load(f)
        except (OSError, ValueError):
            continue
        for place, row in named_rows(contract.get("inputs")):
            if row not in have:
                out.append((relpath, "%s names the row %r, which envelope/parameters.json does not hold" % (place, row)))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2 or argv[0] != "check":
        print(__doc__)
        return 2
    try:
        with open(argv[1], encoding="utf-8") as f:
            contract = json.load(f)
    except (OSError, ValueError) as e:
        print("cannot read %s: %s" % (argv[1], e))
        return 2
    found = problems(contract)
    for msg in found:
        print(msg)
    if not found:
        print("nothing to say")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
