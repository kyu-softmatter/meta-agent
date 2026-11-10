"""Run one skill of the library and write what it ran.

    run(ref, inputs, tools=None)  ->  the record (a dict); write_record(path, record) puts it on disk

The order is fixed: the skill is found, its folder and source are read (contracts/tools/skills.py, what
check 22 reads), the inputs are compared with the manifest, and only then is the entry function called.
A skill that reaches a device gets a tool runner it is given and nothing else: `tools.call(name, payload)`
returns the tool's output, or {"error": <error contract>} when the tool or its gate refused. Here the
runner is a recorded transcript; in a bundle it is the gated src/run_tool.py. With no runner a device
skill is refused, and a held skill runs against a recorded transcript only.

The record is not a card and enters no number anywhere by itself; a card cites it by path and hash.
"""
import os

from .. import cards
from . import LIBRARY, catalogue, rules

REFUSAL_MARKS = ("refused_by_safety",)


class Refused(Exception):
    """The runner did not call the skill."""


class Transcript(object):
    """A recorded transcript as the tool runner: the replies a hand wrote from the fixture profile."""
    kind = "transcript"

    def __init__(self, entries):
        self._inner = rules._Tools(entries)

    def call(self, name, payload=None):
        return self._inner.call(name, payload)

    def unused(self):
        return len(self._inner.transcript) - len(self._inner.calls)


class _Recording(object):
    """Stands between the skill and the runner it was given: every call is written down with its verdict."""

    def __init__(self, inner, allowed):
        self.inner, self.allowed, self.log = inner, set(allowed), []

    def call(self, name, payload=None):
        row = {"n": len(self.log) + 1, "tool": name, "input": payload or {}}
        self.log.append(row)
        if name not in self.allowed:
            row["verdict"] = "not_called"
            raise Refused("the skill asked for the tool %s, which its manifest does not name" % name)
        try:
            reply = self.inner.call(name, payload)
        except Exception:
            row["verdict"] = "not_answered"
            raise
        row["reply"] = reply
        err = reply.get("error") if isinstance(reply, dict) else None
        if err is None:
            row["verdict"] = "ok"
        else:
            marks = {err.get("code"), err.get("category")} if isinstance(err, dict) else set()
            row["verdict"] = "refused" if marks & set(REFUSAL_MARKS) else "error"
        return reply


def tools_closure(skill_dir, seen=None):
    """The tools a skill may reach: its own calls_tools and those of the skills it uses."""
    seen = set() if seen is None else seen
    manifest = rules.read_manifest(skill_dir) or {}
    out = set(manifest.get("calls_tools") or [])
    for ref in manifest.get("uses_skills") or []:
        target = rules.resolve(skill_dir, ref)
        if target and target not in seen:
            seen.add(target)
            out |= tools_closure(target, seen)
    return out


def input_problems(manifest, inputs):
    if not isinstance(inputs, dict):
        return ["the inputs are not a JSON object"]
    named = [i["name"] for i in manifest.get("inputs", [])]
    out = ["input %s is not one the manifest names" % k for k in sorted(inputs) if k not in named]
    out += ["input %s is missing" % k for k in named if k not in inputs]
    return out


def output_problems(manifest, outputs):
    if not isinstance(outputs, dict):
        return ["the skill returned %s, not an object" % type(outputs).__name__]
    named = [o["name"] for o in manifest.get("outputs", [])]
    return ["output %s is not one the manifest names" % k for k in sorted(outputs) if k not in named]


def run(ref, inputs, tools=None, library=LIBRARY, now=None):
    """Run `<id>@v<n>` on the inputs. Always returns a record; its verdict is ran, refused or failed."""
    record = {
        "record": "skill_run", "schema_version": "0.1", "ref": ref, "skill": None, "version": None,
        "kind": None, "side_effect": None, "status": None, "skill_path": None, "skill_sha256": None,
        "runner": getattr(tools, "kind", "given") if tools is not None else "none",
        "inputs": inputs, "verdict": "refused", "why": None, "outputs": None, "outputs_absent": [],
        "tool_calls": [], "ran_at": cards.now_iso(now),
    }
    recording = None
    try:
        skill_dir = catalogue.find(ref, library)
        if skill_dir is None:
            raise Refused("no skill %s in %s" % (ref, catalogue.rel_repo(library)))
        manifest = rules.read_manifest(skill_dir)
        faults = rules.layout_problems(skill_dir, manifest, rules.load_kinds())
        if manifest is not None and not faults:
            faults = rules.source_problems(skill_dir, manifest)
        if faults:
            raise Refused("the skill was read and not run: %s" % "; ".join(faults))
        record.update(skill=manifest["id"], version=manifest["version"], kind=manifest["kind"],
                      side_effect=manifest["side_effect"], status=manifest["status"],
                      skill_path=catalogue.rel_repo(skill_dir), skill_sha256=cards.sha256_tree(skill_dir))
        faults = input_problems(manifest, inputs)
        if faults:
            raise Refused("; ".join(faults))
        device = manifest["side_effect"] != "none"
        if device and tools is None:
            raise Refused("%s is %s and no tool runner was given; a skill reaches a device through a runner or not at all"
                          % (ref, manifest["side_effect"]))
        if manifest["status"] == "held" and record["runner"] != "transcript":
            raise Refused("%s is held: until a person releases it, it runs against a recorded transcript only" % ref)
        if device:
            recording = _Recording(tools, tools_closure(skill_dir))
        record["verdict"] = "failed"
        outputs = rules._call(skill_dir, inputs, recording)
        record["outputs"] = outputs
        faults = output_problems(manifest, outputs)
        if faults:
            record["why"] = "; ".join(faults)
        else:
            record["verdict"] = "ran"
            record["outputs_absent"] = [o["name"] for o in manifest.get("outputs", []) if o["name"] not in outputs]
    except Refused as e:
        record["why"] = str(e)
    except Exception as e:   # the skill, or the transcript it ran against, raised: the run failed and says how
        record["why"] = "%s: %s" % (type(e).__name__, e)
    if recording is not None:
        record["tool_calls"] = recording.log
    if isinstance(tools, Transcript) and tools.unused():
        record["transcript_unused"] = tools.unused()
    return record


def write_record(path, record):
    if os.path.exists(path):
        raise FileExistsError("%s exists; a run's record is not written over" % path)
    cards.write_json(path, record)
    return path
