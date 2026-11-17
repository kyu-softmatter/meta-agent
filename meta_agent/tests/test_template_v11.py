"""Template v11 (tasks/016, test run 20261117-2): what round five's bundle on an engine showed standing alone.

The runner of tools looks for the installer an install's contract names before the install the gate opens, and
returns an unavailable error that names it, and says whose step it is, when it is not there. The build fills a
Workflow section with the order the request gave, or says that it gave none, and marks every task, replay item and
TEMPLATE.json that names a record of the builder's repository the bundle does not carry, quoting the person's words
the builder had for it. The start task says that the agent's own install follows a scientific not_run.

Each mechanism runs on two unrelated kinds: an engine's environment made with pixi beside an analysis package made with
uv; a simulation chain beside a spectrometer's chain; a scientific task and a replay item. Nothing reaches the network:
an installer is a stand-in that is on PATH or is not, and the install's adapter only reports the cache it would use.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.intake import card as card_mod
from meta_agent.tests.test_template_v8 import permission

IO = {"inputs": {"type": "object", "properties": {"message": {"type": "string", "minLength": 1}}, "required": ["message"]},
      "outputs": {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]}}
SEES_CACHE = ("import os\n"
              "def run(payload):\n"
              "    return {'message': os.environ.get('PIXI_CACHE_DIR', '') + '|' + os.environ.get('UV_CACHE_DIR', '')}\n")
INSTALLERS = {"engine_env": {"installer": "pixi", "channel": "conda-forge"},     # an engine's environment
              "analysis_env": {"installer": "uv", "channel": "pypi"}}            # an analysis package, unrelated


def install_bundle():
    tmp = tempfile.mkdtemp(prefix="ma-template-v11-")
    bundle = os.path.join(tmp, "bundle")
    shutil.copytree(template_mod.SOURCES["v11"], bundle, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name, src in INSTALLERS.items():
        c = dict({"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": name,
                  "errors": ["invalid_input", "unavailable", "refused_by_safety"], "side_effects": "network",
                  "safety_gate": {"required": True, "place": "src/gate.py", "opens_by": "execution_permission"},
                  "idempotent": True, "timeout_s": None, "installs_from": dict(src)}, **IO)
        cards.write_json(os.path.join(bundle, "tools", name, "tool.json"), c)
        cards.write_text(os.path.join(bundle, "tools", name, "adapter.py"), SEES_CACHE)
    p = permission("engine")
    p["package_sources"] = [dict(s) for s in INSTALLERS.values()]
    cards.write_json(os.path.join(bundle, "envelope", "execution_permission.json"), p)
    return tmp, bundle


def call_with_path(bundle, tool, path_dir):
    env = {k: v for k, v in os.environ.items() if k not in ("PATH",) and not k.endswith("CACHE_DIR")}
    env["PATH"] = path_dir
    p = subprocess.run([sys.executable, "-I", os.path.join(bundle, "src", "run_tool.py"), tool], input=json.dumps({"message": "go"}),
                       capture_output=True, text=True, cwd=bundle, env=env)
    assert p.returncode == 0, p.stdout + p.stderr
    return json.loads(p.stdout)


class TheInstaller(unittest.TestCase):
    def setUp(self):
        self.tmp, self.bundle = install_bundle()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.empty = os.path.join(self.tmp, "empty-bin")
        self.full = os.path.join(self.tmp, "full-bin")
        os.makedirs(self.empty)
        os.makedirs(self.full)
        for src in INSTALLERS.values():
            exe = os.path.join(self.full, src["installer"])
            cards.write_text(exe, "#!/bin/sh\nexit 0\n")
            os.chmod(exe, os.stat(exe).st_mode | stat.S_IEXEC)

    def test_an_installer_not_on_the_computer_is_named_and_is_the_person_s_step(self):
        for name, src in INSTALLERS.items():
            out = call_with_path(self.bundle, name, self.empty)
            self.assertEqual((out.get("artifact"), out.get("category")), ("error_contract", "unavailable"), (name, out))
            self.assertEqual(out["code"], "%s-INSTALLER-MISSING" % name.upper())
            self.assertIn("the installer %s" % src["installer"], out["message"])
            self.assertIn("never installs the installer", out["message"])
            self.assertIn("a person puts %s on this computer" % src["installer"], out["remediation"]["action"])
            self.assertIn("the person's step", out["remediation"]["note"])
            self.assertTrue(out["retryable"])
            self.assertEqual(out["evidence"], {"installer": src["installer"], "looked_on": "PATH"})
        self.assertFalse(os.path.exists(os.path.join(self.bundle, "runs")))     # nothing was made before the refusal

    def test_an_installer_on_the_computer_lets_the_install_run_as_before(self):
        for name in INSTALLERS:
            out = call_with_path(self.bundle, name, self.full)
            pixi, uv = out["message"].split("|")
            self.assertEqual(os.path.realpath(pixi), os.path.realpath(os.path.join(self.bundle, "runs", "cache", "pixi_cache_dir")), name)
            self.assertEqual(os.path.realpath(uv), os.path.realpath(os.path.join(self.bundle, "runs", "cache", "uv_cache_dir")), name)

    def test_the_tools_section_names_the_installer_and_whose_step_it_is(self):
        for name, src in INSTALLERS.items():
            tc = cards.load_json(os.path.join(self.bundle, "tools", name, "tool.json"))
            self.assertIn("the installer `%s` must already be on the computer, and putting it there is the person's step"
                          % src["installer"], bundle_mod.tools_section([tc]))


# two unrelated chains: a simulation on an engine, and a spectrometer whose readings are fitted
CHAINS = {"simulation": ["install", "lattice", "compress", "analyze"],
          "spectrometer": ["connect", "read_spectrum", "fit_peak"]}


def contract(name):
    return dict({"artifact": "tool_contract", "schema_version": "0.1", "name": name, "description": "the step %s" % name,
                 "errors": ["invalid_input"], "side_effects": "none", "safety_gate": {"required": False, "place": "no side effects"},
                 "idempotent": True, "timeout_s": None}, **IO)


def compose(tmp, kind, workflow=None, words=None, sci=None, replay=None, extra_tools=()):
    names = CHAINS[kind] + list(extra_tools)
    tools = [{"name": n, "contract": contract(n), "adapter_source": "def run(payload):\n    return {'message': payload['message']}\n",
              "errors": []} for n in names]
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([t["contract"] for t in tools]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    iface = [{"id": "if-a", "call": {"tool": names[-1], "input": {"message": "a"}}, "expected_verdict": "pass"}]
    path = os.path.join(tmp, kind)
    bundle_mod.compose(template_mod.SOURCES["v11"], path, fill, tools, {"capabilities": []}, {"safety": {}},
                       iface, sci or [], replay or [], workflow=workflow, words=words)
    return path


class TheWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v11-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_request_s_order_is_the_workflow_section(self):
        for kind, order in CHAINS.items():
            text = cards.read_text(os.path.join(compose(self.tmp, kind, workflow=order, extra_tools=["status"]), "CLAUDE.md"))
            self.assertIn("## Workflow", text)
            self.assertIn("The workflow calls the tools in this order", text)
            self.assertIn(", then ".join("`%s`" % n for n in order) + ".", text)
            self.assertIn("Outside the order: `status`", text)
            self.assertEqual([ch for ch in text if ch.isdigit()], [], kind)          # B6

    def test_without_an_order_the_section_says_the_request_gave_none(self):
        for kind in CHAINS:
            text = cards.read_text(os.path.join(compose(self.tmp, kind), "CLAUDE.md"))
            self.assertIn("gave no order in which its workflow calls the tools", text)
            self.assertIn("an order you read from the descriptions is an inference", text)

    def test_an_order_that_names_no_tool_of_the_bundle_is_refused_before_anything_is_written(self):
        for kind, order in CHAINS.items():
            with self.assertRaises(ValueError):
                compose(self.tmp, kind, workflow=order + ["valve"])
            self.assertFalse(os.path.exists(os.path.join(self.tmp, kind)))
            with self.assertRaises(ValueError):
                compose(self.tmp, kind, workflow=order + order[:1])

    def test_the_intake_refuses_a_workflow_that_names_no_tool_of_its_own(self):
        for kind, order in CHAINS.items():
            card = {"tools": [{"contract": contract(n), "adapter_source": "x"} for n in order], "workflow": order}
            self.assertEqual(card_mod.workflow_problems(card), [], kind)
            card["workflow"] = order + ["valve"]
            self.assertIn("'valve' is not a tool of this card", " ".join(card_mod.workflow_problems(card)))
            card["workflow"] = order + order[:1]
            self.assertIn("a tool is named twice", " ".join(card_mod.workflow_problems(card)))
        self.assertEqual(card_mod.workflow_problems({"tool_contract": contract("x")}), [])     # no workflow, nothing asked


class TheBuilderRecords(unittest.TestCase):
    WORDS = {"docs/ideas/20261116.md": [{"verbatim": "그 값들은 정확히 비교한다", "gloss": "those values are compared exactly",
                                         "date": "2026-11-16"}]}

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v11-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_an_item_that_names_a_record_the_bundle_lacks_says_so_and_quotes_the_words(self):
        for kind in CHAINS:
            last = CHAINS[kind][-1]
            sci = [{"id": "sci-a", "call": {"tool": last, "input": {"message": "a"}}, "expected_verdict": "undecided",
                    "note": "compared exactly, on the person's word (docs/ideas/20261116.md)."},
                   {"id": "sci-b", "call": {"tool": last, "input": {"message": "b"}}, "expected_verdict": "undecided",
                    "note": "nothing cited here"}]
            replay = [{"id": "rp-a", "call": {"tool": last, "input": {"message": "a"}}, "expected_verdict": "pass",
                       "expected": {"message": "a"}, "why": "see meta_agent/tasks/016-tests.md and plan.md"}]
            b = compose(self.tmp, kind, sci=sci, replay=replay, words=self.WORDS)
            a = cards.load_json(os.path.join(b, "validation", "scientific", "sci-a.json"))
            self.assertEqual([r["path"] for r in a["builder_records"]], ["docs/ideas/20261116.md"])
            rec = a["builder_records"][0]
            self.assertFalse(rec["in_this_bundle"])
            self.assertIn("a record of the builder's repository; it is not in this bundle", rec["whose"])
            self.assertEqual(rec["words"], self.WORDS["docs/ideas/20261116.md"])
            self.assertNotIn("builder_records", cards.load_json(os.path.join(b, "validation", "scientific", "sci-b.json")))
            r = cards.load_json(os.path.join(b, "replay", "rp-a.json"))
            self.assertEqual([x["path"] for x in r["builder_records"]], ["meta_agent/tasks/016-tests.md", "plan.md"])
            self.assertTrue(all("words_here" in x and "words" not in x for x in r["builder_records"]))
            t = cards.load_json(os.path.join(b, "TEMPLATE.json"))
            self.assertIn("docs/ideas/20261116.md", [x["path"] for x in t["builder_records"]])
            self.assertIn("meta_agent/inbox/seats/20261117-design-macbook-20261116-1-4.json", [x["path"] for x in t["builder_records"]])
            self.assertNotIn("builder_records", cards.load_json(os.path.join(b, "validation", "interface", "if-a.json")))

    def test_a_path_the_bundle_carries_is_not_marked(self):
        b = os.path.join(self.tmp, "b")
        cards.write_text(os.path.join(b, "docs", "kept.md"), "kept")
        self.assertEqual(bundle_mod.builder_paths({"note": "docs/kept.md and docs/gone.md."}, b), ["docs/gone.md"])
        self.assertEqual(bundle_mod.builder_paths({"note": "tools/x/tool.json, runs/docs/a.md"}, b), [])

    def test_the_person_s_words_are_gathered_from_the_answers_that_name_their_record(self):
        intake = {"questions_for_the_person": [
            {"n": 1, "answer": {"verbatim": "예", "gloss": "yes", "date": "2026-11-16", "recorded_in": "docs/ideas/20261116.md"}},
            {"n": 2, "answer": {"verbatim": "no record named", "date": "2026-11-16"}}]}
        spec = {"held": [{"item": "x", "said": {"verbatim": "hold it", "date": "2026-11-17", "recorded_in": "docs/ideas/20261117.md"}}]}
        self.assertEqual(bundle_mod.words_by_record(intake, spec),
                         {"docs/ideas/20261116.md": [{"verbatim": "예", "date": "2026-11-16", "gloss": "yes"}],
                          "docs/ideas/20261117.md": [{"verbatim": "hold it", "date": "2026-11-17"}]})


class TheVersion(unittest.TestCase):
    def test_v11_changes_the_text_and_the_runner_of_tools(self):
        v10, v11 = template_mod.SOURCES["v10"], template_mod.SOURCES["v11"]
        self.assertEqual(cards.tree_files(v10), cards.tree_files(v11))
        changed = sorted(r for r in cards.tree_files(v10) if cards.sha256_file(os.path.join(v10, r)) != cards.sha256_file(os.path.join(v11, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/run_tool.py", "tasks/001-start.md"])
        self.assertEqual(template_mod.LATEST, "v11")
        meta = cards.load_json(os.path.join(v11, "TEMPLATE.json"))
        self.assertEqual(meta["version"], "v11")
        self.assertIn("workflow_section", meta["placeholders"])
        text = cards.read_text(os.path.join(v11, "CLAUDE.md"))
        self.assertEqual([ch for ch in text if ch.isdigit()], [])          # B6
        self.assertIn("{{workflow_section}}", text)
        for words in ("That record is not in this directory, and you do not look for it",
                      "`builder_records`",
                      "never installs the installer",
                      "Putting the installer on the computer is the person's step"):
            self.assertIn(words, text)
        task = cards.read_text(os.path.join(v11, "tasks", "001-start.md"))
        self.assertIn("that install is this agent's own next step", task)
        self.assertIn("run `python src/validate_tasks.py` again", task)


if __name__ == "__main__":
    unittest.main()
