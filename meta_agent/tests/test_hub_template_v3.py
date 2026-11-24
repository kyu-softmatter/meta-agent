"""The hub template v3 (tasks/034; hub-5, hub-6 and hub-7 of meta_agent/failures.jsonl, read from run
multiscale/20261121-1, collection collect-4).

- hub-5: `status` lists what is held from the latest result of each assignment alone, so that what a later round answered
  is not reported held.
- hub-6: `round` takes what the round asks from the session's words (--asks), refuses a round with none and one whose
  words carry a digit, and no longer copies the list item's asks.
- hub-7: `round` may be written before any round of its list item has been carried, so that the first carry of a member
  that waited for a hand-over already quotes the person's later words; `carry` then refuses the superseded list item and
  carries the round, as the thread's first envelope. The folder then passes checks 1, 2 and 25.

Two unrelated kinds: DFT->MD over the repository's builds qe-h2-bond/0004 and hoomd-h2-bond/0004 (their scripts run;
the engines do not: the tool results are written by the test), and three mock engines of a photonic device heated by the
light it absorbs, the heat engine holding for a value the person then gives.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import hubs as hubs_mod
from meta_agent.tests import test_template_v40 as v40
from meta_agent.tests.test_hub_template_v1 import (BUILDS, DFT, MD, PURPOSE, REPO, VALIDATE, WORDS, copy_build, draft,
                                                   lay_out, ok, run)

LATER = "the dumbbell count 64, the box side 10 and kT 1; for the heat engine the power absorbed is 2 mW"
FIRST_ASKS = "run your engine; this assignment carries no setting"
LATER_ASKS = "run your engine on the settings the person's words quoted here give"


class TheBuilder(unittest.TestCase):
    def test_v3_builds_as_it_was_made_and_carries_the_bridge_as_it_now_is(self):
        # v3 was the latest when this test was written; hub template v4 followed (tasks/034, hub-8 and hub-9)
        tmp = tempfile.mkdtemp(prefix="ma-hub3-")
        self.addCleanup(shutil.rmtree, tmp, True)
        root = os.path.join(tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        out = hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261122-1", root=root, template="v3")
        self.assertEqual(out["gate"], "pass", out["gate_printed"])
        bundle = os.path.join(root, "builds", "h2-bond-hub", "0001", "bundle")
        self.assertEqual(cards.sha256_file(os.path.join(bundle, "src", "bridge.py")),
                         cards.sha256_file(os.path.join(REPO, "contracts", "tools", "bridge.py")))
        self.assertEqual(cards.load_json(os.path.join(bundle, "TEMPLATE.json"))["version"], "v3")


class DftThenMd(unittest.TestCase):
    """The first kind: the person gives the MD settings before the bond has crossed; the MD's first carry is the round
    that quotes them (hub-7), asking in the session's words (hub-6)."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub3-dftmd-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261122-1", root=root, template="v3")
        self.run_dir, self.hub = lay_out(self, self.tmp, "h2-bond-hub/0001", {
            DFT: os.path.join(BUILDS, "qe-h2-bond", "0004", "bundle"), MD: os.path.join(BUILDS, "hoomd-h2-bond", "0004", "bundle")})
        self.dft = os.path.join(self.run_dir, "qe-h2-bond-0004")
        self.md = os.path.join(self.run_dir, "hoomd-h2-bond-0004")

    def test_the_mds_first_carry_quotes_the_persons_later_words(self):
        hub = self.hub
        q = ok(self, hub, "src/hub.py", "question", "--draft", draft(os.path.join(self.tmp, "d.json"), {
            "question": "the bond of H2 from DFT, and an MD run of H2 gas with it",
            "done_when": [{"id": "dw-bond", "what": "the bond from DFT"}, {"id": "dw-md", "what": "the MD run's temperature"}],
            "assignments": [
                {"to": "qe-h2-bond", "asks": "fit the harmonic bond of H2", "answers_items": ["dw-bond"],
                 "returns": [{"card": "result"}, {"card": "handover", "to": "hoomd-h2-bond"}], "done_when": "the bond"},
                {"to": "hoomd-h2-bond", "asks": FIRST_ASKS, "answers_items": ["dw-md"],
                 "returns": [{"card": "result"}], "done_when": "the temperature the engine reports"}]}))
        qid = os.path.basename(q["written"])[:-5]
        a_dft, a_md = [x["id"] for x in q["list"]]
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS)
        p = ok(self, hub, "src/hub.py", "carry", "--assignment", a_dft, "--session", "hub-s")
        # the person gives the MD's settings while the MD still waits for the bond, its list item never carried
        w = ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", LATER)
        rev = str(cards.load_json(os.path.join(hub, w["written"]))["revision"])
        quote = "the dumbbell count 64, the box side 10 and kT 1"
        refused = ok(self, hub, "src/hub.py", "round", "--assignment", a_md, "--quote", rev, "0", quote, code=3)["refused"]
        self.assertIn("--asks", refused)                                                       # hub-6: no asks of its own
        ok(self, hub, "src/hub.py", "round", "--assignment", a_md, "--asks", "run 64 dumbbells", "--quote", rev, "0",
           quote, code=3)                                                                      # hub-6: a digit
        r2 = ok(self, hub, "src/hub.py", "round", "--assignment", a_md, "--asks", LATER_ASKS, "--quote", rev, "0",
                quote)["card"]                                                                 # hub-7: v2 refused here
        self.assertEqual((r2["round"], r2["list_item"], r2["asks"]), (2, a_md, LATER_ASKS))
        self.assertNotIn("carries no setting", r2["asks"])
        # the hand-over has not crossed: the round waits as the list item did
        self.assertIn("h2_bond_force_constant", ok(self, hub, "src/hub.py", "carry", "--assignment", r2["id"],
                                                   "--session", "hub-s", code=3)["refused"])
        os.makedirs(os.path.join(self.dft, "runs"))
        scan = {"run_dir": "runs/scan", "energy_curve": [[1.3, -2.2945], [1.4, -2.3000], [1.5, -2.2952]],
                "printed_conditions": {"xc": "PBE"}, "program_version": "test", "points": []}
        cards.write_json(os.path.join(self.dft, "runs", "scan.json"), scan)
        c, out = run(self.dft, "src/run_skill.py", "harmonic_well_fit@v1", "--record", "runs/fit.json",
                     stdin=json.dumps({"points": scan["energy_curve"]}).encode())
        self.assertEqual(c, 0, out)
        ho = ok(self, self.dft, "src/handover.py", "write", "--record", "runs/fit.json", "--runs", "runs/scan.json")
        ok(self, self.dft, "src/handover.py", "result", "--assignment", p["envelope"], "--handover", ho["written"])
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        ok(self, hub, "src/hub.py", "handover", "--card", "../qe-h2-bond-0004/" + ho["written"], "--to", "hoomd-h2-bond",
           "--session", "hub-s", "--words", "the person's words for this crossing")
        refused = ok(self, hub, "src/hub.py", "carry", "--assignment", a_md, "--session", "hub-s", code=3)["refused"]
        self.assertIn("superseded by %s" % r2["id"], refused)                                 # only the latest round
        p2 = ok(self, hub, "src/hub.py", "carry", "--assignment", r2["id"], "--session", "hub-s")
        self.assertEqual(p2["round"], 1)                                                       # the thread's first carry
        listed = ok(self, self.md, "src/handover.py", "assignments")["assignments"]
        self.assertEqual([a["id"] for a in listed], [r2["id"]])
        os.makedirs(os.path.join(self.md, "runs"), exist_ok=True)
        cards.write_json(os.path.join(self.md, "runs", "md.json"), {
            "hoomd_version": "test", "steps_run": 10, "bond_energy": 0.1, "potential_energy": 0.1,
            "kinetic_temperature": 0.0259, "series": {}, "run_dir": "runs/md"})
        ok(self, self.md, "src/handover.py", "result", "--assignment", p2["envelope"], "--report", "run_h2_md",
           "kinetic_temperature", "runs/md.json")
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["questions"][0]["solved"], st)
        md_entry = st["questions"][0]["assignments"][1]
        self.assertEqual(md_entry["rounds"], [a_md, r2["id"]])
        self.assertEqual(md_entry["superseded_rounds"], [a_md])
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


