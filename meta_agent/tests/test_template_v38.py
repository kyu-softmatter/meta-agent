"""Template v38 and the builder, at the design role's ask 20261118-design-macbook-20261117-3-1, (2) (the person,
2026-11-18, docs/ideas/20261118.md, 'Another collection's QuTiP skill, as a reference for the builder').

- README.md is named after the agent and says whom it is for (the person whose work is the request's science task, on
  its tool and the tool's kind, and the request it was built for) and what it is not for (another tool, with none named
  in its place; work beyond the science task; what CLAUDE.md says it does not do; each item CAPABILITIES.json holds,
  with its reason). The build renders both from the fill and the capabilities it writes.
- CLAUDE.md's sentence on README.md says so; nothing else a session reads changes.

Two unrelated kinds, neither rheology: a plane-wave DFT engine whose request holds a comparison for want of materials,
and an optical spectrometer whose build holds a skill that would change the device and the tools it would call. Each
tool is a mock adapter that returns its output and starts no engine and reaches no instrument.

Watched failing with v37's tree in v38's place. Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.validate import gate as gate_mod

OLD_V, NEW_V = template_mod.SOURCES["v37"], template_mod.SOURCES["v38"]

KINDS = {
    "dft": {"agent": "pw-si-lattice", "tool": "plane-wave DFT code (mock)", "tool_kind": "engine", "call": "run_scf_mock",
            "science_task": "the equilibrium lattice constant of bulk silicon from total energies at several cell sizes",
            "held": [{"item": "the comparison of the lattice constant with a measured one as a scientific task",
                      "reason": "no published values of the same functional were taken as materials for a span"}],
            "shown": ["the comparison of the lattice constant with a measured one as a scientific task",
                      "no published values of the same functional were taken as materials for a span"],
            "kind_words": "a simulation engine"},
    "spectrometer": {"agent": "uvvis-absorbance", "tool": "fibre spectrometer (mock)", "tool_kind": "instrument",
                     "call": "read_spectrum_mock",
                     "science_task": "the absorbance spectrum of a dye solution against a blank, and where its peak lies",
                     "held": [{"skill": "set_integration_time@v1", "calls_tools": ["set_integration_time"],
                               "reason": "held by the builder until a person releases it"}],
                     "shown": ["`set_integration_time@v1`", "`set_integration_time`",
                               "held by the builder until a person releases it"],
                     "kind_words": "an instrument"},
}


def contract(k):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["call"], "description": "a mock that returns its output",
            "inputs": {"type": "object", "properties": {}, "required": []},
            "outputs": {"type": "object", "properties": {"done": {"type": "boolean", "description": "whether it answered"}},
                        "required": ["done"]},
            "errors": ["invalid_input", "execution_failure"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "a mock touches nothing"}, "idempotent": True, "timeout_s": None}


def compose(tmp, kind, template):
    k = KINDS[kind]
    path = os.path.join(tmp, k["agent"], "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    fill = {"agent_name": k["agent"], "template": "agent@test", "rid": "req-%s-001" % k["agent"], "purpose": "p",
            "science_task": k["science_task"], "tools_section": bundle_mod.tools_section([contract(k)]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    replay = [{"id": "rp-001", "name": "the mock answers", "call": {"tool": k["call"], "input": {}},
               "expected": {"output": {"done": True}}, "expected_verdict": "pass"}]
    bundle_mod.compose(template, path, fill, [{"name": k["call"], "contract": contract(k),
                                               "adapter_source": "def run(payload):\n    return {'done': True}\n",
                                               "errors": []}],
                       {"tool": k["tool"], "held": k["held"], "observed": []}, {"safety": {}, "parameters": {"rows": []}},
                       [], [], replay, skills=[], simulation=False, tool_kind=k["tool_kind"])
    return path


class TheReadmeSaysWhomItIsFor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v38-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def readme(self, kind, template=None):
        template = template or NEW_V
        return cards.read_text(os.path.join(compose(os.path.join(self.tmp, template[-3:]), kind, template), "README.md"))

    def test_it_is_named_after_the_agent_and_says_whom_it_is_for(self):
        for kind, k in KINDS.items():
            text = self.readme(kind)
            self.assertTrue(text.startswith("# %s\n" % k["agent"]), kind)
            whom = text.split("## Whom it is for")[1].split("## What it is not for")[0]
            self.assertIn("`%s`, %s" % (k["tool"], k["kind_words"]), whom, kind)
            self.assertIn(k["science_task"], whom, kind)
            self.assertIn("`req-%s-001`" % k["agent"], whom, kind)
            self.assertNotIn("{{", text, kind)

    def test_it_says_what_it_is_not_for_and_names_no_tool_in_its_place(self):
        for kind, k in KINDS.items():
            text = self.readme(kind)
            not_for = text.split("## What it is not for")[1].split("## What is here")[0]
            self.assertIn("Another tool, engine or instrument than `%s`" % k["tool"], not_for, kind)
            self.assertIn("names no other tool to use instead", not_for, kind)
            self.assertIn("What this agent does not do", not_for, kind)
            self.assertIn("Not yet, while it is held", not_for, kind)
            for words in k["shown"]:
                self.assertIn(words, not_for, kind)
            other = [o["tool"] for n, o in KINDS.items() if n != kind]
            for t in other:
                self.assertNotIn(t, text, kind)

    def test_the_folders_are_still_said_and_the_bundle_still_checks_itself(self):
        for kind in KINDS:
            path = compose(os.path.join(self.tmp, "gate-" + kind), kind, NEW_V)
            text = cards.read_text(os.path.join(path, "README.md"))
            self.assertIn("## What is here", text, kind)
            self.assertIn("python src/replay.py", text, kind)
            self.assertTrue(gate_mod.run_bundle(path)["replay"]["ok"], kind)

    def test_under_the_old_version_the_readme_said_neither(self):
        # the gap of the ask's (2), kept as it was: v37's README was the same for every agent
        for kind, k in KINDS.items():
            text = self.readme(kind, OLD_V)
            self.assertNotIn("Whom it is for", text, kind)
            self.assertNotIn(k["science_task"], text, kind)


class TheSections(unittest.TestCase):
    def test_a_tool_with_no_name_or_kind_and_nothing_held(self):
        whom = bundle_mod.for_whom_section("a task\n\nOf what this science task names, ...", None, None, "req-x")
        self.assertIn("on the tool under `tools/`: a task.", whom)
        self.assertNotIn("Of what this science task names", whom)
        not_for = bundle_mod.not_for_section(None, [])
        self.assertIn("than its own", not_for)
        self.assertNotIn("Not yet", not_for)

    def test_a_template_whose_readme_names_a_placeholder_the_build_cannot_fill_is_refused(self):
        tmp = tempfile.mkdtemp(prefix="ma-v38-t-")
        self.addCleanup(shutil.rmtree, tmp, True)
        tree = os.path.join(tmp, "template")
        shutil.copytree(NEW_V, tree, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        card = cards.load_json(os.path.join(tree, "TEMPLATE.json"))
        card["readme_placeholders"] = card["readme_placeholders"] + ["use_instead"]
        cards.write_json(os.path.join(tree, "TEMPLATE.json"), card)
        with self.assertRaises(ValueError):
            compose(os.path.join(tmp, "b"), "dft", tree)


class TheVersion(unittest.TestCase):
    def test_v38_is_the_latest_and_changes_its_readme_one_sentence_and_its_card(self):
        self.assertEqual(template_mod.LATEST, "v38")
        self.assertEqual(sorted(set(cards.tree_files(NEW_V)) ^ set(cards.tree_files(OLD_V))), [])
        both = set(cards.tree_files(OLD_V)) & set(cards.tree_files(NEW_V))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(OLD_V, r)) != cards.sha256_file(os.path.join(NEW_V, r)))
        self.assertEqual(changed, ["CLAUDE.md", "README.md", "TEMPLATE.json"])
        card = cards.load_json(os.path.join(NEW_V, "TEMPLATE.json"))
        self.assertEqual(card["version"], "v38")
        self.assertEqual(card["readme_placeholders"], ["agent_name", "for_whom", "not_for"])
        self.assertIn("whom this agent is for and what it is not for", cards.read_text(os.path.join(NEW_V, "CLAUDE.md")))


if __name__ == "__main__":
    unittest.main()
