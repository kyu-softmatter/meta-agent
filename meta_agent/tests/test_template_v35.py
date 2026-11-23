"""Template v35 (meta_agent/failures.jsonl dft-23, dft-24; the design role's ask 20261118-design-macbook-20261117-2-2,
tasks/018), shown on two unrelated kinds, neither rheology: a self-consistent field solver that prints the energy it
converged to, and a heat-diffusion solver that writes a temperature profile. Both are fake engines this test writes, each
started by its adapter through src/engine_wait.py, directly or through a fake launcher that starts it on a count of
processes and tells it the count, as an MPI launcher does.

- each call writes into a new folder of its own, runs/<kind>/<UTC stamp>/ (engine_wait.new_run_folder), so a call made
  again leaves the earlier run's outputs and log as they were (dft-24); engine_wait.run never opens a log that exists;
- a call runs its engine on the count of processes it names, through the launcher the adapter names, and directly with
  none (dft-23); a count that is not a positive integer comes back as invalid_input, and a count asked of a tool whose
  launcher is not there as unavailable, with no engine started;
- the builder refuses, under v35, an adapter that starts an engine through engine_wait and makes no new run folder,
  which v34's builder takes.

Watched failing with v34's tree in v35's place: v34's engine_wait has no new_run_folder, processes_error or launcher, so
the adapters do not run, and v34's builder takes the adapter that writes into a fixed folder.

Every bundle call runs in a fresh process. Run from the repository root:
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

V34, V35 = template_mod.SOURCES["v34"], template_mod.SOURCES["v35"]

# a fake engine of two kinds: it prints how many processes it was started on (the count its launcher gave it, else one)
# and its result; the scf kind prints a converged energy, the heat kind writes a temperature profile into its folder
ENGINE = r'''
import os, sys
kind, work, steps = sys.argv[1], sys.argv[2], int(sys.argv[3])
n = int(os.environ.get("FAKE_LAUNCHER_NP", "1"))
print("processes: %d" % n, flush=True)
if kind == "scf":
    e = -1.0
    for i in range(steps):
        e = e - 0.5 ** (i + 1)
        print("iteration %d energy %.6f" % (i + 1, e), flush=True)
    print("converged energy %.6f" % e, flush=True)
else:
    profile = [0.0] * 5
    profile[0] = 1.0
    for _ in range(steps):
        profile = [profile[0]] + [(profile[i - 1] + profile[i] + profile[i + 1]) / 3.0 for i in range(1, 4)] + [0.0]
    with open(os.path.join(work, "profile.txt"), "w") as f:
        f.write(" ".join("%.6f" % t for t in profile) + "\n")
    print("profile written after %d steps" % steps, flush=True)
'''

# a fake launcher: launcher.py -np <n> <argv...> starts argv with the count in its environment, as mpirun -np does
LAUNCHER = r'''
import os, subprocess, sys
assert sys.argv[1] == "-np", sys.argv
n = int(sys.argv[2])
sys.exit(subprocess.call(sys.argv[3:], env=dict(os.environ, FAKE_LAUNCHER_NP=str(n))))
'''

KINDS = {"scf": "run_scf", "heat": "run_heat"}

ADAPTER = '''import os
import re
import sys

import engine_wait

ENGINE, LAUNCHER_SCRIPT, KIND, TOOL = %r, %r, %r, %r
LAUNCHER = [%s, LAUNCHER_SCRIPT, "-np", "{n}"]


def run(payload):
    n = payload.get("n_processes")
    bad = engine_wait.processes_error(TOOL, n, launcher=LAUNCHER)
    if bad is not None:
        return bad
    work = engine_wait.new_run_folder(KIND)
    out = os.path.join(work, "engine.out")
    r = engine_wait.run([sys.executable, ENGINE, KIND, work, str(payload["steps"])], cwd=work, poll_s=0.05,
                        n_processes=n, launcher=LAUNCHER, stdout_path=out, stderr_path=os.path.join(work, "engine.err"))
    with open(out) as f:
        text = f.read()
    return {"run_dir": os.path.relpath(work, engine_wait.BUNDLE), "processes_printed": int(re.search(r"processes: (\\d+)", text).group(1)),
            "returncode": r["returncode"], "started": r["argv"]}
'''

# the adapter of v34's day: one fixed folder for every call, so a call made again writes over the run before it
FIXED = '''import os
import sys

import engine_wait


def run(payload):
    work = os.path.join(engine_wait.__file__, "..", "..", "runs", "fixed")
    os.makedirs(work, exist_ok=True)
    r = engine_wait.run([sys.executable, "-c", "print(1)"], cwd=work, poll_s=0.05)
    return {"run_dir": "runs/fixed", "processes_printed": 1, "returncode": r["returncode"], "started": r["argv"]}
'''


def contract(tool):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": tool, "description": "runs the fake engine once",
            "inputs": {"type": "object", "required": ["steps"],
                       "properties": {"steps": {"type": "integer", "unit": "count", "minimum": 1},
                                      "n_processes": {"type": ["integer", "null"], "unit": "count", "default": None,
                                                      "description": "how many processes the engine runs on; null starts it directly"}}},
            "outputs": {"type": "object", "required": ["run_dir", "processes_printed", "returncode"],
                        "properties": {"run_dir": {"type": "string"}, "processes_printed": {"type": "integer", "unit": "count"},
                                       "returncode": {"type": "integer", "unit": "1"}, "started": {"type": "array"}}},
            "errors": ["invalid_input", "unavailable", "execution_failure", "timeout", "cancelled"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "no side effects"}, "idempotent": False, "timeout_s": None}


def fixtures(tmp):
    engine, launcher = os.path.join(tmp, "engine.py"), os.path.join(tmp, "launcher.py")
    if not os.path.isfile(engine):
        cards.write_text(engine, ENGINE)
        cards.write_text(launcher, LAUNCHER)
    return engine, launcher


def compose(tmp, kind, template=V35, adapter=None, launcher_program="sys.executable", name=None):
    tool = KINDS[kind]
    engine, launcher = fixtures(tmp)
    con = contract(tool)
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([con]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    path = os.path.join(tmp, name or "%s-%s" % (kind, os.path.basename(template)))
    source = adapter if adapter is not None else ADAPTER % (engine, launcher, kind, tool, launcher_program)
    bundle_mod.compose(template, path, fill, [{"name": tool, "contract": con, "adapter_source": source, "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": []}}, [], [], [], skills=[], simulation=False)
    return path


def call(bundle, kind, given):
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "run_tool.py"), KINDS[kind]], input=json.dumps(given),
                       capture_output=True, text=True, cwd=bundle, timeout=120)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {"not_json": p.stdout, "stderr": p.stderr[-2000:]}


class EachCallKeepsItsRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v35-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_call_made_again_leaves_the_earlier_run_as_it_was(self):
        for kind in KINDS:
            b = compose(self.tmp, kind)
            first = call(b, kind, {"steps": 3})
            self.assertIn("run_dir", first, (kind, first))
            log = os.path.join(b, first["run_dir"], "engine.out")
            before = cards.read_text(log)
            second = call(b, kind, {"steps": 4})
            self.assertIn("run_dir", second, (kind, second))
            self.assertNotEqual(first["run_dir"], second["run_dir"], kind)
            self.assertEqual(os.path.dirname(first["run_dir"]), os.path.join("runs", kind), kind)
            self.assertEqual(cards.read_text(log), before, kind)       # the first run's log, as it was
            self.assertNotEqual(cards.read_text(os.path.join(b, second["run_dir"], "engine.out")), before, kind)
            if kind == "heat":
                self.assertTrue(os.path.isfile(os.path.join(b, first["run_dir"], "profile.txt")))

    def test_the_engine_runs_on_the_count_named_and_directly_with_none(self):
        for kind in KINDS:
            b = compose(self.tmp, kind)
            direct = call(b, kind, {"steps": 2})
            self.assertEqual(direct.get("processes_printed"), 1, (kind, direct))
            self.assertNotIn("-np", direct["started"], kind)
            three = call(b, kind, {"steps": 2, "n_processes": 3})
            self.assertEqual(three.get("processes_printed"), 3, (kind, three))
            self.assertEqual(three["started"][2:4], ["-np", "3"], kind)

    def test_a_count_that_is_not_positive_is_invalid_input_and_starts_nothing(self):
        for kind in KINDS:
            b = compose(self.tmp, kind)
            r = call(b, kind, {"steps": 2, "n_processes": 0})
            self.assertEqual((r.get("artifact"), r.get("category")), ("error_contract", "invalid_input"), (kind, r))
            self.assertFalse(os.path.isdir(os.path.join(b, "runs", kind)), kind)

    def test_a_count_asked_of_a_launcher_that_is_not_there_is_unavailable(self):
        for kind in KINDS:
            b = compose(self.tmp, kind, launcher_program=repr(os.path.join(self.tmp, "no-such-launcher")),
                        name="%s-nolauncher" % kind)
            r = call(b, kind, {"steps": 2, "n_processes": 2})
            self.assertEqual((r.get("artifact"), r.get("category")), ("error_contract", "unavailable"), (kind, r))
            self.assertEqual(call(b, kind, {"steps": 2}).get("processes_printed"), 1, kind)   # directly, it runs

    def test_engine_wait_never_opens_a_log_that_exists(self):
        b = compose(self.tmp, "scf")
        log = os.path.join(self.tmp, "kept.log")
        cards.write_text(log, "an earlier run\n")
        code = ("import sys; sys.path.insert(0, %r); import engine_wait\n"
                "try:\n    engine_wait.run([sys.executable, '-c', 'print(2)'], stdout_path=%r, poll_s=0.05)\n"
                "except FileExistsError:\n    print('refused')\n") % (os.path.join(b, "src"), log)
        p = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, timeout=60)
        self.assertEqual(p.stdout.strip(), "refused", p.stderr)
        self.assertEqual(cards.read_text(log), "an earlier run\n")


class TheBuilderRefusesAFixedFolder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v35-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_v35_refuses_an_engine_adapter_with_no_new_run_folder_and_v34_took_it(self):
        for kind in KINDS:
            with self.assertRaises(ValueError) as cm:
                compose(self.tmp, kind, template=V35, adapter=FIXED, name="%s-fixed-v35" % kind)
            self.assertIn("makes no new folder", str(cm.exception), kind)
            self.assertTrue(os.path.isdir(compose(self.tmp, kind, template=V34, adapter=FIXED, name="%s-fixed-v34" % kind)))

    def test_v35_takes_the_adapters_of_both_kinds(self):
        for kind in KINDS:
            self.assertTrue(os.path.isdir(compose(self.tmp, kind)))


class TheVersion(unittest.TestCase):
    def test_v35_is_the_latest_and_changes_one_script_its_text_and_its_card(self):
        self.assertEqual(template_mod.LATEST, "v35")
        self.assertEqual(sorted(set(cards.tree_files(V35)) ^ set(cards.tree_files(V34))), [])
        both = set(cards.tree_files(V34)) & set(cards.tree_files(V35))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V34, r)) != cards.sha256_file(os.path.join(V35, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/engine_wait.py"])
        self.assertEqual(cards.load_json(os.path.join(V35, "TEMPLATE.json")).get("run_folders"), "src/engine_wait.py")


class UnderV34(unittest.TestCase):
    """The adapters of this test under v34's tree: its engine_wait has none of what they take."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v35-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_v34s_engine_wait_has_no_processes_error_and_the_call_does_not_run(self):
        for kind in KINDS:
            r = call(compose(self.tmp, kind, template=V34), kind, {"steps": 2})
            self.assertIn("processes_error", r.get("stderr", ""), (kind, r))


if __name__ == "__main__":
    unittest.main()
