#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""contracts/tools/skills.py -- what a skill is and how it is judged (plan.md 14-30, 14-31; tasks/010).

  python contracts/tools/skills.py check SKILL_DIR        every problem check 22 would name, for one skill
  python contracts/tools/skills.py run-cases SKILL_DIR    run the worked cases of one skill, print the results as JSON
  python contracts/tools/skills.py run SKILL_DIR < inputs.json    run a skill with no side effect once

A skill is a folder `<id>@v<version>/` under a folder named `skills/`:

  SKILL.md       what a model reads to choose it (front matter: name, description)
  skill.json     the manifest code reads (contracts/schemas/skill.schema.json)
  scripts/       the source; the manifest's `entry` names one function
  cases.json     worked cases: inputs, for a device skill the recorded replies of the tools, the expected output

The entry function is `f(inputs)` for a skill with no side effect and `f(inputs, tools)` or
`f(inputs, tools, skills)` for one that reaches a device: `tools.call(name, payload)` is the only way to a
device (in a bundle it is the gated runner, here a recorded transcript), and `skills.run("<id>@v<n>", inputs)`
runs another skill of the same library with the same tools. A skill opens nothing, imports nothing that
reaches outside, and, when it reaches a device, compares no input against a number of its own: a limit is
a safety value or an input row, never a literal in a skill.

