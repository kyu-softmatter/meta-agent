# -*- coding: utf-8 -*-
"""Tests of contracts/tools/session_skills.py: what check 24 and bundle check B15 say (tasks/015).

Run from the repository root:  python -m unittest discover -s contracts/tests
"""
import os
import shutil
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "contracts", "tools"))
import session_skills as ss  # noqa: E402

SKILL = """---
name: begin-work
description: Start the work. Use at the start of a session.
---

# Begin the work

1. Run `python tools/check.py` and read `docs/rules.md`.
2. Commit with `python tools/check.py --seat <name> -m "tools/nothing: a message" docs/rules.md`.

```
python -m tools.check
python -m unittest discover -s docs
```
"""
RUNNER_SKILL = """---
name: run-skills
description: Get the values a question needs from the runner. Use whenever a value must be computed.
---

Run `python src/run_skill.py` with the skill's id and its inputs. Never type a value.
"""


class Tree(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="session-skills-")
        self.addCleanup(shutil.rmtree, self.root, True)

    def write(self, relpath, text):
        path = os.path.join(self.root, *relpath.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return path


class Check24(Tree):
    def setUp(self):
        super().setUp()
        self.write("CLAUDE.md", "Use the `begin-work` skill at the start.\n")
        self.write("tools/check.py", "print('ok')\n")
        self.write("docs/rules.md", "# rules\n")
        self.skill = os.path.dirname(self.write(".claude/skills/begin-work/SKILL.md", SKILL))

    def problems(self):
        return ss.problems(self.root, self.skill)

    def test_a_sound_skill_has_nothing_said_about_it(self):
        self.assertEqual(self.problems(), [])
        self.assertEqual(ss.judge(self.root), [])

    def test_a_folder_without_skill_md(self):
        os.remove(os.path.join(self.skill, "SKILL.md"))
        self.assertEqual(self.problems(), ["no SKILL.md"])

    def test_the_name_is_the_folders(self):
        self.write(".claude/skills/begin-work/SKILL.md", SKILL.replace("name: begin-work", "name: start-work"))
        self.assertTrue(any("is not the folder's" in m for m in self.problems()))

    def test_a_description_says_when_it_is_loaded(self):
        self.write(".claude/skills/begin-work/SKILL.md", SKILL.replace("description: Start the work. Use at the start of a session.\n", ""))
        self.assertTrue(any("no description" in m for m in self.problems()))

    def test_a_path_a_script_and_a_module_it_names_exist(self):
        for gone, said in (("docs/rules.md", "docs/rules.md"), ("tools/check.py", "tools/check.py")):
            path = os.path.join(self.root, *gone.split("/"))
            text = open(path, encoding="utf-8").read()
            os.remove(path)
            self.assertTrue(any(said in m for m in self.problems()), gone)
            self.write(gone, text)
        self.write(".claude/skills/begin-work/SKILL.md", SKILL.replace("python -m tools.check", "python -m tools.absent"))
        self.assertEqual(self.problems(), ["names the module tools.absent, which is not in the tree"])

    def test_a_placeholder_a_quoted_message_and_a_library_module_are_not_paths(self):
        # <name>, "tools/nothing: a message" and unittest are all in SKILL and none is reported
        self.assertEqual(self.problems(), [])

    def test_a_path_inside_the_skills_own_folder_counts(self):
        self.write(".claude/skills/begin-work/SKILL.md", SKILL + "\nSee `pages/stage.md`.\n")
        self.assertTrue(any("pages/stage.md" in m for m in self.problems()))
        self.write(".claude/skills/begin-work/pages/stage.md", "# a page\n")
        self.assertEqual(self.problems(), [])

    def test_a_claude_md_names_it_beside_or_one_folder_below(self):
        self.write("CLAUDE.md", "Run the gate.\n")
        self.assertTrue(any("names `begin-work`" in m for m in self.problems()))
        self.write("agent/CLAUDE.md", "Use `begin-work`.\n")
        self.assertEqual(self.problems(), [])
        os.remove(os.path.join(self.root, "agent", "CLAUDE.md"))
        self.write("agent/deeper/CLAUDE.md", "Use `begin-work`.\n")
        self.assertTrue(any("names `begin-work`" in m for m in self.problems()))

    def test_no_number_outside_code(self):
        self.write(".claude/skills/begin-work/SKILL.md", SKILL + "\nStop after 5 rounds.\n")
        self.assertTrue(any("carries a number" in m and "5" in m for m in self.problems()))
        self.write(".claude/skills/begin-work/SKILL.md", SKILL + "\nSee `plan.md 14-37`, stage S0, grade E6, on 2026-11-12.\n")
        self.assertEqual(self.problems(), [])

    def test_judge_skips_what_it_is_told_to(self):
        self.write("CLAUDE.md", "Run the gate.\n")
        self.assertEqual(len(ss.judge(self.root)), 1)
        self.assertEqual(ss.judge(self.root, skip=[self.root]), [])


class B15(Tree):
    def bundle(self, version="v3", claude="Get every computed value through the `run-skills` skill.\n"):
        self.write("TEMPLATE.json", '{"template": "agent", "version": "%s"}\n' % version)
        self.write("CLAUDE.md", claude)
        self.write("src/run_skill.py", "print('runner')\n")

    def said(self):
        return [m for _, m in ss.bundle_problems(self.root)]

    def test_an_earlier_template_is_not_judged(self):
        self.bundle(version="v2")
        self.assertEqual(self.said(), [])

    def test_a_bundle_with_no_template_file_is_not_judged(self):
        self.write("CLAUDE.md", "nothing\n")
        self.assertEqual(self.said(), [])

    def test_one_session_skill_that_names_the_runner_passes(self):
        self.bundle()
        self.write(".claude/skills/run-skills/SKILL.md", RUNNER_SKILL)
        self.assertEqual(self.said(), [])

    def test_none_and_two_are_refused(self):
        self.bundle(claude="Use `run-skills` and `run-more`.\n")
        self.assertTrue(any("has 0 session skills" in m for m in self.said()))
        self.write(".claude/skills/run-skills/SKILL.md", RUNNER_SKILL)
        self.write(".claude/skills/run-more/SKILL.md", RUNNER_SKILL.replace("name: run-skills", "name: run-more"))
        self.assertTrue(any("has 2 session skills" in m for m in self.said()))

    def test_it_names_a_runner_that_exists(self):
        self.bundle()
        self.write(".claude/skills/run-skills/SKILL.md", RUNNER_SKILL.replace("Run `python src/run_skill.py` with", "Work out"))
        self.assertTrue(any("names no script under src/" in m for m in self.said()))

    def test_a_library_skill_is_not_a_session_skill(self):
        self.bundle()
        self.write(".claude/skills/run-skills/SKILL.md", RUNNER_SKILL)
        self.write(".claude/skills/drag@v1/skill.json", "{}\n")
        self.assertEqual(self.said(), ["a library skill sits where a session loads skills: a page is not a trigger"])

    def test_the_session_skill_is_what_check_24_asks(self):
        self.bundle(claude="Compute what the question needs.\n")
        self.write(".claude/skills/run-skills/SKILL.md", RUNNER_SKILL)
        self.assertTrue(any("names `run-skills`" in m for m in self.said()))


if __name__ == "__main__":
    unittest.main()
