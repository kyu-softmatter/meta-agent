"""Template v39 and the builder, after the two bundles built on Windows were tested standing alone (meta_agent/failures.jsonl
office-9; runs mc-windows/20261122-1 and md-windows/20261120-8).

- Under checks_call the builder refuses what a build's checks would get wrong: a check whose call is an install (the
  install ran inside a check in the lattice engine's bundle), an error code that does not begin with its tool's name as
  the runner spells it (RUN_TUTORIAL- and RUN-TUTORIAL- in one bundle), and an expected error that names no code where
  its tool has more than one contract of that category (a replay item named for reading a run that does not exist passed
  on the missing environment, both unavailable).
- tasks/001-start.md names the lines it asks for after the install, where v38 said 'the second line of each of the last
  two', which both sessions found unclear.

Two unrelated kinds, neither rheology, as the v38 test composes them: a plane-wave DFT engine and an optical
spectrometer; and, for the install, an engine's environment made with pixi beside an analysis package made with uv. Each
tool is a mock adapter that starts no engine, reaches no instrument and installs nothing. Watched failing with v38's tree
in v39's place and before compose called the check.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.tests import test_template_v38 as v38

OLD_V, NEW_V = template_mod.SOURCES["v38"], template_mod.SOURCES["v39"]
INSTALLS = {"pixi": {"installer": "pixi", "channel": "conda-forge"}, "uv": {"installer": "uv", "channel": "pypi"}}


def error(tool, category, code):
    return {"artifact": "error_contract", "schema_version": "0.1", "code": code, "category": category,
            "message": "%s: %s" % (tool, category), "retryable": False,
            "remediation": {"action": "see the message", "note": "a mock"}}


def tool(kind, codes=None, installs=None):
    k = v38.KINDS[kind]
    name = k["call"]
    c = v38.contract(k)
    if installs:
        c = dict(c, installs_from=INSTALLS[installs])
    errors = [error(name, cat, code) for cat, code in (codes or [])]
    if errors:
        c = dict(c, errors=sorted({e["category"] for e in errors} | set(c["errors"])))
    return {"name": name, "contract": c, "adapter_source": "def run(payload):\n    return {'done': True}\n", "errors": errors}


def replay(kind, error_expected=None):
    k = v38.KINDS[kind]
    expected = {"error": error_expected} if error_expected else {"output": {"done": True}}
    return [{"id": "rp-001", "name": "the mock answers", "call": {"tool": k["call"], "input": {}},
             "expected": expected, "expected_verdict": "pass"}]


def interface(kind):
    return [{"id": "if-1", "call": {"tool": v38.KINDS[kind]["call"], "input": {}}, "expected_verdict": "pass"}]


def compose(tmp, kind, template, t, items):
    k = v38.KINDS[kind]
    path = os.path.join(tmp, k["agent"], "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    fill = {"agent_name": k["agent"], "template": "agent@test", "rid": "req-%s-001" % k["agent"], "purpose": "p",
            "science_task": k["science_task"], "tools_section": bundle_mod.tools_section([t["contract"]]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    bundle_mod.compose(template, path, fill, [t], {"tool": k["tool"], "held": k["held"], "observed": []},
                       {"safety": {}, "parameters": {"rows": []}}, [], [], items, skills=[], simulation=False,
                       tool_kind=k["tool_kind"])
    return path


class TheChecksCallNoInstall(unittest.TestCase):
    def test_a_check_whose_call_installs_is_refused(self):
        for kind, installer in (("dft", "pixi"), ("spectrometer", "uv")):
            t = tool(kind, installs=installer)
            for label, args in (("interface task", (interface(kind), [], [])), ("scientific task", ([], interface(kind), [])),
                                ("replay item", ([], [], replay(kind)))):
                faults = bundle_mod.checks_call_problems([t], *args, template_path=NEW_V)
                self.assertEqual(len(faults), 1, (kind, label, faults))
                self.assertIn("%s %s: its call is %s, which installs from the network" % (
                    label, args[0][0]["id"] if args[0] else (args[1] or args[2])[0]["id"], t["name"]), faults[0])
                self.assertEqual(bundle_mod.checks_call_problems([t], *args, template_path=OLD_V), [], (kind, label))

    def test_a_check_of_a_tool_that_installs_nothing_stands(self):
        for kind in v38.KINDS:
            self.assertEqual(bundle_mod.checks_call_problems([tool(kind)], interface(kind), [], replay(kind), NEW_V), [])


class TheErrorCodes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v39-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_a_code_spelled_otherwise_than_the_runner_spells_its_tool_is_refused(self):
        for kind in v38.KINDS:
            name = v38.KINDS[kind]["call"]
            wrong = name.upper().replace("_", "-") + "-001"
            t = tool(kind, codes=[("execution_failure", wrong)])
            with self.assertRaises(ValueError) as e:
                compose(os.path.join(self.tmp, "new-" + kind), kind, NEW_V, t, replay(kind))
            self.assertIn("its error code %s does not begin with %s-" % (wrong, name.upper()), str(e.exception))
            compose(os.path.join(self.tmp, "old-" + kind), kind, OLD_V, t, replay(kind))   # v38 built it

    def test_a_code_the_runner_s_way_is_built(self):
        for kind in v38.KINDS:
            name = v38.KINDS[kind]["call"]
            t = tool(kind, codes=[("execution_failure", name.upper() + "-001")])
            path = compose(os.path.join(self.tmp, "ok-" + kind), kind, NEW_V, t, replay(kind))
            self.assertTrue(os.path.isfile(os.path.join(path, "tools", name, "errors", "execution_failure.json")))


class TheExpectedError(unittest.TestCase):
    def test_an_expected_error_with_no_code_where_two_share_its_category_is_refused(self):
        for kind in v38.KINDS:
            p = v38.KINDS[kind]["call"].upper()
            t = tool(kind, codes=[("unavailable", p + "-NO-ENVIRONMENT"), ("unavailable", p + "-NO-RUN")])
            faults = bundle_mod.checks_call_problems([t], [], [], replay(kind, {"category": "unavailable"}), NEW_V)
            self.assertEqual(len(faults), 1, (kind, faults))
            self.assertIn("replay item rp-001: it expects an error of category unavailable and names no code", faults[0])
            self.assertIn("has 2 contracts of that category", faults[0])
            named = replay(kind, {"category": "unavailable", "code": p + "-NO-RUN"})
            self.assertEqual(bundle_mod.checks_call_problems([t], [], [], named, NEW_V), [], kind)
            self.assertEqual(bundle_mod.checks_call_problems([t], [], [], replay(kind, {"category": "unavailable"}),
                                                             OLD_V), [], kind)

    def test_one_contract_of_the_category_needs_no_code(self):
        for kind in v38.KINDS:
            p = v38.KINDS[kind]["call"].upper()
            t = tool(kind, codes=[("unavailable", p + "-NO-ENVIRONMENT"), ("execution_failure", p + "-001")])
            self.assertEqual(bundle_mod.checks_call_problems([t], [], [], replay(kind, {"category": "unavailable"}),
                                                             NEW_V), [], kind)


class TheStartTask(unittest.TestCase):
    def test_it_names_the_lines_it_asks_for_after_the_install(self):
        new = cards.read_text(os.path.join(NEW_V, "tasks", "001-start.md"))
        self.assertNotIn("the second line of each of the last two", new)
        self.assertIn("from the runs of `python src/replay.py` and `python src/validate_tasks.py` made after the install, "
                      "the line replay printed for each item whose call starts the engine and the verdict line of the "
                      "check", new)
        self.assertIn("the second line of each of the last two", cards.read_text(os.path.join(OLD_V, "tasks", "001-start.md")))


class TheVersion(unittest.TestCase):
    def test_v39_is_the_latest_and_changes_its_start_task_and_its_card(self):
        self.assertEqual(template_mod.LATEST, "v39")
        self.assertEqual(sorted(set(cards.tree_files(NEW_V)) ^ set(cards.tree_files(OLD_V))), [])
        both = set(cards.tree_files(OLD_V)) & set(cards.tree_files(NEW_V))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(OLD_V, r)) != cards.sha256_file(os.path.join(NEW_V, r)))
        self.assertEqual(changed, ["TEMPLATE.json", "tasks/001-start.md"])
        card = cards.load_json(os.path.join(NEW_V, "TEMPLATE.json"))
        self.assertEqual(card["version"], "v39")
        self.assertEqual(card["checks_call"], "src/run_tool.py")


if __name__ == "__main__":
    unittest.main()
