from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from . import __version__
from .core import ProjectSpec, SUPPORTED_FRAMEWORKS, SUPPORTED_LANGUAGES, ScaffoldError, format_supported_stacks, sanitize_project_name
from .ops import scaffold_project

try:
    from rich.console import Console
    from rich.panel import Panel
except Exception:  # pragma: no cover - fallback path for minimal environments
    Console = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]


BANNER = r"""
 ___ _   _ ___ _____ ____      _
|_ _| \ | |_ _|_   _|  _ \    / \\
 | ||  \| || |  | | | |_) |  / _ \\
 | || |\  || |  | | |  _ <  / ___ \\
|___|_| \_|___| |_| |_| \_\/_/   \_\\
""".strip("\n")


class InitraArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ScaffoldError(f"Invalid command arguments: {message}. Run `initra --help` or `initra man`.")


class CliRenderer:
    def __init__(self, enabled: bool) -> None:
        self.enabled = bool(enabled and Console is not None and Panel is not None)
        self.console = Console(highlight=False, soft_wrap=True) if self.enabled else None
        self.error_console = Console(stderr=True, highlight=False, soft_wrap=True) if self.enabled else None

        unicode_ok = "utf" in ((sys.stdout.encoding or "").lower())
        self.ok_icon = "✓" if unicode_ok else "[OK]"
        self.warn_icon = "⚠" if unicode_ok else "[WARN]"
        self.err_icon = "✗" if unicode_ok else "[ERR]"

    def banner(self) -> None:
        if not self.enabled or self.console is None or Panel is None:
            return
        self.console.print(
            Panel.fit(
                f"[bold cyan]{BANNER}[/bold cyan]\n[dim]Scaffold production-ready starter projects[/dim]",
                border_style="cyan",
                padding=(0, 1),
            )
        )

    def success(self, message: str) -> None:
        if self.enabled and self.console is not None:
            self.console.print(f"[green]{self.ok_icon} {message}[/green]")
        else:
            print(f"{self.ok_icon} {message}")

    def warning(self, message: str) -> None:
        if self.enabled and self.console is not None:
            self.console.print(f"[yellow]{self.warn_icon} {message}[/yellow]")
        else:
            print(f"{self.warn_icon} {message}")

    def error(self, message: str) -> None:
        if self.enabled and self.error_console is not None:
            self.error_console.print(f"[bold red]{self.err_icon} {message}[/bold red]")
        else:
            print(f"error: {message}", file=sys.stderr)

    def muted(self, message: str) -> None:
        if self.enabled and self.console is not None:
            self.console.print(f"[dim]{message}[/dim]")
        else:
            print(message)

    def info(self, message: str) -> None:
        if self.enabled and self.console is not None:
            self.console.print(message)
        else:
            print(message)


def main(argv: Sequence[str] | None = None) -> int:
    incoming_argv = list(sys.argv[1:] if argv is None else argv)
    if is_manual_command(incoming_argv):
        print_manual()
        return 0

    try:
        args = parse_args(incoming_argv)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 0 if exc.code is None else 1

    renderer = CliRenderer(enabled=not args.json_output)

    validation_error = validate_mode_args(args)
    if validation_error:
        renderer.error(validation_error)
        return 1

    if args.uninstall:
        try:
            run_uninstall(args.uninstall_method)
        except ScaffoldError as exc:
            renderer.error(str(exc))
            return 1
        return 0

    if args.update:
        try:
            run_self_update(args.update_method, args.from_path)
        except ScaffoldError as exc:
            renderer.error(str(exc))
            return 1
        return 0

    if args.list_stacks:
        print(format_supported_stacks())
        return 0

    if renderer.enabled:
        renderer.banner()

    try:
        args = fill_missing_args_interactively(args)
        spec = build_spec(args)
    except ScaffoldError as exc:
        renderer.error(str(exc))
        return 1

    try:
        if spec.output_json:
            result = scaffold_project(spec, echo=False)
        elif renderer.enabled and renderer.console is not None and renderer.console.is_terminal and not spec.dry_run:
            with renderer.console.status("[bold cyan]Scaffolding project...[/bold cyan]", spinner="dots"):
                result = scaffold_project(spec, echo=False)
        elif renderer.enabled:
            result = scaffold_project(spec, echo=False)
        else:
            result = scaffold_project(spec)
    except ScaffoldError as exc:
        renderer.error(str(exc))
        return 1

    if spec.output_json:
        print(json.dumps(result, indent=2))
        return 0

    if renderer.enabled:
        if spec.dry_run:
            render_dry_run(renderer, spec, result)
        else:
            render_success(renderer, spec, result)
    return 0


