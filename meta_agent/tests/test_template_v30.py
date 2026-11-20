"""Template v30 (meta_agent/failures.jsonl gmx-21, gmx-22, gmx-24, gmx-26, gmx-27; meta_agent/tasks/017), shown on two
unrelated kinds each, neither rheology nor molecular dynamics:

- src/engine_wait.py, what an adapter that starts an engine waits through: its budget counts running time only, so an
  engine paused from outside (SIGSTOP) longer than the budget runs on to its end, where a wall-clock timeout would kill
  it; a call that gives up (its budget, or no progress file changing) stops the engine with TERM first; a run the call
  gave up on, or that a TERM from outside ended, comes back as timeout or cancelled with retryable true, saying whether a
  call made again resumes from a checkpoint. The kinds are two fake engines a test writes: a time-stepping solver that
  writes its state to a checkpoint and prints that it stopped when it takes a TERM, and an iterative batch that takes
  TERM's default and keeps no checkpoint. Under v29 there is no such module and the adapter does not load.
- the builder refuses, under v30, an adapter that waits on a process with a wall-clock timeout, and one that waits
  through src/engine_wait.py in a tool whose contract does not declare timeout and cancelled.
- src/validate_tasks.py prints each run of the agreement skill whatever the verdict, and takes the agreement of a task
  the person's rule left undecided: the flow coefficient and the spectral peak of the v23 test.
- tasks/001-start.md says what a scientific fail is once the task's call was made.

Every bundle call runs in a fresh process. Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.tests import test_template_v23 as v23
from meta_agent.tests import test_template_v26 as v26

V29, V30 = template_mod.SOURCES["v29"], template_mod.SOURCES["v30"]
AGREEMENT = "measurement_error@v2"
POSIX = os.name == "posix"

# a fake engine of two kinds: it writes its pid, then one line of progress per step to a log; the solver, on TERM, writes
# its state to a checkpoint and says so before it exits with status zero, as an engine that checkpoints on TERM does; the
# batch takes TERM's default action and keeps nothing. With hang_after, it stops making progress after that many steps.
ENGINE = r'''
import os, signal, sys, time
kind, work, steps, hang_after = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
log = os.path.join(work, "progress.log")
step = 0
if kind == "solver":
    def on_term(signum, frame):
        with open(os.path.join(work, "state.cpt"), "w") as f:
            f.write("step %d\n" % step)
        print("caught TERM at step %d, checkpoint written" % step, flush=True)
        sys.exit(0)
    signal.signal(signal.SIGTERM, on_term)
with open(os.path.join(work, "pid"), "w") as f:
    f.write(str(os.getpid()))
for step in range(1, steps + 1):
    while hang_after and step > hang_after:
        time.sleep(0.05)
    time.sleep(0.1)
    with open(log, "a") as f:
        f.write("step %d\n" % step)
    if kind == "batch":
        print("iteration %d" % step, flush=True)
print("done after %d steps" % steps, flush=True)
'''

KINDS = {"solver": "advance_solver", "batch": "iterate_batch"}

ADAPTER = '''import os
import sys

import engine_wait

ENGINE, KIND, TOOL = %r, %r, %r


def run(payload):
    work = payload["work"]
    os.makedirs(work, exist_ok=True)
    log = os.path.join(work, "progress.log")
    r = engine_wait.run([sys.executable, ENGINE, KIND, work, str(payload["steps"]), str(payload["hang_after"])], cwd=work,
                        budget_s=payload["budget_s"], stall_s=payload["stall_s"], progress=[log],
                        stop_markers=["caught TERM"], poll_s=0.05, grace_s=5.0)
    stop = engine_wait.stop_error(TOOL, r, resumes_from=os.path.join(work, "state.cpt") if KIND == "solver" else None)
    if stop is not None:
        return stop
    with open(log) as f:
        done = len(f.read().split())
    return {"steps_done": done // 2, "returncode": r["returncode"], "paused_s": r["paused_s"], "running_s": r["running_s"]}
'''

TIMED = '''import subprocess
import sys


def run(payload):
    p = subprocess.run([sys.executable, "-c", "print(1)"], capture_output=True, text=True, timeout=payload["budget_s"])
    return {"steps_done": 1, "returncode": p.returncode, "paused_s": 0.0, "running_s": 0.0}
'''


def contract(tool, errors=("invalid_input", "timeout", "cancelled", "execution_failure")):
    num = {"type": "number", "unit": "s"}
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": tool, "description": "advances the fake engine",
            "inputs": {"type": "object", "required": ["work", "steps", "hang_after", "budget_s", "stall_s"],
                       "properties": {"work": {"type": "string", "unit": "1"}, "steps": {"type": "integer", "unit": "count"},
                                      "hang_after": {"type": "integer", "unit": "count"}, "budget_s": num,
                                      "stall_s": {"type": ["number", "null"], "unit": "s"}}},
            "outputs": {"type": "object", "properties": {"steps_done": {"type": "integer", "unit": "count"},
                                                         "returncode": {"type": "integer", "unit": "1"},
                                                         "paused_s": num, "running_s": num}},
            "errors": list(errors), "side_effects": "none", "safety_gate": {"required": False, "place": "no side effects"},
            "idempotent": False, "timeout_s": None}


def compose(tmp, kind, template=V30, adapter=None, errors=None):
    tool = KINDS[kind]
    engine = os.path.join(tmp, "engine.py")
    if not os.path.isfile(engine):
        cards.write_text(engine, ENGINE)
    con = contract(tool) if errors is None else contract(tool, errors)
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([con]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    path = os.path.join(tmp, "%s-%s" % (kind, os.path.basename(template)))
    source = adapter if adapter is not None else ADAPTER % (engine, kind, tool)
    bundle_mod.compose(template, path, fill, [{"name": tool, "contract": con, "adapter_source": source, "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": []}}, [], [], [], skills=[], simulation=False)
    return path


def payload(work, steps, budget_s, stall_s=None, hang_after=0):
    return {"work": work, "steps": steps, "hang_after": hang_after, "budget_s": budget_s, "stall_s": stall_s}


class Call:
    """One call of the tool through the bundle's runner, in a fresh process, which the test may pause or stop."""

    def __init__(self, bundle, kind, given):
        self.work = given["work"]
        self.proc = subprocess.Popen([sys.executable, "-I", os.path.join(bundle, "src", "run_tool.py"), KINDS[kind]],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=bundle)
        self.proc.stdin.write(json.dumps(given))
        self.proc.stdin.close()
        self.proc.stdin = None          # written and closed: communicate() only reads

    def engine_pid(self, steps_seen=1, limit=30.0):
        """The engine's pid once it has made steps_seen steps; None where the call ended first (no engine started)."""
        end = time.monotonic() + limit
        while time.monotonic() < end:
            log = os.path.join(self.work, "progress.log")
            pid = os.path.join(self.work, "pid")
            if os.path.isfile(pid) and os.path.isfile(log) and len(cards.read_text(log).split()) // 2 >= steps_seen:
                return int(cards.read_text(pid))
            if self.proc.poll() is not None:
                return None
            time.sleep(0.02)
        return None

    def result(self):
        out, err = self.proc.communicate(timeout=120)
        try:
            return json.loads(out)
        except ValueError:
            return {"not_json": out, "stderr": err[-2000:]}