The source is read before anything of it is run, and it is run in a separate process. Standard library
only. contracts/validate.py reads the same functions (check 22, B11).
"""
import ast
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS_PATH = os.path.join(os.path.dirname(HERE), "skill_kinds.json")
DIR_RE = re.compile(r"^([a-z][a-z0-9_]*)@v([1-9][0-9]*)$")
REF_RE = DIR_RE
FILES = ("SKILL.md", "skill.json", "cases.json")
ALLOWED_IMPORTS = {"math", "statistics", "json", "typing", "dataclasses", "collections", "itertools", "functools",
                   "fractions", "decimal", "re"}
FORBIDDEN_CALLS = {"open", "exec", "eval", "compile", "__import__", "input", "breakpoint", "globals", "locals",
                   "vars", "getattr", "setattr", "delattr"}
FRONT_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)


def load_kinds(path=KINDS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_skill_dirs(tree, skip=()):
    """Every folder holding a skill.json somewhere under a folder named skills/."""
    out = []
    skip = [os.path.abspath(s) for s in skip]
    for root, dirs, files in os.walk(tree):
        dirs[:] = sorted(d for d in dirs if d not in (".git", "__pycache__", "node_modules", ".venv", ".pixi", ".agent"))
        if any(os.path.abspath(root).startswith(s) for s in skip):
            dirs[:] = []
            continue
        if "skill.json" in files and "skills" in os.path.abspath(root).split(os.sep):
            out.append(root)
    return out


def library_root(skill_dir):
    """The nearest folder named skills/ above a skill."""
    d = os.path.abspath(skill_dir)
    while os.path.dirname(d) != d:
        d = os.path.dirname(d)
        if os.path.basename(d) == "skills":
            return d
    return None


def resolve(skill_dir, ref):
    """The folder of `<id>@v<n>` in the same library, or None."""
    root = library_root(skill_dir)
    if root is None:
        return None
    for d in find_skill_dirs(os.path.dirname(root)):
        if os.path.basename(d) == ref and library_root(d) == root:
            return d
    return None


def read_manifest(skill_dir):
    try:
        with open(os.path.join(skill_dir, "skill.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def front_matter(text):
    m = FRONT_RE.match(text)
    out = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith((" ", "\t", "-")):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def front_list(text, key):
    """A list in front matter: `key: [a, b]` or `key:` followed by `- a` lines."""
    m = FRONT_RE.match(text)
    if not m:
        return []
    lines = m.group(1).splitlines()
    for i, line in enumerate(lines):
        if line.startswith(key + ":"):
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("["):
                return [x.strip().strip('"').strip("'") for x in rest.strip("[]").split(",") if x.strip()]
            items = []
            for nxt in lines[i + 1:]:
                if nxt.strip().startswith("- "):
                    items.append(nxt.strip()[2:].strip().strip('"').strip("'"))
                elif nxt.strip():
                    break
            return items
    return []


def layout_problems(skill_dir, manifest, kinds, schema_errors=None):
    out = []
    name = os.path.basename(os.path.abspath(skill_dir))
    m = DIR_RE.match(name)
    if not m:
        out.append("the folder is not <id>@v<version>")
    for f in FILES:
        if not os.path.isfile(os.path.join(skill_dir, f)):
            out.append("no %s" % f)
    if manifest is None:
        return out + ["skill.json is not a JSON object"]
    if schema_errors:
        out.extend("skill.json: %s" % e for e in schema_errors)
        return out
    if m and (manifest.get("id") != m.group(1) or manifest.get("version") != int(m.group(2))):
        out.append("skill.json says %s@v%s and the folder says %s" % (manifest.get("id"), manifest.get("version"), name))
    kind = manifest.get("kind")
    known = kinds.get("kinds", {})
    if kind not in known:
        out.append("kind %r is not in contracts/skill_kinds.json" % (kind,))
    elif manifest.get("side_effect") not in known[kind].get("side_effects", []):
        out.append("a %s skill does not have side_effect %s" % (kind, manifest.get("side_effect")))
    parent = os.path.basename(os.path.dirname(os.path.abspath(skill_dir)))
    if parent in known and parent != kind:
        out.append("the skill is under %s/ and its kind is %s" % (parent, kind))
    md = os.path.join(skill_dir, "SKILL.md")
    if os.path.isfile(md):
        with open(md, "r", encoding="utf-8") as f:
            fm = front_matter(f.read())
        if fm.get("name") != manifest.get("id"):
            out.append("SKILL.md front matter name %r is not the skill's id" % (fm.get("name"),))
        if not fm.get("description"):
            out.append("SKILL.md front matter has no description: it is what a model reads to choose")
    script = os.path.join(skill_dir, *str(manifest.get("entry", {}).get("script", "")).split("/"))
    if not os.path.isfile(script):
        out.append("entry script %s does not exist" % manifest.get("entry", {}).get("script"))
    if manifest.get("side_effect") == "write_device" and manifest.get("status") != "held" and not manifest.get("release"):
        out.append("a write_device skill is held until a person releases it (status: held, or release with the person's words)")
    if manifest.get("release") and manifest.get("status") == "held":
        out.append("a released skill is not held")
    for ref in manifest.get("uses_skills", []):
        if resolve(skill_dir, ref) is None:
            out.append("uses_skills names %s, which is not in this library" % ref)
    return out


def scripts_of(skill_dir):
    sdir = os.path.join(skill_dir, "scripts")
    return sorted(os.path.join(sdir, n) for n in os.listdir(sdir) if n.endswith(".py")) if os.path.isdir(sdir) else []


def source_problems(skill_dir, manifest):
    """Read off the source, without running it."""
    out = []
    siblings = {os.path.basename(p)[:-3] for p in scripts_of(skill_dir)}
    device = manifest.get("side_effect") != "none"
    tools_named = list(manifest.get("calls_tools", []))
    skills_named = list(manifest.get("uses_skills", []))
    entry = manifest.get("entry", {})
    called = []
    found_entry = False
    for path in scripts_of(skill_dir):
        rel = "scripts/" + os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=rel)
        except (SyntaxError, UnicodeDecodeError) as e:
            out.append("%s does not parse: %s" % (rel, e))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] not in ALLOWED_IMPORTS | siblings:
                        out.append("%s imports %s; a skill imports %s and its own siblings" % (rel, a.name, ", ".join(sorted(ALLOWED_IMPORTS))))
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if node.level == 0 and mod not in ALLOWED_IMPORTS | siblings:
                    out.append("%s imports from %s; a skill imports %s and its own siblings" % (rel, node.module, ", ".join(sorted(ALLOWED_IMPORTS))))
            elif isinstance(node, ast.Call):
                fn = node.func
                if isinstance(fn, ast.Name) and fn.id in FORBIDDEN_CALLS:
                    out.append("%s calls %s(); a skill opens nothing and reaches a device through tools.call only" % (rel, fn.id))
                if isinstance(fn, ast.Attribute) and fn.attr in ("call", "run") and node.args \
                        and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    name = node.args[0].value
                    if fn.attr == "call":
                        called.append((node.lineno, node.col_offset, name))
                        if not device:
                            out.append("%s calls the tool %s and the skill declares no side effect" % (rel, name))
                        elif name not in tools_named:
                            out.append("%s calls the tool %s, which calls_tools does not name" % (rel, name))
                    elif name not in skills_named:
                        out.append("%s runs the skill %s, which uses_skills does not name" % (rel, name))
            elif isinstance(node, ast.Attribute) and node.attr.startswith("__"):
                out.append("%s reaches for %s; a skill does not use dunder attributes" % (rel, node.attr))
            elif isinstance(node, ast.Compare) and device:
                for side in [node.left] + list(node.comparators):
                    if isinstance(side, ast.Constant) and isinstance(side.value, (int, float)) \
                            and not isinstance(side.value, bool) and side.value != 0:
                        out.append("%s line %d compares against the number %r; a limit is a safety value or an input, "
                                   "never a literal in a skill that reaches a device" % (rel, node.lineno, side.value))
            elif isinstance(node, ast.FunctionDef) and rel == entry.get("script") and node.name == entry.get("function"):
                found_entry = True
                n = len(node.args.args)
                if not device and n != 1:
                    out.append("%s: %s takes (inputs) in a skill with no side effect" % (rel, node.name))
                if device and n not in (2, 3):
                    out.append("%s: %s takes (inputs, tools) or (inputs, tools, skills) in a skill that reaches a device" % (rel, node.name))
    if not found_entry and os.path.isfile(os.path.join(skill_dir, *str(entry.get("script", "")).split("/"))):
        out.append("%s has no function %s" % (entry.get("script"), entry.get("function")))
    if manifest.get("kind") == "hardware_boot":
        out.extend(boot_problems(skill_dir, manifest, [name for _, _, name in sorted(called)]))
    return out


def boot_problems(skill_dir, manifest, called):
    out = []
    steps = manifest.get("steps", [])
    if [s.get("n") for s in steps] != list(range(1, len(steps) + 1)):
        out.append("steps are numbered from 1 without a gap")
    for s in steps:
        if s.get("actor") == "person" and s.get("tool"):
            out.append("step %s is a person's and names a tool" % s.get("n"))
        if s.get("actor") == "device" and not s.get("tool") and not s.get("verify", {}).get("skill"):
            out.append("step %s is the device's and names no tool" % s.get("n"))
        if s.get("tool") and s["tool"] not in manifest.get("calls_tools", []):
            out.append("step %s uses the tool %s, which calls_tools does not name" % (s.get("n"), s["tool"]))
    last = steps[-1].get("verify", {}) if steps else {}
    target = resolve(skill_dir, last.get("skill", "")) if last.get("skill") else None
    tm = read_manifest(target) if target else None
    if last.get("verdict") != "ready" or not tm or tm.get("kind") != "hardware_state":
        out.append("the last step is verified by a hardware_state skill of this library returning ready")
    elif last.get("skill") not in manifest.get("uses_skills", []):
        out.append("the last step's skill %s is not in uses_skills" % last.get("skill"))
    wanted = [s["tool"] for s in steps if s.get("actor") == "device" and s.get("tool")]
    if [c for c in called if c in wanted] != wanted:
        out.append("the source calls %s and the steps say %s: the code follows the sequence it declares" % (called, wanted))
    return out


# ---- running the worked cases (in a separate process, after the source was read) ----------------------------

class _Tools(object):
    """A recorded transcript standing in for the bundle's gated runner."""

    def __init__(self, transcript):
        self.transcript = list(transcript or [])
        self.calls = []

    def call(self, name, payload=None):
        self.calls.append(name)
        if len(self.calls) > len(self.transcript):
            raise AssertionError("call %d (%s) is beyond the recorded transcript" % (len(self.calls), name))
        entry = self.transcript[len(self.calls) - 1]
        if entry.get("tool") != name:
            raise AssertionError("call %d is %s and the transcript has %s" % (len(self.calls), name, entry.get("tool")))
        if "input" in entry and entry["input"] != (payload or {}):
            raise AssertionError("call %d (%s) was given %r and the transcript has %r" % (len(self.calls), name, payload, entry["input"]))
        return entry.get("output", {"error": entry["error"]} if "error" in entry else {})