def is_manual_command(argv: Sequence[str]) -> bool:
    if not argv:
        return False
    return argv[0].lower().strip() in {"man", "manual"}


def print_manual() -> None:
    print(
        """initra manual

Purpose:
  Scaffold production-ready starter projects with sensible defaults.

Commands:
  initra <name> <language> <framework>
    Create a project directly.
  initra
    Start interactive prompts for missing values.
  initra --list
    Show supported language/framework combinations.
  initra --update [--update-method auto|pipx|pip] [--from-path <path>]
    Update the installed CLI.
  initra --uninstall [--uninstall-method auto|pipx|pip]
    Remove the installed CLI.
  initra -v | --version
    Print CLI version and exit.
  initra man
    Show this manual.

Tags / options:
  --gh
    Create a GitHub repository with `gh`.
  --public
    Make the GitHub repo public (requires --gh).
  --open
    Open the generated project in VS Code.
  --ts
    Use TypeScript for `node express` starter only.
  -t, --tutorial
    Add beginner-friendly explanatory comments to scaffolded files.
  --no-install
    Skip dependency install commands.
  --no-git
    Skip git init/add/commit steps.
  --dry-run
    Preview actions without creating files.
  --license
    Include an MIT LICENSE file plus language-specific metadata.
  --output-dir <path>
    Set the parent directory where the project folder is created.
  --json
    Print scaffold results as JSON.
  --list
    Print supported stacks and exit.
  -v, --version
    Print CLI version and exit.
  --update
    Update initra.
  --update-method auto|pipx|pip
    Choose update backend (valid only with --update).
  --from-path <path>
    Update from a local clone path (valid only with --update).
  --uninstall
    Uninstall initra.
  --uninstall-method auto|pipx|pip
    Choose uninstall backend (valid only with --uninstall).
"""
    )


