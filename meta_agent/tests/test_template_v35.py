"""Template v35 and the builder (tasks/033): any agent of v35 may be a member of a hub agent.

- The build writes envelope/results.json for every bundle, one report for each output field of its tools that is a number
  in a unit, with the grade derived from contracts/grades.json (an engine's value computed, an instrument's measured),
  and makes outbox/, inbox/ and received/.
- src/handover.py receive passes over an envelope that carried an assignment, where v34 refused it as not a hand-over
  and stopped every receive after it; `assignments` lists it; `result` answers it with one result card in outbox/,
  quoting a declared tool field or holding what it cannot answer, and refuses a field not declared, a changed
  assignment and a second result to one envelope.

Two unrelated kinds: an engine whose mock reports a temperature, and an instrument whose mock reports a viscosity.
Each tool is a mock adapter that returns its output and starts no engine.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V34, V35 = template_mod.SOURCES["v34"], template_mod.SOURCES["v35"]
BRIDGE = os.path.join(REPO, "contracts", "tools", "bridge.py")
VALIDATE = os.path.join(REPO, "contracts", "validate.py")

KINDS = {
    "engine": {"tool": "run_mock", "field": "kinetic_temperature", "unit": "K", "value": 301.5, "grade": "E4",
               "source_kind": "computed", "description": "the kinetic temperature the engine reports at the end"},
    "instrument": {"tool": "measure_mock", "field": "viscosity", "unit": "Pa.s", "value": 0.00098, "grade": "E1",
                   "source_kind": "measured", "description": "the dynamic viscosity the plateau gives"},
}


def contract(k):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["tool"], "description": "a mock that returns its output",
            "inputs": {"type": "object", "properties": {}, "required": []},
            "outputs": {"type": "object", "properties": {
                k["field"]: {"type": "number", "unit": k["unit"], "description": k["description"]},
                "label": {"type": "string"}}, "required": [k["field"]]},
            "errors": ["invalid_input"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "a mock touches nothing"}, "idempotent": True, "timeout_s": None}


def compose(root, name, kind, template=V35, build_id="0001"):
    k = KINDS[kind]
    path = os.path.join(root, name, build_id, "bundle")
    os.makedirs(os.path.dirname(path))
    fill = {"agent_name": name, "template": "agent@test", "rid": "req-%s" % name, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([contract(k)]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    answers = {"id": "if-1", "name": "the mock answers", "call": {"tool": k["tool"], "input": {}},
               "expected": {"output": {k["field"]: k["value"]}}, "expected_verdict": "pass"}
    sci = {"id": "sci-1", "name": "held", "call": {"tool": k["tool"], "input": {}}, "measure": {},
           "reference": {"kind": "source", "ref": "none yet"}, "held": {"reason": "no tolerance", "needs": "one"},
           "tolerance": None, "expected_verdict": "not_run"}
    adapter = "def run(payload):\n    return %r\n" % ({k["field"]: k["value"], "label": "mock"},)
    bundle_mod.compose(template, path, fill, [{"name": k["tool"], "contract": contract(k), "adapter_source": adapter, "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": []}}, [answers], [sci],
                       [dict(answers, id="rp-001")], simulation=False, tool_kind=kind)
    return path


def card(card_name, ident, author, **fields):
    c = {"card": card_name, "schema_version": "0.1", "id": ident, "revision": 1, "author": author,
         "created_at": "2026-11-20T12:00:00Z", "numbers": [], "assumptions": [], "degraded": [], "status": "draft"}
    c.update(fields)
    return c


def hub_beside(tmp, member_name, member_build):
    """A hub folder with members.json, an agreed question and one assignment to the member; the member's folder is
    ../<agent>-<NNNN> beside it."""
    hub = os.path.join(tmp, "test-hub")
    for d in ("question", "assignments", "inbox"):
        os.makedirs(os.path.join(hub, d))
    other = {"agent": "other-agent", "build": "other-agent/0001", "folder": "../other-agent-0001",
             "build_card_sha256": "sha256:" + "0" * 64}
    cards.write_json(os.path.join(hub, "members.json"), card(
        "hub_members", "members-test-hub", "builder", hub={"agent": "test-hub", "build": "test-hub/0001"},
        members=[{"agent": member_name, "build": member_build, "folder": "../%s" % member_build.replace("/", "-"),
                  "build_card_sha256": "sha256:" + "0" * 64}, other]))
    cards.write_json(os.path.join(hub, "question", "q-test-hub-001.json"), card(
        "hub_question", "q-test-hub-001", "test-hub", question="a test question", done_when=[{"id": "dw-1", "what": "x"}],
        assignments=["as-001-%s-r1" % member_name], agreed={"words": "a test's words", "at": "2026-11-20T12:00:00Z"}))
    cards.write_json(os.path.join(hub, "assignments", "as-001-%s-r1.json" % member_name), card(
        "assignment", "as-001-%s-r1" % member_name, "test-hub", thread="thr-test-hub-%s" % member_name, round=1,
        question="q-test-hub-001", **{"from": {"agent": "test-hub", "build": "test-hub/0001"}},
        to={"agent": member_name, "build": member_build}, asks="report the value your tool gives",
        answers_items=["dw-1"], returns=[{"card": "result", "to": {"agent": "test-hub", "build": "test-hub/0001"}}],
        done_when="the value, or what holds it"))
    return hub


def run(cwd, *args, stdin=None):
    p = subprocess.run([sys.executable] + list(args), cwd=cwd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")


class AnyAgentOfV35MayBeAMember(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v35-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_build_declares_what_it_may_report_with_a_derived_grade(self):
        for kind, k in KINDS.items():
            path = compose(os.path.join(self.tmp, "builds"), "agent-" + kind, kind)
            d = cards.load_json(os.path.join(path, "envelope", "results.json"))
            self.assertEqual(d["agent"], {"agent": "agent-" + kind, "build": "agent-%s/0001" % kind}, kind)
            self.assertEqual([(r["tool"], r["field"], r["unit"], r["grade"], r["source_kind"]) for r in d["reports"]],
                             [(k["tool"], k["field"], k["unit"], k["grade"], k["source_kind"])], kind)
            for sub in ("outbox", "inbox", "received"):
                self.assertTrue(os.path.isdir(os.path.join(path, sub)), (kind, sub))
            deny = cards.load_json(os.path.join(path, ".claude", "settings.json"))["permissions"]["deny"]
            self.assertIn("Write(envelope/results.json)", deny)

    def test_an_assignment_is_received_listed_and_answered_and_the_folder_passes_checks_1_2_25(self):
        for kind, k in KINDS.items():
            tmp = os.path.join(self.tmp, kind)
            built = compose(os.path.join(tmp, "builds"), "agent-" + kind, kind)
            hub = hub_beside(tmp, "agent-" + kind, "agent-%s/0001" % kind)
            member = os.path.join(tmp, "agent-%s-0001" % kind)
            shutil.copytree(built, member)
            code, out = run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card",
                            os.path.join(hub, "assignments", "as-001-agent-%s-r1.json" % kind), "--to", member,
                            "--released-by", "hub", "--ran-by", "hub", "--session", "test-session")
            self.assertEqual(code, 0, out)
            code, out = run(member, "src/handover.py", "receive")
            self.assertEqual(code, 0, out)           # v34 refused here: the payload is not a hand-over
            code, out = run(member, "src/handover.py", "assignments")
            listed = json.loads(out)["assignments"]
            self.assertEqual([a["id"] for a in listed], ["as-001-agent-%s-r1" % kind], out)
            env = listed[0]["envelope"]
            code, out = run(member, "src/run_tool.py", k["tool"], stdin=b"{}")
            os.makedirs(os.path.join(member, "runs"))
            with open(os.path.join(member, "runs", "call.json"), "w") as f:
                f.write(out)
            code, out = run(member, "src/handover.py", "result", "--assignment", env, "--report", k["tool"], "label",
                            "runs/call.json")
            self.assertEqual(code, 3, out)            # a field not declared
            code, out = run(member, "src/handover.py", "result", "--assignment", env, "--report", k["tool"], k["field"],
                            "runs/call.json")
            self.assertEqual(code, 0, out)
            res = json.loads(out)["card"]
            self.assertEqual(res["state"], "answered")
            self.assertEqual([(n["value"], n["unit"], n["grade"], n["value_kind"]) for n in res["numbers"]],
                             [(k["value"], k["unit"], k["grade"], k["source_kind"])])
            self.assertEqual(res["answers"], {"assignment": "as-001-agent-%s-r1" % kind, "envelope": env})
            code, out = run(member, "src/handover.py", "result", "--assignment", env, "--held", "a", "b", "c")
            self.assertEqual(code, 3, out)            # one envelope, one result
            code, out = run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card",
                            os.path.join(member, "outbox", "result-thr-test-hub-agent-%s-r1.json" % kind), "--to", hub,
                            "--released-by", "hub", "--ran-by", "hub", "--session", "test-session")
            self.assertEqual(code, 0, out)
            shutil.rmtree(os.path.join(tmp, "builds"))
            code, out = run(REPO, VALIDATE, tmp, "--checks", "1,2,25")
            self.assertEqual(code, 0, out)
            self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])

    def test_a_held_result_and_a_changed_assignment(self):
        kind = "engine"
        tmp = os.path.join(self.tmp, "held")
        built = compose(os.path.join(tmp, "builds"), "agent-" + kind, kind)
        hub = hub_beside(tmp, "agent-" + kind, "agent-%s/0001" % kind)
        member = os.path.join(tmp, "agent-%s-0001" % kind)
        shutil.copytree(built, member)
        run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card", os.path.join(hub, "assignments", "as-001-agent-engine-r1.json"),
            "--to", member, "--released-by", "hub", "--ran-by", "hub", "--session", "s")
        env = "inbox/thr-test-hub-agent-engine/r1_envelope.json"
        code, out = run(member, "src/handover.py", "result", "--assignment", env)
        self.assertEqual(code, 3, out)                # neither a value nor a hold
        code, out = run(member, "src/handover.py", "result", "--assignment", env, "--held", "the value",
                        "an input has not arrived", "the person's value for it")
        self.assertEqual(code, 4, out)
        self.assertEqual(json.loads(out)["card"]["state"], "held")
        # a second envelope whose payload was changed after the hub wrote it is not answered
        run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card", os.path.join(hub, "assignments", "as-001-agent-engine-r1.json"),
            "--to", member, "--released-by", "hub", "--ran-by", "hub", "--session", "s")
        p = os.path.join(member, "inbox", "thr-test-hub-agent-engine", "r2_as-001-agent-engine-r1.json")
        with open(p, "a") as f:
            f.write(" ")
        code, out = run(member, "src/handover.py", "result", "--assignment",
                        "inbox/thr-test-hub-agent-engine/r2_envelope.json", "--held", "a", "b", "c")
        self.assertEqual(code, 3, out)
        self.assertIn("not the bytes", out)

    def test_v34_refused_the_assignment_and_stopped(self):
        """Watched failing first: the same receive on v34's tree refuses the assignment."""
        tmp = os.path.join(self.tmp, "v34")
        built = compose(os.path.join(tmp, "builds"), "agent-engine", "engine", template=V34)
        hub = hub_beside(tmp, "agent-engine", "agent-engine/0001")
        member = os.path.join(tmp, "agent-engine-0001")
        shutil.copytree(built, member)
        os.makedirs(os.path.join(member, "inbox"), exist_ok=True)
        run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card", os.path.join(hub, "assignments", "as-001-agent-engine-r1.json"),
            "--to", member, "--released-by", "hub", "--ran-by", "hub", "--session", "s")
        cards.write_json(os.path.join(member, "envelope", "handovers.json"),
                         {"agent": {"agent": "agent-engine", "build": "agent-engine/0001"}, "gives": [], "takes": [],
                          "engine_scales": []})
        cards.write_json(os.path.join(member, "envelope", "units.json"), {"units": {}})
        code, out = run(member, "src/handover.py", "receive")
        self.assertEqual(code, 3, out)
        self.assertIn("is not the hand-over", out)


class TheVersion(unittest.TestCase):
    def test_v35_is_the_latest_and_changes_one_script_its_text_its_settings_and_its_card(self):
        self.assertIn("v35", template_mod.SOURCES)                  # v36 is the latest since a hand-over may be read off a chain of steps
        self.assertEqual(sorted(set(cards.tree_files(V35)) ^ set(cards.tree_files(V34))), [])
        both = set(cards.tree_files(V34)) & set(cards.tree_files(V35))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V34, r)) != cards.sha256_file(os.path.join(V35, r)))
        self.assertEqual(changed, [".claude/settings.json", "CLAUDE.md", "README.md", "TEMPLATE.json", "src/handover.py"])


if __name__ == "__main__":
    unittest.main()
