"""The hub template v2 and its builder (tasks/034; hub-1, hub-2 and hub-3 of meta_agent/failures.jsonl; the person,
2026-11-21, 'Append to the question (Recommended)', 'Next round quotes them (Recommended)').

- A build of the latest version carries contracts/tools/bridge.py as it now is.
- `members` lists each member's parameter rows: whether each holds a value, who chose it and on what basis, and whether
  it takes a hand-over (hub-2).
- `carry` refuses an assignment to a member that takes a hand-over from another member before that hand-over has crossed
  into its inbox, and says what it waits for (hub-1).
- `words` appends the person's words given after the agreement to the question's next revision, and `round` writes the
  next round of an assignment of the agreed list, naming its list item and quoting parts of those words character for
  character, only after the member answered the last round; a quote that is not in the words is refused (hub-3). The
  folder then passes checks 1, 2 and 25.

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
from meta_agent.tests import test_template_v35 as v35
from meta_agent.tests.test_hub_template_v1 import (BUILDS, DFT, MD, PURPOSE, REPO, VALIDATE, WORDS, copy_build, draft,
                                                   lay_out, ok, run)

LATER = "the dumbbell count 64, the box side 10 and kT 1; for the heat engine the power absorbed is 2 mW"


class TheBuilder(unittest.TestCase):
    def test_v2_is_the_latest_and_carries_the_bridge_as_it_now_is(self):
        self.assertEqual(hubs_mod.LATEST, "v2")
        tmp = tempfile.mkdtemp(prefix="ma-hub2-")
        self.addCleanup(shutil.rmtree, tmp, True)
        root = os.path.join(tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        out = hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261120-4", root=root)
        self.assertEqual(out["gate"], "pass", out["gate_printed"])
        bundle = os.path.join(root, "builds", "h2-bond-hub", "0001", "bundle")
        self.assertEqual(cards.sha256_file(os.path.join(bundle, "src", "bridge.py")),
                         cards.sha256_file(os.path.join(REPO, "contracts", "tools", "bridge.py")))
        self.assertEqual(cards.load_json(os.path.join(bundle, "TEMPLATE.json"))["version"], "v2")


class DftThenMd(unittest.TestCase):
    """The first kind: the MD agent's assignment waits for the bond; its settings come in the person's later words."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub2-dftmd-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261120-4", root=root)
        self.run_dir, self.hub = lay_out(self, self.tmp, "h2-bond-hub/0001", {
            DFT: os.path.join(BUILDS, "qe-h2-bond", "0004", "bundle"), MD: os.path.join(BUILDS, "hoomd-h2-bond", "0004", "bundle")})
        self.dft = os.path.join(self.run_dir, "qe-h2-bond-0004")
        self.md = os.path.join(self.run_dir, "hoomd-h2-bond-0004")

    def test_the_md_waits_for_the_bond_and_takes_the_persons_later_words(self):
        hub = self.hub
        m = {x["agent"]: x for x in ok(self, hub, "src/hub.py", "members")["members"]}
        dft_rows = {r["name"]: r for r in m["qe-h2-bond"]["rows"]}
        self.assertTrue(dft_rows["ecutwfc"]["holds_a_value"] and dft_rows["ecutwfc"]["chosen_by"] == "human", dft_rows)
        md_rows = {r["name"]: r for r in m["hoomd-h2-bond"]["rows"]}
        self.assertFalse(md_rows["n_molecules"]["holds_a_value"], md_rows)
        self.assertTrue(md_rows["bond_k"]["takes_handover"], md_rows)
        q = ok(self, hub, "src/hub.py", "question", "--draft", draft(os.path.join(self.tmp, "d.json"), {
            "question": "the bond of H2 from DFT, and an MD run of H2 gas with it",
            "done_when": [{"id": "dw-bond", "what": "the bond from DFT"}, {"id": "dw-md", "what": "the MD run's temperature"}],
            "assignments": [
                {"to": "qe-h2-bond", "asks": "fit the harmonic bond of H2", "answers_items": ["dw-bond"],
                 "returns": [{"card": "result"}, {"card": "handover", "to": "hoomd-h2-bond"}], "done_when": "the bond"},
                {"to": "hoomd-h2-bond", "asks": "run H2 gas with the bond handed to you", "answers_items": ["dw-md"],
                 "returns": [{"card": "result"}], "done_when": "the temperature the engine reports"}]}))
        qid = os.path.basename(q["written"])[:-5]
        a_dft, a_md = [x["id"] for x in q["list"]]
        ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", LATER, code=3)    # not agreed yet
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS)
        refused = ok(self, hub, "src/hub.py", "carry", "--assignment", a_md, "--session", "hub-s", code=3)["refused"]
        self.assertIn("h2_bond_force_constant over thr-h2-bond from qe-h2-bond", refused)
        p = ok(self, hub, "src/hub.py", "carry", "--assignment", a_dft, "--session", "hub-s")
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
        p2 = ok(self, hub, "src/hub.py", "carry", "--assignment", a_md, "--session", "hub-s")
        ok(self, hub, "src/hub.py", "round", "--assignment", a_md, code=3)                    # not answered yet
        ok(self, self.md, "src/handover.py", "result", "--assignment", p2["envelope"], "--held", "the MD run",
           "the run's settings are the person's", "the person's values for them", code=4)
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        w = ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", LATER)
        rev = cards.load_json(os.path.join(hub, w["written"]))["revision"]
        ok(self, hub, "src/hub.py", "round", "--assignment", a_md, "--quote", str(rev), "0", "the dumbbell count 65",
           code=3)                                                                               # not their words
        r2 = ok(self, hub, "src/hub.py", "round", "--assignment", a_md, "--quote", str(rev), "0",
                "the dumbbell count 64, the box side 10 and kT 1")["card"]
        self.assertEqual((r2["round"], r2["list_item"], r2["to"]["agent"]), (2, a_md, "hoomd-h2-bond"))
        p3 = ok(self, hub, "src/hub.py", "carry", "--assignment", r2["id"], "--session", "hub-s")
        self.assertEqual(p3["round"], 2)
        os.makedirs(os.path.join(self.md, "runs"), exist_ok=True)
        cards.write_json(os.path.join(self.md, "runs", "md.json"), {
            "hoomd_version": "test", "steps_run": 10, "bond_energy": 0.1, "potential_energy": 0.1,
            "kinetic_temperature": 0.0259, "series": {}, "run_dir": "runs/md"})
        ok(self, self.md, "src/handover.py", "result", "--assignment", p3["envelope"], "--report", "run_h2_md",
           "kinetic_temperature", "runs/md.json")
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["questions"][0]["solved"], st)
        self.assertEqual(st["questions"][0]["person_words"][0]["words"], LATER)
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


