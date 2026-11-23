"""Template v37 (meta_agent/failures.jsonl dft-16, dft-17, dft-19, dft-20; the design role's ask
20261118-design-macbook-20261117-2-1, tasks/018), each change shown on two unrelated kinds, neither rheology:

- src/engine_wait.py returns, under written, the files a run made or changed under the folders it was told to watch
  (dft-16): an example script of a plane-wave code that writes one output into reference/, over a file the examples
  ship, and another into results_dscf/, leaving results/ as it was; and a flow solver that writes a profile into a
  time folder of postProcessing/. Under v36, engine_wait.run takes no watch.
- the builder refuses, under v37, an adapter that starts its engine through engine_wait and watches no folder (dft-16),
  and an adapter of a tool that runs a process and waits on it with subprocess.run and no budget (dft-17); v36's builder
  takes both.
- the agreement skill is measurement_error@v4 and src/validate_tasks.py hands it the reference as printed, so that the
  error has the printed digits and no float's (dft-20): a total energy printed to eight decimals and a drag coefficient
  printed with a trailing zero. Under v36 the agreement is v3's float difference.
- the common set carries same_measurand@v1 (dft-19): two outputs made under each other's target, and a flow run that
  stopped at its maximum number of steps, are each different, through the bundle's runner of skills.

Watched failing with v36's tree in v37's place. Every bundle call runs in a fresh process. Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import importlib.util
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

V36, V37 = template_mod.SOURCES["v36"], template_mod.SOURCES["v37"]

# two fake engines whose own scripts choose where they write: the examples kind as a plane-wave code's example script
# does (one output over a shipped reference file, one into a folder of its own), the flow kind as a solver writing its
# post-processing into a time folder
ENGINE = r'''
import os, sys
kind, work = sys.argv[1], sys.argv[2]
if kind == "examples":
    os.makedirs(os.path.join(work, "reference"), exist_ok=True)
    with open(os.path.join(work, "reference", "si.scf.out"), "w") as f:
        f.write("!    total energy              =     -15.85521263 Ry\n     convergence has been achieved\n")
    os.makedirs(os.path.join(work, "results_dscf"), exist_ok=True)
    with open(os.path.join(work, "results_dscf", "si.dscf.out"), "w") as f:
        f.write("!    total energy              =     -15.71000000 Ry\n")
else:
    os.makedirs(os.path.join(work, "postProcessing", "0.5"), exist_ok=True)
    with open(os.path.join(work, "postProcessing", "0.5", "profile.dat"), "w") as f:
        f.write("0.0 1.0\n0.5 0.4\n1.0 0.0\n")
print("done", flush=True)
'''

EXPECTED = {"examples": ["reference/si.scf.out", "results_dscf/si.dscf.out"],
            "flow": ["postProcessing/0.5/profile.dat"]}
KINDS = {"examples": "run_example", "flow": "run_flow"}


def prepare(work, kind):
    """The folder as the engine finds it: the examples ship a reference output and an earlier results/ file."""
    os.makedirs(work, exist_ok=True)
    if kind == "examples":
        cards.write_text(os.path.join(work, "reference", "si.scf.out"), "shipped reference\n")
        cards.write_text(os.path.join(work, "results", "old.out"), "an earlier run\n")
    else:
        cards.write_text(os.path.join(work, "system", "controlDict"), "endTime 0.5;\n")


def engine_wait_of(template, tag):
    spec = importlib.util.spec_from_file_location("engine_wait_%s" % tag, os.path.join(template, "src", "engine_wait.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ADAPTER = '''import os
import sys

import engine_wait

ENGINE, KIND = %r, %r


def run(payload):
    work = engine_wait.new_run_folder(KIND)
    r = engine_wait.run([sys.executable, ENGINE, KIND, work], cwd=work, poll_s=0.05%s)
    return {"run_dir": os.path.relpath(work, engine_wait.BUNDLE), "returncode": r["returncode"],
            "written": r.get("written") or []}
'''

BARE = '''import os
import subprocess
import sys

import engine_wait

ENGINE, KIND = %r, %r


def run(payload):
    work = engine_wait.new_run_folder(KIND)
    p = subprocess.run([sys.executable, ENGINE, KIND, work], cwd=work, capture_output=True, text=True)
    return {"run_dir": os.path.relpath(work, engine_wait.BUNDLE), "returncode": p.returncode, "written": []}
'''


def contract(tool, side_effects="none"):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": tool, "description": "runs the fake engine once",
            "inputs": {"type": "object", "required": [], "properties": {}},
            "outputs": {"type": "object", "required": ["run_dir", "returncode"],
                        "properties": {"run_dir": {"type": "string"}, "returncode": {"type": "integer", "unit": "1"},
                                       "written": {"type": "array"}}},
            "errors": ["invalid_input", "unavailable", "execution_failure", "timeout", "cancelled"],
            "side_effects": side_effects, "safety_gate": {"required": False, "place": "no side effects"},
            "idempotent": False, "timeout_s": None}


def compose(tmp, kind, template=V37, adapter=None, side_effects="none", name=None, simulation=False):
    tool = KINDS[kind]
    engine = os.path.join(tmp, "engine.py")
    if not os.path.isfile(engine):
        cards.write_text(engine, ENGINE)
    con = contract(tool, side_effects)
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([con]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    path = os.path.join(tmp, name or "%s-%s" % (kind, os.path.basename(template)))
    source = adapter if adapter is not None else ADAPTER % (engine, kind, ", watch=[work]")
    bundle_mod.compose(template, path, fill, [{"name": tool, "contract": con, "adapter_source": source, "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": []}}, [], [], [], skills=[],
                       simulation=simulation)
    return path


def python(code, cwd):
    p = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, cwd=cwd, timeout=120)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"not_json": p.stdout, "stderr": p.stderr[-2000:]}


def run_skill(bundle, ref, inputs):
    code = ("import json, sys; sys.path.insert(0, %r); import run_skill\n"
            "print(json.dumps(run_skill.run(%r, json.loads(%r))))") % (os.path.join(bundle, "src"), ref, json.dumps(inputs))
    return python(code, bundle)


def agreement_of(bundle, out, stated, printed):
    """src/validate_tasks.py's comparison of an output with a source's stated values, the task carrying them printed."""
    item = {"measure": {"stated": stated, "printed": printed}}
    code = ("import json, sys; sys.path.insert(0, %r); import validate_tasks\n"
            "print(json.dumps(validate_tasks.against_stated(json.loads(%r), json.loads(%r), json.loads(%r))))") % (
        os.path.join(bundle, "src"), json.dumps(out), json.dumps(stated), json.dumps(item))
    return python(code, bundle)


class WhatARunWrote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v37-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.engine = os.path.join(self.tmp, "engine.py")
        cards.write_text(self.engine, ENGINE)

    def test_written_lists_what_the_run_made_or_changed_and_nothing_else(self):
        ew = engine_wait_of(V37, "v37")
        for kind in KINDS:
            work = os.path.join(self.tmp, kind)
            prepare(work, kind)
            r = ew.run([sys.executable, self.engine, kind, work], cwd=work, poll_s=0.05, watch=[work])
            self.assertEqual(r["returncode"], 0, (kind, r))
            self.assertEqual(r["written"], EXPECTED[kind], kind)
            self.assertEqual(r["watched"], [os.path.abspath(work)], kind)

    def test_with_no_folder_watched_written_is_none(self):
        ew = engine_wait_of(V37, "v37b")
        work = os.path.join(self.tmp, "flow")
        prepare(work, "flow")
        r = ew.run([sys.executable, self.engine, "flow", work], cwd=work, poll_s=0.05)
        self.assertIsNone(r["written"])

    def test_v36s_engine_wait_takes_no_watch(self):
        ew = engine_wait_of(V36, "v36")
        for kind in KINDS:
            work = os.path.join(self.tmp, "v36-" + kind)
            prepare(work, kind)
            with self.assertRaises(TypeError):
                ew.run([sys.executable, self.engine, kind, work], cwd=work, poll_s=0.05, watch=[work])


class TheBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v37-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.engine = os.path.join(self.tmp, "engine.py")
        cards.write_text(self.engine, ENGINE)

    def test_v37_refuses_an_adapter_that_watches_no_folder_and_v36_took_it(self):
        for kind in KINDS:
            unwatched = ADAPTER % (self.engine, kind, "")
            with self.assertRaises(ValueError) as cm:
                compose(self.tmp, kind, adapter=unwatched, name="%s-unwatched-v37" % kind)
            self.assertIn("names no folder to watch", str(cm.exception), kind)
            self.assertTrue(os.path.isdir(compose(self.tmp, kind, template=V36, adapter=unwatched,
                                                  name="%s-unwatched-v36" % kind)))

    def test_v37_refuses_a_process_tool_that_waits_with_no_budget_and_v36_took_it(self):
        for kind in KINDS:
            bare = BARE % (self.engine, kind)
            with self.assertRaises(ValueError) as cm:
                compose(self.tmp, kind, adapter=bare, side_effects="runs_process", name="%s-bare-v37" % kind)
            self.assertIn("subprocess.run", str(cm.exception), kind)
            self.assertIn("other than through", str(cm.exception), kind)
            self.assertTrue(os.path.isdir(compose(self.tmp, kind, template=V36, adapter=bare, side_effects="runs_process",
                                                  name="%s-bare-v36" % kind)))

    def test_v37_takes_a_watched_adapter_and_its_call_names_what_the_run_wrote(self):
        for kind in KINDS:
            b = compose(self.tmp, kind, side_effects="runs_process", name="%s-good" % kind)
            code = ("import json, sys; sys.path.insert(0, %r); import run_tool\n"
                    "print(json.dumps(run_tool.run_call(%r, {})))") % (os.path.join(b, "src"), KINDS[kind])
            out = python(code, b)
            self.assertEqual(out.get("returncode"), 0, (kind, out))
            self.assertEqual(out.get("written"), EXPECTED[kind], kind)


class TheAgreementAndTheMeasurand(unittest.TestCase):
    """measurement_error@v4 and same_measurand@v1 in a simulation bundle of v37, against the same bundle of v36."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="ma-template-v37-")
        cls.v37 = compose(cls.tmp, "flow", simulation=True, name="sim-v37")
        cls.v36 = compose(cls.tmp, "flow", template=V36, simulation=True, name="sim-v36",
                          adapter=ADAPTER % (os.path.join(cls.tmp, "engine.py"), "flow", ""))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, True)

    PAIRS = [  # (the output, the stated value, its printed text, the error as written, its places)
        ({"total_energy": -15.85521263}, {"total_energy": -16.03732708}, {"total_energy": "-16.03732708"}, "0.18211445", 8),
        ({"drag_coefficient": 3.2299}, {"drag_coefficient": 3.23}, {"drag_coefficient": "3.2300"}, "-0.0001", 4),
    ]

    def test_v37_carries_the_two_skills_and_names_the_agreement(self):
        card = cards.load_json(os.path.join(self.v37, "TEMPLATE.json"))
        self.assertEqual(card["agreement_skill"], "measurement_error@v4")
        self.assertEqual(card["measurand_skill"], "same_measurand@v1")
        for ref in ("measurement_error@v4", "same_measurand@v1"):
            self.assertTrue(os.path.isfile(os.path.join(self.v37, "skills", ref, "skill.json")), ref)

    def test_the_check_hands_the_reference_as_printed_and_the_error_has_its_digits(self):
        for out, stated, printed, written, places in self.PAIRS:
            r = agreement_of(self.v37, out, stated, printed)
            field = next(iter(stated))
            run = (r.get("agreement_runs") or {}).get(field) or {}
            self.assertEqual(run.get("inputs", {}).get("reference"), printed[field], r)
            self.assertEqual(run.get("outputs", {}).get("error_written"), written, r)
            self.assertEqual(run.get("outputs", {}).get("places"), places, r)

    def test_under_v36_the_agreement_is_a_float_difference(self):
        for out, stated, printed, written, places in self.PAIRS:
            r = agreement_of(self.v36, out, stated, printed)
            run = (r.get("agreement_runs") or {}).get(next(iter(stated))) or {}
            self.assertEqual(run.get("skill"), "measurement_error@v3", r)
            self.assertNotIn("error_written", run.get("outputs") or {}, r)
            self.assertNotEqual(repr(run["outputs"]["error"]), written, r)    # the float's digits, not the printed ones

    def test_same_measurand_tells_a_pair_of_two_kinds_apart_through_the_runner(self):
        pairs = [
            ({"measured_conditions": {"target_fermi_energy": "-0.5"}, "reference_conditions": {"target_fermi_energy": "0.5"},
              "measured_end": "converged", "reference_end": "converged", "accept_ends": ["converged"]}, "different"),
            ({"measured_conditions": {"inlet_velocity": 0.3}, "reference_conditions": {"inlet_velocity": "0.30"},
              "measured_end": "maximum steps reached", "reference_end": "converged", "accept_ends": ["converged"]}, "different"),
            ({"measured_conditions": {"inlet_velocity": 0.3}, "reference_conditions": {"inlet_velocity": "0.30"},
              "measured_end": "converged", "reference_end": "converged", "accept_ends": None}, "undecided"),
        ]
        for inputs, state in pairs:
            r = run_skill(self.v37, "same_measurand@v1", inputs)
            self.assertEqual((r.get("verdict"), (r.get("outputs") or {}).get("state")), ("ran", state), r)
        self.assertFalse(os.path.isdir(os.path.join(self.v36, "skills", "same_measurand@v1")))


class TheVersion(unittest.TestCase):
    def test_v37_is_the_latest_and_changes_two_scripts_a_skill_its_text_and_its_card(self):
        self.assertEqual(template_mod.LATEST, "v37")
        self.assertEqual(sorted(set(cards.tree_files(V37)) ^ set(cards.tree_files(V36))), [])
        both = set(cards.tree_files(V36)) & set(cards.tree_files(V37))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V36, r)) != cards.sha256_file(os.path.join(V37, r)))
        self.assertEqual(changed, [".claude/skills/run-skill/SKILL.md", "CLAUDE.md", "TEMPLATE.json", "src/engine_wait.py",
                                   "src/validate_tasks.py"])
        card = cards.load_json(os.path.join(V37, "TEMPLATE.json"))
        self.assertEqual(card.get("written_files"), "src/engine_wait.py")
        self.assertEqual(card.get("engine_waits"), "src/engine_wait.py")
        self.assertIn("measurement_error@v4", card["common_skills"])
        self.assertIn("same_measurand@v1", card["common_skills"])
        self.assertNotIn("measurement_error@v3", card["common_skills"])


if __name__ == "__main__":
    unittest.main()
