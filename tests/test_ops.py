from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from typing import cast
from unittest import mock

from initra.core import CommandError, ProjectSpec
from initra.ops import (
    COMMAND_TIMEOUT_SECONDS,
    create_github_repo,
    ensure_target_directory,
    init_git_repo,
    open_in_vscode,
    run_command,
    scaffold_project,
)


def make_spec(path: Path, **overrides: object) -> ProjectSpec:
    defaults: dict[str, object] = {
        "name": "demo",
        "language": "node",
        "framework": "koa",
        "path": path,
        "no_git": True,
        "no_install": True,
    }
    defaults.update(overrides)
    return ProjectSpec(**defaults)  # type: ignore[arg-type]


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


class ScaffoldToDiskTests(unittest.TestCase):
    """The real (non-dry-run) path: files actually land on disk."""

    def test_scaffold_writes_plan_files_and_generated_extras(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            result = scaffold_project(make_spec(target), echo=False)

            self.assertFalse(result["dry_run"])
            self.assertFalse(result["git_initialized"])
            self.assertEqual(result["path"], str(target))
            self.assertTrue((target / "package.json").is_file())
            self.assertTrue((target / ".gitignore").is_file())
            self.assertTrue((target / "README.md").is_file())
            self.assertFalse((target / "LICENSE").exists())

            created_files = cast(list[str], result["created_files"])
            self.assertIn(".gitignore", created_files)
            self.assertIn("README.md", created_files)
            for relative_path in created_files:
                self.assertTrue((target / relative_path).is_file(), relative_path)

            readme = (target / "README.md").read_text(encoding="utf-8")
            self.assertIn("demo", readme)
            self.assertNotIn("{{", readme)

    def test_scaffold_writes_license_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            result = scaffold_project(make_spec(target, include_license=True), echo=False)

            license_text = (target / "LICENSE").read_text(encoding="utf-8")
            self.assertIn("MIT", license_text)
            self.assertNotIn("{{", license_text)
            self.assertIn("LICENSE", cast(list[str], result["created_files"]))

    def test_scaffold_creates_nested_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "deeper" / "demo"
            scaffold_project(make_spec(target, language="java", framework="javalin"), echo=False)

            self.assertTrue((target / "src/main/java/com/example/App.java").is_file())

    def test_external_initializer_reports_missing_scaffold_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            spec = make_spec(target, language="ruby", framework="rails")
            # `rails new` is expected to create the directory itself; patching the
            # command runner to a no-op simulates it silently failing to do so.
            with mock.patch("initra.ops.run_generation_commands"):
                with self.assertRaises(CommandError) as ctx:
                    scaffold_project(spec, echo=False)

            self.assertIn("Expected scaffold directory was not created", str(ctx.exception))

    def test_external_initializer_runs_commands_in_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            spec = make_spec(target, language="node", framework="next")
            observed: list[Path] = []

            def fake_run(commands, cwd, collector, echo):  # type: ignore[no-untyped-def]
                observed.append(cwd)
                cwd.joinpath("demo").mkdir(parents=True, exist_ok=True)

            with mock.patch("initra.ops.run_generation_commands", fake_run):
                scaffold_project(spec, echo=False)

            self.assertEqual(observed[0], target.parent)


class EnsureTargetDirectoryTests(unittest.TestCase):
    def test_accepts_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ensure_target_directory(Path(tmp) / "does-not-exist")

    def test_accepts_existing_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ensure_target_directory(Path(tmp))

    def test_rejects_path_that_is_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            target.write_text("", encoding="utf-8")
            with self.assertRaises(CommandError) as ctx:
                ensure_target_directory(target)
            self.assertIn("not a directory", str(ctx.exception))

    def test_rejects_non_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            target.mkdir()
            (target / "keep.txt").write_text("", encoding="utf-8")
            with self.assertRaises(CommandError) as ctx:
                ensure_target_directory(target)
            self.assertIn("not empty", str(ctx.exception))

    def test_scaffold_refuses_to_overwrite_existing_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            target.mkdir()
            (target / "precious.txt").write_text("keep me", encoding="utf-8")

            with self.assertRaises(CommandError):
                scaffold_project(make_spec(target), echo=False)

            self.assertEqual((target / "precious.txt").read_text(encoding="utf-8"), "keep me")


class RunCommandTests(unittest.TestCase):
    def test_missing_executable_is_reported_by_name(self) -> None:
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaises(CommandError) as ctx:
                run_command(["nope"], cwd=Path("."), echo=False)
        self.assertIn("Required command not found: nope", str(ctx.exception))

    def test_timeout_reports_the_configured_limit(self) -> None:
        error = subprocess.TimeoutExpired(cmd=["sleep"], timeout=COMMAND_TIMEOUT_SECONDS)
        with mock.patch("subprocess.run", side_effect=error):
            with self.assertRaises(CommandError) as ctx:
                run_command(["sleep", "1"], cwd=Path("."), echo=False)
        self.assertIn(f"timed out after {COMMAND_TIMEOUT_SECONDS}s", str(ctx.exception))

    def test_failure_includes_captured_output(self) -> None:
        error = subprocess.CalledProcessError(1, ["npm"], output="stdout detail", stderr="stderr detail")
        with mock.patch("subprocess.run", side_effect=error):
            with self.assertRaises(CommandError) as ctx:
                run_command(["npm", "install"], cwd=Path("."), echo=False)
        message = str(ctx.exception)
        self.assertIn("Command failed: npm install", message)
        self.assertIn("stdout detail", message)
        self.assertIn("stderr detail", message)

    def test_failure_without_output_still_names_the_command(self) -> None:
        error = subprocess.CalledProcessError(1, ["npm"], output="", stderr="")
        with mock.patch("subprocess.run", side_effect=error):
            with self.assertRaises(CommandError) as ctx:
                run_command(["npm", "install"], cwd=Path("."), echo=False)
        self.assertEqual(str(ctx.exception), "Command failed: npm install")

    def test_interrupt_is_surfaced_as_command_error(self) -> None:
        with mock.patch("subprocess.run", side_effect=KeyboardInterrupt):
            with self.assertRaises(CommandError) as ctx:
                run_command(["sleep", "1"], cwd=Path("."), echo=False)
        self.assertIn("interrupted by user", str(ctx.exception))

    def test_eintr_is_surfaced_as_command_error(self) -> None:
        # Python instantiates OSError(EINTR, ...) as InterruptedError, so this
        # lands in the same handler as a Ctrl-C.
        error = OSError(4, "Interrupted system call")
        self.assertIsInstance(error, InterruptedError)
        with mock.patch("subprocess.run", side_effect=error):
            with self.assertRaises(CommandError) as ctx:
                run_command(["sleep", "1"], cwd=Path("."), echo=False)
        self.assertIn("interrupted by user", str(ctx.exception))

    def test_unrelated_oserror_propagates(self) -> None:
        with mock.patch("subprocess.run", side_effect=OSError(13, "Permission denied")):
            with self.assertRaises(OSError):
                run_command(["sleep", "1"], cwd=Path("."), echo=False)

    def test_collector_records_the_displayed_command(self) -> None:
        collector: list[str] = []
        completed = subprocess.CompletedProcess(["git", "init"], 0, stdout="", stderr="")
        with mock.patch("subprocess.run", return_value=completed):
            run_command(["git", "init"], cwd=Path("."), collector=collector, echo=False)
        self.assertEqual(collector, ["git init"])


class InitGitRepoTests(unittest.TestCase):
    def test_runs_init_add_and_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collector: list[str] = []
            with mock.patch("initra.ops.run_command") as run_mock:
                init_git_repo(Path(tmp), collector, echo=False)
            commands = [call.args[0] for call in run_mock.call_args_list]
            self.assertEqual(commands[0], ["git", "init"])
            self.assertEqual(commands[1], ["git", "add", "."])
            self.assertEqual(commands[2], ["git", "commit", "-m", "Initial scaffold"])

    def test_skips_init_when_repo_already_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()
            with mock.patch("initra.ops.run_command") as run_mock:
                init_git_repo(Path(tmp), [], echo=False)
            commands = [call.args[0] for call in run_mock.call_args_list]
            self.assertNotIn(["git", "init"], commands)

    def test_unconfigured_identity_gets_actionable_guidance(self) -> None:
        def fail_on_commit(command, **kwargs):  # type: ignore[no-untyped-def]
            if "commit" in command:
                raise CommandError("Command failed: git commit\nAuthor identity unknown")

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("initra.ops.run_command", side_effect=fail_on_commit):
                with self.assertRaises(CommandError) as ctx:
                    init_git_repo(Path(tmp), [], echo=False)
        message = str(ctx.exception)
        self.assertIn("user.name", message)
        self.assertIn("user.email", message)

    def test_other_commit_failures_propagate_unchanged(self) -> None:
        def fail_on_commit(command, **kwargs):  # type: ignore[no-untyped-def]
            if "commit" in command:
                raise CommandError("Command failed: git commit\nnothing to commit")

        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("initra.ops.run_command", side_effect=fail_on_commit):
                with self.assertRaises(CommandError) as ctx:
                    init_git_repo(Path(tmp), [], echo=False)
        self.assertIn("nothing to commit", str(ctx.exception))
        self.assertNotIn("user.email", str(ctx.exception))


class GithubRepoTests(unittest.TestCase):
    def test_missing_gh_is_reported(self) -> None:
        spec = make_spec(Path("/tmp/demo"))
        with mock.patch("initra.ops.shutil.which", return_value=None):
            with self.assertRaises(CommandError) as ctx:
                create_github_repo(spec, [], echo=False)
        self.assertIn("`gh` was not found", str(ctx.exception))

    def test_private_is_the_default_visibility(self) -> None:
        spec = make_spec(Path("/tmp/demo"))
        with mock.patch("initra.ops.shutil.which", return_value="/usr/bin/gh"):
            with mock.patch("initra.ops.run_command") as run_mock:
                create_github_repo(spec, [], echo=False)
        command = run_mock.call_args.args[0]
        self.assertIn("--private", command)
        self.assertNotIn("--public", command)

    def test_public_flag_is_forwarded(self) -> None:
        spec = make_spec(Path("/tmp/demo"), gh=True, public=True)
        with mock.patch("initra.ops.shutil.which", return_value="/usr/bin/gh"):
            with mock.patch("initra.ops.run_command") as run_mock:
                create_github_repo(spec, [], echo=False)
        command = run_mock.call_args.args[0]
        self.assertIn("--public", command)
        self.assertNotIn("--private", command)
        self.assertIn("demo", command)


class OpenInVscodeTests(unittest.TestCase):
    def test_prefers_the_code_command(self) -> None:
        with mock.patch("initra.ops.shutil.which", return_value="/usr/local/bin/code"):
            with mock.patch("initra.ops.run_command") as run_mock:
                open_in_vscode(Path("/tmp/demo"), [], echo=False)
        self.assertEqual(run_mock.call_args.args[0], ["code", "/tmp/demo"])

    def test_falls_back_to_open_on_macos(self) -> None:
        with mock.patch("initra.ops.shutil.which", return_value=None):
            with mock.patch("initra.ops.sys.platform", "darwin"):
                with mock.patch("initra.ops.run_command") as run_mock:
                    open_in_vscode(Path("/tmp/demo"), [], echo=False)
        self.assertEqual(run_mock.call_args.args[0], ["open", "-a", "Visual Studio Code", "/tmp/demo"])

    def test_reports_when_vscode_is_unavailable(self) -> None:
        with mock.patch("initra.ops.shutil.which", return_value=None):
            with mock.patch("initra.ops.sys.platform", "linux"):
                with self.assertRaises(CommandError) as ctx:
                    open_in_vscode(Path("/tmp/demo"), [], echo=False)
        self.assertIn("VS Code was not found", str(ctx.exception))


class ScaffoldSideEffectTests(unittest.TestCase):
    def test_git_github_and_vscode_steps_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            spec = make_spec(target, no_git=False, gh=True, open_in_vscode=True)
            with mock.patch("initra.ops.init_git_repo") as git_mock:
                with mock.patch("initra.ops.create_github_repo") as gh_mock:
                    with mock.patch("initra.ops.open_in_vscode") as code_mock:
                        result = scaffold_project(spec, echo=False)

            self.assertTrue(git_mock.called)
            self.assertTrue(gh_mock.called)
            self.assertTrue(code_mock.called)
            self.assertTrue(result["git_initialized"])
            self.assertTrue(result["github_repo_created"])
            self.assertTrue(result["opened_in_vscode"])

    def test_optional_steps_are_skipped_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            result = scaffold_project(make_spec(target), echo=False)
            self.assertFalse(result["git_initialized"])
            self.assertFalse(result["github_repo_created"])
            self.assertFalse(result["opened_in_vscode"])

    def test_files_are_written_before_post_commands_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "demo"
            # express has no pre-file commands and one post-command, `npm install`,
            # which can only work if package.json is already on disk.
            spec = make_spec(target, language="node", framework="express", no_install=False)
            manifest_present_when_installing: list[bool] = []

            def record(commands, cwd, collector, echo):  # type: ignore[no-untyped-def]
                for command in commands:
                    if "install" in command:
                        manifest_present_when_installing.append((cwd / "package.json").exists())

            with mock.patch("initra.ops.run_generation_commands", record):
                scaffold_project(spec, echo=False)

            self.assertEqual(manifest_present_when_installing, [True])


if __name__ == "__main__":
    unittest.main()