class ThreeEnginesOneHub(unittest.TestCase):
    """The second kind: three mock engines; the heat engine holds for the power in its first round and answers in its
    second, after which nothing is reported held (hub-5)."""

    NAMES = ("mpb-waveguide-mode", "meep-waveguide-absorption", "fenics-waveguide-heat")

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub3-photonic-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        self.bundles = {}
        for n in self.NAMES:
            b = v40.compose(os.path.join(root, "builds"), n, "engine")
            cards.write_json(os.path.join(os.path.dirname(b), "build.json"),
                             {"card": "build", "bundle_path": b, "bundle_sha256": cards.sha256_tree(b)})
            self.bundles[n + "/0001"] = b
        out = hubs_mod.build("waveguide-heating-hub", [n + "/0001" for n in self.NAMES], PURPOSE, "lab", "seat", root=root, template="v3")
        self.assertEqual(out["gate"], "pass", out["gate_printed"])
        self.run_dir, self.hub = lay_out(self, self.tmp, "waveguide-heating-hub/0001", self.bundles)

    def answer(self, name, envelope, held=False):
        member = os.path.join(self.run_dir, name + "-0001")
        if held:
            return ok(self, member, "src/handover.py", "result", "--assignment", envelope, "--held", "the temperature rise",
                      "the power absorbed has not been given", "the person's value for it", code=4)
        c, out = run(member, "src/run_tool.py", "run_mock", stdin=b"{}")
        os.makedirs(os.path.join(member, "runs"), exist_ok=True)
        rp = os.path.join("runs", "call-%d.json" % len(os.listdir(os.path.join(member, "runs"))))
        with open(os.path.join(member, rp), "w") as f:
            f.write(out)
        return ok(self, member, "src/handover.py", "result", "--assignment", envelope, "--report", "run_mock",
                  "kinetic_temperature", rp)

    def test_what_a_later_round_answered_is_not_reported_held(self):
        hub = self.hub
        items = [{"id": "dw-%d" % i, "what": w} for i, w in enumerate(("the effective index", "the power absorbed",
                                                                         "the temperature rise"))]
        q = ok(self, hub, "src/hub.py", "question", "--draft", draft(os.path.join(self.tmp, "d.json"), {
            "question": "how much does the waveguide heat?", "done_when": items,
            "assignments": [{"to": n, "asks": FIRST_ASKS, "answers_items": [items[i]["id"]],
                             "returns": [{"card": "result"}], "done_when": "the value"} for i, n in enumerate(self.NAMES)]}))
        qid = os.path.basename(q["written"])[:-5]
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS)
        ids = [x["id"] for x in q["list"]]
        envs = {n: ok(self, hub, "src/hub.py", "carry", "--assignment", aid, "--session", "hub-s")["envelope"]
                for aid, n in zip(ids, self.NAMES)}
        self.answer(self.NAMES[0], envs[self.NAMES[0]])
        self.answer(self.NAMES[1], envs[self.NAMES[1]])
        self.answer(self.NAMES[2], envs[self.NAMES[2]], held=True)
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertEqual([h["what"] for h in st["questions"][0]["held"]], ["the temperature rise"])
        w = ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", LATER)
        rev = str(cards.load_json(os.path.join(hub, w["written"]))["revision"])
        r2 = ok(self, hub, "src/hub.py", "round", "--assignment", ids[2], "--asks", LATER_ASKS, "--quote", rev, "0",
                "the power absorbed is 2 mW")["card"]
        self.assertEqual(r2["asks"], LATER_ASKS)
        again = ok(self, hub, "src/hub.py", "carry", "--assignment", r2["id"], "--session", "hub-s")
        self.assertEqual(again["round"], 2)
        self.answer(self.NAMES[2], again["envelope"])
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["questions"][0]["solved"], st)
        self.assertEqual(st["questions"][0]["held"], [], st["questions"][0]["held"])         # hub-5: v2 listed round one's
        heat = st["questions"][0]["assignments"][2]
        self.assertEqual(heat["rounds"], [ids[2], r2["id"]])
        self.assertTrue(heat["latest_result"].endswith("r2.json"), heat)
        self.assertEqual(heat["superseded_rounds"], [])
        shutil.rmtree(os.path.join(self.tmp, "meta_agent"))
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
