"""The hub template v1 and its builder (tasks/033; the person, 2026-11-20, 'A hub bundle (Recommended)', 'Assign freely,
carry on my word (Recommended)', 'Pointer to a card (Recommended)', 'Ask once per question (Recommended)', 'until solve
the problem').

- The builder makes a hub beside its members' builds: members.json names each by agent, build, folder ../<agent>-<NNNN>
  and the hash of its build card; it refuses a member whose bundle is not its build card's digest, one of a template
  that cannot answer an assignment, fewer than two members and two of one agent; the hub's gate finds every member.
- In a folder laid out as members.json says, src/hub.py writes the question and its list, refuses to carry before the
  person agreed, carries each assignment and each result on the hub's trigger, carries a hand-over between members only
  with the person's words, opens a member's session on the model, effort and mode given and on none it was not given,
  and says the question is solved only when every item is answered by a result that is not held; the folder then passes
  checks 1, 2 and 25.

Two unrelated kinds: DFT->MD over the repository's builds qe-h2-bond/0004 and hoomd-h2-bond/0004 (their scripts run;
the engines do not: the tool results are written by the test), and three mock engines of a photonic device heated by
the light it absorbs, one of which holds first and answers in a second round.

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
from meta_agent.src.build import hubs as hubs_mod
from meta_agent.tests import test_template_v40 as v40

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BUILDS = os.path.join(REPO, "meta_agent", "builds")
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
DFT, MD = "qe-h2-bond/0004", "hoomd-h2-bond/0004"
PURPOSE = "A test hub over the agents it is given."
WORDS = "a test's words agreeing to the list"
V1 = "v1"          # each build here names the version, so the test does not depend on the bridge as it now is


def run(cwd, *args, stdin=None, env=None):
    p = subprocess.run([sys.executable] + list(args), cwd=cwd, input=stdin, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")


def ok(test, cwd, *args, code=0, env=None):
    c, out = run(cwd, *args, env=env)
    test.assertEqual(c, code, out)
    return json.loads(out) if out.strip().startswith("{") else out


def copy_build(src_builds, dst_builds, build):
    agent, bid = build.split("/")
    shutil.copytree(os.path.join(src_builds, agent, bid), os.path.join(dst_builds, agent, bid))


def lay_out(test, root, hub_build, members):
    """A run folder: the hub and each member beside it, as members.json names them."""
    run_dir = os.path.join(root, "run")
    hub = os.path.join(run_dir, hub_build.replace("/", "-"))
    shutil.copytree(os.path.join(root, "meta_agent", "builds", *hub_build.split("/"), "bundle"), hub)
    for m in cards.load_json(os.path.join(hub, "members.json"))["members"]:
        shutil.copytree(members[m["build"]], os.path.normpath(os.path.join(hub, m["folder"])))
    return run_dir, hub


def fake_claude(root):
    """A command-line claude that answers at once, so that `open` and `wait` run without a model."""
    d = os.path.join(root, "bin")
    os.makedirs(d)
    p = os.path.join(d, "claude")
    with open(p, "w") as f:
        f.write("#!%s\nimport json, sys\nbrief = sys.stdin.read()\nprint(json.dumps({'result': 'read: ' + brief.strip(), "
                "'session_id': 'fake', 'is_error': False}))\n" % sys.executable)
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    return dict(os.environ, PATH=d + os.pathsep + os.environ.get("PATH", ""))


def draft(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


class TheBuilder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = os.path.join(self.tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(self.root, "builds"), b)

    def test_members_json_names_each_member_by_build_folder_and_card_hash(self):
        out = hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261120-4",
                             now="2026-11-20T12:00:00Z", root=self.root, template=V1)
        self.assertEqual(out["gate"], "pass", out["gate_printed"])
        b = os.path.join(self.root, "builds", "h2-bond-hub", "0001")
        m = cards.load_json(os.path.join(b, "bundle", "members.json"))
        self.assertEqual(m["hub"], {"agent": "h2-bond-hub", "build": "h2-bond-hub/0001"})
        for e, build in zip(m["members"], (DFT, MD)):
            self.assertEqual(e["folder"], "../" + build.replace("/", "-"))
            self.assertEqual(e["build_card_sha256"], "sha256:" + cards.sha256_file(
                os.path.join(self.root, "builds", *build.split("/"), "build.json")))
        card = cards.load_json(os.path.join(b, "build.json"))
        self.assertTrue(card["template_version"].startswith("hub@"))
        self.assertEqual(card["bundle_sha256"], cards.sha256_tree(os.path.join(b, "bundle")))
        self.assertEqual(card["gate_verdict"]["interface"], "pass")
        self.assertEqual(cards.sha256_file(os.path.join(b, "bundle", "src", "bridge.py")),
                         cards.sha256_file(os.path.join(hubs_mod.SOURCES[V1], "src", "bridge.py")))
        for absent in ("tools", "skills", "envelope", "src/run_tool.py", "src/gate.py", "src/run_skill.py"):
            self.assertFalse(os.path.exists(os.path.join(b, "bundle", *absent.split("/"))), absent)
        self.assertNotIn("{{", cards.read_text(os.path.join(b, "bundle", "CLAUDE.md")))

    def test_it_refuses_what_cannot_be_a_member(self):
        with self.assertRaises(ValueError):
            hubs_mod.build("h2-bond-hub", [DFT], PURPOSE, "lab", "seat", root=self.root, template=V1)
        with self.assertRaises(ValueError):
            hubs_mod.build("h2-bond-hub", [DFT, DFT], PURPOSE, "lab", "seat", root=self.root, template=V1)
        with self.assertRaises(ValueError):
            hubs_mod.build("h2-bond-hub", [DFT, MD], "a purpose with 3 parts", "lab", "seat", root=self.root, template=V1)
        old = v40.compose(os.path.join(self.root, "builds"), "old-agent", "engine", template=v40.V39)
        cards.write_json(os.path.join(os.path.dirname(old), "build.json"),
                         {"card": "build", "bundle_path": old, "bundle_sha256": cards.sha256_tree(old)})
        with self.assertRaises(ValueError) as e:
            hubs_mod.build("h2-bond-hub", [DFT, "old-agent/0001"], PURPOSE, "lab", "seat", root=self.root, template=V1)
        self.assertIn("v40", str(e.exception))
        # a member changed after it was built is not the build its card names
        bundle = os.path.join(self.root, "builds", "hoomd-h2-bond", "0004", "bundle")
        card = cards.load_json(os.path.join(self.root, "builds", "hoomd-h2-bond", "0004", "build.json"))
        card["bundle_path"] = bundle
        cards.write_json(os.path.join(self.root, "builds", "hoomd-h2-bond", "0004", "build.json"), card)
        shutil.rmtree(bundle)
        shutil.copytree(os.path.join(BUILDS, "hoomd-h2-bond", "0004", "bundle"), bundle)
        with open(os.path.join(bundle, "failures.jsonl"), "a") as f:
            f.write("{}\n")
        with self.assertRaises(ValueError) as e:
            hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab", "seat", root=self.root, template=V1)
        self.assertIn("digest", str(e.exception))
        self.assertFalse(os.path.exists(os.path.join(self.root, "builds", "h2-bond-hub")))


    def test_a_named_version_does_not_depend_on_the_bridge_as_it_now_is(self):
        # the design role's ask 20261121-design-macbook-20261120-3-3: a changed contracts/tools/bridge.py refuses a new
        # hub of the latest version, and a build that names its version carries that version's bridge and passes
        changed = os.path.join(self.tmp, "bridge.py")
        shutil.copyfile(hubs_mod.BRIDGE, changed)
        with open(changed, "a") as f:
            f.write("# a line the bridge gained after this version was made\n")
        self.addCleanup(setattr, hubs_mod, "BRIDGE", hubs_mod.BRIDGE)
        hubs_mod.BRIDGE = changed
        with self.assertRaises(ValueError) as e:
            hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab", "seat", root=self.root)
        self.assertIn("bridge as it now is", str(e.exception))
        self.assertFalse(os.path.exists(os.path.join(self.root, "builds", "h2-bond-hub")))
        out = hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab", "seat", root=self.root, template=V1)
        self.assertEqual(out["gate"], "pass", out["gate_printed"])
        card = cards.load_json(os.path.join(self.root, "builds", "h2-bond-hub", "0001", "build.json"))
        self.assertIn("which contracts/tools/bridge.py no longer is", card["note"])
        with self.assertRaises(ValueError):
            hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab", "seat", root=self.root, template="v0")


class DftThenMd(unittest.TestCase):
    """The first kind: the DFT agent answers and hands its bond to the MD agent on the person's word; the MD agent answers."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub-dftmd-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        for b in (DFT, MD):
            copy_build(BUILDS, os.path.join(root, "builds"), b)
        hubs_mod.build("h2-bond-hub", [DFT, MD], PURPOSE, "lab-kyu-softmatter", "meta-macbook-20261120-4", root=root, template=V1)
        self.run_dir, self.hub = lay_out(self, self.tmp, "h2-bond-hub/0001", {
            DFT: os.path.join(BUILDS, "qe-h2-bond", "0004", "bundle"), MD: os.path.join(BUILDS, "hoomd-h2-bond", "0004", "bundle")})
        self.dft = os.path.join(self.run_dir, "qe-h2-bond-0004")
        self.md = os.path.join(self.run_dir, "hoomd-h2-bond-0004")

    def test_a_question_goes_round_until_solved_and_the_folder_passes(self):
        hub = self.hub
        m = ok(self, hub, "src/hub.py", "members")
        self.assertTrue(all(x["there"] and x["holds_this_build"] and x["answers_assignments"] for x in m["members"]), m)
        self.assertEqual([t["from"] for x in m["members"] for t in x["takes"]], ["qe-h2-bond", "qe-h2-bond"])
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
        ok(self, hub, "src/hub.py", "carry", "--assignment", a_dft, "--session", "hub-s", code=3)   # not agreed yet
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS)
        ok(self, hub, "src/hub.py", "agree", "--question", qid, "--words", WORDS, code=3)       # once per question
        p = ok(self, hub, "src/hub.py", "carry", "--assignment", a_dft, "--session", "hub-s")
        self.assertEqual(p["folder"], "../qe-h2-bond-0004")
        ok(self, hub, "src/hub.py", "carry", "--assignment", a_dft, "--session", "hub-s", code=3)  # carried already
        text = ok(self, hub, "src/hub.py", "brief", "--assignment", a_dft)
        self.assertIn(p["card"], text)
        self.assertIn(p["sha256"], text)
        env = fake_claude(self.tmp)
        ok(self, hub, "src/hub.py", "open", "--assignment", a_dft, "--model", "m", "--effort", "e",
           "--permission-mode", "bypassPermissions", "--words", "w", code=3, env=env)
        ok(self, hub, "src/hub.py", "open", "--assignment", a_dft, "--model", "m", "--effort", "e", code=3, env=env)
        s = ok(self, hub, "src/hub.py", "open", "--assignment", a_dft, "--model", "a-model", "--effort", "an-effort",
               "--permission-mode", "auto", "--words", "the person's words naming them", env=env)
        self.assertEqual((s["model"], s["effort"], s["permission_mode"]), ("a-model", "an-effort", "auto"))
        w = ok(self, hub, "src/hub.py", "wait", env=env)
        self.assertEqual([x["state"] for x in w["sessions"]], ["ended"], w)
        # the member's session, done here by the test: a scan result as the tool would print it, the fit, the hand-over
        os.makedirs(os.path.join(self.dft, "runs"))
        scan = {"run_dir": "runs/scan", "energy_curve": [[1.3, -2.2945], [1.4, -2.3000], [1.5, -2.2952]],
                "printed_conditions": {"xc": "PBE"}, "program_version": "test", "points": []}
        cards.write_json(os.path.join(self.dft, "runs", "scan.json"), scan)
        c, out = run(self.dft, "src/run_skill.py", "harmonic_well_fit@v1", "--record", "runs/fit.json",
                     stdin=json.dumps({"points": scan["energy_curve"]}).encode())
        self.assertEqual(c, 0, out)
        ho = ok(self, self.dft, "src/handover.py", "write", "--record", "runs/fit.json", "--runs", "runs/scan.json")
        ok(self, self.dft, "src/handover.py", "result", "--assignment", p["envelope"], "--handover", ho["written"])
        got = ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        self.assertEqual([x.get("state") for x in got["collected"]], ["answered"], got)
        st = ok(self, hub, "src/hub.py", "status")
        items = {i["id"]: i["answered_by"] for i in st["questions"][0]["items"]}
        self.assertTrue(items["dw-bond"] and not items["dw-md"], st)
        self.assertFalse(st["questions"][0]["solved"])
        self.assertEqual([h["waits_for"] for h in st["handovers"]], ["the person's word for this crossing"])
        card = "../qe-h2-bond-0004/" + ho["written"]
        ok(self, hub, "src/hub.py", "handover", "--card", card, "--to", "hoomd-h2-bond", "--session", "hub-s", code=3)
        ok(self, hub, "src/hub.py", "handover", "--card", card, "--to", "hoomd-h2-bond", "--session", "hub-s",
           "--words", "the person's words for this crossing")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["handovers"][0]["crossed"], st)
        p2 = ok(self, hub, "src/hub.py", "carry", "--assignment", a_md, "--session", "hub-s")
        c, out = run(self.md, "src/handover.py", "receive")
        self.assertIn(c, (0, 4), out)                 # the bond's receipts, used or held as the MD build declares
        os.makedirs(os.path.join(self.md, "runs"), exist_ok=True)
        cards.write_json(os.path.join(self.md, "runs", "md.json"), {
            "hoomd_version": "test", "steps_run": 10, "bond_energy": 0.1, "potential_energy": 0.1,
            "kinetic_temperature": 0.0259, "series": {}, "run_dir": "runs/md"})
        ok(self, self.md, "src/handover.py", "result", "--assignment", p2["envelope"], "--report", "run_h2_md",
           "kinetic_temperature", "runs/md.json")
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["questions"][0]["solved"], st)
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