class _Skills(object):
    def __init__(self, skill_dir, tools):
        self.skill_dir, self.tools = skill_dir, tools

    def run(self, ref, inputs=None):
        target = resolve(self.skill_dir, ref)
        if target is None:
            raise AssertionError("skill %s is not in this library" % ref)
        return _call(target, inputs or {}, self.tools)


def _load(skill_dir, manifest):
    import importlib.util
    script = os.path.join(skill_dir, *manifest["entry"]["script"].split("/"))
    sdir = os.path.dirname(script)
    for name in [os.path.basename(p)[:-3] for p in scripts_of(skill_dir)]:
        sys.modules.pop(name, None)
    sys.path.insert(0, sdir)
    try:
        spec = importlib.util.spec_from_file_location("skill_" + re.sub(r"\W", "_", os.path.abspath(skill_dir)), script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(sdir)
    return getattr(mod, manifest["entry"]["function"])


def _call(skill_dir, inputs, tools):
    manifest = read_manifest(skill_dir)
    fn = _load(skill_dir, manifest)
    if manifest.get("side_effect") == "none":
        return fn(inputs)
    import inspect
    if len(inspect.signature(fn).parameters) >= 3:
        return fn(inputs, tools, _Skills(skill_dir, tools))
    return fn(inputs, tools)


# The public names: a runner outside this file (meta_agent/src/skills/) replays a transcript and calls an
# entry through these, so that a skill is run one way everywhere.
Transcript = _Tools
call_entry = _call


def _same(expected, actual, rel):
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected is actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(expected - actual) <= rel * max(abs(expected), abs(actual), 1e-300)
    if isinstance(expected, dict) and isinstance(actual, dict):
        return all(k in actual and _same(v, actual[k], rel) for k, v in expected.items())
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(_same(a, b, rel) for a, b in zip(expected, actual))
    return expected == actual


def run_cases_here(skill_dir):
    """Run every case of one skill in this process. [{name, verdict: pass | fail | not_run, why}]"""
    manifest = read_manifest(skill_dir)
    with open(os.path.join(skill_dir, "cases.json"), "r", encoding="utf-8") as f:
        cases = json.load(f)
    results = []
    for case in cases if isinstance(cases, list) else []:
        name = case.get("name", "?")
        if case.get("not_run"):
            results.append({"name": name, "verdict": "not_run", "why": case["not_run"]})
            continue
        tools = _Tools(case.get("transcript"))
        try:
            got = _call(skill_dir, case.get("inputs", {}), tools)
        except Exception as e:  # a case that raises has failed, whatever it raised
            results.append({"name": name, "verdict": "fail", "why": "%s: %s" % (type(e).__name__, e)})
            continue
        rel = case.get("tolerance", {}).get("rel", 1e-9)
        if not _same(case.get("expect"), got, rel):
            results.append({"name": name, "verdict": "fail", "why": "expected %s, got %s" % (json.dumps(case.get("expect")), json.dumps(got, default=str))})
        elif "expect_calls" in case and case["expect_calls"] != tools.calls:
            results.append({"name": name, "verdict": "fail", "why": "tool calls %s, expected %s" % (tools.calls, case["expect_calls"])})
        else:
            results.append({"name": name, "verdict": "pass", "why": ""})
    return results


def case_problems(skill_dir):
    """Run the cases in a separate process and say what failed."""
    try:
        with open(os.path.join(skill_dir, "cases.json"), "r", encoding="utf-8") as f:
            cases = json.load(f)
    except (OSError, ValueError) as e:
        return ["cases.json: %s" % e]
    if not isinstance(cases, list) or not any(isinstance(c, dict) and not c.get("not_run") for c in cases):
        return ["cases.json holds no case that runs: a skill lands with a worked case"]
    p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "run-cases", os.path.abspath(skill_dir)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    try:
        results = json.loads(p.stdout)
    except ValueError:
        return ["the cases could not be run: %s" % (p.stderr.strip() or p.stdout.strip())[:300]]
    return ["case %s: %s" % (r["name"], r["why"]) for r in results if r["verdict"] == "fail"]


def run_once(skill_dir, inputs):
    """Run a skill with no side effect once, in a separate process: (outputs, None) or (None, why)."""
    p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "run", os.path.abspath(skill_dir)],
                       input=json.dumps(inputs), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    try:
        out = json.loads(p.stdout)
    except ValueError:
        return None, (p.stderr.strip() or p.stdout.strip() or "no output")[-300:]
    if isinstance(out, dict) and "__error__" in out:
        return None, out["__error__"]
    return out, None


