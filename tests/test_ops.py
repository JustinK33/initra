from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import cast

from initra.core import ProjectSpec
from initra.ops import scaffold_project


class OpsTests(unittest.TestCase):
    def test_dry_run_returns_structured_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            spec = ProjectSpec(
                name="demo",
                language="node",
                framework="koa",
                path=output_dir / "demo",
                no_git=True,
                dry_run=True,
            )
            result = scaffold_project(spec)
            created_files = cast(list[str], result["created_files"])
            executed_commands = cast(list[str], result["executed_commands"])

            self.assertTrue(result["dry_run"])
            self.assertEqual(result["name"], "demo")
            self.assertEqual(result["language"], "node")
            self.assertEqual(result["framework"], "koa")
            self.assertFalse(result["git_initialized"])
            self.assertIn("package.json", created_files)
            self.assertIn("npm install", executed_commands)
            self.assertNotIn("LICENSE", created_files)
            self.assertFalse((output_dir / "demo").exists())

    def test_dry_run_includes_license_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            spec = ProjectSpec(
                name="demo",
                language="node",
                framework="koa",
                path=output_dir / "demo",
                no_git=True,
                dry_run=True,
                include_license=True,
            )
            result = scaffold_project(spec)
            created_files = cast(list[str], result["created_files"])
            self.assertIn("LICENSE", created_files)


if __name__ == "__main__":
    unittest.main()
