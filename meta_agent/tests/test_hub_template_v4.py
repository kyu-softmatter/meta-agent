"""The hub template v4 (tasks/034; hub-8 and hub-9 of meta_agent/failures.jsonl, read from run multiscale/20261122-1,
collection collect-4).

- hub-8: a result that quotes values and holds something its item does not wait on answers no item in v3, so the
  question could not be solved. `release` records the person's release of one held entry, for the items of its
  assignment they name, quoting their words, which `words` appended to the question first; it refuses a release with no
  quote, a quote that is not the person's words, an item of another assignment, an entry that is not there and one
  released already. `status` then counts the result as answering those items alone, and lists the entry as released,
  with the person's words, apart from what is held. The member's card is unchanged, and the folder passes checks 1, 2
  and 25.
- hub-9: `open` refuses dontAsk as well as bypassPermissions, and a mode it does not know, before any session starts.

Two unrelated kinds: DFT->MD over the repository's builds qe-h2-bond/0004 and hoomd-h2-bond/0004 (their scripts run;
the engines do not: the tool results are written by the test), the DFT agent holding an input of the MD agent beside its
bond; and three mock engines of a photonic device heated by the light it absorbs, the heat engine's result answering two
items and the person releasing its held entry for one of them.

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

RELEASE = "the MD agent's temperature is not the DFT agent's to give: release it, the bond is answered"
ASKS = "run your engine; this assignment carries no setting"


class TheBuilder(unittest.TestCase):
    def test_v4_is_the_latest_and_carries_the_bridge_as_it_now_is(self):
        self.assertEqual(hubs_mod.LATEST, "v4")
        tmp = tempfile.mkdtemp(prefix="ma-hub4-")
        self.addCleanup(shutil.rmtree, tmp, True)
        root = os.path.join(tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        out = hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261122-1", root=root)
        self.assertEqual(out["gate"], "pass", out["gate_printed"])
        bundle = os.path.join(root, "builds", "h2-bond-hub", "0001", "bundle")
        self.assertEqual(cards.sha256_file(os.path.join(bundle, "src", "bridge.py")),
                         cards.sha256_file(os.path.join(REPO, "contracts", "tools", "bridge.py")))
        self.assertEqual(cards.load_json(os.path.join(bundle, "TEMPLATE.json"))["version"], "v4")


def refuses_modes(test, hub, aid):
    for mode in ("dontAsk", "bypassPermissions", "yolo"):
        refused = ok(test, hub, "src/hub.py", "open", "--assignment", aid, "--model", "m", "--effort", "high",
                     "--permission-mode", mode, "--words", "the person's words", code=3)["refused"]
        test.assertIn(mode, refused)                                                      # hub-9: v3 let dontAsk through
    test.assertFalse(os.path.exists(os.path.join(hub, "sessions", "releases")))
    test.assertEqual([n for n in os.listdir(os.path.join(hub, "sessions")) if n.endswith(".session.json")], [])


class DftThenMd(unittest.TestCase):
    """The first kind: the DFT agent quotes its bond and holds the MD agent's temperature; the person releases it."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub4-dftmd-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261122-1", root=root)
        self.run_dir, self.hub = lay_out(self, self.tmp, "h2-bond-hub/0001", {
            DFT: os.path.join(BUILDS, "qe-h2-bond", "0004", "bundle"), MD: os.path.join(BUILDS, "hoomd-h2-bond", "0004", "bundle")})
        self.dft = os.path.join(self.run_dir, "qe-h2-bond-0004")
        self.md = os.path.join(self.run_dir, "hoomd-h2-bond-0004")

    def test_the_person_releases_what_the_dft_agent_held_for_the_md(self):
        hub = self.hub
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
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS)
        p = ok(self, hub, "src/hub.py", "carry", "--assignment", a_dft, "--session", "hub-s")
        refuses_modes(self, hub, a_dft)
        os.makedirs(os.path.join(self.dft, "runs"))
        scan = {"run_dir": "runs/scan", "energy_curve": [[1.3, -2.2945], [1.4, -2.3000], [1.5, -2.2952]],
                "printed_conditions": {"xc": "PBE"}, "program_version": "test", "points": []}
        cards.write_json(os.path.join(self.dft, "runs", "scan.json"), scan)
        c, out = run(self.dft, "src/run_skill.py", "harmonic_well_fit@v1", "--record", "runs/fit.json",
                     stdin=json.dumps({"points": scan["energy_curve"]}).encode())
        self.assertEqual(c, 0, out)
        ho = ok(self, self.dft, "src/handover.py", "write", "--record", "runs/fit.json", "--runs", "runs/scan.json")
        res = ok(self, self.dft, "src/handover.py", "result", "--assignment", p["envelope"], "--handover", ho["written"],
                 "--held", "the MD run's thermostat temperature", "it is the MD agent's input, not this agent's",
                 "the person's value for the MD agent", code=4)
        self.assertEqual(res["card"]["state"], "partly_held")
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")["questions"][0]
        self.assertEqual(st["items"][0]["answered_by"], [])                                    # v3 stopped here (hub-8)
        copy = [b for a in st["assignments"] for b in a["results_here"]][0]["copy"]
        ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "0", code=3)          # no quote of the person
        w = ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", RELEASE)
        rev = str(cards.load_json(os.path.join(hub, w["written"]))["revision"])
        ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "0", "--quote", rev, "0", "release them all",
           code=3)                                                                             # not their words
        ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "1", "--quote", rev, "0", "release it",
           code=3)                                                                             # no such entry
        ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "0", "--quote", rev, "0", "release it",
           "--item", "dw-md", code=3)                                                          # another assignment's item
        before = cards.sha256_file(os.path.join(hub, copy))
        r = ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "0", "--quote", rev, "0", "release it")
        self.assertEqual((r["release"]["items"], r["release"]["by"]), (["dw-bond"], "the person"))
        ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "0", "--quote", rev, "0", "release it", code=3)
        self.assertEqual(cards.sha256_file(os.path.join(hub, copy)), before)                   # the card is unchanged
        st = ok(self, hub, "src/hub.py", "status")["questions"][0]
        self.assertEqual(st["items"][0]["answered_by"], [copy])
        self.assertEqual(st["held"], [])
        self.assertEqual([(x["what"], x["for_items"]) for x in st["released"]],
                         [("the MD run's thermostat temperature", ["dw-bond"])])
        self.assertEqual(st["released"][0]["quotes"][0]["quote"], "release it")
        ok(self, hub, "src/hub.py", "handover", "--card", "../qe-h2-bond-0004/" + ho["written"], "--to", "hoomd-h2-bond",
           "--session", "hub-s", "--words", "the person's words for this crossing")
        p2 = ok(self, hub, "src/hub.py", "carry", "--assignment", a_md, "--session", "hub-s")
        os.makedirs(os.path.join(self.md, "runs"), exist_ok=True)
        cards.write_json(os.path.join(self.md, "runs", "md.json"), {
            "hoomd_version": "test", "steps_run": 10, "bond_energy": 0.1, "potential_energy": 0.1,
            "kinetic_temperature": 0.0259, "series": {}, "run_dir": "runs/md"})
        ok(self, self.md, "src/handover.py", "result", "--assignment", p2["envelope"], "--report", "run_h2_md",
           "kinetic_temperature", "runs/md.json")
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        self.assertTrue(ok(self, hub, "src/hub.py", "status")["questions"][0]["solved"])
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


