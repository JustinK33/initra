from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from initra_core import ProjectSpec, SUPPORTED_FRAMEWORKS, SUPPORTED_LANGUAGES, ScaffoldError, format_supported_stacks, sanitize_project_name
from initra_ops import scaffold_project


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.uninstall:
        if any((args.name, args.language, args.framework, args.self_update, args.list_stacks)):
            print("error: `--uninstall` cannot be combined with other arguments.", file=sys.stderr)
            return 1
        try:
            run_uninstall(args.uninstall_method)
        except ScaffoldError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.self_update:
        if any((args.name, args.language, args.framework)):
            print("error: `--self-update` cannot be combined with project scaffold arguments.", file=sys.stderr)
            return 1
        try:
            run_self_update(args.update_method, args.from_path)
        except ScaffoldError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    if args.list_stacks:
        print(format_supported_stacks())
        return 0

    args = fill_missing_args_interactively(args)

    spec = build_spec(args)
    try:
        result = scaffold_project(spec)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if spec.output_json:
        print(json.dumps(result, indent=2))
    return 0


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="initra",
        description="Scaffold a production-ready project for common web stacks.",
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
    parser.add_argument("--output-dir", default=".", help="Base directory where the project folder is created")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Print a machine-readable JSON summary")
    parser.add_argument("--list", action="store_true", dest="list_stacks", help="List supported languages/frameworks and exit")
    parser.add_argument("--self-update", action="store_true", help="Update the installed initra CLI")
    parser.add_argument(
        "--update-method",
        choices=["auto", "pipx", "pip"],
        default="auto",
        help="Updater backend for --self-update (default: auto)",
    )
    parser.add_argument(
        "--from-path",
        help="Local path to install from when using --self-update (useful for upgrading from a local clone)",
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
    source_path = str(Path(from_path).expanduser().resolve()) if from_path else None
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
        completed = subprocess.run(list(command), check=True, capture_output=True, text=True)
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
    )
