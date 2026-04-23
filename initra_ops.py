from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from initra_core import CommandError, FrameworkPlan, ProjectSpec, generate_framework_plan, render_gitignore, render_license, render_readme

COMMAND_TIMEOUT_SECONDS = 1800


@dataclass
class ScaffoldResult:
    name: str
    path: str
    language: str
    framework: str
    dry_run: bool
    created_files: list[str]
    executed_commands: list[str]
    git_initialized: bool
    github_repo_created: bool
    opened_in_vscode: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "path": self.path,
            "language": self.language,
            "framework": self.framework,
            "dry_run": self.dry_run,
            "created_files": self.created_files,
            "executed_commands": self.executed_commands,
            "git_initialized": self.git_initialized,
            "github_repo_created": self.github_repo_created,
            "opened_in_vscode": self.opened_in_vscode,
        }


def scaffold_project(spec: ProjectSpec) -> dict[str, object]:
    echo = not spec.output_json
    spec.path.parent.mkdir(parents=True, exist_ok=True)
    ensure_target_directory(spec.path)
    plan = generate_framework_plan(spec)
    created_files: list[str] = []
    executed_commands: list[str] = []

    if spec.dry_run:
        if echo:
            print_dry_run(spec, plan)
        return ScaffoldResult(
            name=spec.name,
            path=str(spec.path),
            language=spec.language,
            framework=spec.framework,
            dry_run=True,
            created_files=_dry_run_file_list(plan),
            executed_commands=_commands_preview(plan),
            git_initialized=False,
            github_repo_created=False,
            opened_in_vscode=False,
        ).as_dict()

    external_initializer = (
        (spec.language == "node" and spec.framework == "next")
        or (spec.language == "ruby" and spec.framework == "rails")
        or (spec.language == "java" and spec.framework == "springboot")
    )

    if external_initializer:
        if echo:
            print(f"Creating {spec.language}/{spec.framework} project in {spec.path}")
        run_generation_commands(plan.commands, spec.path.parent, executed_commands, echo=echo)
        if not spec.path.exists():
            raise CommandError(f"Expected scaffold directory was not created: {spec.path}")
    else:
        spec.path.mkdir(parents=True, exist_ok=True)
        if echo:
            print(f"Creating {spec.language}/{spec.framework} project in {spec.path}")
        run_generation_commands(plan.commands, spec.path, executed_commands, echo=echo)

    for relative_path, content in plan.files:
        write_file(spec.path / relative_path, content)
        created_files.append(relative_path)

    write_file(spec.path / ".gitignore", render_gitignore(spec))
    created_files.append(".gitignore")
    write_file(spec.path / "README.md", render_readme(spec, plan))
    created_files.append("README.md")
    write_file(spec.path / "LICENSE", render_license(spec))
    created_files.append("LICENSE")
    run_generation_commands(plan.post_commands, spec.path, executed_commands, echo=echo)

    git_initialized = False
    github_repo_created = False
    opened_in_vscode = False

    if not spec.no_git:
        init_git_repo(spec.path, executed_commands, echo=echo)
        git_initialized = True

    if spec.gh:
        create_github_repo(spec, executed_commands, echo=echo)
        github_repo_created = True

    if spec.open_in_vscode:
        open_in_vscode(spec.path, executed_commands, echo=echo)
        opened_in_vscode = True

    if echo:
        print(f"Done. Project created at {spec.path}")
    return ScaffoldResult(
        name=spec.name,
        path=str(spec.path),
        language=spec.language,
        framework=spec.framework,
        dry_run=False,
        created_files=created_files,
        executed_commands=executed_commands,
        git_initialized=git_initialized,
        github_repo_created=github_repo_created,
        opened_in_vscode=opened_in_vscode,
    ).as_dict()


def _commands_preview(plan: FrameworkPlan) -> list[str]:
    return [" ".join(cmd) for cmd in [*plan.commands, *plan.post_commands]]