class ThreeEnginesOneHub(unittest.TestCase):
    """The second kind: the heat engine answers two items; the person releases its held entry for one of them only."""

    NAMES = ("mpb-waveguide-mode", "meep-waveguide-absorption", "fenics-waveguide-heat")

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub4-photonic-")
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

    def answer(self, name, envelope, held=None):
        member = os.path.join(self.run_dir, name + "-0001")
        c, out = run(member, "src/run_tool.py", "run_mock", stdin=b"{}")
        os.makedirs(os.path.join(member, "runs"), exist_ok=True)
        rp = os.path.join("runs", "call-%d.json" % len(os.listdir(os.path.join(member, "runs"))))
        with open(os.path.join(member, rp), "w") as f:
            f.write(out)
        argv = ["src/handover.py", "result", "--assignment", envelope, "--report", "run_mock", "kinetic_temperature", rp]
        if held:
            argv += ["--held"] + list(held)
        return ok(self, member, *argv, code=4 if held else 0)

    def test_a_release_answers_only_the_items_the_person_names(self):
        hub = self.hub
        items = [{"id": "dw-%d" % i, "what": w} for i, w in enumerate(("the effective index", "the power absorbed",
                                                                         "the temperature rise", "the heat's time"))]
        answers = [["dw-0"], ["dw-1"], ["dw-2", "dw-3"]]
        q = ok(self, hub, "src/hub.py", "question", "--draft", draft(os.path.join(self.tmp, "d.json"), {
            "question": "how much does the waveguide heat, and how fast?", "done_when": items,
            "assignments": [{"to": n, "asks": ASKS, "answers_items": answers[i], "returns": [{"card": "result"}],
                             "done_when": "the value"} for i, n in enumerate(self.NAMES)]}))
        qid = os.path.basename(q["written"])[:-5]
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS)
        ids = [x["id"] for x in q["list"]]
        envs = {n: ok(self, hub, "src/hub.py", "carry", "--assignment", aid, "--session", "hub-s")["envelope"]
                for aid, n in zip(ids, self.NAMES)}
        refuses_modes(self, hub, ids[2])
        self.answer(self.NAMES[0], envs[self.NAMES[0]])
        self.answer(self.NAMES[1], envs[self.NAMES[1]])
        self.answer(self.NAMES[2], envs[self.NAMES[2]], held=("the heat's time constant", "the transient run was not asked",
                                                              "the person's word for a transient run"))
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")["questions"][0]
        self.assertEqual([i["id"] for i in st["items"] if not i["answered_by"]], ["dw-2", "dw-3"])
        copy = st["assignments"][2]["results_here"][0]["copy"]
        w = ok(self, hub, "src/hub.py", "words", "--question", qid,
               "--words", "the temperature rise is answered; the time constant waits for a transient run")
        rev = str(cards.load_json(os.path.join(hub, w["written"]))["revision"])
        ok(self, hub, "src/hub.py", "release", "--result", copy, "--held", "0", "--quote", rev, "0",
           "the temperature rise is answered", "--item", "dw-2")
        st = ok(self, hub, "src/hub.py", "status")["questions"][0]
        self.assertEqual([i["id"] for i in st["items"] if not i["answered_by"]], ["dw-3"])     # only the item named
        self.assertFalse(st["solved"])
        self.assertEqual(st["held"], [])
        self.assertEqual([x["for_items"] for x in st["released"]], [["dw-2"]])
        w = ok(self, hub, "src/hub.py", "words", "--question", qid, "--words", "run it again with the transient")
        r2 = ok(self, hub, "src/hub.py", "round", "--assignment", ids[2], "--asks",
                "run your engine on what the person's words quoted here ask", "--quote",
                str(cards.load_json(os.path.join(hub, w["written"]))["revision"]), "1", "run it again with the transient")["card"]
        again = ok(self, hub, "src/hub.py", "carry", "--assignment", r2["id"], "--session", "hub-s")
        self.answer(self.NAMES[2], again["envelope"])
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")["questions"][0]
        self.assertTrue(st["solved"], st)
        self.assertEqual((st["held"], st["released"]), ([], []))                               # the latest result holds nothing
        shutil.rmtree(os.path.join(self.tmp, "meta_agent"))
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