def validate_mode_args(args: argparse.Namespace) -> str | None:
    scaffold_args_used = any(
        (
            args.name,
            args.language,
            args.framework,
            args.gh,
            args.public,
            args.open_in_vscode,
            args.ts,
            getattr(args, "tutorial", False),
            args.no_install,
            args.no_git,
            args.dry_run,
            args.json_output,
            getattr(args, "license", False),
            args.output_dir != ".",
        )
    )

    if args.list_stacks:
        if any((args.update, args.uninstall, scaffold_args_used, args.from_path, args.update_method != "auto", args.uninstall_method != "auto")):
            return "`--list` cannot be combined with other arguments."
        return None

    if args.update:
        if any((args.uninstall, scaffold_args_used, args.list_stacks, args.uninstall_method != "auto")):
            return "`--update` cannot be combined with project scaffold arguments."
        return None

    if args.uninstall:
        if any((args.update, scaffold_args_used, args.list_stacks, args.from_path, args.update_method != "auto")):
            return "`--uninstall` cannot be combined with other arguments."
        return None

    if args.from_path:
        return "`--from-path` can only be used with `--update`."

    if args.update_method != "auto":
        return "`--update-method` can only be used with `--update`."

    if args.uninstall_method != "auto":
        return "`--uninstall-method` can only be used with `--uninstall`."

    return None


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = InitraArgumentParser(
        prog="initra",
        description="Scaffold a production-ready project for common web stacks. Use `initra man` for a quick manual.",
    )
    parser.add_argument("name", nargs="?", help="Project directory name")
    parser.add_argument("language", nargs="?", help="Language: python, node, ruby, java")
    parser.add_argument(
        "framework",
        nargs="?",
        help="Framework: flask, fastapi, django, aiohttp, express, next, koa, rails, sinatra, springboot, javalin",
    )
    parser.add_argument("--gh", action="store_true", help="Create a GitHub repo with gh")
    parser.add_argument("--public", action="store_true", help="Create a public GitHub repo")
    parser.add_argument("--open", action="store_true", dest="open_in_vscode", help="Open the project in VS Code")
    parser.add_argument("--ts", action="store_true", help="Use TypeScript for the Express starter")
    parser.add_argument("-t", "--tutorial", action="store_true", help="Add explanatory comments to help beginners understand the code")
    parser.add_argument("--no-install", action="store_true", help="Skip package/dependency install steps")
    parser.add_argument("--no-git", action="store_true", help="Skip git init/add/commit")
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without creating files")
    parser.add_argument(
        "--license",
        action="store_true",
        help="Include an MIT license file and language-specific license metadata",
    )
    parser.add_argument("--output-dir", default=".", help="Base directory where the project folder is created")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print a machine-readable JSON summary")
    parser.add_argument("--list", action="store_true", dest="list_stacks", help="List supported languages/frameworks and exit")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}", help="Print CLI version and exit")
    parser.add_argument("--update", "--upgrade", action="store_true", help="Update the installed initra CLI")
    parser.add_argument(
        "--update-method",
        choices=["auto", "pipx", "pip"],
        default="auto",
        help="Updater backend for --update (default: auto)",
    )
    parser.add_argument(
        "--from-path",
        help="Local path to install from when using --update (useful for upgrading from a local clone)",
    )
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the initra CLI")
    parser.add_argument(
        "--uninstall-method",
        choices=["auto", "pipx", "pip"],
        default="auto",
        help="Uninstall backend (default: auto)",
    )
    return parser.parse_args(argv)


def run_self_update(method: str, from_path: str | None) -> None:
    source_path: str | None = None
    if from_path:
        resolved = Path(from_path).expanduser().resolve()
        if not resolved.exists():
            raise ScaffoldError(f"`--from-path` does not exist: {resolved}")
        source_path = str(resolved)
    selected_method = detect_update_method() if method == "auto" else method

    if selected_method == "pipx":
        command = ["pipx", "install", "--force", source_path] if source_path else ["pipx", "upgrade", "initra"]
    elif selected_method == "pip":
        command = [sys.executable, "-m", "pip", "install", "--upgrade", source_path or "initra"]
    else:
        raise ScaffoldError(f"Unsupported update method: {selected_method}")

    execute_update_command(command)
    print("Update complete.")


def detect_update_method() -> str:
    return "pipx" if shutil.which("pipx") else "pip"


def run_uninstall(method: str) -> None:
    selected_method = detect_update_method() if method == "auto" else method

    if selected_method == "pipx":
        command = ["pipx", "uninstall", "initra"]
    elif selected_method == "pip":
        # Use -y to avoid interactive prompts and keep CLI uninstall scriptable.
        command = [sys.executable, "-m", "pip", "uninstall", "-y", "initra"]
    else:
        raise ScaffoldError(f"Unsupported uninstall method: {selected_method}")

    execute_update_command(command)
    print("Uninstall complete.")


