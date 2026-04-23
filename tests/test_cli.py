from __future__ import annotations

import argparse
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from initra_cli import build_spec, fill_missing_args_interactively, main
from initra_core import ProjectSpec, ScaffoldError, format_supported_stacks, generate_framework_plan, sanitize_project_name


class CliBehaviorTests(unittest.TestCase):
    def test_sanitize_project_name(self) -> None:
        self.assertEqual(sanitize_project_name(" My App "), "my-app")
        self.assertEqual(sanitize_project_name("hello___world"), "hello-world")

    def test_partial_interactive_prompts_only_missing_fields(self) -> None:
        args = argparse.Namespace(
            name="demo",
            language="node",
            framework=None,
            gh=False,
            public=False,
            open_in_vscode=False,
            ts=False,
            no_install=False,
            no_git=False,
            dry_run=False,
            output_dir=".",
            json_output=False,
            list_stacks=False,
        )

        # Framework is the only required missing field in this case.
        with patch("builtins.input", side_effect=["express"]):
            filled = fill_missing_args_interactively(args)

        self.assertEqual(filled.framework, "express")
        self.assertFalse(filled.gh)
        self.assertFalse(filled.open_in_vscode)
        self.assertFalse(filled.ts)

    def test_public_requires_gh(self) -> None:
        args = argparse.Namespace(
            name="demo",
            language="python",
            framework="flask",
            gh=False,
            public=True,
            open_in_vscode=False,
            ts=False,
            no_install=False,
            no_git=False,
            dry_run=False,
            output_dir=".",
            json_output=False,
            list_stacks=False,
        )
        with self.assertRaises(ScaffoldError):
            build_spec(args)

    def test_ts_only_allowed_for_node_express(self) -> None:
        args = argparse.Namespace(
            name="demo",
            language="python",
            framework="flask",
            gh=False,
            public=False,
            open_in_vscode=False,
            ts=True,
            no_install=False,
            no_git=False,
            dry_run=False,
            output_dir=".",
            json_output=False,
            list_stacks=False,
        )
        with self.assertRaises(ScaffoldError):
            build_spec(args)

    def test_output_dir_changes_target_path(self) -> None:
        args = argparse.Namespace(
            name="demo",
            language="python",
            framework="flask",
            gh=False,
            public=False,
            open_in_vscode=False,
            ts=False,
            no_install=False,
            no_git=False,
            dry_run=False,
            output_dir="/tmp/newproj-out",
            json_output=False,
            list_stacks=False,
        )
        spec = build_spec(args)
        self.assertEqual(spec.path, Path("/tmp/newproj-out").resolve() / "demo")

    def test_supported_stacks_formatter_contains_new_frameworks(self) -> None:
        output = format_supported_stacks()
        self.assertIn("aiohttp", output)
        self.assertIn("koa", output)
        self.assertIn("sinatra", output)
        self.assertIn("javalin", output)

    def test_list_flag_prints_stacks(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["--list"])
        self.assertEqual(code, 0)
        self.assertIn("Supported stacks:", buffer.getvalue())

    def test_json_flag_returns_machine_readable_output(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            code = main(["demo-json", "node", "koa", "--dry-run", "--no-git", "--json"])
        self.assertEqual(code, 0)
        parsed = json.loads(buffer.getvalue())
        self.assertEqual(parsed["name"], "demo-json")
        self.assertTrue(parsed["dry_run"])
        self.assertEqual(parsed["framework"], "koa")

    @patch("initra_cli.run_self_update")
    def test_self_update_invokes_update_handler(self, update_mock) -> None:
        code = main(["--self-update"])
        self.assertEqual(code, 0)
        update_mock.assert_called_once_with("auto", None)

    @patch("initra_cli.run_uninstall")
    def test_uninstall_invokes_uninstall_handler(self, uninstall_mock) -> None:
        code = main(["--uninstall"])
        self.assertEqual(code, 0)
        uninstall_mock.assert_called_once_with("auto")

    def test_self_update_rejects_scaffold_args(self) -> None:
        code = main(["demo", "python", "flask", "--self-update"])
        self.assertEqual(code, 1)

    def test_uninstall_rejects_scaffold_args(self) -> None:
        code = main(["demo", "python", "flask", "--uninstall"])
        self.assertEqual(code, 1)

    def test_uninstall_rejects_list_flag(self) -> None:
        code = main(["--uninstall", "--list"])
        self.assertEqual(code, 1)

    @patch("initra_cli.execute_update_command")
    def test_self_update_pipx_from_path_uses_force_install(self, command_mock) -> None:
        from initra_cli import run_self_update

        run_self_update("pipx", "./")
        expected = ["pipx", "install", "--force", str(Path("./").resolve())]
        command_mock.assert_called_once_with(expected)

    @patch("initra_cli.execute_update_command")
    def test_self_update_pip_without_path_uses_pypi(self, command_mock) -> None:
        from initra_cli import run_self_update
        import sys

        run_self_update("pip", None)
        command_mock.assert_called_once_with([sys.executable, "-m", "pip", "install", "--upgrade", "initra"])

    @patch("initra_cli.execute_update_command")
    def test_uninstall_pipx_uses_pipx_uninstall(self, command_mock) -> None:
        from initra_cli import run_uninstall

        run_uninstall("pipx")
        command_mock.assert_called_once_with(["pipx", "uninstall", "initra"])

    @patch("initra_cli.execute_update_command")
    def test_uninstall_pip_uses_pip_uninstall(self, command_mock) -> None:
        from initra_cli import run_uninstall
        import sys

        run_uninstall("pip")
        command_mock.assert_called_once_with([sys.executable, "-m", "pip", "uninstall", "-y", "initra"])


class PlanTests(unittest.TestCase):
    def _spec(self, **overrides) -> ProjectSpec:
        spec = ProjectSpec(
            name="demo",
            language="node",
            framework="express",
            path=Path("/tmp/demo"),
            gh=False,
            public=False,
            open_in_vscode=False,
            typescript=False,
            no_install=False,
            no_git=False,
            dry_run=False,
        )
        for key, value in overrides.items():
            setattr(spec, key, value)
        return spec

    def test_express_install_runs_after_files(self) -> None:
        spec = self._spec()
        plan = generate_framework_plan(spec)
        self.assertEqual(plan.commands, [])
        self.assertEqual(plan.post_commands, [["npm", "install"]])

    def test_express_no_install_skips_install_step(self) -> None:
        spec = self._spec(no_install=True)
        plan = generate_framework_plan(spec)
        self.assertEqual(plan.post_commands, [])

    def test_next_no_install_uses_skip_install_flag(self) -> None:
        spec = self._spec(framework="next", no_install=True)
        plan = generate_framework_plan(spec)
        self.assertIn("--skip-install", plan.commands[0])

    def test_django_no_install_rejected(self) -> None:
        spec = self._spec(language="python", framework="django", no_install=True)
        with self.assertRaises(ScaffoldError):
            generate_framework_plan(spec)

    def test_aiohttp_plan_created(self) -> None:
        spec = self._spec(language="python", framework="aiohttp")
        plan = generate_framework_plan(spec)
        self.assertTrue(any(path == "src/main.py" for path, _ in plan.files))
        self.assertGreaterEqual(len(plan.commands[0]), 3)
        self.assertEqual(plan.commands[0][1:3], ["-m", "venv"])

    def test_koa_plan_created(self) -> None:
        spec = self._spec(language="node", framework="koa")
        plan = generate_framework_plan(spec)
        self.assertTrue(any(path == "src/app.js" for path, _ in plan.files))
        self.assertTrue(any(path == "src/routes/users.js" for path, _ in plan.files))
        self.assertEqual(plan.post_commands, [["npm", "install"]])

    def test_sinatra_plan_created(self) -> None:
        spec = self._spec(language="ruby", framework="sinatra")
        plan = generate_framework_plan(spec)
        self.assertTrue(any(path == "Gemfile" for path, _ in plan.files))
        self.assertEqual(plan.commands, [])

    def test_javalin_plan_created(self) -> None:
        spec = self._spec(language="java", framework="javalin")
        plan = generate_framework_plan(spec)
        self.assertTrue(any(path == "pom.xml" for path, _ in plan.files))
        self.assertEqual(plan.commands, [])


if __name__ == "__main__":
    unittest.main()