@unittest.skipUnless(POSIX, "pausing a process group from outside is a POSIX signal")
class AnEngineCall(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v30-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def call(self, kind, template=V30, **given):
        b = compose(self.tmp, kind, template)
        work = os.path.join(self.tmp, "work-%s-%s-%d" % (kind, os.path.basename(template), len(os.listdir(self.tmp))))
        return Call(b, kind, payload(work, **given))

    def test_an_engine_paused_longer_than_its_budget_runs_on_to_its_end(self):
        for kind in KINDS:
            # eight steps of a tenth of a second against a budget of 3 s, paused 4.5 s: a wall-clock limit would kill it
            c = self.call(kind, steps=8, budget_s=3.0, stall_s=1.5)
            pid = c.engine_pid(steps_seen=2)
            self.assertIsNotNone(pid, kind)
            os.killpg(pid, signal.SIGSTOP)
            time.sleep(4.5)
            os.killpg(pid, signal.SIGCONT)
            r = c.result()
            self.assertEqual((r.get("steps_done"), r.get("returncode")), (8, 0), (kind, r))
            self.assertGreater(r["paused_s"], 3.0, (kind, r))
            self.assertLess(r["running_s"], 3.0, (kind, r))

    def test_v29_has_no_engine_wait_and_its_adapter_does_not_load(self):
        for kind in KINDS:
            c = self.call(kind, template=V29, steps=8, budget_s=3.0, stall_s=1.5)
            self.assertIsNone(c.engine_pid(limit=10.0), kind)
            r = c.result()
            self.assertIn("No module named 'engine_wait'", r.get("stderr", ""), (kind, r))

    def test_a_stop_from_outside_is_a_retryable_cancel_and_says_whether_it_resumes(self):
        for kind, resumable in (("solver", True), ("batch", False)):
            c = self.call(kind, steps=200, budget_s=60.0)
            pid = c.engine_pid(steps_seen=2)
            self.assertIsNotNone(pid, kind)
            os.kill(pid, signal.SIGTERM)
            r = c.result()
            self.assertEqual((r.get("artifact"), r.get("category"), r.get("retryable")), ("error_contract", "cancelled", True), (kind, r))
            self.assertEqual(r["code"], KINDS[kind].upper() + "-STOPPED", kind)
            self.assertEqual(r["evidence"]["resumable"], resumable, (kind, r))
            if resumable:
                # the solver caught the TERM, wrote its checkpoint and exited with status zero: its words say it stopped
                self.assertEqual((r["evidence"]["returncode"], r["evidence"]["stop_marker"]), (0, "caught TERM"), kind)
                self.assertIn("state.cpt", r["remediation"]["action"], kind)
            else:
                self.assertEqual(r["evidence"]["signal"], "SIGTERM", kind)
                self.assertIn("starts over", r["message"], kind)

    def test_an_engine_that_makes_no_progress_is_stopped_with_term_first(self):
        for kind, resumable in (("solver", True), ("batch", False)):
            r = self.call(kind, steps=50, hang_after=2, budget_s=60.0, stall_s=0.6).result()
            self.assertEqual((r.get("category"), r.get("retryable")), ("timeout", True), (kind, r))
            ev = r["evidence"]
            self.assertEqual((ev["gave_up"], ev["ended"], ev["resumable"]), ("stalled", "stopped_by_call", resumable), (kind, r))
            self.assertEqual(r["code"], KINDS[kind].upper() + "-GAVE-UP", kind)

    def test_an_engine_that_outruns_its_budget_is_stopped_with_term_first(self):
        for kind, resumable in (("solver", True), ("batch", False)):
            r = self.call(kind, steps=200, budget_s=0.8).result()
            self.assertEqual((r.get("category"), r["evidence"]["gave_up"], r["evidence"]["resumable"]),
                             ("timeout", "budget", resumable), (kind, r))
            self.assertGreaterEqual(r["evidence"]["running_s"], 0.8, kind)

    def test_a_run_that_ends_is_its_output(self):
        for kind in KINDS:
            r = self.call(kind, steps=3, budget_s=30.0, stall_s=5.0).result()
            self.assertEqual((r.get("steps_done"), r.get("returncode")), (3, 0), (kind, r))


class TheBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v30-build-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_an_adapter_with_a_wall_clock_timeout_is_refused_under_v30_and_not_under_v29(self):
        for kind in KINDS:
            with self.assertRaises(ValueError) as cm:
                compose(self.tmp, kind, adapter=TIMED)
            self.assertIn("src/engine_wait.py", str(cm.exception), kind)
            self.assertIn("wall-clock timeout (run)", str(cm.exception), kind)
            self.assertFalse(os.path.exists(os.path.join(self.tmp, "%s-template_v30" % kind)), kind)
            self.assertTrue(os.path.isdir(compose(self.tmp, kind, template=V29, adapter=TIMED)), kind)

    def test_a_contract_that_does_not_declare_the_stop_is_refused(self):
        for kind in KINDS:
            with self.assertRaises(ValueError) as cm:
                compose(self.tmp, kind, errors=("invalid_input", "execution_failure"))
            self.assertIn("declares execution_failure, invalid_input", str(cm.exception), kind)

    def test_an_adapter_that_waits_through_engine_wait_is_built(self):
        for kind in KINDS:
            b = compose(self.tmp, kind)
            self.assertTrue(os.path.isfile(os.path.join(b, "src", "engine_wait.py")), kind)


class TheAgreementIsPrinted(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v30-agree-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def as_built(self, kind):
        tool, inp, limit, c, h, hf = v23.KINDS[kind]
        return limit + c * h * h, limit

    def test_a_task_the_rule_leaves_undecided_takes_and_prints_its_agreement(self):
        for kind in v23.KINDS:
            built, limit = self.as_built(kind)
            for template, taken in ((V29, False), (V30, True)):
                b = v23.compose(self.tmp, "%s-rule-%s" % (kind, os.path.basename(template)),
                                [v26.exact_task(kind, stated=limit, printed=v26.SHORT[kind])], rows={"order": (None, "1")},
                                template=template)
                r = v23.validate(b)
                self.assertEqual(r["verdict"], "undecided", (kind, r))
                self.assertEqual("agreement_runs" in r, taken, (kind, template, r))
                out = printed(b)
                self.assertEqual("agreement by %s, field value" % AGREEMENT in out, taken, (kind, template, out))
            run = r["agreement_runs"]["value"]
            self.assertEqual((run["skill"], run["verdict"]), (AGREEMENT, "ran"), kind)
            self.assertAlmostEqual(run["outputs"]["error"], built - limit, places=12)
            self.assertAlmostEqual(r["agreement"], abs(built - limit), places=12)
            self.assertIn("measured %r, reference %r -> error %r, magnitude %r" % (
                built, limit, run["outputs"]["error"], run["outputs"]["magnitude"]), out, kind)

    def test_every_verdict_prints_the_runs_of_the_agreement_skill(self):
        for kind in v23.KINDS:
            built, limit = self.as_built(kind)
            cases = {"pass": {"value": 1.0, "unit": "1", "chosen_by": "human"},
                     "fail": {"value": 0.0, "unit": "1", "chosen_by": "human"}}
            for verdict, tol in cases.items():
                for template, shown in ((V29, False), (V30, True)):
                    b = v23.compose(self.tmp, "%s-%s-%s" % (kind, verdict, os.path.basename(template)),
                                    [v23.task(kind, stated=limit, tolerance=tol, refinement=False)], template=template)
                    self.assertEqual(v23.validate(b)["verdict"], verdict, kind)
                    out = printed(b)
                    self.assertEqual("agreement by %s, field value: measured %r, reference %r -> error" % (AGREEMENT, built, limit) in out,
                                     shown, (kind, verdict, template, out))


def printed(bundle):
    return subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "validate_tasks.py")],
                          capture_output=True, text=True, cwd=bundle).stdout


