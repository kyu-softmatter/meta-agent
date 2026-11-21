"""Template v33: a hand-over card carries each value's definition (meta_agent/failures.jsonl dftmd-13, dftmd-14; run
multiscale/20261120-8, where the receiving agent's session could not tell from its folder how the force constant it
received was defined).

src/handover.py write puts under each value's conditions.definition the meaning the skill's manifest gives the output it
is, and refuses an output with no meaning; receive writes the definition into the receipt's note, values prints it; the
Hand-overs text says to read it, and what the card's draft status and its grade are. On the two kinds of v32's test,
DFT→MD and rheometer→flow solver, carried with contracts/tools/bridge.py on temporary folders and judged by checks 1, 2
and 25.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import template as template_mod
from meta_agent.tests import test_template_v32 as v32

V32, V33 = template_mod.SOURCES["v32"], template_mod.SOURCES["v33"]


def meaning(skill, output):
    folder = os.path.join(v32.REPO, "meta_agent", "skills")
    for kind in os.listdir(folder):
        p = os.path.join(folder, kind, skill, "skill.json")
        if os.path.isfile(p):
            return next(o["meaning"] for o in cards.load_json(p)["outputs"] if o["name"] == output)
    raise LookupError(skill)


class EachValueCarriesItsDefinition(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-handover-v33-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.t = v32.TwoAgentsHandValuesOver("test_the_build_declares_what_it_gives_and_takes")
        self.t.tmp = self.tmp

    def pair(self, kind):
        k = v32.KINDS[kind]
        root = os.path.join(self.tmp, kind)
        giver = v32.compose(root, k["giver"], v32.giver_rows(k), [k["skill"]], template=V33)
        taker = v32.compose(root, k["taker"], v32.taker_rows(k), [], template=V33)
        return k, root, giver, taker

    def test_the_card_the_receipt_and_values_carry_the_definition(self):
        for kind in v32.KINDS:
            k, root, giver, taker = self.pair(kind)
            card = self.t.write_handover(k, giver)
            ho = cards.load_json(os.path.join(giver, card))
            for (name, output, _), n in zip(k["gives"], ho["numbers"]):
                d = n["conditions"]["definition"]
                self.assertIn(meaning(k["skill"], output), d, (kind, name))
                self.assertTrue(d.startswith("%s, the output %s of %s: " % (name, output, k["skill"])), (kind, d))
            code, out, err = v32.run([v32.BRIDGE, "carry", "--card", os.path.join(giver, card), "--to", taker,
                                      "--released-by", "human"], v32.REPO)
            self.assertEqual(code, 0, out + err)
            v32.run(["src/handover.py", "receive"], taker)
            code, out, err = v32.run(["src/handover.py", "values"], taker)
            values = json.loads(out)
            for row, (state, _) in k["expect"].items():
                name = next(n for r, n, _ in k["takes"] if r == row)
                output = next(o for g, o, _ in k["gives"] if g == name)
                rc = cards.load_json(os.path.join(taker, "received", "%s-r1-%s.json" % (k["thread"], row)))
                if state == "used":
                    self.assertIn("the hand-over defines it as: ", rc["note"], (kind, row))
                    self.assertIn(meaning(k["skill"], output), rc["note"], (kind, row))
                    self.assertIn(meaning(k["skill"], output), values[row]["definition"], (kind, row))
            code, out, err = v32.run([v32.VALIDATE, root, "--checks", "1,2,25"], v32.REPO)
            self.assertEqual(code, 0, out[-3000:] + err[-2000:])

    def test_who_ran_the_bridge_is_said_as_the_envelope_says_it(self):
        # the design role's ask 20261120-design-macbook-20261120-2-4 (tasks/032, bridge-2): the receiving session of run
        # multiscale/20261120-8 told the person a person had carried a card that a session carried
        k, root, giver, taker = self.pair("dft-md")
        card = self.t.write_handover(k, giver)
        v32.run([v32.BRIDGE, "carry", "--card", os.path.join(giver, card), "--to", taker, "--released-by", "human"], v32.REPO)
        env = cards.load_json(os.path.join(taker, "inbox", k["thread"], "r1_envelope.json"))
        if not isinstance(env.get("ran_by"), dict):
            self.skipTest("the bridge of this tree records no ran_by")
        said = "a session (%s) ran the bridge on the person's words: %s" % (env["ran_by"]["session"], env["ran_by"]["words"])
        code, out, err = v32.run(["src/handover.py", "receive"], taker)
        self.assertEqual({w["carried"] for w in json.loads(out)["written"]}, {said})
        code, out, err = v32.run(["src/handover.py", "values"], taker)
        self.assertEqual({v["carried"] for v in json.loads(out).values()}, {said})
        code, out, err = v32.run(["src/handover.py", "board"], taker)
        self.assertEqual([c["carried"] for c in json.loads(out)["carried"]], [said])
        rc = cards.load_json(os.path.join(taker, "received", "%s-r1-bond_k.json" % k["thread"]))
        self.assertIn(said, rc["note"])
        cards.write_json(os.path.join(taker, "inbox", k["thread"], "r1_envelope.json"),
                         {key: val for key, val in env.items() if key != "ran_by"})
        code, out, err = v32.run(["src/handover.py", "board"], taker)
        self.assertEqual([c["carried"] for c in json.loads(out)["carried"]], ["the envelope does not say who ran the bridge"])

    def test_an_output_with_no_meaning_is_not_handed_over(self):
        k, root, giver, taker = self.pair("rheometer-solver")
        p = os.path.join(giver, "skills", k["skill"], "skill.json")
        m = cards.load_json(p)
        for o in m["outputs"]:
            if o["name"] == "mean":
                o["meaning"] = ""
        cards.write_json(p, m)
        with self.assertRaises(AssertionError) as cm:
            self.t.write_handover(k, giver)
        self.assertIn("gives no meaning for its output mean", str(cm.exception))
        self.assertEqual([f for f in os.listdir(os.path.join(giver, "outbox")) if f.endswith(".json")], [])

    def test_the_text_says_what_the_definition_the_status_the_grade_and_the_carrier_are(self):
        k, root, giver, taker = self.pair("dft-md")
        text = cards.read_text(os.path.join(giver, "CLAUDE.md"))
        for words in ("`conditions.definition`", "Read the definition before you use a value", "status `draft`",
                      "the one the build derived for a computed value", "A converted value keeps no grade",
                      "the envelope's `ran_by` says which", "never write that the person carried a card a session carried"):
            self.assertIn(words, text)


class TheVersion(unittest.TestCase):
    def test_v33_is_the_latest_and_changes_one_script_its_text_and_its_card(self):
        self.assertEqual(template_mod.LATEST, "v33")
        self.assertEqual(sorted(set(cards.tree_files(V33)) ^ set(cards.tree_files(V32))), [])
        both = set(cards.tree_files(V32)) & set(cards.tree_files(V33))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V32, r)) != cards.sha256_file(os.path.join(V33, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/handover.py"])


if __name__ == "__main__":
    unittest.main()
