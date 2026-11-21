"""Template v32 and the builder: two built agents hand values to each other through cards (meta_agent/tasks/031; the
person, 2026-11-20, '둘로하고 각각 소통을 할 수 있게', 'Design a bridge now', 'Use if declared').

A build whose parameter rows declare a hand-over writes envelope/handovers.json and the registry it converts by, makes
outbox/, inbox/ and received/, and fills the Hand-overs section; src/handover.py writes a hand-over card from a skill's
record and the tool results it was read off, and receives what the bridge delivered, one receipt per value, used only
for a declared row converted through the unit skill, into an engine's own unit only through a scale a person confirmed.

Two unrelated kinds: a DFT agent that fits a bond and an MD agent that takes it into its own units through scales the
person confirmed; and a rheometer agent that hands a mean viscosity to a flow solver, which takes it into mPa.s and
holds the same value for a row in its engine's own unit, for which no scale is confirmed. The bridge is
contracts/tools/bridge.py, run here by the test on its own temporary folders, as the design role ran it on its fixtures:
in a bundle's life only a person starts it. Under v31 the same declaration is refused.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from meta_agent.src import cards
from meta_agent.src.build import bundle as bundle_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V31, V32 = template_mod.SOURCES["v31"], template_mod.SOURCES["v32"]
BRIDGE = os.path.join(REPO, "contracts", "tools", "bridge.py")
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
SCALE_EVIDENCE = ["the person's word for this test's bundle, as a request records it"]

# each kind: the giving agent, its skill, the skill's inputs from tool result fields, the results, the rows it gives;
# the taking agent and its rows (and scale rows)
KINDS = {
    "dft-md": {
        "giver": "dft-bond", "taker": "md-bond", "thread": "thr-bond",
        "skill": "harmonic_well_fit@v1", "record_inputs": {"points": "energy_curve"}, "from": "one_result",
        "results": [{"energy_curve": [[1.3, -2.298], [1.4, -2.3], [1.5, -2.298]],
                     "printed_conditions": {"xc": "PBE", "cutoff_Ry": 46.0}}],
        "gives": [("bond_force_constant", "force_constant", "Ry/bohr^2"), ("bond_rest_length", "rest_position", "bohr")],
        "accept": ["fitted"],
        "takes": [("bond_k", "bond_force_constant", "engine_energy/engine_length^2"),
                  ("bond_r0", "bond_rest_length", "engine_length")],
        "scales": [{"unit": "engine_energy", "stands_for": "eV", "state": "confirmed", "confirmed_by": "human"},
                   {"unit": "engine_length", "stands_for": "Angstrom", "state": "confirmed", "confirmed_by": "human"},
                   {"unit": "engine_energy/engine_length^2", "stands_for": "eV/Angstrom^2", "state": "confirmed",
                    "confirmed_by": "human", "rests_on": ["engine_energy", "engine_length"]}],
        "expect": {"bond_k": ("used", 0.4 * 778.4465524669654 / 16.02176634),
                   "bond_r0": ("used", 1.4 * 5.29177210544e-11 / 1e-10)},
    },
    "rheometer-solver": {
        "giver": "rheometer", "taker": "flow-solver", "thread": "thr-oil",
        "skill": "standard_error_of_independent_estimates@v2", "record_inputs": {"estimates": "viscosity"},
        "from": "each_result",
        "results": [{"viscosity": 0.98, "conditions": {"geometry": "cone and plate", "temperature_K": 298.15}},
                    {"viscosity": 1.0, "conditions": {"geometry": "cone and plate", "temperature_K": 298.15}},
                    {"viscosity": 1.02, "conditions": {"geometry": "cone and plate", "temperature_K": 298.15}}],
        "gives": [("oil_viscosity", "mean", "Pa.s")],
        "accept": None,
        "takes": [("eta_mpas", "oil_viscosity", "mPa.s"), ("eta_engine", "oil_viscosity", "engine_viscosity")],
        "scales": [],
        "expect": {"eta_mpas": ("used", 1.0 * 1000.0), "eta_engine": ("held", None)},
    },
}


def fill(name):
    return {"agent_name": name, "template": "agent@test", "rid": "req-%s" % name, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}


def giver_rows(k):
    cond = "printed_conditions" if "printed_conditions" in k["results"][0] else "conditions"
    rows = []
    for name, output, unit in k["gives"]:
        g = {"thread": k["thread"], "to_agent": k["taker"], "to_build": "%s/0001" % k["taker"], "skill": k["skill"],
             "output": output, "record_inputs": k["record_inputs"], "conditions_field": cond,
             "conditions": {"system": "the test's system"}, "what": "the values the other agent's model takes",
             "record_inputs_from": k["from"]}
        if k["accept"]:
            g["accept_states"] = k["accept"]
        rows.append({"name": name, "value": None, "unit": unit, "handover": {"gives": g}})
    return rows


def taker_rows(k, scales=None):
    rows = [{"name": row, "value": None, "unit": unit,
             "handover": {"takes": {"name": name, "thread": k["thread"], "from_agent": k["giver"]}}}
            for row, name, unit in k["takes"]]
    for s in k["scales"] if scales is None else scales:
        rows.append({"name": "scale_" + s["unit"].replace("/", "_per_").replace("^", ""),
                     "engine_scale": dict(s, evidence=SCALE_EVIDENCE)})
    return rows


def compose(tmp, name, rows, skills, template=V32):
    path = os.path.join(tmp, name, "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    bundle_mod.compose(template, path, fill(name), [], {"capabilities": []},
                       {"safety": {}, "parameters": {"rows": rows}}, [], [], [],
                       skills=catalogue_mod.take(skills) if skills else [], simulation=False)
    return path


def run(argv, cwd, stdin=None):
    if argv and argv[0] == BRIDGE and "carry" in argv:
        argv = list(argv) + who_ran()
    p = subprocess.run([sys.executable] + argv, cwd=cwd, input=stdin, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def who_ran():
    """What the bridge asks of whoever runs it, where it asks (tasks/032 has it say who ran a carry): this test runs it,
    a session's code on its own temporary folders, and no person's word is behind it but the test's."""
    p = subprocess.run([sys.executable, BRIDGE, "carry", "--help"], capture_output=True, text=True, encoding="utf-8")
    if "--ran-by" not in p.stdout:
        return []
    return ["--ran-by", "session", "--session", "meta_agent/tests/test_template_v32.py",
            "--words", "a unit test's carry on its own temporary folders"]


