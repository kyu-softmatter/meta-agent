"""Template v14 (tasks/021; test runs electromagnetics/20261117-2 and dft/20261117-2): what two bundles on engines of
unrelated kinds, Meep and Quantum ESPRESSO, showed standing alone.

A bundle's task, replay item or parameter row may cite a card of the builder's repository by its id (a material, a
parameter sheet) or a question the builder put to the person by its number ('question 1'); neither is in the bundle,
and a session standing alone could not tell what it named (em-7, dft-5). The build marks them with builder_records, as
it marks a path, envelope/parameters.json among the files, quoting the question and its answer. An optional input of a
tool contract that names neither a row nor a default left its value to the adapter, and a session guessed it (em-8):
the build refuses it, and the Tools section prints a default. The start task says that an interface task whose call
starts the engine fails before the install for want of the environment (em-9).

Each mechanism runs on two unrelated kinds: a simulation chain on an engine and a spectrometer's chain.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src import designer
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.tests.test_template_v11 import CHAINS, contract

ADAPTER = "def run(payload):\n    return {'message': payload['message']}\n"

# what each kind's request carried: the cards a build read, and the questions its intake put to the person
KINDS = {
    "simulation": {"material": "mat-20261117-001", "sheet": "ps-ring-modes-001",
                   "questions": [{"n": 1, "needed_before": "S6", "question": "Which tolerance judges the mode's frequency?"},
                                 {"n": 2, "needed_before": "S4", "question": "Is the page a registered material?",
                                  "answer": {"verbatim": "아직", "gloss": "not yet", "date": "2026-11-17"}}]},
    "spectrometer": {"material": "mat-20261105-004", "sheet": "ps-peak-fit-002",
                     "questions": [{"n": 1, "needed_before": "S6", "question": "Which tolerance judges the peak position?"},
                                   {"n": 3, "needed_before": "S4", "question": "May the vendor's manual be kept?",
                                    "answer": {"verbatim": "yes, keep it", "date": "2026-11-05"}}]},
}


def with_optional(name, prop):
    c = contract(name)
    c = copy.deepcopy(c)
    c["inputs"]["properties"]["mirror"] = prop
    return c


def compose(tmp, kind, sci=None, replay=None, rows=None, ids=None, questions=None, last_contract=None, sub=None):
    names = CHAINS[kind]
    tools = [{"name": n, "contract": contract(n), "adapter_source": ADAPTER, "errors": []} for n in names]
    if last_contract is not None:
        tools[-1]["contract"] = last_contract
    fill = {"agent_name": kind, "template": "agent@test", "rid": "req-%s" % kind, "purpose": "the purpose",
            "science_task": "the task", "tools_section": bundle_mod.tools_section([t["contract"] for t in tools]),
            "must_not": bundle_mod.must_not_section([]), "skills_section": bundle_mod.skills_section([]),
            "seat_form": "%s-<machine>-<YYYYMMDD>-<n>" % kind}
    iface = [{"id": "if-a", "call": {"tool": names[-1], "input": {"message": "a"}}, "expected_verdict": "pass"}]
    envelope = {"safety": {}}
    if rows is not None:
        envelope["parameters"] = {"rows": rows}
    path = os.path.join(tmp, sub or kind)
    bundle_mod.compose(template_mod.SOURCES["v14"], path, fill, tools, {"capabilities": []}, envelope,
                       iface, sci or [], replay or [], ids=ids, questions=questions)
    return path


class TheCardsAndQuestions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v14-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def build(self, kind):
        k = KINDS[kind]
        last = CHAINS[kind][-1]
        q_named = k["questions"][1]["n"]
        sci = [{"id": "sci-a", "call": {"tool": last, "input": {"message": "a"}}, "expected_verdict": "undecided",
                "reference": {"kind": "source", "ref": "%s, the section the task reads" % k["material"]},
                "note": "the tolerance is the person's (question 1); see also Question %d" % q_named},
               {"id": "sci-b", "call": {"tool": last, "input": {"message": "b"}}, "expected_verdict": "undecided",
                "note": "question 9 was never asked; %s0 and x-%s are other names" % (k["material"], k["sheet"])}]
        replay = [{"id": "rp-a", "call": {"tool": last, "input": {"message": "a"}}, "expected_verdict": "pass",
                   "expected": {"message": "a"}, "why": "questions 12 and 13 of another request"}]
        rows = [{"name": "width", "value": 1, "unit": "1", "source": "literature:%s" % kind,
                 "note": "read in %s; inside the interval of %s" % (k["material"], k["sheet"])},
                {"name": "plain", "value": 2, "unit": "1", "note": "nothing cited"}]
        b = compose(self.tmp, kind, sci=sci, replay=replay, rows=rows,
                    ids=[k["material"], k["sheet"], "req-%s" % kind], questions=bundle_mod.questions_by_number(
                        {"questions_for_the_person": k["questions"]}))
        return k, q_named, b

    def test_a_task_naming_a_card_and_a_question_says_they_are_the_builder_s_and_quotes_the_question(self):
        for kind in KINDS:
            k, q_named, b = self.build(kind)
            recs = cards.load_json(os.path.join(b, "validation", "scientific", "sci-a.json"))["builder_records"]
            self.assertEqual([r.get("card") for r in recs if "card" in r], [k["material"]], kind)
            qs = {r["question"]: r for r in recs if "question" in r}
            self.assertEqual(sorted(qs), sorted({1, q_named}), kind)
            self.assertEqual(qs[1]["asked"], k["questions"][0]["question"])
            self.assertIn("answer_here", qs[1])
            self.assertEqual(qs[q_named]["answer"], {x: y for x, y in k["questions"][1]["answer"].items()})
            self.assertTrue(all(r["in_this_bundle"] is False for r in recs))
            self.assertIn("is not in this bundle", qs[1]["whose"])

    def test_an_unasked_number_a_longer_number_and_a_longer_id_are_not_marked(self):
        for kind in KINDS:
            k, _, b = self.build(kind)
            self.assertNotIn("builder_records", cards.load_json(os.path.join(b, "validation", "scientific", "sci-b.json")), kind)
            self.assertNotIn("builder_records", cards.load_json(os.path.join(b, "replay", "rp-a.json")), kind)
            self.assertNotIn("builder_records", cards.load_json(os.path.join(b, "validation", "interface", "if-a.json")), kind)

    def test_the_parameter_rows_are_marked_as_a_file(self):
        for kind in KINDS:
            k, _, b = self.build(kind)
            params = cards.load_json(os.path.join(b, "envelope", "parameters.json"))
            self.assertEqual(sorted(r["card"] for r in params["builder_records"]), sorted([k["material"], k["sheet"]]), kind)
            self.assertEqual([r["name"] for r in params["rows"]], ["width", "plain"])     # the rows themselves unchanged

    def test_the_bundle_still_runs_its_checks_with_the_marks(self):
        for kind in KINDS:
            _, _, b = self.build(kind)
            for args in (["src/gate.py", "--self-check"], ["src/replay.py"]):
                p = subprocess.run([sys.executable, "-I"] + args, cwd=b, capture_output=True, text=True)
                self.assertEqual(p.returncode, 0, (kind, args, p.stdout + p.stderr))
            p = subprocess.run([sys.executable, "-I", "src/validate_tasks.py"], cwd=b, capture_output=True, text=True)
            self.assertIn("gates: interface pass", p.stdout, (kind, p.stdout + p.stderr))

    def test_the_builder_s_ids_are_the_request_s_cards_the_materials_and_the_profiles(self):
        root = os.path.join(self.tmp, "root")
        cards.write_json(os.path.join(root, "requests", "req-x", "intake.json"), {"id": "intake-x"})
        cards.write_json(os.path.join(root, "requests", "req-x", "parameter_sheet.json"), {"id": "ps-x-001"})
        cards.write_json(os.path.join(root, "requests", "req-x", "list.json"), ["not", "a", "card"])
        cards.write_json(os.path.join(root, "requests", "req-y", "intake.json"), {"id": "intake-y"})       # another request
        cards.write_json(os.path.join(root, "inbox", "materials", "m1", "MATERIAL.json"), {"id": "mat-20261117-001"})
        cards.write_json(os.path.join(root, "profiles", "lab-a", "profile.json"), {"id": "lab-a"})
        self.assertEqual(designer.builder_ids(root, "req-x"), ["intake-x", "lab-a", "mat-20261117-001", "ps-x-001"])
        self.assertEqual(designer.builder_ids(os.path.join(self.tmp, "empty"), "req-x"), [])


class TheDefault(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-template-v14-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_an_optional_input_with_neither_a_row_nor_a_default_is_refused_before_anything_is_written(self):
        for kind in CHAINS:
            c = with_optional(CHAINS[kind][-1], {"type": "string", "enum": ["none", "even", "odd"]})
            with self.assertRaises(ValueError) as e:
                compose(self.tmp, kind, last_contract=c)
            self.assertIn("the optional input mirror names neither a row nor a default", str(e.exception))
            self.assertFalse(os.path.exists(os.path.join(self.tmp, kind)))
            self.assertEqual(bundle_mod.default_problems([c]),
                             ["tool %s: the optional input mirror names neither a row nor a default" % CHAINS[kind][-1]])

    def test_a_default_is_printed_and_a_row_or_a_required_input_needs_none(self):
        for kind in CHAINS:
            last = CHAINS[kind][-1]
            word = with_optional(last, {"type": "string", "enum": ["none", "even", "odd"], "default": "none"})
            text = cards.read_text(os.path.join(compose(self.tmp, kind, last_contract=word, sub=kind + "-w"), "CLAUDE.md"))
            self.assertIn("`mirror` (string; one of `none`, `even`, `odd`; left out, it is `none`)", text)
            number = with_optional(last, {"type": "number", "default": 0.5})
            text = cards.read_text(os.path.join(compose(self.tmp, kind, last_contract=number, sub=kind + "-n"), "CLAUDE.md"))
            self.assertIn("left out, it is the default its contract states", text)
            self.assertEqual([ch for ch in text if ch.isdigit()], [])                          # B6
            self.assertEqual(bundle_mod.default_problems([with_optional(last, {"type": "number", "row": "mirror_row"})]), [])
            req = with_optional(last, {"type": "string"})
            req["inputs"]["required"] = list(req["inputs"]["required"]) + ["mirror"]
            self.assertEqual(bundle_mod.default_problems([req]), [])


class TheVersion(unittest.TestCase):
    def test_v14_changes_text_only(self):
        v13, v14 = template_mod.SOURCES["v13"], template_mod.SOURCES["v14"]
        self.assertEqual(cards.tree_files(v13), cards.tree_files(v14))
        changed = sorted(r for r in cards.tree_files(v13) if cards.sha256_file(os.path.join(v13, r)) != cards.sha256_file(os.path.join(v14, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "tasks/001-start.md"])
        self.assertEqual(template_mod.LATEST, "v14")
        self.assertEqual(cards.load_json(os.path.join(v14, "TEMPLATE.json"))["version"], "v14")
        text = cards.read_text(os.path.join(v14, "CLAUDE.md"))
        self.assertEqual([ch for ch in text if ch.isdigit()], [])          # B6
        for words in ("a card of the builder's repository by its id", "a question the builder put to the person by its number",
                      "`envelope/parameters.json` among the files", "a path, an id or a number alone settles nothing here"):
            self.assertIn(words, text)
        task = cards.read_text(os.path.join(v14, "tasks", "001-start.md"))
        self.assertIn("an interface task whose call starts the engine fails too", task)
        self.assertIn("the verdict after the install is the one that says whether the interface works", task)


if __name__ == "__main__":
    unittest.main()
