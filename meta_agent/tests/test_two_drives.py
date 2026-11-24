"""A working copy and a temporary folder on two drives (office-10: the repository on D:, the temporary folder on C:).

os.path.relpath and os.path.commonpath raise ValueError for paths on two Windows drives. cards.rel_posix gives the
absolute path where no relative one exists, and cards.is_under says that a path on another drive is not in the tree;
gate.outside, the skills catalogue's rel_repo and the Designer's rel_repo go through them. Judged with ntpath, so the
test runs on any computer.

Run from the repository root:
    PYTHONUTF8=1 python -m unittest discover -s meta_agent/tests -t .
"""
import ntpath
import posixpath
import unittest

from meta_agent.src import cards


class TwoDrives(unittest.TestCase):
    def test_a_path_on_another_drive_is_given_whole(self):
        self.assertEqual(cards.rel_posix(r"C:\Temp\ma-x\skills\a@v1", r"D:\codes\meta-agent", ntpath),
                         "C:/Temp/ma-x/skills/a@v1")

    def test_a_path_on_the_same_drive_stays_relative(self):
        self.assertEqual(cards.rel_posix(r"D:\codes\meta-agent\meta_agent\skills", r"D:\codes\meta-agent", ntpath),
                         "meta_agent/skills")
        self.assertEqual(cards.rel_posix("/tmp/ma-x", "/Users/p/meta-agent", posixpath), "../../../tmp/ma-x")

    def test_a_path_on_another_drive_is_not_under_the_tree(self):
        self.assertFalse(cards.is_under(r"C:\Temp\ma-x", r"D:\codes\meta-agent", ntpath))
        self.assertTrue(cards.is_under(r"D:\codes\meta-agent\builds", r"D:\codes\meta-agent", ntpath))
        self.assertFalse(cards.is_under(r"D:\codes\other", r"D:\codes\meta-agent", ntpath))


if __name__ == "__main__":
    unittest.main()