class ThreeEnginesOneHub(unittest.TestCase):
    """The second kind: a mode solver, an FDTD engine and a heat-conduction engine, as mocks; the heat engine holds in the
    first round and answers when the hub carries its assignment again."""

    NAMES = ("mpb-waveguide-mode", "meep-waveguide-absorption", "fenics-waveguide-heat")

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-hub-photonic-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        root = os.path.join(self.tmp, "meta_agent")
        self.bundles = {}
        for n in self.NAMES:
            b = v40.compose(os.path.join(root, "builds"), n, "engine")
            cards.write_json(os.path.join(os.path.dirname(b), "build.json"),
                             {"card": "build", "bundle_path": b, "bundle_sha256": cards.sha256_tree(b)})
            self.bundles[n + "/0001"] = b
        out = hubs_mod.build("waveguide-heating-hub", [n + "/0001" for n in self.NAMES], PURPOSE, "lab", "seat", root=root, template=V1)
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

    def test_three_members_answer_one_after_a_second_round(self):
        hub = self.hub
        items = [{"id": "dw-%d" % i, "what": w} for i, w in enumerate(("the effective index", "the power absorbed",
                                                                         "the temperature rise"))]
        q = ok(self, hub, "src/hub.py", "question", "--draft", draft(os.path.join(self.tmp, "d.json"), {
            "question": "how much does the waveguide heat?", "done_when": items,
            "assignments": [{"to": n, "asks": "what your engine reports", "answers_items": [items[i]["id"]],
                             "returns": [{"card": "result"}], "done_when": "the value"} for i, n in enumerate(self.NAMES)]}))
        ok(self, hub, "src/hub.py", "agree", "--question", os.path.basename(q["written"])[:-5], "--words", WORDS)
        ids = [x["id"] for x in q["list"]]
        envs = {}
        for aid, n in zip(ids, self.NAMES):
            envs[n] = ok(self, hub, "src/hub.py", "carry", "--assignment", aid, "--session", "hub-s")["envelope"]
        self.answer(self.NAMES[0], envs[self.NAMES[0]])
        self.answer(self.NAMES[1], envs[self.NAMES[1]])
        ok(self, hub, "src/hub.py", "carry", "--assignment", ids[2], "--session", "hub-s", "--again", code=3)  # not answered
        self.answer(self.NAMES[2], envs[self.NAMES[2]], held=True)
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertFalse(st["questions"][0]["solved"])
        self.assertEqual([h["what"] for h in st["questions"][0]["held"]], ["the temperature rise"])
        again = ok(self, hub, "src/hub.py", "carry", "--assignment", ids[2], "--session", "hub-s", "--again")
        self.assertEqual(again["round"], 2)
        self.answer(self.NAMES[2], again["envelope"])
        ok(self, hub, "src/hub.py", "collect", "--session", "hub-s")
        st = ok(self, hub, "src/hub.py", "status")
        self.assertTrue(st["questions"][0]["solved"], st)
        shutil.rmtree(os.path.join(self.tmp, "meta_agent"))
        c, out = run(REPO, VALIDATE, self.run_dir, "--checks", "1,2,25")
        self.assertEqual(c, 0, out)
        self.assertIn("VERDICT PASS", out.strip().splitlines()[-1])


if __name__ == "__main__":
    unittest.main()
