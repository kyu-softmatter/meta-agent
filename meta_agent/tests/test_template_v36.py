"""Template v36 and the builder (tasks/034): a hand-over read off a chain of skill records, the last of which takes a
value out of the engine's own unit through a scale a person confirmed.

- The build checks a chain's declaration: every step's skill is carried, every declared input comes from one place (a
  tool result's field, an earlier step's output, the registry's entry of a unit, or the unit a person confirmed an
  engine unit stands for), and the row is an output of a step; a composite scale whose unit names no parts is checked by
  dimension against its bases. Template v35 refuses a chain.
- src/handover.py write takes one record for each step with --step and refuses a missing step, a record of another
  skill, an input that is not what the declaration says, and a scale no person confirmed; each value's definition names
  every step back to the tool's fields.

Two unrelated kinds: an MD agent of a polymer model that hands a relaxation time and a viscosity, read off a stress
series through three skills and converted out of its engine's units, to a flow solver; and an MD agent of a diatomic
molecule that hands a mean bond length, converted out of its engine's length unit, back to a DFT agent in bohr. Each
tool is a contract alone: the test writes the results it would return, and no engine runs.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import json
import math
import os
import random
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
V35, V36 = template_mod.SOURCES["v35"], template_mod.SOURCES["v36"]
BRIDGE = os.path.join(REPO, "contracts", "tools", "bridge.py")
VALIDATE = os.path.join(REPO, "contracts", "validate.py")
EVIDENCE = ["the person's word for this test's bundle, as a request records it"]
CONVERT = "unit_convert@v2"


def scale(unit, stands_for, rests_on=None, state="confirmed"):
    s = {"unit": unit, "stands_for": stands_for, "state": state, "evidence": EVIDENCE}
    if state == "confirmed":
        s["confirmed_by"] = "human"
    if rests_on:
        s["rests_on"] = rests_on
    return s


def ar_series(seed, n, phi):
    rng = random.Random(seed)
    x, out = 0.0, []
    for _ in range(n):
        x = phi * x + rng.gauss(0.0, 1.0)
        out.append(x)
    return out


BASES = ["engine_length", "engine_energy", "engine_mass"]
KINDS = {
    "polymer-flow": {
        "giver": "md-polymer", "taker": "flow-solver", "thread": "thr-polymer", "tool": "run_polymer",
        "fields": {"stress_series": "the off-diagonal stress components the engine logged at equilibrium, one list each",
                   "sample_interval": "the engine time between two logged samples",
                   "volume": "the box's volume", "kT": "the thermal energy the thermostat held"},
        "result": {"stress_series": [ar_series(s, 3000, 0.9) for s in (1, 2, 3)], "sample_interval": 0.1, "volume": 50.0,
                   "kT": 1.0, "printed_conditions": {"model": "a test's dumbbells"}},
        "steps": [
            {"id": "acf", "skill": "autocorrelation_of_series@v2", "accept_states": ["computed"],
             "inputs": {"series": {"field": "stress_series"}, "interval": {"field": "sample_interval"}},
             "free": {"max_lag": 30}},
            {"id": "gk", "skill": "shear_relaxation_modulus_green_kubo@v2", "accept_states": ["computed"],
             "inputs": {"correlation": {"step": "acf", "output": "correlation"}, "volume": {"field": "volume"},
                        "thermal_energy": {"field": "kT"}}, "free": {"end": 3.0}},
            {"id": "fit", "skill": "exponential_decay_fit@v2", "accept_states": ["fitted"],
             "inputs": {"points": {"step": "gk", "output": "modulus"}}, "free": {"window": [0.0, 1.5]}},
            {"id": "lambda_si", "skill": CONVERT, "accept_states": ["converted"],
             "inputs": {"value": {"step": "fit", "output": "decay_time"}, "from_unit": {"registry": "engine_time"},
                        "to_unit": {"registry": "s"}, "from_stands_for": {"scale_of": "engine_time"}},
             "free": {"stands_for": None}},
            {"id": "eta_si", "skill": CONVERT, "accept_states": ["converted"],
             "inputs": {"value": {"step": "gk", "output": "viscosity"}, "from_unit": {"registry": "engine_viscosity"},
                        "to_unit": {"registry": "Pa.s"}, "from_stands_for": {"scale_of": "engine_viscosity"}},
             "free": {"stands_for": None}},
        ],
        "gives": [("relaxation_time", "lambda_si", "converted", "s"), ("polymer_viscosity", "eta_si", "converted", "Pa.s")],
        "giver_scales": [scale("engine_length", "m"), scale("engine_energy", "J"), scale("engine_mass", "kg"),
                         scale("engine_time", "s", BASES), scale("engine_viscosity", "Pa.s", BASES)],
        "takes": [("lambda", "relaxation_time", "s"), ("eta_p", "polymer_viscosity", "mPa.s")],
        "factor": {"lambda": 1.0, "eta_p": 1000.0},
    },
    "bond-dft": {
        "giver": "md-diatomic", "taker": "dft-diatomic", "thread": "thr-bond-back", "tool": "run_diatomic",
        "fields": {"bond_lengths": "the bond's length at each logged frame", "printed_conditions": "what the engine printed"},
        "result": {"bond_lengths": [0.741, 0.745, 0.739, 0.743, 0.742], "printed_conditions": {"molecule": "H2"}},
        "steps": [
            {"id": "mean", "skill": "standard_error_of_independent_estimates@v2",
             "inputs": {"estimates": {"field": "bond_lengths"}}, "free": {}},
            {"id": "to_bohr", "skill": CONVERT, "accept_states": ["converted"],
             "inputs": {"value": {"step": "mean", "output": "mean"}, "from_unit": {"registry": "engine_length"},
                        "to_unit": {"registry": "bohr"}, "from_stands_for": {"scale_of": "engine_length"}},
             "free": {"stands_for": None}},
        ],
        "gives": [("bond_length", "to_bohr", "converted", "bohr")],
        "giver_scales": [scale("engine_length", "Angstrom"), scale("engine_energy", "eV"), scale("engine_mass", "Da")],
        "takes": [("r_mean", "bond_length", "bohr")],
        "factor": {"r_mean": 1.0},
    },
}


def contract(k):
    props = {f: {"type": ["number", "array", "object"], "description": d} for f, d in k["fields"].items()}
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["tool"], "description": "a contract alone",
            "inputs": {"type": "object", "properties": {}, "required": []},
            "outputs": {"type": "object", "properties": props, "required": []},
            "errors": ["invalid_input"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "it touches nothing"}, "idempotent": True, "timeout_s": None}


def fill(name):
    return {"agent_name": name, "template": "agent@test", "rid": "req-%s" % name, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}


def giver_rows(k, steps=None, scales=None):
    steps = [{x: v for x, v in st.items() if x != "free"} for st in (steps or k["steps"])]
    rows = []
    for name, step, output, unit in k["gives"]:
        g = {"thread": k["thread"], "to_agent": k["taker"], "to_build": "%s/0001" % k["taker"], "steps": steps,
             "step": step, "output": output, "record_inputs_from": "one_result", "record_tool": k["tool"],
             "conditions_field": "printed_conditions", "conditions": {"system": "the test's system"},
             "what": "the values the other agent's model takes"}
        rows.append({"name": name, "value": None, "unit": unit, "handover": {"gives": g}})
    for s in k["giver_scales"] if scales is None else scales:
        rows.append({"name": "scale_" + s["unit"], "engine_scale": s})
    return rows


def taker_rows(k):
    return [{"name": row, "value": None, "unit": unit,
             "handover": {"takes": {"name": name, "thread": k["thread"], "from_agent": k["giver"]}}}
            for row, name, unit in k["takes"]]


def skills_of(k):
    return sorted({st["skill"] for st in k["steps"]})


def compose(tmp, name, rows, skills, template=V36, tools=()):
    path = os.path.join(tmp, name, "0001", "bundle")
    os.makedirs(os.path.dirname(path))
    bundle_mod.compose(template, path, fill(name),
                       [{"name": c["name"], "contract": c, "adapter_source": "def run(payload):\n    return {}\n",
                         "errors": []} for c in tools],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": rows}}, [], [], [],
                       skills=catalogue_mod.take(skills) if skills else [], simulation=False)
    return path


def run(argv, cwd, stdin=None):
    if argv and argv[0] == BRIDGE and "carry" in argv:
        argv = list(argv) + ["--ran-by", "session", "--session", "meta_agent/tests/test_template_v36.py",
                             "--words", "a unit test's carry on its own temporary folders"]
    p = subprocess.run([sys.executable] + argv, cwd=cwd, input=stdin, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout, p.stderr


def registry_entry(name):
    u = cards.load_json(os.path.join(REPO, "contracts", "units.json"))["units"][name]
    return {"name": name, "si_factor": u.get("si_factor"), "dim": u.get("dim") or {}}


class AChainIsHandedOver(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v36-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def pair(self, kind, scales=None):
        k = KINDS[kind]
        root = os.path.join(self.tmp, kind)
        giver = compose(root, k["giver"], giver_rows(k, scales=scales), skills_of(k), tools=[contract(k)])
        taker = compose(root, k["taker"], taker_rows(k), [])
        return k, root, giver, taker

    def run_steps(self, k, giver, upto=None, scales=None):
        """Run each step through the bundle's runner with --record, its declared inputs taken as declared; return the
        --step arguments."""
        os.makedirs(os.path.join(giver, "runs"), exist_ok=True)
        cards.write_json(os.path.join(giver, "runs", "result.json"), k["result"])
        by_scale = {s["unit"]: s["stands_for"] for s in (k["giver_scales"] if scales is None else scales)}
        outs, args = {}, []
        for st in k["steps"]:
            if upto is not None and st["id"] == upto:
                break
            inputs = dict(st["free"])
            for inp, src in st["inputs"].items():
                if "field" in src:
                    inputs[inp] = k["result"][src["field"]]
                elif "step" in src:
                    inputs[inp] = outs[src["step"]][src["output"]]
                elif "registry" in src:
                    inputs[inp] = registry_entry(src["registry"])
                else:
                    inputs[inp] = registry_entry(by_scale[src["scale_of"]])
            rec = "runs/%s.json" % st["id"]
            code, out, err = run(["src/run_skill.py", st["skill"], "--record", rec], giver, json.dumps(inputs))
            self.assertEqual(code, 0, (st["id"], out[-2000:], err[-2000:]))
            outs[st["id"]] = cards.load_json(os.path.join(giver, rec))["outputs"]
            args += ["--step", st["id"], rec]
        return args, outs

    def test_the_build_declares_the_chain_and_its_scales(self):
        for kind, k in KINDS.items():
            _, root, giver, taker = self.pair(kind)
            g = cards.load_json(os.path.join(giver, "envelope", "handovers.json"))["gives"][0]
            self.assertEqual([st["id"] for st in g["steps"]], [st["id"] for st in k["steps"]], kind)
            self.assertNotIn("skill", g, kind)
            self.assertEqual([(n["name"], n["step"]) for n in g["numbers"]], [(x[0], x[1]) for x in k["gives"]], kind)
            first = g["steps"][0]["fields"]
            self.assertTrue(first and all(f["tool"] == k["tool"] for f in first.values()), kind)
            text = cards.read_text(os.path.join(giver, "CLAUDE.md"))
            self.assertIn("--step <step> <record>", text, kind)
            self.assertIn("`%s`: `%s`" % (k["steps"][0]["id"], k["steps"][0]["skill"]), text, kind)
            self.assertNotIn("{{", text, kind)
            self.assertTrue(os.path.isdir(os.path.join(taker, "skills", CONVERT)), kind)

    def test_a_chain_is_written_carried_received_and_judged_by_check_25(self):
        for kind, k in KINDS.items():
            _, root, giver, taker = self.pair(kind)
            args, outs = self.run_steps(k, giver)
            code, out, err = run(["src/handover.py", "write"] + args + ["--runs", "runs/result.json"], giver)
            self.assertEqual(code, 0, (kind, out[-3000:], err[-2000:]))
            rel = json.loads(out)["written"]
            ho = cards.load_json(os.path.join(giver, rel))
            self.assertEqual([c["step"] for c in ho["produced_by"]["chain"]], [st["id"] for st in k["steps"]], kind)
            for name, step, output, unit in k["gives"]:
                n = next(x for x in ho["numbers"] if x["name"] == name)
                self.assertEqual((n["value"], n["unit"], n["grade"]), (outs[step][output], unit, "E4"), (kind, name))
                d = n["conditions"]["definition"]
                for st in k["steps"]:
                    if st["id"] == step:
                        self.assertIn("(step %s)" % st["id"], d, (kind, name))
                self.assertIn("the field %s of the result of %s" % (k["steps"][0]["inputs"][next(iter(sorted(
                    i for i in k["steps"][0]["inputs"] if "field" in k["steps"][0]["inputs"][i])))]["field"], k["tool"]),
                    d, (kind, name))
                self.assertIn("the unit a person confirmed", d, (kind, name))
            code, out, err = run([BRIDGE, "carry", "--card", os.path.join(giver, rel), "--to", taker,
                                  "--released-by", "human"], REPO)
            self.assertEqual(code, 0, out + err)
            code, out, err = run(["src/handover.py", "receive"], taker)
            self.assertEqual(code, 0, (kind, out, err))
            values = json.loads(run(["src/handover.py", "values"], taker)[1])
            for row, name, unit in k["takes"]:
                step = next(x[1] for x in k["gives"] if x[0] == name)
                self.assertTrue(math.isclose(values[row]["value"], outs[step]["converted"] * k["factor"][row],
                                             rel_tol=1e-12), (kind, row, values[row]))
            code, out, err = run([VALIDATE, root, "--checks", "1,2,25"], REPO)
            self.assertEqual(code, 0, out[-3000:] + err[-2000:])
            self.assertIn("VERDICT PASS", out.strip().splitlines()[-1], kind)

    def test_a_scale_no_person_confirmed_keeps_the_value_in_the_engine(self):
        for kind, k in KINDS.items():
            scales = [dict(s, state="inferred") for s in k["giver_scales"]]
            for s in scales:
                s.pop("confirmed_by", None)
            _, root, giver, taker = self.pair(kind, scales)
            args, _ = self.run_steps(k, giver, scales=scales)
            code, out, err = run(["src/handover.py", "write"] + args + ["--runs", "runs/result.json"], giver)
            self.assertEqual(code, 3, (kind, out, err))
            self.assertIn("which no person confirmed", json.loads(out)["refused"], kind)
            self.assertEqual([f for f in os.listdir(os.path.join(giver, "outbox")) if f.endswith(".json")], [], kind)

    def test_a_missing_step_another_skill_or_an_input_from_elsewhere_is_refused(self):
        k = KINDS["bond-dft"]
        _, root, giver, taker = self.pair("bond-dft")
        args, outs = self.run_steps(k, giver)
        code, out, _ = run(["src/handover.py", "write"] + args[:3] + ["--runs", "runs/result.json"], giver)
        self.assertEqual(code, 3, out)
        self.assertIn("no record was named for the step(s) to_bohr", json.loads(out)["refused"])
        code, out, _ = run(["src/handover.py", "write", "--step", "mean", "runs/to_bohr.json", "--step", "to_bohr",
                            "runs/to_bohr.json", "--runs", "runs/result.json"], giver)
        self.assertEqual(code, 3, out)
        self.assertIn("is not a run of standard_error_of_independent_estimates@v2", json.loads(out)["refused"])
        inputs = {"value": outs["mean"]["mean"] + 0.01, "from_unit": registry_entry("engine_length"),
                  "to_unit": registry_entry("bohr"), "stands_for": None, "from_stands_for": registry_entry("Angstrom")}
        code, out, err = run(["src/run_skill.py", CONVERT, "--record", "runs/other.json"], giver, json.dumps(inputs))
        self.assertEqual(code, 0, out + err)
        code, out, _ = run(["src/handover.py", "write", "--step", "mean", "runs/mean.json", "--step", "to_bohr",
                            "runs/other.json", "--runs", "runs/result.json"], giver)
        self.assertEqual(code, 3, out)
        self.assertIn("the step to_bohr's input value is not the output mean of the step mean's record",
                      json.loads(out)["refused"])
        code, out, _ = run(["src/handover.py", "write", "--record", "runs/mean.json", "--runs", "runs/result.json"], giver)
        self.assertEqual(code, 3, out)
        self.assertIn("name each step's record with --step", json.loads(out)["refused"])
        self.assertEqual([f for f in os.listdir(os.path.join(giver, "outbox")) if f.endswith(".json")], [])


class TheChainIsCheckedWhenBuilt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v36-decl-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def refused(self, kind, rows, words, template=V36):
        k = KINDS[kind]
        sub = os.path.join(self.tmp, str(len(os.listdir(self.tmp))))
        with self.assertRaises(ValueError) as cm:
            compose(sub, k["giver"], rows, skills_of(k), template=template, tools=[contract(k)])
        self.assertIn(words, str(cm.exception))

    def test_v35_refuses_a_chain(self):
        for kind, k in KINDS.items():
            self.refused(kind, giver_rows(k), "needs v36 or later", template=V35)

    def test_an_input_from_a_later_step_or_nowhere_is_refused(self):
        k = KINDS["polymer-flow"]
        steps = json.loads(json.dumps(k["steps"]))
        steps[1]["inputs"]["correlation"] = {"step": "fit", "output": "decay_time"}
        self.refused("polymer-flow", giver_rows(k, steps), "which is not a step before it")
        steps = json.loads(json.dumps(k["steps"]))
        steps[0]["inputs"]["max_lag"] = {"value": 30}
        self.refused("polymer-flow", giver_rows(k, steps), "comes from none, or more than one")
        steps = json.loads(json.dumps(k["steps"]))
        steps[3]["inputs"]["from_stands_for"] = {"scale_of": "s"}
        self.refused("polymer-flow", giver_rows(k, steps), "which is not an engine's own unit")

    def test_a_row_must_be_an_output_of_a_step(self):
        k = KINDS["bond-dft"]
        rows = giver_rows(k)
        rows[0]["handover"]["gives"]["output"] = "standard_error"
        self.refused("bond-dft", rows, "which its skill does not give")

    def test_a_composite_scale_its_bases_do_not_make_is_refused(self):
        k = KINDS["polymer-flow"]
        scales = [dict(s) for s in k["giver_scales"]]
        scales[3] = dict(scales[3], stands_for="ms")
        self.refused("polymer-flow", giver_rows(k, scales=scales), "the bases make an si_factor of 1.0")
        scales = [dict(s) for s in k["giver_scales"]]
        scales[4] = dict(scales[4], rests_on=["engine_length", "engine_mass"])
        self.refused("polymer-flow", giver_rows(k, scales=scales), "is no product of its bases' dimensions")

    def test_a_handed_value_still_leaves_the_engine_unit_before_the_card(self):
        k = KINDS["bond-dft"]
        rows = giver_rows(k)
        rows[0]["unit"] = "engine_length"
        self.refused("bond-dft", rows, "no si_factor")


class TheVersion(unittest.TestCase):
    def test_v36_is_the_latest_and_changes_two_scripts_and_the_text(self):
        self.assertIn("v36", template_mod.SOURCES)                  # v37 is the latest since a result quotes a series
        meta = cards.load_json(os.path.join(V36, "TEMPLATE.json"))
        self.assertEqual((meta["version"], meta["unit_skill"]), ("v36", CONVERT))
        self.assertEqual(sorted(cards.tree_files(V36)), sorted(cards.tree_files(V35)))
        changed = sorted(r for r in cards.tree_files(V35)
                         if cards.sha256_file(os.path.join(V35, r)) != cards.sha256_file(os.path.join(V36, r)))
        self.assertEqual(changed, ["CLAUDE.md", "TEMPLATE.json", "src/handover.py", "src/validate_tasks.py"])


if __name__ == "__main__":
    unittest.main()