def execute_update_command(command: Sequence[str]) -> None:
    display = " ".join(command)
    print(f"$ {display}")
    try:
        # Run from a neutral temp directory so pipx package-name args are not
        # misclassified as local paths when cwd contains similarly named folders.
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(list(command), check=True, capture_output=True, text=True, cwd=tmp)
    except FileNotFoundError as exc:
        raise ScaffoldError(f"Update command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        stdout = (exc.stdout or "").strip()
        stderr = (exc.stderr or "").strip()
        details = "\n".join(part for part in [stdout, stderr] if part)
        if details:
            raise ScaffoldError(f"Update failed: {display}\n{details}") from exc
        raise ScaffoldError(f"Update failed: {display}") from exc

    if completed.stdout.strip():
        print(completed.stdout.rstrip())
    if completed.stderr.strip():
        print(completed.stderr.rstrip(), file=sys.stderr)


def fill_missing_args_interactively(existing: argparse.Namespace) -> argparse.Namespace:
    if existing.list_stacks:
        return existing

    no_positionals = not any((existing.name, existing.language, existing.framework))
    if not no_positionals and all((existing.name, existing.language, existing.framework)):
        return existing
    if not sys.stdin.isatty():
        raise ScaffoldError(
            "Missing required arguments in non-interactive mode. "
            "Use `initra <name> <language> <framework>` or run from an interactive terminal."
        )

    print(
        "No arguments supplied. Enter project details interactively."
        if no_positionals
        else "Some required arguments are missing. Enter remaining details interactively."
    )

    if not existing.name:
        existing.name = prompt_text("Project name")

    if not existing.language:
        existing.language = prompt_choice("Language", sorted(SUPPORTED_LANGUAGES))
    else:
        existing.language = existing.language.lower().strip()
        if existing.language not in SUPPORTED_LANGUAGES:
            raise ScaffoldError(
                f"Unsupported language '{existing.language}'. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}"
            )

    if not existing.framework:
        existing.framework = prompt_choice("Framework", sorted(SUPPORTED_FRAMEWORKS[existing.language]))

    if no_positionals:
        if existing.gh is False:
            existing.gh = prompt_yes_no("Create a GitHub repo with gh?", default=False)
        if existing.gh and existing.public is False:
            existing.public = prompt_yes_no("Make the GitHub repo public?", default=False)
        if existing.open_in_vscode is False:
            existing.open_in_vscode = prompt_yes_no("Open the project in VS Code?", default=True)

        if existing.language == "node" and (existing.framework or "") == "express" and not existing.ts:
            existing.ts = prompt_yes_no("Use TypeScript for Express?", default=False)

    return existing


def prompt_text(label: str) -> str:
    value = input(f"{label}: ").strip()
    if not value:
        raise ScaffoldError(f"{label} is required.")
    return value


def prompt_choice(label: str, options: Sequence[str]) -> str:
    print(f"{label} options: {', '.join(options)}")
    value = input(f"{label}: ").strip().lower()
    if value not in options:
        raise ScaffoldError(f"Invalid {label.lower()} '{value}'. Expected one of: {', '.join(options)}")
    return value


def prompt_yes_no(label: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    value = input(f"{label} {suffix} ").strip().lower()
    if not value:
        return default
    if value in {"y", "yes"}:
        return True
    if value in {"n", "no"}:
        return False
    raise ScaffoldError(f"Please answer yes or no for: {label}")


def build_spec(args: argparse.Namespace) -> ProjectSpec:
    if not (args.name and args.language and args.framework):
        raise ScaffoldError("Expected: initra <name> <language> <framework> [options]")

    language = args.language.lower().strip()
    framework = args.framework.lower().strip()

    if language not in SUPPORTED_LANGUAGES:
        raise ScaffoldError(f"Unsupported language '{language}'. Supported: {', '.join(sorted(SUPPORTED_LANGUAGES))}")
    if framework not in SUPPORTED_FRAMEWORKS[language]:
        raise ScaffoldError(
            f"Unsupported framework '{framework}' for {language}. Supported: {', '.join(sorted(SUPPORTED_FRAMEWORKS[language]))}"
        )

    if args.public and not args.gh:
        raise ScaffoldError("`--public` can only be used with `--gh`.")

    if args.ts and not (language == "node" and framework == "express"):
        raise ScaffoldError("`--ts` is only valid for `node express`.")

    output_dir = Path(args.output_dir).expanduser()
    if output_dir.exists() and not output_dir.is_dir():
        raise ScaffoldError(f"`--output-dir` must be a directory: {output_dir}")
    output_dir = output_dir.resolve()

    project_name = sanitize_project_name(args.name)
    project_path = output_dir / project_name
    if framework == "express" and args.ts:
        framework = "express-ts"

    return ProjectSpec(
        name=project_name,
        language=language,
        framework=framework,
        path=project_path,
        gh=bool(args.gh),
        public=bool(args.public),
        open_in_vscode=bool(args.open_in_vscode),
        typescript=bool(args.ts),
        no_install=bool(args.no_install),
        no_git=bool(args.no_git),
        dry_run=bool(args.dry_run),
        output_json=bool(args.json_output),
        tutorial=bool(getattr(args, "tutorial", False)),
        include_license=bool(getattr(args, "license", False)),
    )


def render_dry_run(renderer: CliRenderer, spec: ProjectSpec, result: dict[str, object]) -> None:
    renderer.warning("Preview mode enabled (--dry-run). No files were created.")
    renderer.info(f"Target: {spec.path}")
    renderer.muted(f"Stack: {spec.language}/{spec.framework}")

    commands = [str(cmd) for cmd in result.get("executed_commands", [])]
    files = [str(file_name) for file_name in result.get("created_files", [])]

    if commands:
        renderer.info("\nCommands to run:")
        for command in commands:
            renderer.muted(f"  - {command}")

    if files:
        renderer.info("\nFiles to create:")
        for file_name in files:
            renderer.muted(f"  - {file_name}")

    if spec.no_install:
        renderer.warning("Optional dependency installation step was skipped (--no-install).")
    if spec.no_git:
        renderer.warning("Optional Git initialization step was skipped (--no-git).")


def render_success(renderer: CliRenderer, spec: ProjectSpec, result: dict[str, object]) -> None:
    renderer.success(f"Project created at {spec.path}")

    if result.get("git_initialized"):
        renderer.success("Initialized a Git repository.")
    elif spec.no_git:
        renderer.warning("Skipped optional Git initialization (--no-git).")

    if result.get("github_repo_created"):
        renderer.success("Created GitHub repository.")

    if result.get("opened_in_vscode"):
        renderer.success("Opened project in VS Code.")

    if spec.no_install:
        renderer.warning("Skipped optional dependency installation (--no-install).")

    created_files = list(result.get("created_files", []))
    executed_commands = list(result.get("executed_commands", []))
    renderer.muted(f"Created files: {len(created_files)}")
    renderer.muted(f"Executed commands: {len(executed_commands)}")

    renderer.info("\nTips")
    renderer.muted(f"  cd {spec.name}")
    renderer.muted(f"  {run_hint_for(spec)}")
    renderer.muted(f"  {open_readme_hint()}")


def run_hint_for(spec: ProjectSpec) -> str:
    command_map = {
        ("python", "flask"): "Start the dev server: flask --app src.app:create_app run --debug",
        ("python", "fastapi"): "Start the dev server: uvicorn src.main:app --reload",
        ("python", "django"): "Start the dev server: python manage.py runserver",
        ("python", "aiohttp"): "Start the dev server: python src/main.py",
        ("node", "express"): "Start the dev server: npm run dev",
        ("node", "express-ts"): "Start the dev server: npm run dev",
        ("node", "next"): "Start the dev server: npm run dev",
        ("node", "koa"): "Start the dev server: npm run dev",
        ("ruby", "rails"): "Start the dev server: bin/rails server",
        ("ruby", "sinatra"): "Start the dev server: bundle exec ruby app.rb",
        ("java", "springboot"): "Start the dev server: ./mvnw spring-boot:run",
        ("java", "javalin"): "Start the dev server: mvn exec:java",
    }
    return command_map.get((spec.language, spec.framework), "Start the dev server: follow README.md")


def open_readme_hint() -> str:
    if sys.platform == "darwin":
        return "Open README.md: open README.md"
    if sys.platform.startswith("win"):
        return "Open README.md: start README.md"
    return "Open README.md: xdg-open README.md"