def find_in_library(root, ref):
    """The folder of `<id>@v<n>` under a skills/ folder, or None."""
    for d in find_skill_dirs(root):
        if os.path.basename(d) == ref:
            return d
    return None


def problems(skill_dir, kinds, schema_errors=None):
    """Everything check 22 says about one skill. The source is run only when reading it found nothing."""
    manifest = read_manifest(skill_dir)
    out = layout_problems(skill_dir, manifest, kinds, schema_errors)
    if manifest is None or schema_errors:
        return out
    src = source_problems(skill_dir, manifest)
    out.extend(src)
    if not src and not any(o.startswith(("no ", "entry script")) for o in out):
        out.extend(case_problems(skill_dir))
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) == 2 and argv[0] == "run":      # one skill with no side effect, inputs as JSON on stdin
        manifest = read_manifest(argv[1]) or {}
        try:
            if manifest.get("side_effect") != "none":
                raise ValueError("only a skill with no side effect is run this way")
            print(json.dumps(_call(argv[1], json.loads(sys.stdin.read() or "{}"), None)))
        except Exception as e:
            print(json.dumps({"__error__": "%s: %s" % (type(e).__name__, e)}))
        return 0
    if len(argv) != 2 or argv[0] not in ("check", "run-cases"):
        print(__doc__)
        return 2
    if argv[0] == "run-cases":
        print(json.dumps(run_cases_here(argv[1])))
        return 0
    found = problems(argv[1], load_kinds())
    for msg in found:
        print(msg)
    if not found:
        print("nothing to say (the manifest's schema is judged by contracts/validate.py)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
