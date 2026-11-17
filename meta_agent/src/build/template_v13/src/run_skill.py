"""Run one skill of this bundle through its manifest and the gated tool runner.

    python src/run_skill.py <id@vN> [--record FILE] < inputs.json

Reads one JSON object from stdin, one key per input the skill's manifest names. Compares the inputs with
skills/<id@vN>/skill.json, calls the entry function, compares what it returned with the manifest, and
prints what it ran: the skill, its version, the inputs, the outputs, and every tool call with its
verdict. A skill reaches a device only by `tools.call(name, payload)`, and here that is
run_tool.run_call: the gate is asked on every call, and a refusal comes back to the skill as
{"error": <error contract>}. A skill that is held and not released by a person is refused before any of
its code runs.

The exit status is 0 when the skill ran, 3 when the runner refused it, 4 when it ran and failed, and 2
when the bundle has no such skill.
"""
import importlib.util
import inspect
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLE = os.path.dirname(HERE)
SKILLS = os.path.join(BUNDLE, "skills")
sys.path.insert(0, HERE)
import run_tool  # noqa: E402

REF_RE = re.compile(r"^[a-z][a-z0-9_]*@v[1-9][0-9]*$")
EXIT = {"ran": 0, "refused": 3, "failed": 4}


class Refused(Exception):
    """The runner did not call the skill."""


def manifest_of(ref):
    path = os.path.join(SKILLS, ref, "skill.json")
    if not REF_RE.match(ref) or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tools_closure(ref, seen=None):
    """The tools a skill may reach: its own calls_tools and those of the skills it uses."""
    seen = set() if seen is None else seen
    seen.add(ref)
    manifest = manifest_of(ref) or {}
    out = set(manifest.get("calls_tools") or [])
    for other in manifest.get("uses_skills") or []:
        if other not in seen:
            out |= tools_closure(other, seen)
    return out


def held(manifest):
    return manifest.get("status") == "held" and not manifest.get("release")


class Gated(object):
    """Every device call goes through run_tool.run_call, and every call is written down."""

    def __init__(self, allowed):
        self.allowed, self.log = set(allowed), []

    def call(self, name, payload=None):
        row = {"n": len(self.log) + 1, "tool": name, "input": payload or {}}
        self.log.append(row)
        if name not in self.allowed:
            row["verdict"] = "not_called"
            raise Refused("the skill asked for the tool %s, which its manifest does not name" % name)
        out = run_tool.run_call(name, payload or {})
        if isinstance(out, dict) and out.get("artifact") == "error_contract":
            row["verdict"] = "refused" if out.get("category") == "refused_by_safety" else "error"
            row["reply"] = {"error": out}
        else:
            row["verdict"] = "ok"
            row["reply"] = out
        return row["reply"]


class Skills(object):
    """skills.run("<id>@v<n>", inputs): another skill of this bundle, with the same tools."""

    def __init__(self, tools):
        self.tools = tools

    def run(self, ref, inputs=None):
        manifest = manifest_of(ref)
        if manifest is None:
            raise Refused("skill %s is not in this bundle" % ref)
        if held(manifest):
            raise Refused("%s is held until a person releases it" % ref)
        return call(ref, manifest, inputs or {}, self.tools)


def entry_of(ref, manifest):
    script = os.path.join(SKILLS, ref, *manifest["entry"]["script"].split("/"))
    sdir = os.path.dirname(script)
    for name in os.listdir(sdir):
        if name.endswith(".py"):
            sys.modules.pop(name[:-3], None)
    sys.path.insert(0, sdir)
    try:
        spec = importlib.util.spec_from_file_location("skill_" + re.sub(r"\W", "_", ref), script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(sdir)
    return getattr(mod, manifest["entry"]["function"])


def call(ref, manifest, inputs, tools):
    fn = entry_of(ref, manifest)
    if manifest.get("side_effect") == "none":
        return fn(inputs)
    if len(inspect.signature(fn).parameters) >= 3:
        return fn(inputs, tools, Skills(tools))
    return fn(inputs, tools)


def run(ref, inputs):
    """Always a record; its verdict is ran, refused or failed."""
    manifest = manifest_of(ref)
    if manifest is None:
        raise FileNotFoundError("no skill %r in this bundle" % ref)
    record = {"record": "skill_run", "schema_version": "0.1", "ref": ref, "skill": manifest.get("id"),
              "version": manifest.get("version"), "kind": manifest.get("kind"), "side_effect": manifest.get("side_effect"),
              "status": manifest.get("status"), "runner": "src/run_tool.py", "inputs": inputs, "verdict": "refused",
              "why": None, "outputs": None, "outputs_absent": [], "tool_calls": []}
    tools = Gated(tools_closure(ref))
    try:
        if held(manifest):
            raise Refused("%s is held: a person releases it before it runs here" % ref)
        if not isinstance(inputs, dict):
            raise Refused("the inputs are not a JSON object")
        named = [i["name"] for i in manifest.get("inputs", [])]
        faults = ["input %s is not one the manifest names" % k for k in sorted(inputs) if k not in named]
        faults += ["input %s is missing" % k for k in named if k not in inputs]
        if faults:
            raise Refused("; ".join(faults))
        record["verdict"] = "failed"
        outputs = call(ref, manifest, inputs, tools)
        record["outputs"] = outputs
        named = [o["name"] for o in manifest.get("outputs", [])]
        if not isinstance(outputs, dict):
            record["why"] = "the skill returned %s, not an object" % type(outputs).__name__
        elif [k for k in outputs if k not in named]:
            record["why"] = "; ".join("output %s is not one the manifest names" % k for k in sorted(outputs) if k not in named)
        else:
            record["verdict"] = "ran"
            record["outputs_absent"] = [k for k in named if k not in outputs]
    except Refused as e:
        record["why"] = str(e)
    except Exception as e:   # the skill raised: the run failed and says how
        record["why"] = "%s: %s" % (type(e).__name__, e)
    record["tool_calls"] = tools.log
    return record


def main(argv):
    record_path = None
    if "--record" in argv:
        i = argv.index("--record")
        record_path = argv[i + 1] if i + 1 < len(argv) else None
        argv = argv[:i] + argv[i + 2:]
        if record_path is None or os.path.exists(record_path):
            print("--record names a file that does not exist yet; a run's record is not written over", file=sys.stderr)
            return 1
    if len(argv) != 1:
        print(__doc__)
        return 1
    try:
        record = run(argv[0], json.load(sys.stdin))
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    text = json.dumps(record, indent=2, ensure_ascii=False)
    if record_path:
        with open(record_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    print(text)
    return EXIT[record["verdict"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
