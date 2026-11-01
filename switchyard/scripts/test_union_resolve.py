"""Exercise append-only resolution and CHANGELOG section consolidation."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("union-resolve.py")


class UnionResolve(unittest.TestCase):
    def resolve(self, text, succeeds=True):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "file.md"
            path.write_text(text)
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode == 0, succeeds, result.stderr)
            return path.read_text()

    def test_spec_union_is_unchanged(self):
        self.assertEqual(self.resolve("# Spec\n<<<<<<< HEAD\nupstream\n=======\nincoming\n>>>>>>> topic\n"),
                         "# Spec\nupstream\n\nincoming\n")

    def test_added_headings_merge_upstream_first(self):
        text = "## [Unreleased]\n\n<<<<<<< HEAD\n### Added\n\n- upstream\n=======\n### Added\n\n- incoming\n>>>>>>> topic\n"
        self.assertEqual(self.resolve(text), "## [Unreleased]\n\n### Added\n\n- upstream\n\n- incoming\n\n")

    def test_known_order_prefix_and_release_preserved(self):
        release = "## [1.0.0] - 2026-10-31\n\n### Added\n\n- old\n"
        text = ("# Changelog\n\n## [Unreleased]\n\nWork in progress.\n\n"
                "<<<<<<< HEAD\n### Fixed\n\n- fix\n\n### Added\n\n- upstream\n"
                "=======\n### Added\n\n- incoming\n>>>>>>> topic\n\n" + release)
        output = self.resolve(text)
        self.assertEqual(output.count("### Added"), 2)
        self.assertLess(output.index("### Added"), output.index("### Fixed"))
        self.assertLess(output.index("- upstream"), output.index("- incoming"))
        self.assertIn("## [Unreleased]\n\nWork in progress.\n\n", output)
        self.assertTrue(output.endswith(release))

    def test_all_known_and_unknown_sections(self):
        names = ["Notes", "Security", "Fixed", "Removed", "Other", "Deprecated", "Changed", "Added", "Notes"]
        text = "## [Unreleased]\n\n" + "".join(f"### {name}\n\n- {index}\n\n" for index, name in enumerate(names))
        output = self.resolve(text)
        self.assertEqual([line[4:] for line in output.splitlines() if line.startswith("### ")],
                         ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security", "Notes", "Other"])
        self.assertIn("### Notes\n\n- 0\n\n- 8\n", output)

    def test_diff3_leaves_file_unchanged(self):
        text = "<<<<<<< HEAD\nupstream\n||||||| base\nbase\n=======\nincoming\n>>>>>>> topic\n"
        self.assertEqual(self.resolve(text, succeeds=False), text)

    def test_malformed_conflict_leaves_file_unchanged(self):
        for text in ("<<<<<<< HEAD\nno end\n", "<<<<<<< HEAD\n<<<<<<< nested\n=======\na\n>>>>>>> topic\n"):
            with self.subTest(text=text):
                self.assertEqual(self.resolve(text, succeeds=False), text)

    def test_setext_underline_outside_conflict(self):
        text = "Title\n=======\n\n<<<<<<< HEAD\na\n=======\nb\n>>>>>>> t\n"
        self.assertEqual(self.resolve(text), "Title\n=======\n\na\n\nb\n")

    def test_plain_file_unchanged(self):
        text = "## Requirements\n\n### Added\n\n- a\n"
        self.assertEqual(self.resolve(text), text)


if __name__ == "__main__":
    unittest.main()