def _dry_run_file_list(plan: FrameworkPlan) -> list[str]:
    files = [relative_path for relative_path, _ in plan.files]
    files.extend([".gitignore", "README.md", "LICENSE"])
    return files


def print_dry_run(spec: ProjectSpec, plan: FrameworkPlan) -> None:
    print("Dry run enabled. No files or commands will be executed.")
    print(f"Target: {spec.path}")
    print(f"Stack: {spec.language}/{spec.framework}")
    if plan.commands:
        print("Initial commands:")
        for command in plan.commands:
            print(f"- {' '.join(command)}")
    if plan.files:
        print("Files to create:")
        for relative_path, _ in plan.files:
            print(f"- {relative_path}")
        print("- .gitignore")
        print("- README.md")
        print("- LICENSE")
    if plan.post_commands:
        print("Post commands:")
        for command in plan.post_commands:
            print(f"- {' '.join(command)}")
    if spec.no_git:
        print("Git initialization: skipped (--no-git)")


def ensure_target_directory(path: Path) -> None:
    if path.exists():
        if not path.is_dir():
            raise CommandError(f"Target path exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise CommandError(f"Target directory already exists and is not empty: {path}")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def run_generation_commands(commands: Sequence[Sequence[str]], cwd: Path, collector: list[str], echo: bool) -> None:
    for command in commands:
        run_command(command, cwd=cwd, collector=collector, echo=echo)


def run_command(command: Sequence[str], cwd: Path, collector: list[str] | None = None, echo: bool = True) -> None:
    display = " ".join(command)
    if echo:
        print(f"$ {display}")
    if collector is not None:
        collector.append(display)
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise CommandError(f"Required command not found: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise CommandError(f"Command timed out after {COMMAND_TIMEOUT_SECONDS}s: {display}") from exc
    except subprocess.CalledProcessError as exc:
        stdout = exc.stdout.strip()
        stderr = exc.stderr.strip()
        details = "\n".join(part for part in [stdout, stderr] if part)
        if details:
            raise CommandError(f"Command failed: {display}\n{details}") from exc
        raise CommandError(f"Command failed: {display}") from exc

    if echo and completed.stdout.strip():
        print(completed.stdout.rstrip())
    if echo and completed.stderr.strip():
        print(completed.stderr.rstrip(), file=sys.stderr)


def init_git_repo(path: Path, collector: list[str], echo: bool) -> None:
    if not (path / ".git").exists():
        run_command(["git", "init"], cwd=path, collector=collector, echo=echo)
    run_command(["git", "add", "."], cwd=path, collector=collector, echo=echo)
    try:
        run_command(["git", "commit", "-m", "Initial scaffold"], cwd=path, collector=collector, echo=echo)
    except CommandError as exc:
        if "author identity unknown" in str(exc).lower():
            raise CommandError(
                "Git commit failed because user.name and user.email are not configured. Run `git config --global user.name` and `git config --global user.email`, then rerun initra."
            ) from exc
        raise


def create_github_repo(spec: ProjectSpec, collector: list[str], echo: bool) -> None:
    gh = shutil.which("gh")
    if gh is None:
        raise CommandError("`gh` was not found. Install GitHub CLI or omit --gh.")
    visibility = "--public" if spec.public else "--private"
    run_command(
        [
            gh,
            "repo",
            "create",
            spec.name,
            visibility,
            "--source",
            ".",
            "--remote",
            "origin",
            "--push",
            "--confirm",
        ],
        cwd=spec.path,
        collector=collector,
        echo=echo,
    )


def open_in_vscode(path: Path, collector: list[str], echo: bool) -> None:
    if shutil.which("code"):
        run_command(["code", str(path)], cwd=path, collector=collector, echo=echo)
        return
    if sys.platform == "darwin":
        run_command(["open", "-a", "Visual Studio Code", str(path)], cwd=path, collector=collector, echo=echo)
        return
    raise CommandError(
        "VS Code was not found on PATH. Install the `code` command or open the project manually."
    )
