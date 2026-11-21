# -*- coding: utf-8 -*-
"""Tests of the hub's trigger of contracts/tools/bridge.py and of check 25 on a hub and its members (tasks/033).

Run from the repository root:  python -m unittest discover -s contracts/tests

Of two unrelated kinds on purpose (the person, 2026-11-11, and 2026-11-20 'Three engines, one hub'): the
accepted fixtures under contracts/examples/hub/, DFT→MD under one hub and a hub over three engines (a mode
solver, an FDTD engine and a heat-conduction engine). The person, 2026-11-20: 'Assign freely, carry on my word
(Recommended)', 'Ask once per question (Recommended)'.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import bridge  # noqa: E402

EXAMPLES = os.path.join(REPO, "contracts", "examples", "hub")
KINDS = [("dft-md", "h2-bond-hub", ["qe-h2-bond", "hoomd-h2-bond"]),
         ("photonic-heating", "waveguide-heating-hub", ["mpb-waveguide-mode", "meep-waveguide-absorption", "fenics-waveguide-heat"])]
HUB = {"by": "hub", "session": "test-hub-session"}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class HubTrigger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="hub-test-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def blank(self, kind, hub, members):
        """The hub's members.json, question and assignments, and each member's outbox: nothing carried yet."""
        dest = os.path.join(self.tmp, kind)
        os.makedirs(os.path.join(dest, hub))
        shutil.copyfile(os.path.join(EXAMPLES, kind, hub, "members.json"), os.path.join(dest, hub, "members.json"))
        for sub in ("question", "assignments"):
            shutil.copytree(os.path.join(EXAMPLES, kind, hub, sub), os.path.join(dest, hub, sub))
        for m in members:
            os.makedirs(os.path.join(dest, m))
            shutil.copytree(os.path.join(EXAMPLES, kind, m, "outbox"), os.path.join(dest, m, "outbox"))
        return dest

    def validate(self, folder):
        out = subprocess.run([sys.executable, os.path.join(REPO, "contracts", "validate.py"), folder, "--checks", "1,2,25"],
                             cwd=REPO, capture_output=True, text=True)
        return out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr

    def test_assignments_and_results_cross_on_the_hubs_trigger_and_pass_check_25(self):
        for kind, hub, members in KINDS:
            dest = self.blank(kind, hub, members)
            h = os.path.join(dest, hub)
            for m in members:
                env, payload = bridge.carry(os.path.join(h, "assignments", "as-%s-r1.json" % m), os.path.join(dest, m),
                                            "hub", HUB, trigger="hub")
                e = load(env)
                self.assertEqual((e["trigger"], e["released_by"], e["ran_by"]["by"], e["payload"]["card"]),
                                 ("hub", "hub", "hub", "assignment"))
                self.assertEqual(e["payload"]["origin"], "assignments/as-%s-r1.json" % m)
                env, payload = bridge.carry(os.path.join(dest, m, "outbox", "result-%s-r1.json" % m), h, "hub", HUB, trigger="hub")
                self.assertEqual(load(env)["payload"]["card"], "result")
            self.assertIn("VERDICT PASS", self.validate(dest), kind)

    def test_a_handover_is_refused_on_the_hubs_trigger(self):
        kind, hub, members = KINDS[1]
        dest = self.blank(kind, hub, members)
        meep = os.path.join(dest, "meep-waveguide-absorption")
        res = load(os.path.join(meep, "outbox", "result-meep-waveguide-absorption-r1.json"))
        ho = dict(res, card="handover", id="ho-absorbed-power-001", thread="thr-absorbed-power",
                  to={"agent": "fenics-waveguide-heat", "build": "fenics-waveguide-heat/0001"},
                  produced_by={"skill": "flux_absorbed_power@v1", "record": "runs/0001/record.json"}, what="the absorbed power")
        path = os.path.join(meep, "outbox", "handover-absorbed-power.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(ho, f)
        with self.assertRaisesRegex(bridge.Refused, "only on the person's word"):
            bridge.carry(path, os.path.join(dest, "fenics-waveguide-heat"), "hub", HUB, trigger="hub")

    def test_the_hub_releases_on_its_trigger_and_its_session_runs_the_tool(self):
        kind, hub, members = KINDS[0]
        dest = self.blank(kind, hub, members)
        a = os.path.join(dest, hub, "assignments", "as-qe-h2-bond-r1.json")
        with self.assertRaisesRegex(bridge.Refused, "the hub releases"):
            bridge.carry(a, os.path.join(dest, "qe-h2-bond"), "human", HUB, trigger="hub")
        with self.assertRaisesRegex(bridge.Refused, "hub's session"):
            bridge.carry(a, os.path.join(dest, "qe-h2-bond"), "hub", {"by": "person"}, trigger="hub")

    def test_an_assignment_goes_only_to_its_member_and_only_inside_an_agreed_list(self):
        for kind, hub, members in KINDS:
            dest = self.blank(kind, hub, members)
            h = os.path.join(dest, hub)
            a = os.path.join(h, "assignments", "as-%s-r1.json" % members[0])
            with self.assertRaisesRegex(bridge.Refused, "not the member's folder"):
                bridge.carry(a, os.path.join(dest, members[1]), "hub", HUB, trigger="hub")
            qdir = os.path.join(h, "question")
            for name in os.listdir(qdir):
                q = load(os.path.join(qdir, name))
                q.pop("agreed")
                with open(os.path.join(qdir, name), "w", encoding="utf-8") as f:
                    json.dump(q, f)
            with self.assertRaisesRegex(bridge.Refused, "agreed to"):
                bridge.carry(a, os.path.join(dest, members[0]), "hub", HUB, trigger="hub")

    def test_a_result_goes_on_the_hubs_trigger_only_to_its_hub(self):
        kind, hub, members = KINDS[1]
        dest = self.blank(kind, hub, members)
        r = os.path.join(dest, members[0], "outbox", "result-%s-r1.json" % members[0])
        with self.assertRaisesRegex(bridge.Refused, "to its hub only"):
            bridge.carry(r, os.path.join(dest, members[1]), "hub", HUB, trigger="hub")

    def test_a_later_round_within_the_agreed_list_crosses_without_a_new_agreement(self):
        """hub-3 (the person, 2026-11-21, 'Append to the question (Recommended)'): the second-round assignment names
        its list item and quotes the person's later words from the question's second revision."""
        for kind, hub, members in KINDS:
            dest = self.blank(kind, hub, members)
            h = os.path.join(dest, hub)
            r2 = [n for n in os.listdir(os.path.join(h, "assignments")) if n.endswith("-r2.json")]
            self.assertEqual(len(r2), 1, kind)
            a = load(os.path.join(h, "assignments", r2[0]))
            self.assertTrue(a.get("list_item") and a.get("quotes"))
            member = a["to"]["agent"]
            bridge.carry(os.path.join(h, "assignments", a["list_item"] + ".json"), os.path.join(dest, member), "hub", HUB, trigger="hub")
            env, _ = bridge.carry(os.path.join(h, "assignments", r2[0]), os.path.join(dest, member), "hub", HUB, trigger="hub")
            self.assertEqual(load(env)["round"], 2)


if __name__ == "__main__":
    unittest.main()
