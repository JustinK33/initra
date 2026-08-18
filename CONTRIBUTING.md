# Contributing to initra

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## Running the tests

```bash
python3 -m pytest tests
```

Use `pytest`, not `unittest discover`.
The every-stack parametrized suite lives in `tests/templates_pytest.py`, and `unittest discover` does not collect it - it reports `OK` after running roughly half the tests.
`pyproject.toml` sets `python_files = ["test_*.py", "*_pytest.py"]` so `pytest` picks up both naming conventions.

## Architecture

[WALKTHROUGH.md](WALKTHROUGH.md) is the reference.
Read section 2 for the Spec → Plan → Execution model and section 3 for the file map before changing anything structural.

The short version: `cli.py` parses arguments and renders output, `core.py` turns a validated `ProjectSpec` into a `FrameworkPlan` (files, commands, README text) without touching the filesystem, and `ops.py` executes that plan.
The dependency direction is one-way: `cli` → `ops` → `core`.

Keeping `core.py` free of side effects is what makes `--dry-run` trustworthy and the plan tests fast.
If you find yourself wanting to write a file or run a subprocess from `core.py`, put it in the plan instead.

## Templates

Templates are real files under `initra/templates/<language>/<framework>/`, laid out so the path in the template tree matches the path in the generated project.
They are not Python strings, and they are not Jinja.
That means `initra/templates/go/gin/main.go` is a valid `.go` file your editor can highlight and `gofmt` can format.

The only substitution is literal `{{placeholder}}` replacement via `render_template`.
There are no conditionals or loops. A stack that needs conditional content uses two template files, or builds the string in Python.

`load_template` raises on a missing file. Do not add a fallback.
A missing template means the package is broken, and that should be loud - see WALKTHROUGH section 8 for the release this rule came from.
If a template is genuinely optional, branch on `template_exists` at the call site so the choice is visible.

Tutorial variants (`-t`) mirror the standard tree under `initra/templates/tutorial/<same path>`.
They are purely additive: drop a file in and it is picked up with no code change. Stacks without one fall through to their standard templates.

## Adding a stack

Seven places, in order:

1. **Register it** in `SUPPORTED_FRAMEWORKS` (`initra/core.py:22`), and add the language to `SUPPORTED_LANGUAGES` if it is new.
2. **Add the templates** under `initra/templates/<language>/<framework>/`.
3. **Write the plan builder**, `generate_<language>_plan`. Copy the shape of `generate_go_plan` (`initra/core.py:443`): a module-level list of paths plus one comprehension, rather than hand-written tuples. Honour `spec.no_install` by returning empty `post_commands`.
4. **Add the dispatch branch** in `generate_framework_plan` (`initra/core.py:109`).
5. **Add a `render_gitignore` branch** (`initra/core.py:1047`) for that language's build artifacts.
6. **Add a run hint** to `run_hint_for` (`initra/cli.py:588`), or the generated README's next-steps line will fall back to "follow README.md".
7. **Add tests and CI**: a `pytest.param` in `STACK_CASES` (`tests/templates_pytest.py:17`), which gets you the every-stack template checks for free, and a `--dry-run --no-git` line in `.github/workflows/ci.yml`.

If the stack delegates to an official scaffolder that creates its own directory (like `create-next-app`, `rails new`, or `spring init`), also add it to the `external_initializer` condition in `initra/ops.py:74`.
Those stacks run their commands in the parent directory; everything else runs inside a pre-created project directory.

WALKTHROUGH section 11 walks through the same checklist with a worked `rust/axum` example.

## Pull requests

1. Fork and create a feature branch.
2. Keep changes focused - one concern per PR.
3. `python3 -m pytest tests` passes.
4. If you changed generated output, say so explicitly in the PR description and include a before/after of the affected files. If you did *not* intend to change it, diff two output trees to prove it:

```bash
initra demo <lang> <framework> --output-dir /tmp/before --no-install --no-git   # on main
initra demo <lang> <framework> --output-dir /tmp/after  --no-install --no-git   # on your branch
diff -r --exclude=.venv --exclude=node_modules /tmp/before /tmp/after
```

5. Do not hand-edit `CHANGELOG.md`; it is generated at release time.
