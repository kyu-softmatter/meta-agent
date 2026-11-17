# -*- coding: utf-8 -*-
"""Tests of contracts/tools/testfolder.py: a run made outside the repository, collected and removed (tasks/016).

The fixture repository holds builds of two unrelated kinds, an echo tool and a balance, neither of them
rheology (the rule of 2026-11-11). Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import testfolder as tf  # noqa: E402

BUNDLES = {
    "echo/0001": {"CLAUDE.md": "# echo\n", "src/run.py": "print('echo 1')\n"},
    "echo/0002": {"CLAUDE.md": "# echo\n", "src/run.py": "print('echo 2')\n", "tools/echo/tool.json": "{}\n"},
    "balance/0001": {"CLAUDE.md": "# balance\n", "src/run.py": "print('balance')\n", "envelope/safety.json": "{}\n"},
}


def sh(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t.invalid"] + list(args), cwd=cwd, env=env, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def put(root, rel, text):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


class TestFolder(unittest.TestCase):
    def setUp(self):
        self.top = os.path.realpath(tempfile.mkdtemp(prefix="testfolder-"))
        self.addCleanup(shutil.rmtree, self.top, True)
        self.repo, self.root, self.logs, self.projects = (os.path.join(self.top, n) for n in ("source", "tests", "logs", "projects"))
        put(self.repo, "contracts/validate.py", "print('VERDICT PASS tree=fixture')\n")
        put(self.repo, "contracts/hooks/.gitkeep", "")
        for build, files in BUNDLES.items():
            bdir = "meta_agent/builds/%s" % build
            for rel, text in files.items():
                put(self.repo, "%s/bundle/%s" % (bdir, rel), text)
            digest = tf.tree_digest(tf.tree_hashes(os.path.join(self.repo, *bdir.split("/"), "bundle")))
            put(self.repo, bdir + "/build.json", json.dumps({"card": "build", "id": "build-" + build.replace("/", "-"),
                                                             "bundle_path": bdir + "/bundle", "bundle_sha256": digest}))
        sh(self.repo, "init", "--quiet", "-b", "main")
        sh(self.repo, "config", "meta-agent.machine", "bench")
        sh(self.repo, "add", ".")
        sh(self.repo, "commit", "--quiet", "-m", "fixture")

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = tf.main(["--root", self.root, "--logs", self.logs, "--transcripts", self.projects] + list(argv), repo=self.repo)
        return code, out.getvalue(), err.getvalue()

    def make(self, *argv):
        code, out, err = self.run_tool("make", *argv)
        self.assertEqual(code, 0, err)
        return out.splitlines()[0].split()[-1]

    def session(self, cwd, sid, lines):
        pdir = os.path.join(self.projects, "p-" + sid)
        os.makedirs(pdir, exist_ok=True)
        with open(os.path.join(pdir, sid + ".jsonl"), "w", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "cwd": cwd, "timestamp": "2026-11-16T00:00:00Z",
                                "message": {"role": "user", "content": "Do task 001."}}) + "\n")
            for line in lines:
                f.write(json.dumps(line) + "\n")
        return pdir

    def collection(self, run, n=1):
        return os.path.join(self.logs, run, "collect-%d" % n)

    # ------------------------------------------------------------------ make
    def test_a_run_holds_a_clone_and_the_newest_build_of_each_kind(self):
        run = self.make()
        path = os.path.join(self.root, run)
        made = tf.read_json(os.path.join(self.logs, run, "made.json"))
        self.assertEqual([it["name"] for it in made["items"]], ["repo", "balance-0001", "echo-0002"])
        self.assertTrue(os.path.isfile(os.path.join(path, tf.MARK)))
        for it in made["items"][1:]:
            copy = os.path.join(path, *it["path"].split("/"))
            self.assertEqual(tf.tree_digest(tf.tree_hashes(copy)), it["bundle_sha256"])
            self.assertFalse(os.path.exists(os.path.join(copy, "build.json")))          # the bundle alone
        self.assertEqual(tf.stands_above(os.path.join(path, "bundles")), [])           # nothing above a bundle
        clone = os.path.join(path, "repo")
        self.assertEqual(tf.git(clone, "rev-parse", "HEAD").strip(), made["source"]["head"])
        self.assertEqual(tf.git(clone, "config", "--get", "meta-agent.machine").strip(), "bench")
        self.assertEqual(tf.git(clone, "config", "--get", "core.hooksPath").strip(), "contracts/hooks")

    def test_the_clones_origin_is_inside_the_run_and_never_moves(self):
        run = self.make("--no-bundles")
        path = os.path.join(self.root, run)
        clone, origin = os.path.join(path, "repo"), os.path.join(path, "origin.git")
        self.assertTrue(tf.inside(tf.git(clone, "remote", "get-url", "origin").strip(), path))
        self.assertEqual(tf.git(origin, "remote").strip(), "")                         # nothing points at the working copy
        put(self.repo, "later.txt", "the working copy moves on\n")
        sh(self.repo, "add", "later.txt")
        sh(self.repo, "commit", "--quiet", "-m", "after the run was made")
        tf.git(clone, "fetch", "origin")
        self.assertEqual(tf.git(clone, "rev-list", "--count", "HEAD..origin/main").strip(), "0")   # never behind
        put(clone, "note.txt", "x\n")
        sh(clone, "add", "note.txt")
        sh(clone, "commit", "--quiet", "-m", "in the test")
        tf.git(clone, "push", "origin", "HEAD:refs/heads/from-test")                   # a push ends inside the run
        self.assertIn("from-test", tf.git(origin, "branch", "--list"))
        self.assertNotIn("from-test", tf.git(self.repo, "branch", "--list"))

    def test_a_bundle_built_in_an_earlier_runs_clone_can_be_tested_standing_alone(self):
        first = self.make("--no-bundles")
        clone = os.path.join(self.root, first, "repo")
        bdir = "meta_agent/builds/sim/0001"
        put(clone, bdir + "/bundle/CLAUDE.md", "# sim\n")
        digest = tf.tree_digest(tf.tree_hashes(os.path.join(clone, *bdir.split("/"), "bundle")))
        put(clone, bdir + "/build.json", json.dumps({"card": "build", "id": "build-sim-0001", "bundle_path": bdir + "/bundle", "bundle_sha256": digest}))
        sh(clone, "add", ".")
        sh(clone, "commit", "--quiet", "-m", "a build made in the clone")
        second = self.make("--no-clone", "--source", clone, "--bundle", os.path.join(clone, bdir))
        made = tf.read_json(os.path.join(self.logs, second, "made.json"))
        self.assertEqual([it["name"] for it in made["items"]], ["sim-0001"])
        self.assertEqual(made["source"]["repository"], clone)
        self.assertTrue(os.path.isfile(os.path.join(self.root, second, "bundles", "sim-0001", "CLAUDE.md")))
        stray = os.path.join(self.root, "not-a-run")
        sh(self.top, "init", "--quiet", stray)
        self.assertEqual(self.run_tool("make", "--no-clone", "--source", stray)[0], 1)

    def test_uncommitted_work_is_not_in_a_run(self):
        put(self.repo, "meta_agent/builds/echo/0002/bundle/stray.txt", "not committed\n")
        run = self.make()
        self.assertFalse(os.path.exists(os.path.join(self.root, run, "bundles", "echo-0002", "stray.txt")))
        self.assertIn("meta_agent/builds/echo/0002/bundle/stray.txt", tf.read_json(os.path.join(self.logs, run, "made.json"))["source"]["uncommitted"])

    def test_a_copy_that_is_not_what_the_build_card_says_is_refused(self):
        card = os.path.join(self.repo, "meta_agent", "builds", "balance", "0001", "build.json")
        data = tf.read_json(card)
        data["bundle_sha256"] = "sha256:" + "0" * 64
        put(self.repo, "meta_agent/builds/balance/0001/build.json", json.dumps(data))
        sh(self.repo, "commit", "--quiet", "-am", "a card that is wrong")
        code, _, err = self.run_tool("make")
        self.assertEqual(code, 1)
        self.assertIn("the build card says", err)
        self.assertEqual(tf.run_names(self.root, self.logs), [])                       # nothing half made is left

    def test_a_folder_inside_the_repository_or_under_instructions_is_refused(self):
        code, _, err = tf_main(self, ["--root", os.path.join(self.repo, "tests"), "--logs", self.logs, "make"])
        self.assertEqual(code, 1)
        self.assertIn("must lie apart", err)
        code, _, err = tf_main(self, ["--root", self.root, "--logs", os.path.join(self.root, "logs"), "make"])
        self.assertEqual(code, 1)
        put(self.top, "CLAUDE.md", "# instructions of another project\n")
        code, _, err = self.run_tool("make")
        self.assertEqual(code, 1)
        self.assertIn("would not stand alone", err)

    def test_a_name_is_never_used_twice(self):
        first = self.make("--no-clone")
        self.assertEqual(self.run_tool("wipe", first)[0], 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, first)))
        second = self.make("--no-clone")
        self.assertNotEqual(first, second)
        shutil.rmtree(self.root)                                                        # even with the test folder gone
        self.assertNotIn(self.make("--no-clone"), (first, second))

    # ------------------------------------------------------------------ collect
    def test_a_collection_says_what_each_session_did(self):
        run = self.make()
        bundle = os.path.join(self.root, run, "bundles", "echo-0002")
        inside_file, outside_file = os.path.join(bundle, "runs", "in.json"), os.path.join(self.top, "elsewhere", "note.md")
        self.session(bundle, "aaaa", [
            {"type": "assistant", "timestamp": "2026-11-16T00:00:01Z", "effort": "medium", "message": {"id": "m1", "model": "model-a", "usage": {"input_tokens": 3, "output_tokens": 5}, "content": [
                {"type": "tool_use", "id": "t1", "name": "Skill", "input": {"skill": "run-skill"}},
                {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "python src/run.py"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"},
                                                     {"type": "tool_result", "tool_use_id": "t2", "is_error": True, "content": "exit 2"}]}},
            {"type": "assistant", "timestamp": "2026-11-16T00:00:09Z", "message": {"id": "m2", "model": "model-a", "usage": {"input_tokens": 4, "output_tokens": 6}, "content": [
                {"type": "tool_use", "id": "t3", "name": "Write", "input": {"file_path": inside_file, "content": "{}"}},
                {"type": "tool_use", "id": "t4", "name": "Write", "input": {"file_path": outside_file, "content": "a note"}}]}},
            {"type": "assistant", "timestamp": "2026-11-16T00:00:09Z", "message": {"id": "m3", "model": "model-a", "content": [
                {"type": "text", "text": "task 001: the runner refused, exit 2."}]}},
        ])
        self.session(os.path.join(self.top, "another-project"), "bbbb", [])
        code, out, err = self.run_tool("collect", run)
        self.assertEqual(code, 0, err)
        col = tf.read_json(os.path.join(self.collection(run), "collection.json"))
        self.assertEqual([s["session"] for s in col["sessions"]], ["aaaa"])
        s = col["sessions"][0]
        self.assertEqual((s["item"], s["models"], s["asked"], s["skills_loaded"]), ("echo-0002", ["model-a"], ["Do task 001."], ["run-skill"]))
        self.assertEqual(s["efforts"], ["medium"])
        self.assertEqual((s["calls"], s["calls_in_error"], s["first"], s["last"]), (4, 1, "2026-11-16T00:00:00Z", "2026-11-16T00:00:09Z"))
        self.assertEqual(s["files_written"], [inside_file, outside_file])
        self.assertEqual(s["written_outside"], [outside_file])
        self.assertEqual(s["tokens"], {"input_tokens": 7, "output_tokens": 11})
        with open(os.path.join(self.collection(run), "sessions", "echo-0002", "aaaa.calls.jsonl"), encoding="utf-8") as f:
            calls = [json.loads(l) for l in f]
        self.assertEqual([(c["tool"], c.get("command"), c["error"], c.get("error_text")) for c in calls][1],
                         ("Bash", "python src/run.py", True, "exit 2"))
        self.assertNotIn("error_text", calls[0])
        with open(os.path.join(self.collection(run), "sessions", "echo-0002", "aaaa.said.md"), encoding="utf-8") as f:
            self.assertIn("task 001: the runner refused, exit 2.", f.read())
        self.assertTrue(os.path.isfile(os.path.join(self.collection(run), "sessions", "echo-0002", "aaaa.jsonl")))

    def test_a_collection_says_what_changed_in_a_bundle_and_in_the_clone(self):
        run = self.make()
        path = os.path.join(self.root, run)
        put(path, "bundles/balance-0001/runs/out.json", "{}\n")
        put(path, "bundles/balance-0001/CLAUDE.md", "# balance, edited\n")
        os.remove(os.path.join(path, "bundles", "balance-0001", "envelope", "safety.json"))
        put(path, "repo/meta_agent/failures.jsonl", "{}\n")
        sh(os.path.join(path, "repo"), "add", "meta_agent/failures.jsonl")
        sh(os.path.join(path, "repo"), "commit", "--quiet", "-m", "a line of the test")
        put(path, "repo/untracked.txt", "left behind\n")
        self.assertEqual(self.run_tool("collect")[0], 0)                                # the one run that stands
        col = tf.read_json(os.path.join(self.collection(run), "collection.json"))
        items = {it["name"]: it for it in col["items"]}
        b = items["balance-0001"]
        self.assertEqual((b["added"], b["changed"], b["removed"]), (["runs/out.json"], ["CLAUDE.md"], ["envelope/safety.json"]))
        self.assertNotEqual(b["digest_now"], b["digest_made"])
        self.assertTrue(os.path.isfile(os.path.join(self.collection(run), "items", "balance-0001", "files", "runs", "out.json")))
        e = items["echo-0002"]
        self.assertEqual((e["added"], e["changed"], e["removed"], e["digest_now"]), ([], [], [], e["digest_made"]))
        r = items["repo"]
        self.assertEqual([c["subject"] for c in r["commits"]], ["a line of the test"])
        self.assertEqual((r["untracked"], r["verdict"], r["verdict_exit"]), (["untracked.txt"], "VERDICT PASS tree=fixture", 0))
        self.assertTrue(os.path.isfile(os.path.join(self.collection(run), "items", "repo", "changes.patch")))
        self.assertEqual(self.run_tool("collect", run)[0], 0)                           # a second collection overwrites nothing
        self.assertTrue(os.path.isdir(self.collection(run, 2)))

    # ------------------------------------------------------------------ session
    @unittest.skipIf(sys.platform == "win32", "the stand-in for the command-line claude is a shell script")
    def test_a_session_is_run_in_the_item_from_a_brief_and_what_it_was_asked_is_kept(self):
        run = self.make("--no-clone")
        seen = os.path.join(self.top, "seen.json")
        fake = put(self.top, "claude", "#!/bin/sh\nexec %s %s \"$@\"\n" % (sys.executable, os.path.join(self.top, "fake.py")))
        os.chmod(fake, 0o755)
        put(self.top, "fake.py", "import json, os, sys\n"
            "json.dump({'argv': sys.argv[1:], 'cwd': os.getcwd(), 'stdin': sys.stdin.read(), "
            "'passed_on': sorted(k for k in os.environ if k.startswith('CLAUDE'))}, open(%r, 'w'))\n"
            "print(json.dumps({'session_id': 'abcd', 'is_error': os.environ.get('FAKE_FAILS') == '1', 'result': 'task done'}))\n" % seen)
        brief = put(self.top, "brief.txt", "Read tasks/001-start.md first.\n")
        os.environ["CLAUDE_CODE_SOMETHING_OF_THE_OPENER"] = "1"
        self.addCleanup(os.environ.pop, "CLAUDE_CODE_SOMETHING_OF_THE_OPENER", None)
        code, out, err = self.run_tool("session", run, "balance-0001", "--brief", brief, "--model", "model-a", "--effort", "medium", "--claude", fake)
        self.assertEqual(code, 0, err)
        got = tf.read_json(seen)
        self.assertEqual(got["argv"], ["-p", "--output-format", "json", "--permission-mode", "auto", "--model", "model-a", "--effort", "medium"])
        self.assertEqual((got["cwd"], got["stdin"], got["passed_on"]),
                         (os.path.join(self.root, run, "bundles", "balance-0001"), "Read tasks/001-start.md first.\n", []))
        rec = tf.read_json(os.path.join(self.logs, run, "sessions", "balance-0001-1.json"))
        self.assertEqual((rec["brief"], rec["permission_mode"], rec["result"]["session_id"]), ("Read tasks/001-start.md first.\n", "auto", "abcd"))
        code, _, err = self.run_tool("session", run, "balance-0001", "--brief", brief, "--claude", fake, "--permission-mode", "bypassPermissions")
        self.assertEqual(code, 1)
        self.assertIn("the permission mode is one of", err)
        os.environ["FAKE_FAILS"] = "1"
        self.addCleanup(os.environ.pop, "FAKE_FAILS", None)
        self.assertEqual(self.run_tool("session", run, "balance-0001", "--brief", brief, "--claude", fake)[0], 1)   # a session that could not run
        self.assertTrue(os.path.isfile(os.path.join(self.logs, run, "sessions", "balance-0001-2.json")))

    # ------------------------------------------------------------------ wipe
    def test_wipe_removes_the_collected_transcripts_only_when_asked(self):
        run = self.make("--no-clone")
        bundle = os.path.join(self.root, run, "bundles", "echo-0002")
        mine = self.session(bundle, "dddd", [])
        other = self.session(os.path.join(self.top, "another-project"), "eeee", [])
        code, out, err = self.run_tool("wipe", run, "--sessions")
        self.assertEqual(code, 0, err)
        self.assertFalse(os.path.exists(mine))
        self.assertTrue(os.path.isfile(os.path.join(other, "eeee.jsonl")))
        self.assertTrue(os.path.isfile(os.path.join(self.collection(run), "sessions", "echo-0002", "dddd.jsonl")))
        self.assertEqual(tf.read_json(os.path.join(self.logs, run, "wiped.json"))["sessions_removed"], ["dddd"])
        again = self.make("--no-clone")
        kept = self.session(os.path.join(self.root, again, "bundles", "echo-0002"), "ffff", [])
        self.assertEqual(self.run_tool("wipe", again)[0], 0)
        self.assertTrue(os.path.isfile(os.path.join(kept, "ffff.jsonl")))               # without --sessions nothing of the application goes
        self.assertEqual(self.run_tool("wipe", again, "--sessions", "--no-collect")[0], 1)

    def test_wipe_collects_first_and_the_logs_stay(self):
        run = self.make()
        self.session(os.path.join(self.root, run, "repo"), "cccc", [])
        code, out, err = self.run_tool("wipe", run)
        self.assertEqual(code, 0, err)
        self.assertFalse(os.path.exists(os.path.join(self.root, run)))
        col = tf.read_json(os.path.join(self.collection(run), "collection.json"))
        self.assertEqual([(s["session"], s["item"]) for s in col["sessions"]], [("cccc", "repo")])
        self.assertEqual(tf.read_json(os.path.join(self.logs, run, "wiped.json"))["collected_first"], "collect-1")
        self.assertTrue(os.path.isdir(self.repo))
        self.assertIn("removed", self.run_tool("status")[1])
        self.assertEqual(self.run_tool("collect", run)[0], 0)                           # transcripts may still be taken later
        self.assertTrue(tf.read_json(os.path.join(self.collection(run, 2), "collection.json"))["items"][0]["gone"])

    def test_wipe_removes_only_a_folder_this_tool_made(self):
        mine = os.path.join(self.root, "20261116-7")
        put(mine, "thesis.txt", "not a test\n")
        code, _, err = self.run_tool("wipe", "20261116-7")
        self.assertEqual(code, 1)
        self.assertIn("not a run this tool made", err)
        self.assertTrue(os.path.isfile(os.path.join(mine, "thesis.txt")))
        self.make("--no-clone")
        self.assertEqual(self.run_tool("wipe", "--all")[0], 0)
        self.assertTrue(os.path.isfile(os.path.join(mine, "thesis.txt")))               # --all passes it by


def tf_main(case, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = tf.main(argv, repo=case.repo)
    return code, out.getvalue(), err.getvalue()


class ThisRepository(unittest.TestCase):
    """The digest this tool computes is the one the build cards of this repository carry."""

    def test_the_newest_build_of_every_agent_equals_its_card(self):
        builds = tf.newest_builds(REPO)
        self.assertGreaterEqual(len({b.split("/")[-2] for b in builds}), 2)             # two unrelated kinds
        top = tempfile.mkdtemp(prefix="testfolder-")
        self.addCleanup(shutil.rmtree, top, True)
        for rel in builds:
            item = tf.make_bundle(REPO, rel, os.path.join(top, rel.replace("/", "-")))
            self.assertEqual(item["bundle_sha256"], json.loads(tf.git(REPO, "show", "HEAD:%s/build.json" % rel))["bundle_sha256"])


if __name__ == "__main__":
    unittest.main()
