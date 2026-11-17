"""The stage that writes a request's first card (tasks/016; contracts/schemas/intake.schema.json).

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .

The drafts are taken from the two examples of the schema, contracts/examples/requests/req-fixture-002 (a
request that waits, on an engine) and req-fixture-003 (a specified one, on an echo tool): two unrelated
kinds, neither of them rheology.
"""
import copy
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.intake import card as card_mod

HERE = os.path.dirname(os.path.abspath(__file__))
META = os.path.dirname(HERE)
REPO = os.path.dirname(META)
EXAMPLES = os.path.join(REPO, "contracts", "examples", "requests")
SEAT = "meta-macbook-20261116-1"
NOW = "2026-11-16T12:00:00Z"
ENV = dict(os.environ, PYTHONUTF8="1")


def example(rid):
    return cards.load_json(os.path.join(EXAMPLES, rid, "intake.json"))


def specified_example():
    """req-fixture-003, the specified example, whose contract and error contract are the echo request's in full
    (contracts, 2bde495)."""
    return example("req-fixture-003")


def draft_of(card):
    return {k: copy.deepcopy(v) for k, v in card.items() if k not in card_mod.STAGE_WRITES}


class Write(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-intake-")
        self.root = os.path.join(self.tmp, "meta_agent")
        self.req = os.path.join(self.root, "requests", "req-fixture-002")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def first(self):
        return card_mod.write(self.req, "req-fixture-002", draft_of(example("req-fixture-002")), SEAT, NOW)

    def test_the_two_examples_are_what_their_drafts_give(self):
        for rid, stage in (("req-fixture-002", "reading"), ("req-fixture-003", "specified")):
            ex = example(rid)
            self.assertEqual(card_mod.problems(ex), [], rid)
            card = card_mod.make(rid, draft_of(ex), ex["author"], ex["created_at"])
            self.assertEqual(card["stage"], stage)
            self.assertEqual({k: v for k, v in card.items() if k != "assumptions"}, {k: v for k, v in ex.items() if k != "assumptions"})

    def test_the_first_card_is_revision_one_at_reading_and_a_same_draft_writes_nothing(self):
        path, card = self.first()
        self.assertEqual(os.path.basename(path), "intake.json")
        self.assertEqual((card["card"], card["id"], card["revision"], card["stage"], card["status"], card["numbers"]),
                         ("intake", "intake-fixture-002", 1, "reading", "draft", []))
        self.assertNotIn("supersedes", card)
        self.assertEqual(card["persons_words"]["verbatim"], "이것을 자동화 하고싶어")
        again, same = card_mod.write(self.req, "req-fixture-002", draft_of(example("req-fixture-002")), SEAT, NOW, note="nothing")
        self.assertIsNone(again)
        self.assertEqual(os.listdir(self.req), ["intake.json"])

    def test_a_draft_holds_only_what_changes_and_gives_the_next_revision(self):
        self.first()
        with self.assertRaises(card_mod.Refused) as e:
            card_mod.write(self.req, "req-fixture-002", {"gui_choice": "none"}, SEAT, NOW)
        self.assertIn("give --note", str(e.exception))
        path, card = card_mod.write(self.req, "req-fixture-002", {"gui_choice": "none", "notes": None}, SEAT, NOW,
                                    note="the person said no interface is wanted")
        self.assertEqual(os.path.basename(path), "v2_intake.json")
        self.assertEqual((card["revision"], card["supersedes"], card["gui_choice"], card["stage"]), (2, "intake-fixture-002", "none", "reading"))
        self.assertNotIn("notes", card)
        self.assertEqual(card["paragraph"], example("req-fixture-002")["paragraph"])
        self.assertEqual(card_mod.latest(self.req), (2, path))

    def test_the_person_s_answer_is_recorded_verbatim_and_not_written_over(self):
        self.first()
        path, card = card_mod.answer(self.req, "req-fixture-002", 2, "튜토리얼 그대로 끝까지 돌려줘", "2026-11-16", SEAT,
                                     gloss="Run the tutorial as it is, to the end.", recorded_in="docs/ideas/20261116.md", now=NOW)
        self.assertEqual(os.path.basename(path), "v2_intake.json")
        self.assertEqual(card["questions_for_the_person"][1]["answer"]["verbatim"], "튜토리얼 그대로 끝까지 돌려줘")
        self.assertEqual([q["n"] for q in card_mod.waiting(card)], [1])
        self.assertIn("the person's answer to question 2", card["revision_note"])
        for n in (2, 7):
            with self.assertRaises(card_mod.Refused):
                card_mod.answer(self.req, "req-fixture-002", n, "x", "2026-11-16", SEAT, now=NOW)
        self.assertEqual(sorted(os.listdir(self.req)), ["intake.json", "v2_intake.json"])

    def test_the_card_is_specified_when_it_carries_the_contract_and_the_tasks(self):
        self.first()
        spec = specified_example()
        with self.assertRaises(card_mod.Refused) as e:      # a contract with no task: the schema's rule
            card_mod.write(self.req, "req-fixture-002", {"tool_contract": spec["tool_contract"]}, SEAT, NOW, note="the contract")
        self.assertIn("interface_tasks", str(e.exception))
        written = {k: spec[k] for k in ("tool_contract", "error_contracts", "interface_tasks", "scientific_tasks", "replay_items")}
        with self.assertRaises(card_mod.Refused) as e:      # a specified card in a tree names its adapter, and the tree has it
            card_mod.write(self.req, "req-fixture-002", written, SEAT, NOW, note="the contract and the tasks are written")
        self.assertIn("tool/adapter_source: a specified card names the source of each adapter", str(e.exception))
        written["tool"] = dict(example("req-fixture-002")["tool"], adapter_source="tests/fixtures/echo/adapter.py")
        with self.assertRaises(card_mod.Refused) as e:
            card_mod.write(self.req, "req-fixture-002", written, SEAT, NOW, note="the contract and the tasks are written")
        self.assertIn("tests/fixtures/echo/adapter.py is not a file under meta_agent/", str(e.exception))
        shutil.copytree(os.path.join(META, "tests", "fixtures", "echo"), os.path.join(self.root, "tests", "fixtures", "echo"))
        path, card = card_mod.write(self.req, "req-fixture-002", written, SEAT, NOW, note="the contract and the tasks are written")
        self.assertEqual((card["stage"], card["revision"]), ("specified", 2))

    def test_what_is_refused_writes_nothing(self):
        good = draft_of(example("req-fixture-002"))
        bad = [dict(good, stage="specified"), dict(good, numbers=[]), dict(good, a_field_of_my_own=1),
               dict(good, paragraph="an agent that runs 4 stages"), dict(good, must_not=["run more than 3 times"]),
               dict(good, questions_for_the_person=[{"n": 2, "needed_before": "the goal", "question": "q"}]),
               dict(good, executes="sometimes"), {k: v for k, v in good.items() if k != "persons_words"}, ["not an object"]]
        for draft in bad:
            with self.assertRaises(card_mod.Refused, msg=str(draft)[:80]):
                card_mod.write(self.req, "req-fixture-002", draft, SEAT, NOW)
        self.assertFalse(os.path.exists(self.req))
        self.first()
        with self.assertRaises(card_mod.Refused):
            card_mod.write(self.req, "req-another-001", good, SEAT, NOW, note="x")

    def test_a_record_of_before_the_card_is_followed_by_a_card(self):
        req = os.path.join(self.root, "requests", "req-echo-001")
        os.makedirs(req)
        shutil.copytree(os.path.join(META, "tests", "fixtures", "echo"), os.path.join(self.root, "tests", "fixtures", "echo"))
        shutil.copy(os.path.join(META, "requests", "req-echo-001", "intake.json"), os.path.join(req, "intake.json"))
        self.assertFalse(card_mod.is_card(cards.load_json(os.path.join(req, "intake.json"))))
        record = cards.load_json(os.path.join(req, "intake.json"))
        with self.assertRaises(card_mod.Refused):      # the record as it is lacks what a card must carry
            card_mod.write(req, "req-echo-001", {"gui_choice": record["gui_choice"], "note": "x"}, SEAT, NOW, note="x")
        path, card = card_mod.write(req, "req-echo-001", {
            "persons_words": {"verbatim": "An agent that returns what it is given.", "date": "2026-10-29"},
            "questions_for_the_person": [],
            "tool_reading": [{k: v for k, v in row.items() if k != "gap_reason"} for row in record["tool_reading"]]},
            SEAT, NOW, note="the record of before the card, as a card")
        self.assertEqual((os.path.basename(path), card["revision"], card["stage"]), ("v2_intake.json", 2, "specified"))
        self.assertNotIn("supersedes", card)

    def test_the_command_writes_says_what_waits_and_the_tree_passes_the_validator(self):
        draft = os.path.join(self.tmp, "draft.json")
        cards.write_json(draft, draft_of(example("req-fixture-002")))
        base = [sys.executable, "-m", "meta_agent.src.intake", "--root", self.root]
        p = subprocess.run(base + ["write", "--rid", "req-fixture-002", "--draft", draft, "--seat", SEAT, "--now", NOW],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("wrote  meta_agent/requests/req-fixture-002/intake.json", p.stdout)
        self.assertIn("stage  reading, revision 1", p.stdout)
        p = subprocess.run(base + ["waiting", "--rid", "req-fixture-002"], cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertIn("2 question(s) wait for the person", p.stdout)
        p = subprocess.run(base + ["answer", "--rid", "req-fixture-002", "--n", "1", "--verbatim", "엔진까지", "--gloss", "As far as an engine.",
                                   "--date", "2026-11-16", "--seat", SEAT, "--now", NOW], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        p = subprocess.run(base + ["check", os.path.join(self.req, "v2_intake.json")], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        cards.write_json(draft, {"stage": "specified"})
        p = subprocess.run(base + ["write", "--rid", "req-fixture-002", "--draft", draft, "--seat", SEAT, "--note", "x"],
                           cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=ENV)
        self.assertEqual(p.returncode, 1)
        self.assertIn("refused  stage is written by the stage", p.stdout)
        p = subprocess.run([sys.executable, os.path.join(REPO, "contracts", "validate.py"), self.tmp, "--checks", "1,7"],
                           capture_output=True, text=True, env=ENV)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)



class Signature(unittest.TestCase):
    """The goal's recall signature names its tool as the case store does: check 8 holds a case's engine and
    instrument to registry ids, and recall meets them by equality (test run 20261116-5, collect-1)."""

    def goal(self, name, kind, registry_id, science_task="t", parameters=()):
        return {"science_task": science_task, "executes": kind if kind in ("engine", "instrument") else "none",
                "methods": [], "parameter_scope": list(parameters),
                "tool": {"name": name, "kind": kind, "registry_id": registry_id, "material_refs": []}}

    def test_the_tool_is_named_by_its_registry_id_and_by_its_name_only_without_one(self):
        from meta_agent.src.intake import goal as goal_mod
        self.assertEqual(goal_mod.signature_of(self.goal("HOOMD-blue", "engine", "hoomd_blue"))["engine"], "hoomd_blue")
        self.assertEqual(goal_mod.signature_of(self.goal("the SMA microscope", "instrument", "sma_microscope"))["instrument"],
                         "sma_microscope")
        self.assertEqual(goal_mod.signature_of(self.goal("Fixture Rheometer", "instrument", None))["instrument"], "Fixture Rheometer")
        self.assertNotIn("engine", goal_mod.signature_of(self.goal("echo", "analysis_software", "echo")))

    def test_a_goal_meets_the_cases_that_carry_its_tool_s_id_and_not_by_a_display_name(self):
        """On two unrelated kinds: an engine in the repository's store, an instrument in the fixtures' store."""
        from meta_agent.src.cases import recall as recall_mod
        from meta_agent.src.intake import goal as goal_mod
        for store, name, kind, rid, task, params in (
                (os.path.join(META, "cases"), "HOOMD-blue", "engine", "hoomd_blue", "t", ()),
                (os.path.join(HERE, "fixtures", "cases"), "the SMA microscope", "instrument", "sma_microscope",
                 "particle tracking of tracer beads", ("pixel_size",))):
            by_id = recall_mod.recall(goal_mod.signature_of(self.goal(name, kind, rid, task, params)), store)
            by_name = recall_mod.recall(goal_mod.signature_of(self.goal(name, kind, None, task, params)), store)
            self.assertTrue([h for h in by_id["hits"] if kind in h["matched"]], (kind, by_id))
            self.assertFalse([h for h in by_name["hits"] if kind in h["matched"]], (kind, "a display name meets no case on its tool"))


class TheGatesOwnRules(unittest.TestCase):
    """What the gate refuses after a build, the stage refuses before it writes (test run 20261116-7, collect-1):
    a tolerance the validation report's schema refuses, a number check 3 refuses on tool_profile.md and a number
    check B6 refuses in the Tools section of the bundle's CLAUDE.md. On the two unrelated kinds of the examples:
    an engine whose request waits (req-fixture-002) and an echo tool that is specified (req-fixture-003)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-intake-rules-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def refused(self, rid, draft, *words):
        req = os.path.join(self.tmp, rid)
        with self.assertRaises(card_mod.Refused) as e:
            card_mod.write(req, rid, draft, SEAT, NOW)
        for w in words:
            self.assertIn(w, str(e.exception))
        self.assertFalse(os.path.exists(req), "nothing is written")
        return str(e.exception)

    def written(self, rid, draft):
        path, card = card_mod.write(os.path.join(self.tmp, rid), rid, draft, SEAT, NOW)
        self.assertTrue(os.path.isfile(path))
        return card

    def echo(self, **contract):
        d = draft_of(specified_example())
        d["tool_contract"] = dict(d["tool_contract"], **contract)
        return d

    def test_a_tolerance_or_a_reference_the_report_refuses_is_refused(self):
        d = self.echo()
        task = {"id": "sci-1", "name": "the length of a known text",
                "tolerance": {"value": 0, "unit": "1", "chosen_by": "human", "words": "정확히", "gloss": "exactly"}}
        msg = self.refused("req-fixture-003", dict(d, scientific_tasks=[task]), "scientific_tasks/0/tolerance",
                           "validation report's tolerance")
        self.assertIn("words", msg)
        bad_ref = dict(task, tolerance={"value": 0, "unit": "1", "chosen_by": "human"},
                       reference_spec={"kind": "analytic", "ref": "len", "page": "the first"})
        self.refused("req-fixture-003", dict(d, scientific_tasks=[bad_ref]), "scientific_tasks/0/reference_spec")
        good = dict(bad_ref, reference_spec={"kind": "analytic", "ref": "len"})
        self.assertEqual(self.written("req-fixture-003", dict(d, scientific_tasks=[good, dict(good, id="sci-2", tolerance=None)]))
                         ["stage"], "specified")

    def test_a_number_in_the_tool_s_reading_is_refused_unless_a_card_carries_it(self):
        for rid in ("req-fixture-002", "req-fixture-003"):
            d = draft_of(specified_example() if rid == "req-fixture-003" else example(rid))
            claim = dict(d["tool_reading"][0], claim="the tool reads at most 7.2 items at a time")
            self.refused(rid, dict(d, tool_reading=[claim]), "tool_profile.md would carry the number 7.2", "check 3")
            # the same number, read from a source and carried as a value read, is a number a card of the folder holds
            read = {"name": "items_at_a_time", "value": 7.2, "unit": "count", "locus": "a fixture: no source was read",
                    "role": "a setting the source chooses"}
            card = self.written(rid, dict(d, tool_reading=[claim], values_read=(d.get("values_read") or []) + [read]))
            self.assertEqual(card["revision"], 1)

    def test_a_place_with_numerals_is_a_place_and_passes(self):
        d = draft_of(example("req-fixture-002"))
        claim = dict(d["tool_reading"][0], loci=["page 04, cell 6"])
        self.assertEqual(self.written("req-fixture-002", dict(d, tool_reading=[claim]))["revision"], 1)

    def test_a_number_in_a_contract_s_words_is_refused_as_check_b6_would(self):
        self.refused("req-fixture-003", self.echo(description="returns the text and its length; frame -1 is the last"),
                     "the number -1 from the contract of echo", "B6")
        inputs = {"type": "object", "required": ["text"], "properties": {
            "text": {"type": "string", "description": "the text, at most 03 lines"}}}
        self.refused("req-fixture-003", self.echo(inputs=inputs), "the number 03")
        # what the Tools section does not print as a number passes: a unit of one beside a type, a digit in an
        # enumerated word (named as the contract's), a unit with a digit
        inputs = {"type": "object", "required": ["text", "mode", "size"], "properties": {
            "text": {"type": "string", "description": "the text"},
            "mode": {"type": "string", "enum": ["utf8", "latin1"]},
            "size": {"type": "number", "unit": "1"},
            "volume": {"type": "number", "unit": "m^3"}}}
        self.assertEqual(self.written("req-fixture-003", self.echo(inputs=inputs))["stage"], "specified")

    def test_the_designer_and_the_check_command_read_the_same_rules(self):
        d = self.echo(description="returns the text; frame -1 is the last")
        req = os.path.join(self.tmp, "req-fixture-003")
        os.makedirs(req)
        bad = dict(specified_example(), tool_contract=d["tool_contract"])
        cards.write_json(os.path.join(req, "intake.json"), bad)
        p = subprocess.run([sys.executable, "-m", "meta_agent.src.intake", "check", os.path.join(req, "intake.json")],
                           capture_output=True, text=True, cwd=REPO, env=ENV)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertIn("B6", p.stdout)
        from meta_agent.src import designer
        with self.assertRaises(designer.Stopped) as e:      # the Designer reads the card with the stage's rules
            designer.may_start(bad, os.path.join(req, "intake.json"), req, self.tmp)
        self.assertIn("B6", str(e.exception))



class TheContractsAndTheAdapters(unittest.TestCase):
    """Round five of the clone (test run 20261117-1, collect-1): the stage wrote a contract the gate's tool_contract
    schema refuses (calls_external true), and adapter_source named from the repository root, which the Designer does
    not find under meta_agent/. On two unrelated kinds: an engine named by `tools` and an echo tool named by
    `tool_contract`, each written into a request folder of a scratch meta_agent/ tree that has the echo adapter."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-intake-contracts-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = os.path.join(self.tmp, "meta_agent")
        shutil.copytree(os.path.join(META, "tests", "fixtures", "echo"), os.path.join(self.root, "tests", "fixtures", "echo"))

    def drafts(self, contract_change=None, source="tests/fixtures/echo/adapter.py"):
        """{rid: draft}: the echo example as one tool, and the engine example specified with the same contract as `tools`."""
        ex = specified_example()
        contract = dict(ex["tool_contract"], **(contract_change or {}))
        echo = dict(draft_of(ex), tool_contract=contract, tool=dict(ex["tool"], adapter_source=source))
        engine = draft_of(example("req-fixture-002"))
        engine.update({k: copy.deepcopy(ex[k]) for k in ("interface_tasks", "scientific_tasks", "replay_items")})
        engine["tools"] = [{"contract": contract, "adapter_source": source, "error_contracts": copy.deepcopy(ex["error_contracts"])}]
        return {"req-fixture-003": echo, "req-fixture-002": engine}

    def write(self, rid, draft):
        return card_mod.write(os.path.join(self.root, "requests", rid), rid, draft, SEAT, NOW)

    def test_a_contract_the_gate_s_schema_refuses_is_refused(self):
        for rid, draft in self.drafts({"calls_external": True}).items():
            with self.assertRaises(card_mod.Refused) as e:
                self.write(rid, draft)
            self.assertIn("calls_external", str(e.exception), rid)
            self.assertIn("the gate's tool_contract schema refuses it", str(e.exception))
            self.assertIn("tools/0/contract" if rid == "req-fixture-002" else "tool_contract", str(e.exception))
        for rid, draft in self.drafts({"calls_external": {"program": "echo", "license": "not stated", "bundled": False}}).items():
            self.assertEqual(self.write(rid, draft)[1]["stage"], "specified", rid)

    def test_an_error_contract_the_gate_s_schema_refuses_is_refused(self):
        draft = self.drafts()["req-fixture-002"]
        draft["tools"][0]["error_contracts"][0].pop("remediation")
        with self.assertRaises(card_mod.Refused) as e:
            self.write("req-fixture-002", draft)
        self.assertIn("tools/0/error_contracts/0", str(e.exception))

    def test_an_adapter_named_from_the_repository_root_is_refused_and_the_place_under_the_tree_is_said(self):
        for rid, draft in self.drafts(source="meta_agent/tests/fixtures/echo/adapter.py").items():
            with self.assertRaises(card_mod.Refused) as e:
                self.write(rid, draft)
            self.assertIn("is not a file under meta_agent/, where the Designer reads it", str(e.exception), rid)
            self.assertIn("under meta_agent/ it is tests/fixtures/echo/adapter.py", str(e.exception))
            self.assertFalse(os.path.exists(os.path.join(self.root, "requests", rid)))
        for rid, draft in self.drafts(source="tests/fixtures/echo/missing.py").items():
            with self.assertRaises(card_mod.Refused) as e:
                self.write(rid, draft)
            self.assertNotIn("named from the repository root", str(e.exception))

    def test_the_designer_finds_the_adapters_the_stage_let_through(self):
        from meta_agent.src import designer
        for rid, draft in self.drafts().items():
            path, card = self.write(rid, draft)
            self.assertEqual([t["name"] for t in designer.tools_of(card, self.root)], ["echo"], rid)


if __name__ == "__main__":
    unittest.main()