class TheTexts(unittest.TestCase):
    def test_the_start_task_says_what_a_real_scientific_fail_is(self):
        said = "A scientific task that prints `fail` is a real verdict once its call was made"
        self.assertIn(said, cards.read_text(os.path.join(V30, "tasks", "001-start.md")))
        self.assertNotIn(said, cards.read_text(os.path.join(V29, "tasks", "001-start.md")))

    def test_claude_md_says_how_a_stopped_engine_call_comes_back_and_that_every_agreement_is_printed(self):
        text = cards.read_text(os.path.join(V30, "CLAUDE.md"))
        for said in ("waits through `src/engine_wait.py`", "`timeout` (the call gave up) or `cancelled` (a stop from outside)",
                     "whatever the verdict, `undecided` included"):
            self.assertIn(said, text)
            self.assertNotIn(said, cards.read_text(os.path.join(V29, "CLAUDE.md")))


class TheVersion(unittest.TestCase):
    def test_v30_is_the_latest_adds_one_script_and_changes_one_script_its_card_and_two_texts(self):
        self.assertIn("v30", template_mod.SOURCES)                  # v31 is the latest since the skills name their unit
        both = set(cards.tree_files(V29)) & set(cards.tree_files(V30))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V29, r)) != cards.sha256_file(os.path.join(V30, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/validate_tasks.py", "tasks/001-start.md"])
        self.assertEqual(sorted(set(cards.tree_files(V30)) - set(cards.tree_files(V29))), ["src/engine_wait.py"])
        self.assertEqual(sorted(set(cards.tree_files(V29)) - set(cards.tree_files(V30))), [])
        m = cards.load_json(os.path.join(V30, "TEMPLATE.json"))
        self.assertEqual((m["version"], m["engine_wait"]), ("v30", "src/engine_wait.py"))


if __name__ == "__main__":
    unittest.main()