class ThreeEnginesOneHub(unittest.TestCase):
    """The second kind: three mock engines; the heat engine holds for the power, which the person then gives."""

    NAMES = ("mpb-waveguide-mode", "meep-waveguide-absorption", "fenics-waveguide-heat")

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub2-photonic-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        self.bundles = {}
        for n in self.NAMES:
            b = v35.compose(os.path.join(root, "builds"), n, "engine")
            cards.write_json(os.path.join(os.path.dirname(b), "build.json"),
                             {"card": "build", "bundle_path": b, "bundle_sha256": cards.sha256_tree(b)})
            self.bundles[n + "/0001"] = b
        out = hubs_mod.build("waveguide-heating-hub", [n + "/0001" for n in self.NAMES], PURPOSE, "lab", "seat", root=root)
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

    def test_the_heat_engine_takes_the_power_in_its_second_round(self):
        hub = self.hub
        items = [{"id": "dw-%d" % i, "what": w} for i, w in enumerate(("the effective index", "the power absorbed",
                                                                         "the temperature rise"))]
        q = ok(self, hub, "src/hub.py", "question", "--draft", draft(os.path.join(self.tmp, "d.json"), {
            "question": "how much does the waveguide heat?", "done_when": items,
            "assignments": [{"to": n, "asks": "what your engine reports", "answers_items": [items[i]["id"]],
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
        w = ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", LATER)
        rev = cards.load_json(os.path.join(hub, w["written"]))["revision"]
        ok(self, hub, "src/hub.py", "round", "--assignment", ids[2] + "-x", code=3)            # no such list item
        r2 = ok(self, hub, "src/hub.py", "round", "--assignment", ids[2], "--quote", str(rev), "0",
                "the power absorbed is 2 mW")["card"]
        self.assertEqual(r2["quotes"], [{"question_revision": rev, "index": 0, "quote": "the power absorbed is 2 mW"}])
        again = ok(self, hub, "src/hub.py", "carry", "--assignment", r2["id"], "--session", "hub-s")
        self.answer(self.NAMES[2], again["envelope"])
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["questions"][0]["solved"], st)
        self.assertEqual(st["questions"][0]["assignments"][2]["rounds"], [ids[2], r2["id"]])
        shutil.rmtree(os.path.join(self.tmp, "meta_agent"))
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