class TwoAgentsHandValuesOver(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-handover-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def pair(self, kind):
        k = KINDS[kind]
        root = os.path.join(self.tmp, kind)
        giver = compose(root, k["giver"], giver_rows(k), [k["skill"]])
        taker = compose(root, k["taker"], taker_rows(k), [])
        return k, root, giver, taker

    def write_handover(self, k, giver):
        runs = os.path.join(giver, "runs")
        os.makedirs(runs)
        files = []
        for i, r in enumerate(k["results"]):
            f = os.path.join(runs, "result-%d.json" % i)
            with open(f, "w", encoding="utf-8") as fh:
                json.dump(r, fh)
            files.append("runs/result-%d.json" % i)
        inputs = {inp: (k["results"][0][field] if k["from"] == "one_result" else [r[field] for r in k["results"]])
                  for inp, field in k["record_inputs"].items()}
        code, out, err = run(["src/run_skill.py", k["skill"], "--record", "runs/fit.json"], giver, json.dumps(inputs))
        self.assertEqual(code, 0, out + err)
        code, out, err = run(["src/handover.py", "write", "--record", "runs/fit.json", "--runs"] + files, giver)
        self.assertEqual(code, 0, out + err)
        return json.loads(out)["written"]

    def test_the_build_declares_what_it_gives_and_takes(self):
        for kind in KINDS:
            k, root, giver, taker = self.pair(kind)
            g = cards.load_json(os.path.join(giver, "envelope", "handovers.json"))
            t = cards.load_json(os.path.join(taker, "envelope", "handovers.json"))
            self.assertEqual(g["agent"], {"agent": k["giver"], "build": "%s/0001" % k["giver"]}, kind)
            self.assertEqual([n["name"] for n in g["gives"][0]["numbers"]], [x[0] for x in k["gives"]], kind)
            self.assertEqual({n["grade"] for n in g["gives"][0]["numbers"]}, {"E4"}, kind)
            self.assertEqual([x["row"] for x in t["takes"]], [x[0] for x in k["takes"]], kind)
            self.assertEqual(len(t["engine_scales"]), len(k["scales"]), kind)
            for b in (giver, taker):
                for sub in ("outbox", "inbox", "received"):
                    self.assertTrue(os.path.isdir(os.path.join(b, sub)), (kind, sub))
                self.assertTrue(os.path.isfile(os.path.join(b, "envelope", "units.json")), kind)
                self.assertTrue(os.path.isfile(os.path.join(b, "src", "handover.py")), kind)
                self.assertNotIn("{{", cards.read_text(os.path.join(b, "CLAUDE.md")), kind)
            self.assertTrue(os.path.isdir(os.path.join(taker, "skills", "unit_convert@v1")), kind)
            self.assertNotIn("engine_scale", json.dumps(cards.load_json(os.path.join(taker, "envelope", "parameters.json"))))

    def test_a_carried_handover_is_received_as_declared_and_judged_by_check_25(self):
        for kind in KINDS:
            k, root, giver, taker = self.pair(kind)
            card = self.write_handover(k, giver)
            ho = cards.load_json(os.path.join(giver, card))
            self.assertEqual([n["name"] for n in ho["numbers"]], [x[0] for x in k["gives"]], kind)
            self.assertTrue(all(n["conditions"]["runs"] == ["runs/result-%d.json" % i for i in range(len(k["results"]))]
                                for n in ho["numbers"]), kind)
            self.assertTrue(all("printed_conditions" not in n["conditions"] for n in ho["numbers"]), kind)
            code, out, err = run([BRIDGE, "carry", "--card", os.path.join(giver, card), "--to", taker,
                                  "--released-by", "human"], REPO)
            self.assertEqual(code, 0, out + err)
            code, out, err = run(["src/handover.py", "receive"], taker)
            got = {w["row"]: w for w in json.loads(out)["written"]}
            self.assertEqual(code, 4 if any(s == "held" for s, _ in k["expect"].values()) else 0, out + err)
            code, out, err = run(["src/handover.py", "values"], taker)
            values = json.loads(out)
            for row, (state, value) in k["expect"].items():
                self.assertEqual(got[row]["state"], state, (kind, row, got[row]))
                if state == "used":
                    self.assertAlmostEqual(values[row]["value"], value, places=9, msg=(kind, row))
                else:
                    self.assertEqual(got[row]["reason"], "engine_scale_not_confirmed", (kind, row))
                    self.assertIsNone(values[row]["value"], (kind, row))
            code, out, err = run([VALIDATE, root, "--checks", "1,2,25"], REPO)
            self.assertEqual(code, 0, out[-3000:] + err[-2000:])
            self.assertIn("VERDICT PASS", out.strip().splitlines()[-1], kind)

    def test_a_scale_not_confirmed_holds_the_value(self):
        k = KINDS["dft-md"]
        root = os.path.join(self.tmp, "inferred")
        scales = [dict(s, state="inferred") for s in k["scales"]]
        for s in scales:
            s.pop("confirmed_by")
        giver = compose(root, k["giver"], giver_rows(k), [k["skill"]])
        taker = compose(root, k["taker"], taker_rows(k, scales), [])
        card = self.write_handover(k, giver)
        run([BRIDGE, "carry", "--card", os.path.join(giver, card), "--to", taker, "--released-by", "human"], REPO)
        code, out, err = run(["src/handover.py", "receive"], taker)
        self.assertEqual(code, 4, out + err)
        self.assertEqual({w["row"]: w["reason"] for w in json.loads(out)["written"]},
                         {"bond_k": "engine_scale_not_confirmed", "bond_r0": "engine_scale_not_confirmed"})
        code, out, err = run([VALIDATE, root, "--checks", "1,2,25"], REPO)
        self.assertEqual(code, 0, out[-3000:])

    def test_a_value_no_row_declares_is_held(self):
        k = dict(KINDS["rheometer-solver"], takes=[("eta_mpas", "oil_viscosity", "mPa.s")])
        root = os.path.join(self.tmp, "undeclared")
        giver = compose(root, k["giver"], giver_rows(dict(k, gives=k["gives"] + [("oil_spread", "standard_deviation", "Pa.s")])),
                        [k["skill"]])
        taker = compose(root, k["taker"], taker_rows(k), [])
        card = self.write_handover(k, giver)
        run([BRIDGE, "carry", "--card", os.path.join(giver, card), "--to", taker, "--released-by", "human"], REPO)
        code, out, err = run(["src/handover.py", "receive"], taker)
        got = {w["name"]: (w["state"], w["reason"]) for w in json.loads(out)["written"]}
        self.assertEqual(got, {"oil_viscosity": ("used", None), "oil_spread": ("held", "undeclared")})
        code, out, err = run([VALIDATE, root, "--checks", "1,2,25"], REPO)
        self.assertEqual(code, 0, out[-3000:])

    def test_a_card_changed_on_the_way_is_refused_and_nothing_is_written(self):
        k, root, giver, taker = self.pair("dft-md")
        card = self.write_handover(k, giver)
        run([BRIDGE, "carry", "--card", os.path.join(giver, card), "--to", taker, "--released-by", "human"], REPO)
        copy = [f for f in os.listdir(os.path.join(taker, "inbox", k["thread"])) if not f.endswith("_envelope.json")][0]
        p = os.path.join(taker, "inbox", k["thread"], copy)
        with open(p, "a", encoding="utf-8") as f:
            f.write(" ")
        code, out, err = run(["src/handover.py", "receive"], taker)
        self.assertEqual(code, 3, out + err)
        self.assertIn("not the bytes", json.loads(out)["refused"])
        self.assertEqual([f for f in os.listdir(os.path.join(taker, "received")) if f.endswith(".json")], [])

    def test_a_record_not_taken_from_the_results_named_is_refused(self):
        k, root, giver, taker = self.pair("rheometer-solver")
        self.write_handover(k, giver)
        code, out, err = run(["src/handover.py", "write", "--record", "runs/fit.json", "--runs",
                              "runs/result-0.json", "runs/result-1.json"], giver)
        self.assertEqual(code, 3, out + err)
        self.assertIn("rest on runs other than these", json.loads(out)["refused"])

    def test_results_under_different_conditions_are_not_handed_over(self):
        k = dict(KINDS["rheometer-solver"])
        k["results"] = [dict(r) for r in k["results"]]
        k["results"][2] = dict(k["results"][2], conditions={"geometry": "cone and plate", "temperature_K": 308.15})
        root = os.path.join(self.tmp, "mixed")
        giver = compose(root, k["giver"], giver_rows(k), [k["skill"]])
        with self.assertRaises(AssertionError):
            self.write_handover(k, giver)
        self.assertEqual([f for f in os.listdir(os.path.join(giver, "outbox")) if f.endswith(".json")], [])

    def test_a_record_read_off_one_result_takes_exactly_one(self):
        k, root, giver, taker = self.pair("dft-md")
        self.write_handover(k, giver)
        code, out, err = run(["src/handover.py", "write", "--record", "runs/fit.json", "--runs",
                              "runs/result-0.json", "runs/result-0.json"], giver)
        self.assertEqual(code, 3, out + err)
        self.assertIn("read off one tool result", json.loads(out)["refused"])


class TheDeclarationIsChecked(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-handover-decl-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_v31_refuses_a_declared_handover(self):
        for kind, k in KINDS.items():
            with self.assertRaises(ValueError) as cm:
                compose(os.path.join(self.tmp, kind), k["giver"], giver_rows(k), [k["skill"]], template=V31)
            self.assertIn("handover_script", str(cm.exception), kind)

    def test_a_value_handed_over_in_an_engine_unit_is_refused(self):
        k = KINDS["dft-md"]
        rows = giver_rows(k)
        rows[1]["unit"] = "engine_length"
        with self.assertRaises(ValueError) as cm:
            compose(self.tmp, k["giver"], rows, [k["skill"]])
        self.assertIn("no si_factor", str(cm.exception))

    def test_a_confirmed_composite_scale_needs_confirmed_bases_whose_units_are_its_parts(self):
        k = KINDS["dft-md"]
        scales = [dict(s) for s in k["scales"]]
        scales[0] = dict(scales[0], state="inferred")
        scales[0].pop("confirmed_by")
        with self.assertRaises(ValueError) as cm:
            compose(os.path.join(self.tmp, "a"), k["taker"], taker_rows(k, scales), [])
        self.assertIn("confirmed while one it rests on is not", str(cm.exception))
        scales = [dict(s) for s in k["scales"]]
        scales[1] = dict(scales[1], stands_for="nm")
        with self.assertRaises(ValueError) as cm:
            compose(os.path.join(self.tmp, "b"), k["taker"], taker_rows(k, scales), [])
        self.assertIn("are not the units its bases stand for", str(cm.exception))

    def test_a_scale_confirmed_by_no_person_is_refused(self):
        k = KINDS["dft-md"]
        scales = [dict(s) for s in k["scales"]]
        scales[1] = dict(scales[1], confirmed_by="meta-macbook-20261120-3")
        with self.assertRaises(ValueError) as cm:
            compose(self.tmp, k["taker"], taker_rows(k, scales), [])
        self.assertIn("only a person confirms a scale", str(cm.exception))

    def test_a_bundle_with_no_declaration_is_as_before(self):
        path = compose(self.tmp, "plain", [{"name": "x", "value": None, "unit": "K"}], [])
        self.assertFalse(os.path.exists(os.path.join(path, "envelope", "handovers.json")))
        self.assertFalse(os.path.exists(os.path.join(path, "outbox")))
        self.assertIn("declares no hand-over", cards.read_text(os.path.join(path, "CLAUDE.md")))


class TheVersion(unittest.TestCase):
    def test_v32_is_the_latest_and_adds_the_script(self):
        self.assertIn("v32", template_mod.SOURCES)                  # v33 is the latest since a card carries each value's definition
        meta = cards.load_json(os.path.join(V32, "TEMPLATE.json"))
        self.assertEqual((meta["handover_script"], meta["unit_skill"]), ("src/handover.py", "unit_convert@v1"))
        added = sorted(set(cards.tree_files(V32)) - set(cards.tree_files(V31)))
        self.assertEqual(added, ["src/handover.py"])
        both = set(cards.tree_files(V31)) & set(cards.tree_files(V32))
        changed = sorted(r for r in both if cards.sha256_file(os.path.join(V31, r)) != cards.sha256_file(os.path.join(V32, r)))
        self.assertEqual(changed, [".claude/settings.json", "CLAUDE.md", "README.md", "TEMPLATE.json"])


if __name__ == "__main__":
    unittest.main()
