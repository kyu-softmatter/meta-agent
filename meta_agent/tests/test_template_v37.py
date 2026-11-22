"""Template v37 and the builder (tasks/034, after its first test standing alone, run multiscale/20261121-1; rheo-4, rheo-5
and bd-3 of meta_agent/failures.jsonl).

- rheo-4: the build declares in envelope/results.json each tool output that is a series (an array of numbers with a unit,
  or of arrays of prefixItems each a number with a unit, a title and a description), and refuses one declared short of
  that; src/handover.py result quotes such a field whole, point by point, with the name and unit of each part, under
  series; src/run_tool.py checks an array output item by item.
- rheo-5: the build gives each input of a skill the request names that no row, no tool output field, no hand-over, no
  decision and no analysis gives a row with no value, the person's; a row may say it gives an input of another name
  (gives_inputs); the build refuses an input whose unit the registry lacks, and one name taken in two dimensions.
- bd-3: src/run_tool.py --out keeps what it printed in a new .json file under runs/, whole, and leaves no file where the
  call failed; src/handover.py result refuses an empty kept output, saying what to do, where v36 stopped on a traceback.

Two unrelated kinds for each: a flow solver whose tool returns the centreline velocity of a start-up flow as pairs of a
time and a velocity, and whose analytical skill takes inputs no row gives; and a photonic mode solver whose tool returns
a transmission spectrum as pairs of a wavelength and a transmittance and a list of effective indices, beside an MD agent
whose oscillation period and diffusive regime take inputs the rows give under other names or not at all. Each tool is a
mock adapter that returns its output and starts no engine.

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
from meta_agent.src.build import skill_inputs as skill_inputs_mod
from meta_agent.src.build import template as template_mod
from meta_agent.src.skills import catalogue as catalogue_mod
from meta_agent.tests.test_template_v35 import card, run

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V36, V37 = template_mod.SOURCES["v36"], template_mod.SOURCES["v37"]
BRIDGE = os.path.join(REPO, "contracts", "tools", "bridge.py")
VALIDATE = os.path.join(REPO, "contracts", "validate.py")


def part(unit, title, description):
    return {"type": "number", "unit": unit, "title": title, "description": description}


def pairs(a, b):
    return {"type": "array", "prefixItems": [a, b], "items": False}


KINDS = {
    "flow": {
        "tool": "run_channel",
        "outputs": {
            "centreline_velocity": {"type": "array", "description": "the centreline velocity the probe wrote",
                                    "items": pairs(part("s", "t", "the time since the gradient was applied"),
                                                   part("m/s", "u", "the streamwise velocity at the centreline"))},
            "probe_location": {"type": "array", "description": "the probe's point, in metres"},
            "run_dir": {"type": "string", "description": "the run's folder"}},
        "result": {"centreline_velocity": [[0.0, 0.0], [0.5, 0.012], [1.0, 0.019]], "probe_location": [0.0, 0.0, 0.0],
                   "run_dir": "runs/cfd/1"},
        "series": {"centreline_velocity": [("t", "s"), ("u", "m/s")]},
        "skills": ["oldroyd_b_startup_channel_velocity@v1"],
        "rows": ["half_width", "density", "solvent_viscosity", "polymer_viscosity", "relaxation_time", "driving"],
        "added": [("position", "1"), ("times", "1"), ("terms", "count")],
    },
    "photonic": {
        "tool": "run_modes",
        "outputs": {
            "transmission": {"type": "array", "description": "the transmission spectrum the solver wrote",
                             "items": pairs(part("nm", "wavelength", "the vacuum wavelength"),
                                            part("1", "transmittance", "the transmitted fraction of the power"))},
            "effective_indices": {"type": "array", "description": "the guided modes' effective indices",
                                  "items": {"type": "number", "unit": "1", "title": "n_eff",
                                            "description": "a guided mode's effective index"}},
            "temperature": {"type": "number", "unit": "K", "description": "the device's temperature the run held"}},
        "result": {"transmission": [[1500.0, 0.91], [1550.0, 0.95], [1600.0, 0.89]], "effective_indices": [2.41, 1.98],
                   "temperature": 300.0},
        "series": {"transmission": [("wavelength", "nm"), ("transmittance", "1")], "effective_indices": [("n_eff", "1")]},
        # an MD agent's skills beside the photonic tool: the temperature is a tool field, a mass a row, the force constant
        # nothing; the diffusive regime's window is the row msd_window under another name, its tolerance nothing
        "skills": ["thermal_energy@v1", "harmonic_oscillation_period@v1", "diffusive_regime_from_msd@v2"],
        "rows": ["mass_a", "mass_b", "lags", "msd"],
        "extra_rows": [{"name": "msd_window", "value": None, "unit": "count", "note": "the person's",
                        "gives_inputs": [{"skill": "diffusive_regime_from_msd@v2", "input": "window"}]}],
        "added": [("force_constant", "engine_energy/engine_length^2"), ("tolerance", "1")],
    },
}


def contract(k):
    return {"artifact": "tool_contract", "schema_version": "0.1", "name": k["tool"], "description": "a mock that returns its output",
            "inputs": {"type": "object", "properties": {}, "required": []},
            "outputs": {"type": "object", "properties": k["outputs"], "required": sorted(k["outputs"])},
            "errors": ["invalid_input", "execution_failure"], "side_effects": "none",
            "safety_gate": {"required": False, "place": "a mock touches nothing"}, "idempotent": True, "timeout_s": None}


def compose(root, name, kind, template=V37, build_id="0001", adapter_result=None, outputs=None, rows=None, skills=None):
    k = dict(KINDS[kind])
    if outputs is not None:
        k["outputs"] = outputs
    path = os.path.join(root, name, build_id, "bundle")
    os.makedirs(os.path.dirname(path))
    refs = k["skills"] if skills is None else skills
    rows = rows if rows is not None else [{"name": n, "value": None, "unit": "1", "note": "the person's"} for n in k["rows"]] \
        + k.get("extra_rows", [])
    fill = {"agent_name": name, "template": "agent@test", "rid": "req-%s" % name, "purpose": "p", "science_task": "t",
            "tools_section": bundle_mod.tools_section([contract(k)]), "must_not": bundle_mod.must_not_section([]),
            "skills_section": bundle_mod.skills_section([]), "seat_form": "x-<machine>-<YYYYMMDD>-<n>"}
    sci = {"id": "sci-1", "name": "held", "call": {"tool": k["tool"], "input": {}}, "measure": {},
           "reference": {"kind": "source", "ref": "none yet"}, "held": {"reason": "no tolerance", "needs": "one"},
           "tolerance": None, "expected_verdict": "not_run"}
    if adapter_result is None:
        adapter = "def run(payload):\n    return %r\n" % (k["result"],)
    else:
        adapter = adapter_result
    bundle_mod.compose(template, path, fill, [{"name": k["tool"], "contract": contract(k), "adapter_source": adapter, "errors": []}],
                       {"capabilities": []}, {"safety": {}, "parameters": {"rows": rows}}, [], [sci], [],
                       skills=catalogue_mod.take(refs), simulation=False, tool_kind="engine")
    return path


def hub_beside(tmp, member, build):
    hub = os.path.join(tmp, "test-hub")
    for d in ("question", "assignments", "inbox"):
        os.makedirs(os.path.join(hub, d))
    me = {"agent": "test-hub", "build": "test-hub/0001"}
    cards.write_json(os.path.join(hub, "members.json"), card(
        "hub_members", "members-test-hub", "builder", hub=me,
        members=[{"agent": member, "build": build, "folder": "../%s" % build.replace("/", "-"),
                  "build_card_sha256": "sha256:" + "0" * 64},
                 {"agent": "other-agent", "build": "other-agent/0001", "folder": "../other-agent-0001",
                  "build_card_sha256": "sha256:" + "0" * 64}]))
    cards.write_json(os.path.join(hub, "question", "q-test-hub-001.json"), card(
        "hub_question", "q-test-hub-001", "test-hub", question="a test question", done_when=[{"id": "dw-1", "what": "x"}],
        assignments=["as-001-%s-r1" % member], agreed={"words": "a test's words", "at": "2026-11-22T12:00:00Z"}))
    cards.write_json(os.path.join(hub, "assignments", "as-001-%s-r1.json" % member), card(
        "assignment", "as-001-%s-r1" % member, "test-hub", thread="thr-test-hub-%s" % member, round=1,
        question="q-test-hub-001", **{"from": me}, to={"agent": member, "build": build},
        asks="report the series your tool gives", answers_items=["dw-1"], returns=[{"card": "result", "to": me}],
        done_when="the series, or what holds it"))
    return hub


def carried(tmp, kind, template=V37):
    """A member built from `template`, beside a hub whose assignment has been carried into it; (member, envelope)."""
    name = "agent-" + kind
    built = compose(os.path.join(tmp, "builds"), name, kind, template=template)
    hub = hub_beside(tmp, name, name + "/0001")
    member = os.path.join(tmp, name + "-0001")
    shutil.copytree(built, member)
    c, out = run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card", os.path.join(hub, "assignments", "as-001-%s-r1.json" % name),
                 "--to", member, "--released-by", "hub", "--ran-by", "hub", "--session", "test-session")
    assert c == 0, out
    c, out = run(member, "src/handover.py", "receive")
    assert c == 0, out
    env = json.loads(run(member, "src/handover.py", "assignments")[1])["assignments"][0]["envelope"]
    return member, env, hub


class AResultQuotesASeries(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v37-series-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_build_declares_each_series_with_its_parts(self):
        for kind, k in KINDS.items():
            path = compose(os.path.join(self.tmp, kind, "builds"), "agent-" + kind, kind)
            d = cards.load_json(os.path.join(path, "envelope", "results.json"))
            got = {r["field"]: [(p["name"], p["unit"]) for p in r["parts"]] for r in d["reports"] if r.get("kind") == "series"}
            self.assertEqual(got, k["series"], kind)
            self.assertNotIn("probe_location", {r["field"] for r in d["reports"]})            # an array with no unit
            old = compose(os.path.join(self.tmp, kind, "old"), "agent-" + kind, kind, template=V36)
            self.assertFalse(any(r.get("kind") == "series" for r in cards.load_json(
                os.path.join(old, "envelope", "results.json"))["reports"]), kind)       # v36 declared none

    def test_a_series_declared_short_of_its_parts_is_refused(self):
        for kind, k in KINDS.items():
            outputs = json.loads(json.dumps(k["outputs"]))
            field = sorted(f for f in k["series"] if len(k["series"][f]) > 1)[0]
            del outputs[field]["items"]["prefixItems"][1]["title"]
            with self.assertRaises(ValueError) as e:
                compose(os.path.join(self.tmp, kind, "short"), "agent-" + kind, kind, outputs=outputs)
            self.assertIn(field, str(e.exception))
            self.assertFalse(os.path.exists(os.path.join(self.tmp, kind, "short", "agent-" + kind, "0001", "bundle")))
        outputs = json.loads(json.dumps(KINDS["photonic"]["outputs"]))
        del outputs["effective_indices"]["items"]["description"]
        del outputs["effective_indices"]["description"]
        with self.assertRaises(ValueError) as e:
            compose(os.path.join(self.tmp, "one-part"), "agent-photonic", "photonic", outputs=outputs)
        self.assertIn("effective_indices", str(e.exception))         # a part says what it is (common series, 69f329b)

    def test_result_quotes_the_series_point_by_point(self):
        for kind, k in KINDS.items():
            member, env, _ = carried(os.path.join(self.tmp, kind), kind)
            c, out = run(member, "src/run_tool.py", k["tool"], "--out", "runs/r1/out.json", stdin=b"{}")
            self.assertEqual(c, 0, out)
            argv = ["src/handover.py", "result", "--assignment", env]
            for field in sorted(k["series"]):
                argv += ["--report", k["tool"], field, "runs/r1/out.json"]
            c, out = run(member, *argv)
            self.assertEqual(c, 0, out)
            res = json.loads(out)["card"]
            self.assertEqual(res["state"], "answered")
            for s in res["series"]:
                self.assertEqual([(p["name"], p["unit"]) for p in s["parts"]], k["series"][s["name"]], kind)
                want = k["result"][s["name"]]
                self.assertEqual(s["points"], [p if isinstance(p, list) else [p] for p in want], kind)
                self.assertEqual((s["grade"], s["value_kind"]), ("E4", "computed"))
            self.assertEqual(res["numbers"], [])

    def test_v36_cannot_quote_the_series(self):
        for kind, k in KINDS.items():
            member, env, _ = carried(os.path.join(self.tmp, kind), kind, template=V36)
            c, out = run(member, "src/run_tool.py", k["tool"], stdin=b"{}")
            os.makedirs(os.path.join(member, "runs"))
            with open(os.path.join(member, "runs", "out.json"), "w") as f:
                f.write(out)
            field = sorted(k["series"])[0]
            c, out = run(member, "src/handover.py", "result", "--assignment", env, "--report", k["tool"], field, "runs/out.json")
            self.assertEqual(c, 3, out)
            self.assertIn("declares no report", out)

    def test_the_folder_passes_checks_1_2_25_with_a_series_carried_back(self):
        for kind, k in KINDS.items():
            tmp = os.path.join(self.tmp, kind)
            member, env, hub = carried(tmp, kind)
            run(member, "src/run_tool.py", k["tool"], "--out", "runs/out.json", stdin=b"{}")
            field = sorted(k["series"])[0]
            c, out = run(member, "src/handover.py", "result", "--assignment", env, "--report", k["tool"], field, "runs/out.json")
            self.assertEqual(c, 0, out)
            c, out = run(REPO, BRIDGE, "carry", "--trigger", "hub", "--card", os.path.join(member, json.loads(out)["written"]),
                         "--to", hub, "--released-by", "hub", "--ran-by", "hub", "--session", "test-session")
            self.assertEqual(c, 0, out)
            shutil.rmtree(os.path.join(tmp, "builds"))
            c, out = run(REPO, VALIDATE, tmp, "--checks", "1,2,25")
            self.assertEqual(c, 0, out)


class TheRunnerKeepsWholeOutputs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v37-out-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_out_writes_a_new_file_whole_and_refuses_one_that_exists_or_lies_outside_runs(self):
        for kind, k in KINDS.items():
            path = compose(os.path.join(self.tmp, kind), "agent-" + kind, kind)
            c, out = run(path, "src/run_tool.py", k["tool"], "--out", "runs/a/out.json", stdin=b"{}")
            self.assertEqual(c, 0, out)
            self.assertEqual(cards.load_json(os.path.join(path, "runs", "a", "out.json")), k["result"])
            self.assertEqual(os.listdir(os.path.join(path, "runs", "a")), ["out.json"])           # no part file left
            before = cards.sha256_file(os.path.join(path, "runs", "a", "out.json"))
            c, out = run(path, "src/run_tool.py", k["tool"], "--out", "runs/a/out.json", stdin=b"{}")
            self.assertEqual(c, 1, out)
            self.assertEqual(cards.sha256_file(os.path.join(path, "runs", "a", "out.json")), before)
            for bad in ("out.json", "runs/out.txt", "../runs/out.json"):
                c, out = run(path, "src/run_tool.py", k["tool"], "--out", bad, stdin=b"{}")
                self.assertEqual(c, 1, (bad, out))

    def test_a_call_that_fails_leaves_no_file_and_an_empty_one_is_refused_with_what_to_do(self):
        for kind, k in KINDS.items():
            member, env, _ = carried(os.path.join(self.tmp, kind), kind)
            # an adapter whose call dies: --out leaves nothing behind
            os.chmod(os.path.join(member, "tools", k["tool"], "adapter.py"), 0o644)
            with open(os.path.join(member, "tools", k["tool"], "adapter.py"), "w") as f:
                f.write("def run(payload):\n    raise RuntimeError('cut short')\n")
            c, out = run(member, "src/run_tool.py", k["tool"], "--out", "runs/r2/out.json", stdin=b"{}")
            self.assertNotEqual(c, 0, out)
            self.assertFalse(os.path.exists(os.path.join(member, "runs", "r2", "out.json")))
            # what a shell redirect left in bd-3: an empty file the result is refused on, by name
            os.makedirs(os.path.join(member, "runs", "r2"), exist_ok=True)
            open(os.path.join(member, "runs", "r2", "lost.json"), "w").close()
            c, out = run(member, "src/handover.py", "result", "--assignment", env, "--report", k["tool"],
                         sorted(k["series"])[0], "runs/r2/lost.json")
            self.assertEqual(c, 3, out)
            self.assertIn("--out", json.loads(out)["refused"])

    def test_an_output_whose_series_breaks_the_contract_is_an_error(self):
        for kind, k in KINDS.items():
            bad = json.loads(json.dumps(k["result"]))
            field = sorted(f for f in k["series"] if len(k["series"][f]) > 1)[0]
            bad[field][1] = bad[field][1] + [7.0]
            path = compose(os.path.join(self.tmp, kind, "bad"), "agent-" + kind, kind,
                           adapter_result="def run(payload):\n    return %r\n" % (bad,))
            c, out = run(path, "src/run_tool.py", k["tool"], stdin=b"{}")
            self.assertEqual(c, 0, out)
            e = json.loads(out)
            self.assertEqual(e.get("artifact"), "error_contract", out)
            self.assertIn("%s[1]" % field, e["message"])


class EveryInputOfANamedSkillHasARow(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ma-v37-rows-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_the_build_gives_the_person_a_row_for_each_input_nothing_gives(self):
        for kind, k in KINDS.items():
            path = compose(os.path.join(self.tmp, kind), "agent-" + kind, kind)
            rows = cards.load_json(os.path.join(path, "envelope", "parameters.json"))["rows"]
            added = [(r["name"], r["unit"]) for r in rows if r.get("for_skill_inputs")]
            self.assertEqual(added, k["added"], kind)
            for r in rows:
                if r.get("for_skill_inputs"):
                    self.assertIsNone(r["value"])
                    self.assertNotIn("chosen_by", r)
                    self.assertIn(r["for_skill_inputs"][0]["skill"], r["note"])
            old = compose(os.path.join(self.tmp, kind, "old"), "agent-" + kind, kind, template=V36)
            self.assertFalse(any(r.get("for_skill_inputs") for r in cards.load_json(
                os.path.join(old, "envelope", "parameters.json"))["rows"]), kind)     # v36 gave none (rheo-5)

    def test_a_row_naming_an_input_that_no_skill_takes_is_refused(self):
        rows = [{"name": "msd_window", "value": None, "unit": "count",
                 "gives_inputs": [{"skill": "diffusive_regime_from_msd@v2", "input": "span"}]}]
        with self.assertRaises(ValueError) as e:
            compose(os.path.join(self.tmp, "x"), "agent-x", "photonic", rows=rows)
        self.assertIn("msd_window", str(e.exception))

    def test_an_input_no_row_can_hold_is_refused(self):
        units = {"ref": "made_up@v1", "inputs": [{"name": "dose", "unit": "furlong", "meaning": "a dose"}]}
        two = [{"ref": "a@v1", "inputs": [{"name": "size", "unit": "engine_length", "meaning": "a size"}]},
               {"ref": "b@v1", "inputs": [{"name": "size", "unit": "engine_time", "meaning": "a time"}]}]
        same = [{"ref": "a@v1", "inputs": [{"name": "size", "unit": "engine_length", "meaning": "a size"}]},
                {"ref": "b@v1", "inputs": [{"name": "size", "unit": "engine_length", "meaning": "a size too"}]}]
        meta = cards.load_json(os.path.join(V37, "TEMPLATE.json"))
        rows, faults = skill_inputs_mod.rows_for(["made_up@v1"], [units], [], {}, template_meta=meta)
        self.assertEqual((rows, len(faults)), ([], 1))
        self.assertIn("furlong", faults[0])
        rows, faults = skill_inputs_mod.rows_for(["a@v1", "b@v1"], two, [], {}, template_meta=meta)
        self.assertIn("different dimensions", faults[0])
        rows, faults = skill_inputs_mod.rows_for(["a@v1", "b@v1"], same, [], {}, template_meta=meta)
        self.assertEqual(([r["name"] for r in rows], faults), (["size"], []))
        self.assertEqual([x["skill"] for x in rows[0]["for_skill_inputs"]], ["a@v1", "b@v1"])
        rows, faults = skill_inputs_mod.rows_for([meta["agreement_skill"]], catalogue_mod.take([meta["agreement_skill"]]),
                                                 [], {}, template_meta=meta)
        self.assertEqual((rows, faults), ([], []))                     # the template's own scripts hand those


class TheVersion(unittest.TestCase):
    def test_v37_is_the_latest_and_changes_three_scripts_and_the_text(self):
        self.assertEqual(template_mod.LATEST, "v37")
        meta = cards.load_json(os.path.join(V37, "TEMPLATE.json"))
        self.assertEqual(meta["version"], "v37")
        self.assertEqual(sorted(cards.tree_files(V37)), sorted(cards.tree_files(V36)))
        changed = sorted(r for r in cards.tree_files(V36)
                         if cards.sha256_file(os.path.join(V36, r)) != cards.sha256_file(os.path.join(V37, r)))
        self.assertEqual(changed, [".claude/skills/run-skill/SKILL.md", "CLAUDE.md", "TEMPLATE.json", "src/handover.py",
                                   "src/run_tool.py"])


if __name__ == "__main__":
    unittest.main()
