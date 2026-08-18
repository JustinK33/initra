# initra: A Complete Walkthrough

A teaching document for understanding the whole codebase well enough to explain it to someone else.

Read it top to bottom once.
After that, the "Trace a real command" section is the part worth re-reading, because everything else is detail hanging off that spine.

---

## 1. What initra is

`initra` is a command-line tool that creates a new project directory for you, already filled in and ready to run.

```bash
initra myapi go gin
cd myapi
go run .
```

That is the whole product.
You name a project, pick a language and a framework, and you get a directory containing source code, a test, a `.gitignore`, a `README.md`, a `Dockerfile`, and an initialized git repo with one commit.

### The one-sentence version

initra turns `(name, language, framework, flags)` into a directory on disk.

### Why it exists

Starting a project is repetitive.
You always need the same scaffolding: a config module that reads environment variables, a health endpoint, a users CRUD endpoint to prove routing works, a test, a `.gitignore` with the right entries for that language.
Official tools exist for some stacks (`create-next-app`, `rails new`, `django-admin startproject`) but they disagree with each other, and several languages have no official scaffolder at all.
initra gives 14 stacks one consistent shape.

### The consistent shape

Nearly every generated project exposes the same API:

| Route | Method | Behavior |
|-------|--------|----------|
| `/health` | GET | Returns JSON status plus the app name |
| `/users` | GET | List all users |
| `/users` | POST | Create a user, validating name and email |
| `/users/:id` | GET | Fetch one user, 404 if missing |
| `/users/:id` | PUT | Replace a user |
| `/users/:id` | DELETE | Remove a user |

Data lives in memory behind a mutex.
That is deliberate.
The point is to demonstrate the layering (route to controller to service to store) without dragging in a database on day one.

### The 14 supported stacks

| Language | Frameworks |
|----------|-----------|
| python | flask, fastapi, django, aiohttp |
| node | express, express-ts, next, koa |
| ruby | rails, sinatra |
| java | springboot, javalin |
| go | gin |
| cpp | cmake |

Note that `express-ts` is not something a user types.
The user types `initra app node express --ts`, and the CLI rewrites the framework to `express-ts` internally.
This matters later.

---

## 2. The mental model: Spec, Plan, Execution

This is the single most important idea in the codebase.
If someone only remembers one thing, make it this.

initra runs in three distinct stages, and each stage lives in its own file:

```
  user input
      |
      v
  +-------------------------------------+
  |  cli.py       parse and prompt      |
  |  produces --> ProjectSpec           |   "what does the user want?"
  +-------------------------------------+
      |
      v
  +-------------------------------------+
  |  core.py      decide and render     |
  |  produces --> FrameworkPlan         |   "what files and commands?"
  +-------------------------------------+
      |
      v
  +-------------------------------------+
  |  ops.py       write and run         |
  |  produces --> a directory on disk   |   "do it"
  +-------------------------------------+
```

### Why this split is the good part of the design

Because `FrameworkPlan` is pure data, nothing touches the filesystem until `ops.py` runs.

Three consequences fall out of that for free:

1. **`--dry-run` is nearly free.**
   Build the plan, print it, return.
   No special "pretend" code paths that can drift out of sync with the real ones.
2. **Tests are fast and hermetic.**
   `tests/templates_pytest.py` builds plans for all 14 stacks and inspects the file contents as strings.
   No temp directories, no subprocesses, no network.
3. **Adding a stack is a contained change.**
   You write template files, write one `generate_*_plan` function, and add two registry entries.
   You never touch the writing or git logic.

### The two data structures

Both live in `initra/core.py`.

**`ProjectSpec`** (`core.py:33`) is the normalized, validated user request:

```python
@dataclass
class ProjectSpec:
    name: str              # already sanitized to kebab-case
    language: str
    framework: str
    path: Path             # absolute target directory
    gh: bool = False       # create a GitHub repo
    public: bool = False
    open_in_vscode: bool = False
    typescript: bool = False
    no_install: bool = False
    no_git: bool = False
    dry_run: bool = False
    output_json: bool = False
    tutorial: bool = False
    include_license: bool = False
```

**`FrameworkPlan`** (`core.py:51`) is the recipe:

```python
@dataclass
class FrameworkPlan:
    files: list[tuple[str, str]]      # (relative path, full file content)
    commands: list[list[str]]         # run BEFORE writing files
    post_commands: list[list[str]]    # run AFTER writing files
    readme_summary: str
    readme_run: str
    readme_install: str
    project_notes: list[str]
```

Two details in `FrameworkPlan` are worth pausing on, because they are where the real design decisions are hiding.

**`files` holds full content, not paths.**
By the time a plan exists, every template has already been read from disk and every placeholder substituted.
The plan is self-contained.
That is exactly what makes `--dry-run` and the tests trivial.

**`commands` and `post_commands` are two separate lists, and the order matters.**

- `commands` run first, and they can create the project directory themselves.
  This is for external scaffolders: `npx create-next-app`, `rails new`, `spring init`.
- `post_commands` run after initra has written its own files.
  This is for dependency installs: `npm install`, `go mod tidy`, `bundle install`, `cmake -S . -B build`.

The order is not arbitrary.
`npm install` has to run after `package.json` exists.
`go mod tidy` has to run after `go.mod` exists.
Getting this backwards would break every stack.

---

## 3. File map

```
initra/
  __init__.py        7 lines    __version__ and a re-export of main
  __main__.py        8 lines    enables `python -m initra`
  cli.py           613 lines    argparse, interactive prompts, terminal output
  core.py         1195 lines    registries, plan builders, template loading
  ops.py           275 lines    filesystem writes, subprocess calls, git, gh
  templates/                    on-disk template files, organized by stack

initra.py            9 lines    root shim so `python initra.py ...` works from a clone
pyproject.toml                  packaging, entry point, pytest config
tests/
  test_cli.py      415 lines    argument validation and plan-shape tests (unittest)
  test_ops.py      395 lines    scaffold, filesystem, and subprocess tests (unittest)
  templates_pytest.py 304 lines every-stack template tests (pytest, parametrized)
.github/workflows/ci.yml        pytest on Python 3.10/3.11/3.12, plus 7 dry-run smoke tests
```

### Why core.py used to be 4000 lines

This was the first thing anyone noticed about the file, and the history is worth keeping because it teaches something real about defensive programming.

Every stack used to store each template **twice**:

1. As a real file on disk under `initra/templates/`.
2. As an inline `DEFAULT_*` Python string constant in `core.py`, passed to `load_template` as a fallback.

There were 127 of those `DEFAULT_*` and `TUTORIAL_*` constants, 2967 lines, 73% of the file.

The original reason was defensive: if packaging ever failed to include the template directory, the inline constant would still produce a working project.

In practice it backfired.
Because a missing template silently fell back to a stale inline copy, **packaging bugs became invisible**.
The files on disk and the inline copies drifted apart, and nothing failed loudly enough to notice.
Section 8 tells the story of the bug this hid for months.

The two newest stacks (`go/gin` and `cpp/cmake`) broke the pattern first, keeping templates on disk only.
The rest of the codebase has since followed.
Instrumenting `load_template` across all 14 stacks, with every combination of `--tutorial`, `--license`, and `--no-install`, showed that 113 of 127 lookups resolved from disk - so 113 fallbacks were unreachable by construction.
Of the remaining 14, thirteen were the per-stack README override chain (a deliberate mechanism, described in section 5) and exactly one, `java/javalin/Dockerfile`, was a template that had never been written to disk at all.

That file is now a real template, `load_template` has no `fallback` parameter, and a missing template raises.
core.py went from 4063 lines to 1195 with **byte-identical output** across every stack and flag combination.

The lesson to teach: a fallback that hides a failure is worse than no fallback.
The corollary, learned later: an unreachable fallback is not insurance, it is a second copy of the truth that nobody checks.

---

## 4. Trace a real command end to end

Follow `initra myapi go gin` all the way through.
This is the section to walk someone through at a whiteboard.

### Step 1: Entry point

Two ways in, both landing in the same place:

- Installed via pip or pipx: the `initra` console script from `pyproject.toml:38` calls `initra.__main__:main`.
- From a git clone: `python initra.py ...`, and `initra.py` imports the same `main`.

`initra/__main__.py` imports `main` from `cli.py`.
Everything converges on `cli.main()`.

### Step 2: `cli.main()` (`cli.py:98`)

The order of operations here is deliberate.
Read it as a series of early exits, cheapest first:

```python
def main(argv=None):
    incoming_argv = list(sys.argv[1:] if argv is None else argv)
    if is_manual_command(incoming_argv):     # `initra man` never touches argparse
        print_manual()
        return 0

    args = parse_args(incoming_argv)          # ScaffoldError -> exit 2
    renderer = CliRenderer(enabled=not args.json_output)

    validation_error = validate_mode_args(args)   # flag-combination check
    if validation_error: ... return 1

    if args.uninstall: ...  return 0          # mode flags exit before any scaffolding
    if args.update:    ...  return 0
    if args.list_stacks: ... return 0

    renderer.banner()
    args = fill_missing_args_interactively(args)
    spec = build_spec(args)                   # -> ProjectSpec
    result = scaffold_project(spec)           # -> does the work
    render_success(renderer, spec, result)    # or render_dry_run
    return 0
```

`initra man` bypasses argparse entirely.
That is because `man` is a bare positional word, and argparse would try to interpret it as a project name.

Note the exit codes, they are part of the contract:
`0` success, `1` a scaffold or validation error, `2` an argparse error, `130` interrupted with Ctrl-C.

### Step 3: `parse_args` (`cli.py:297`)

Standard argparse with one customization worth explaining:

```python
class InitraArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ScaffoldError(f"Invalid command arguments: {message}. Run `initra --help` or `initra man`.")
```

By default, argparse prints to stderr and calls `sys.exit(2)` itself.
Overriding `error` converts that into a normal Python exception, which means `main` controls the exit code and the message stays consistent with every other initra error.
Small change, and it is what makes the CLI testable: `tests/test_cli.py:232` asserts on the exact error text.

Three positionals (`name`, `language`, `framework`), all `nargs="?"` so they can be omitted and prompted for later.

### Step 4: `validate_mode_args` (`cli.py:250`)

This function answers one question: are these flags a legal combination?

initra has four mutually exclusive modes: scaffold, `--list`, `--update`, `--uninstall`.
The check builds a single `scaffold_args_used` boolean, then rejects any mode flag mixed with it.

```python
if args.list_stacks:
    if any((args.update, args.uninstall, scaffold_args_used, ...)):
        return "`--list` cannot be combined with other arguments."
```

It returns an error string or `None`, rather than raising.
That keeps it a pure function and makes it directly unit-testable, which `tests/test_cli.py:283` relies on.

There are also three trailing checks for orphaned modifier flags: `--from-path` without `--update`, `--update-method` without `--update`, `--uninstall-method` without `--uninstall`.
Without these, `initra --from-path ./foo` would silently ignore the flag.
Silently ignoring a flag the user typed is a bad failure mode, so it is an error instead.

### Step 5: `fill_missing_args_interactively` (`cli.py:413`)

If any positional is missing, prompt for it.
Three things here are worth pointing out.

**The non-TTY guard:**

```python
if not sys.stdin.isatty():
    raise ScaffoldError("Missing required arguments in non-interactive mode. ...")
```

Without this, running initra in CI with missing arguments would hang forever waiting on stdin.
Instead it fails fast with an explanation.

**The `no_positionals` distinction.**
Only when *zero* positionals were supplied does initra also prompt for the optional extras (`--gh`, `--open`, `--ts`).
The reasoning: `initra` alone means "walk me through it", while `initra myapp node` means "you forgot the framework", and interrogating that user about GitHub visibility would be obnoxious.

**Prompt helpers are strict.**
`prompt_choice` (`cli.py:468`) prints the valid options, then rejects anything outside the list.
`prompt_yes_no` (`cli.py:476`) accepts `y`, `yes`, `n`, `no`, or empty for the default, and raises on anything else.
No silent coercion of garbage input into a default.

### Step 6: `build_spec` (`cli.py:488`)

This is the trust boundary.
Everything downstream assumes the spec is valid, so every check lives here:

```python
if language not in SUPPORTED_LANGUAGES: raise ScaffoldError(...)
if framework not in SUPPORTED_FRAMEWORKS[language]: raise ScaffoldError(...)
if args.public and not args.gh: raise ScaffoldError("`--public` can only be used with `--gh`.")
if args.ts and not (language == "node" and framework == "express"): raise ScaffoldError(...)
```

Error messages always list the valid alternatives.
`"Unsupported framework 'gin' for python. Supported: aiohttp, django, fastapi, flask"` is useful.
`"invalid framework"` is not.

Then the name gets sanitized, and finally the `--ts` rewrite:

```python
project_name = sanitize_project_name(args.name)
project_path = output_dir / project_name
if framework == "express" and args.ts:
    framework = "express-ts"
```

That last line is the trick mentioned in section 1.
`--ts` is a user-facing flag, but internally it becomes a separate framework identifier.
The payoff is that every downstream lookup is a plain dictionary key on `(language, framework)`.
No `if typescript` branches scattered through `core.py`.

**`sanitize_project_name` (`core.py:77`)** deserves a close read, because it is small and does something non-obvious:

```python
def sanitize_project_name(value: str) -> str:
    cleaned = []
    previous_was_separator = False
    for char in value.strip().lower():
        if char.isalnum():
            cleaned.append(char)
            previous_was_separator = False
        else:
            if not previous_was_separator:
                cleaned.append("-")
                previous_was_separator = True
    name = "".join(cleaned).strip("-")
    if not name:
        raise ScaffoldError("Project name must contain at least one letter or number.")
    return name
```

The `previous_was_separator` flag is what collapses runs.
`"hello___world"` becomes `"hello-world"`, not `"hello---world"`.
`.strip("-")` trims the ends.
And an all-punctuation name like `"!!!"` raises rather than producing an empty directory name.

There is a sibling function, `sanitize_python_module_name` (`core.py:94`), because kebab-case is not a legal Python identifier.
`my-app` is a fine directory name but `import my-app` is a syntax error, so Python stacks get `my_app` as their module name.
It also handles the leading-digit case: `2fast` becomes `app_2fast`.

---

## 5. core.py: building the plan

`scaffold_project` immediately calls `generate_framework_plan(spec)` (`core.py:109`), which is a plain dispatch table:

```python
def generate_framework_plan(spec):
    if spec.language == "python": return generate_python_plan(spec)
    if spec.language == "node":   return generate_node_plan(spec)
    if spec.language == "ruby":   return generate_ruby_plan(spec)
    if spec.language == "java":   return generate_java_plan(spec)
    if spec.language == "go":     return generate_go_plan(spec)
    if spec.language == "cpp":    return generate_cpp_plan(spec)
    raise ScaffoldError(f"Unsupported language: {spec.language}")
```

One function per language, framework branching inside.
`build_spec` already validated the language, so the final `raise` is unreachable in normal operation.
It is there so a future language added to `SUPPORTED_LANGUAGES` but not wired here fails loudly instead of returning `None`.

### The template system

Three functions, roughly twenty-five lines total, and they handle everything.

**`load_template` (`core.py:1016`):**

```python
def load_template(relative_path, tutorial=False):
    if tutorial:
        tutorial_candidate = TEMPLATES_DIR / "tutorial" / relative_path
        if tutorial_candidate.exists():
            return tutorial_candidate.read_text(encoding="utf-8")
    candidate = TEMPLATES_DIR / relative_path
    if not candidate.exists():
        raise ScaffoldError(f"Missing packaged template: {relative_path}")
    return candidate.read_text(encoding="utf-8")
```

Resolution order: tutorial variant, then standard file, then raise.
There is no inline fallback - section 3 explains why that parameter was removed.

The tutorial lookup being a soft check (`if exists`) rather than a hard requirement is what makes `-t` degrade gracefully.
Only some stacks have tutorial variants; the rest silently use their standard templates.
Adding a tutorial variant later is purely additive: drop a file into `templates/tutorial/<path>` and it is picked up, no code change.

**`template_exists` (`core.py:1036`)** is a one-line existence check, and it exists for exactly one caller.
When a template is genuinely optional the caller must say so explicitly rather than passing a silent default:

```python
framework_template = f"{spec.language}/{spec.framework}/README.md"
template = load_template(framework_template if template_exists(framework_template) else "shared/README.md")
```

That is the difference between an intentional override chain and a muffled failure.
The chain is visible at the call site; `load_template` itself has no opinion about missing files other than to raise.

**`render_template` (`core.py:1040`):**

```python
def render_template(template, values):
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered
```

That is the entire templating engine.
Literal `str.replace` of `{{key}}`.

No Jinja2, no format strings.
This is a deliberate choice with a real payoff: template files stay **syntactically valid source code in their own language**.
`initra/templates/go/gin/main.go` is a real `.go` file.
Your editor highlights it, `gofmt` formats it, `go vet` checks it.
A Jinja template with `{% if %}` blocks would be none of those things.

The cost is that there are no conditionals or loops in templates.
When a stack needs conditional content it uses two template files, or builds the string in Python (see `build_express_package_json` at `core.py:515`, which assembles `package.json` as a dict and calls `json.dumps`).
That tradeoff is correct here.

The `f"{{{{{key}}}}}"` is five braces: four escape to produce two literal braces, and the fifth pair interpolates `key`.
It produces the string `{{key}}`.

### A data-driven plan: `generate_go_plan` (`core.py:443`)

This is the cleanest plan function, so teach it first.

```python
GO_GIN_FILES = [
    "go.mod", "main.go", "Dockerfile", ".dockerignore", ".env.example",
    "internal/config/config.go", "internal/router/router.go",
    "internal/middleware/logger.go", "internal/models/user.go",
    "internal/store/user_store.go", "internal/handlers/health.go",
    "internal/handlers/users.go", "internal/handlers/users_test.go",
]

def generate_go_plan(spec):
    files = [
        (path, render_template(load_template(f"go/gin/{path}"), {"project_name": spec.name}))
        for path in GO_GIN_FILES
    ]
    post_commands = [] if spec.no_install else [["go", "mod", "tidy"]]
    return FrameworkPlan(files=files, commands=[], post_commands=post_commands, ...)
```

One list of paths, one comprehension.
The relative path in the template tree matches the relative path in the generated project, so there is no mapping table to keep in sync.
Adding a file is a one-line change to `GO_GIN_FILES`.

`generate_cpp_plan` (`core.py:485`) is the same shape with `CPP_CMAKE_FILES`.

Compare this to `generate_java_plan` (`core.py:360`), which still hand-writes 26 tuples mapping template path to output path.
Same outcome, several times the code.
Removing the fallback constants closed most of the gap - each tuple used to carry an inline copy of the file as well - but the list-plus-comprehension shape is still the one to copy for a new stack.
Showing these two side by side is the most effective way to explain why.

### The `--no-install` pattern

Every plan function has this line, in some form:

```python
post_commands = [] if spec.no_install else [["go", "mod", "tidy"]]
```

Uniform across stacks, with two interesting exceptions.

**Django cannot honor it** (`core.py:198`):

```python
if spec.no_install:
    raise ScaffoldError("`--no-install` is not supported for Django because project generation requires installed Django tooling.")
```

Django is generated by running `django-admin startproject`, and `django-admin` only exists after Django is installed.
There is no meaningful "skip install" for Django, so rather than produce a broken project it refuses with an explanation.

**Next.js translates it into a flag** (`core.py:269`):

```python
if spec.no_install:
    command.append("--skip-install")
```

`create-next-app` installs dependencies as part of its own scaffolding, so initra passes the intent through instead of dropping a command.

Both exceptions are the right call.
A flag that silently does nothing on some stacks would be worse than either behavior.

### Two kinds of stack

The 14 stacks divide cleanly, and this distinction explains a branch in `ops.py`:

**Template-driven** (11 stacks: flask, fastapi, aiohttp, express, express-ts, koa, sinatra, javalin, gin, cmake).
initra writes every file itself.
`commands` is empty, `post_commands` installs dependencies.

**Externally scaffolded** (3 stacks: next, rails, springboot).
An official tool creates the project.
`files` is empty or nearly so, and `commands` holds the invocation:

```python
["npx", "create-next-app@latest", spec.name, "--yes", "--use-npm", ...]
["rails", "new", spec.name, "--skip-bundle"]
["spring", "init", "--build", "maven", "--java-version", "21", "--dependencies", "web,actuator", spec.name]
```

Why not template these too?
Because reimplementing `rails new` would mean tracking every Rails release forever.
Delegating to the official tool is strictly better.
initra still contributes a `.gitignore`, a `README.md`, and the git commit on top.

Note that these three commands take `spec.name` as an argument.
They create the directory themselves.
That is exactly why `ops.py` needs a special case.

### Rendering the shared files

Three files are generated for every stack, regardless of language.

**`render_gitignore` (`core.py:1047`)** starts with a common list, then extends it per language:

```python
common = [".DS_Store", "Thumbs.db", ".vscode/", ".idea/", ".env", ".env.*", "!.env.example"]
```

Those last three lines are the security-relevant part, and they are worth calling out explicitly when teaching this:

- `.env` ignores the real secrets file.
- `.env.*` ignores variants like `.env.production` and `.env.local`.
- `!.env.example` re-includes the committed template, which contains only placeholder values.

The negation has to come after the two ignore patterns.
Git applies these in order, and a later pattern wins.
Reordering them would silently start committing secrets.
`tests/templates_pytest.py:254` asserts all three lines exist for all six languages, specifically so a future refactor cannot quietly drop them.

Then per-language additions: `__pycache__/` and `.venv/` for python, `node_modules/` for node, `vendor/bundle/` for ruby, `target/` for java, `bin/` and `*.test` for go, `build/` and `CMakeCache.txt` for cpp.

**`render_readme` (`core.py:1115`)** is the trickiest of the three, and the reason is a bug that section 8 covers:

```python
def render_readme(spec, plan):
    # A stack may ship its own README; otherwise every stack shares one.
    framework_template = f"{spec.language}/{spec.framework}/README.md"
    template = load_template(framework_template if template_exists(framework_template) else "shared/README.md")
    body = render_template(template, {
        "summary": plan.readme_summary,
        "install": plan.readme_install,
        "run": plan.readme_run,
        "notes": format_notes(plan.project_notes),
    })
    # Plan text may itself contain {{project_name}}, so substitute names last.
    return render_template(body, {
        "project_name": spec.name,
        "language": spec.language,
        "framework": spec.framework,
    })
```

Two things happen here.

First, a two-level override: a stack-specific README if one is packaged, otherwise the shared one.
Only `java/javalin` currently ships its own.
This used to be a three-level chain ending in an inline constant, and the inner `load_template("shared/README.md", ...)` was evaluated on *every* scaffold even when the stack-specific file existed, because Python evaluates arguments before the call.
The `template_exists` form is both cheaper and honest about which branch it takes.

Second, and this is the part to emphasize: **two rendering passes, in a specific order**.
Pass one injects the plan's prose.
Pass two substitutes the names.

The order is load-bearing.
`plan.readme_run` for javalin contains the literal text `` docker build -t {{project_name}} . ``.
That placeholder only becomes visible to the renderer *after* pass one has injected it into the body.
Doing names first would leave a raw `{{project_name}}` in the shipped README.
That was a real bug.

**`render_license` (`core.py:1139`)** writes an MIT license with the current year, only when `--license` is passed.

---

## 6. ops.py: doing the work

`scaffold_project` (`ops.py:49`) is the only function that touches the outside world.
Read it in order.

### Safety first

```python
spec.path.parent.mkdir(parents=True, exist_ok=True)
ensure_target_directory(spec.path)
plan = generate_framework_plan(spec)
```

`ensure_target_directory` (`ops.py:173`) is the guard that prevents data loss:

```python
def ensure_target_directory(path):
    if path.exists():
        if not path.is_dir():
            raise CommandError(f"Target path exists and is not a directory: {path}")
        if any(path.iterdir()):
            raise CommandError(f"Target directory already exists and is not empty: {path}")
```

An existing empty directory is fine.
A file with that name, or a non-empty directory, is an error.
initra never overwrites your work.

Note the ordering: the guard runs **before** `generate_framework_plan`.
Failing on a bad target is cheaper than building a plan you are about to throw away.

### Dry run exits early

```python
if spec.dry_run:
    if echo: print_dry_run(spec, plan)
    return ScaffoldResult(..., dry_run=True,
                          created_files=_dry_run_file_list(spec, plan),
                          executed_commands=_commands_preview(plan), ...).as_dict()
```

The preview is derived from the same plan the real run would use:

```python
def _commands_preview(plan):
    return [" ".join(cmd) for cmd in [*plan.commands, *plan.post_commands]]
```

This is the payoff of the Spec/Plan/Execution split.
There is no separate dry-run implementation to drift out of sync.

### The external-initializer branch

```python
external_initializer = (
    (spec.language == "node" and spec.framework == "next")
    or (spec.language == "ruby" and spec.framework == "rails")
    or (spec.language == "java" and spec.framework == "springboot")
)

if external_initializer:
    run_generation_commands(plan.commands, spec.path.parent, executed_commands, echo=echo)
    if not spec.path.exists():
        raise CommandError(f"Expected scaffold directory was not created: {spec.path}")
else:
    spec.path.mkdir(parents=True, exist_ok=True)
    run_generation_commands(plan.commands, spec.path, executed_commands, echo=echo)
```

The difference is the working directory.

`rails new myapp` creates `myapp/` relative to where it runs, so it must run in the **parent** directory.
Template-driven stacks need the directory to exist first, so initra creates it and runs there.

The `if not spec.path.exists()` check after the external command matters.
If `create-next-app` exits 0 but produces nothing (wrong flag, changed CLI behavior, disk full), initra catches it here rather than continuing to write files into a directory that does not exist.

### Write, then post-commands

```python
for relative_path, content in plan.files:
    write_file(spec.path / relative_path, content)
    created_files.append(relative_path)

write_file(spec.path / ".gitignore", render_gitignore(spec))
write_file(spec.path / "README.md", render_readme(spec, plan))
if spec.include_license:
    write_file(spec.path / "LICENSE", render_license(spec))

run_generation_commands(plan.post_commands, spec.path, executed_commands, echo=echo)
```

`write_file` (`ops.py:181`) is three lines and handles nested paths:

```python
def write_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
```

`parents=True` is what lets a plan declare `internal/handlers/users.go` without separately declaring the directories.
`encoding="utf-8"` is explicit rather than platform-dependent, which matters on Windows where the default is not UTF-8.

Post-commands run last, after every file exists.
`npm install` needs `package.json`; `cmake -S . -B build` needs `CMakeLists.txt`.

### Then git, GitHub, and the editor

```python
if not spec.no_git:      init_git_repo(...);      git_initialized = True
if spec.gh:              create_github_repo(...); github_repo_created = True
if spec.open_in_vscode:  open_in_vscode(...);     opened_in_vscode = True
```

### `run_command`: where subprocess discipline lives

`run_command` (`ops.py:191`) is worth reading line by line, because every `except` clause is there for a specific real failure.

```python
completed = subprocess.run(
    list(command), cwd=cwd, check=True,
    capture_output=True, text=True,
    timeout=COMMAND_TIMEOUT_SECONDS,   # 1800 seconds
)
```

Note there is **no `shell=True` anywhere in this codebase**.
Commands are always lists of arguments, passed directly to `execve`.
That means a project name cannot inject a shell command, which matters because the project name is user input that reaches these argument lists.

The handlers:

| Exception | Why it exists |
|-----------|--------------|
| `FileNotFoundError` | The tool is not installed. Becomes `"Required command not found: go"` rather than a traceback. |
| `TimeoutExpired` | A hung install cannot block forever. 30 minutes, generous but bounded. |
| `CalledProcessError` | Non-zero exit. Merges stdout and stderr into the error so the user sees the actual compiler or npm output. |
| `KeyboardInterrupt` / `InterruptedError` | Ctrl-C during a long install gets a clean message, not a stack trace. |
| `OSError` with `errno == 4` | `EINTR`, a syscall interrupted by a signal. Real, and confusing if unhandled. |

The `CalledProcessError` handler is the one that most improves the experience:

```python
stdout = exc.stdout.strip()
stderr = exc.stderr.strip()
details = "\n".join(part for part in [stdout, stderr] if part)
if details:
    raise CommandError(f"Command failed: {display}\n{details}")
```

Because output is captured, a naive implementation would swallow it and report only "command failed".
Re-attaching it is what makes a failed `go mod tidy` diagnosable.

### `init_git_repo`: one targeted error message

`init_git_repo` (`ops.py:227`) does `git init`, `git add .`, `git commit -m "Initial scaffold"`, and then:

```python
except CommandError as exc:
    if "author identity unknown" in str(exc).lower():
        raise CommandError(
            "Git commit failed because user.name and user.email are not configured. "
            "Run `git config --global user.name` and `git config --global user.email`, then rerun initra."
        ) from exc
    raise
```

This is the single most common first-run failure on a fresh machine, and git's own message is not obvious to a beginner.
Special-casing exactly one error and re-raising everything else is the right amount of special-casing.

### `ScaffoldResult`

`ScaffoldResult` (`ops.py:22`) is a dataclass with an `as_dict()` method.
That dict is what `--json` prints and what `tests/test_ops.py` asserts against.
Having one defined shape for the result, rather than assembling a dict inline, is what makes the JSON output a stable contract.

---

## 7. cli.py: presentation

### `CliRenderer` (`cli.py:45`)

All terminal output goes through this class.
Two forms of graceful degradation:

```python
try:
    from rich.console import Console
    from rich.panel import Panel
except Exception:
    Console = None
    Panel = None
```

`rich` is the only runtime dependency, and even it is optional at import time.
If it is missing, every method falls back to plain `print`.

```python
unicode_ok = "utf" in ((sys.stdout.encoding or "").lower())
self.ok_icon   = "✓" if unicode_ok else "[OK]"
self.warn_icon = "⚠" if unicode_ok else "[WARN]"
self.err_icon  = "✗" if unicode_ok else "[ERR]"
```

On a terminal that cannot encode those glyphs, printing them raises `UnicodeEncodeError` and the whole command fails.
Checking the encoding and falling back to ASCII is what makes initra work in a plain Windows console.

`self.enabled` is `False` whenever `--json` is passed, so JSON output is never polluted with decorative text.

### The spinner condition

```python
if spec.output_json:
    result = scaffold_project(spec, echo=False)
elif renderer.enabled and renderer.console.is_terminal and not spec.dry_run:
    with renderer.console.status("[bold cyan]Scaffolding project...[/bold cyan]", spinner="dots"):
        result = scaffold_project(spec, echo=False)
elif renderer.enabled:
    result = scaffold_project(spec, echo=False)
else:
    result = scaffold_project(spec)
```

Four branches, each earning its place:

1. JSON mode: no decoration at all.
2. Interactive terminal, real run: animated spinner.
3. Piped or redirected output: no spinner, because a spinner writing escape codes into a log file is noise.
4. Fallback: let `ops` print its own progress.

`is_terminal` is the check that keeps CI logs clean.

Note `echo=False` in the first three.
When the CLI renders the result itself, `ops` must not also print.
`scaffold_project` defaults `echo` to `not spec.output_json`, and the CLI overrides it explicitly.

### `run_hint_for` (`cli.py:588`)

After a successful run, initra prints the next command to type:

```python
command_map = {
    ("python", "flask"):   "Start the dev server: flask --app src.app:create_app run --debug",
    ("node", "express"):   "Start the dev server: npm run dev",
    ("go", "gin"):         "Start the dev server: go run .",
    ("cpp", "cmake"):      f"Build and run: cmake --build build && ./build/{spec.name}",
    ...
}
return command_map.get((spec.language, spec.framework), "Start the dev server: follow README.md")
```

A `(language, framework)` tuple key, with a `.get` default so an unmapped stack degrades to "read the README" instead of raising a `KeyError`.
This is the payoff of normalizing `express --ts` into `express-ts` back in `build_spec`.

There is also `open_readme_hint` (`cli.py:608`), which returns `open` on macOS, `start` on Windows, `xdg-open` elsewhere.

### `--update` and `--uninstall`

initra can manage its own installation:

```python
def detect_update_method():
    return "pipx" if shutil.which("pipx") else "pip"
```

`pipx` is preferred because it isolates the CLI in its own virtualenv.

One subtle detail in `execute_update_command` (`cli.py:389`):

```python
with tempfile.TemporaryDirectory() as tmp:
    completed = subprocess.run(list(command), check=True, capture_output=True, text=True, cwd=tmp)
```

The comment explains it: pipx treats an argument as a local path if a directory of that name exists in the current directory.
If you happen to be sitting in a folder that contains a subdirectory named `initra`, `pipx upgrade initra` would resolve to that path instead of the PyPI package.
Running from an empty temp directory removes the ambiguity.

`pip uninstall` gets `-y` so it never blocks on a confirmation prompt.

---

## 8. Three real bugs, and what they teach

These are the most useful part of the walkthrough.
Each one is a general lesson wearing a specific costume.

### Bug 1: CI silently never ran a third of the tests

CI ran `python -m unittest discover -s tests`.

`unittest discover` matches the pattern `test*.py` by default.
The file `tests/templates_pytest.py` does not match that pattern.
So the entire every-stack template suite, roughly 55 tests, had **never once executed in CI**.

CI was green.
CI had always been green.
It was green because it was not looking.

The fix was to switch CI to pytest, whose `pyproject.toml` config matches both patterns:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_pytest.py"]
```

CI went from 43 tests to 98.

**The lesson:** a passing test suite tells you nothing unless you know how many tests ran.
Check the count, not just the color.
This bug also had a compounding effect: the go and cpp tests written later would have been dead weight, silently uncollected, if this had not been found first.

### Bug 2: shipped READMEs contained a raw `{{project_name}}`

`render_readme` originally did a single rendering pass, substituting names and plan text together.

But `plan.readme_run` for javalin contains `` docker build -t {{project_name}} . ``.
That placeholder was inside a *value* being injected, not inside the template.
By the time it landed in the body, the substitution pass had already finished.

Every javalin project shipped with a literal `{{project_name}}` in its README.

The fix is the two-pass order in section 5: plan text first, names second.

**The lesson:** if substituted values can themselves contain placeholders, one pass is not enough, and the order of passes is part of your correctness argument.
Worth a comment in the code, which it now has.

The test that locks it in (`templates_pytest.py:291`) is refreshingly blunt:

```python
readme = render_readme(spec, generate_framework_plan(spec))
assert "{{" not in readme
assert spec.name in readme
```

Parametrized over all 14 stacks.
It does not care *which* placeholder leaked, only that none did.
That is the right assertion, because it catches placeholders nobody has thought of yet.

### Bug 3: template dotfiles were missing from every installed build

`pyproject.toml` packaged templates with:

```toml
initra = ["templates/**/*"]
```

Setuptools glob `**` does **not** match files beginning with a dot.

So `.env.example`, `.dockerignore`, and `.clang-format` were never included in the wheel.
Scaffolding from a git clone worked perfectly, because the files were right there on disk.
Scaffolding from `pip install initra` was broken.

Here is the part that matters most.

For `java/javalin`, this failure was **completely silent**.
`load_template("java/javalin/.env.example", DEFAULT_JAVA_ENV)` found no file and quietly returned the inline constant.
A working-looking project, generated from a code path nobody intended to use.
This had presumably been true for multiple releases.

For `go/gin`, it failed immediately and loudly:

```
✗ Missing packaged template: go/gin/.dockerignore
```

Because those templates were written with no fallback, on purpose.

The fix:

```toml
[tool.setuptools.package-data]
# The second pattern is needed because ** does not match dotfiles such as
# .env.example, .dockerignore, and .clang-format.
initra = ["templates/**/*", "templates/**/.*"]
```

**The lesson, and it is the big one:** the defensive fallback that was supposed to make the system robust is precisely what hid the bug for months.
Removing the safety net on the newest stacks is what surfaced it.

Teach this one as a pair with the `load_template` design in section 3.
A fallback is only good if it fires in situations you actually anticipated.
A fallback that catches "the package is broken" and responds with "carry on quietly" is not resilience, it is a muffler on your alarm.

The epilogue: the fallbacks are all gone now, and measuring them on the way out showed 113 of 127 had never been reachable in the first place.
`java/javalin/.env.example` was fixed by the packaging change above, but `java/javalin/Dockerfile` was still resolving from its inline constant, undetected, until the audit that removed the mechanism.
One silent fallback in the codebase outlived the bug story written about silent fallbacks.

**Corollary:** test the built artifact, not the source tree.
All three of these were invisible when running from a clone.

---

## 9. The test suite

129 tests, three files, two frameworks.
The framework mix is historical: the newer file uses pytest for parametrization, the older two are `unittest`.
pytest runs both, so it works, though standardizing on one would be cleaner.

### `tests/templates_pytest.py`: the every-stack suite

This is the interesting one.
Its structure is worth copying.

`STACK_CASES` is a list of `pytest.param(language, framework, typescript, expected_files, id=...)`, one per stack.
Four separate test functions consume that same list.
Adding a stack means adding one `pytest.param` and getting four new tests automatically.

**Test 1 (`:194`): expected files are present.**
Parametrized over `STACK_CASES` **and** over `tutorial in [False, True]`, so 28 cases.
Uses `expected_files.issubset(generated_files)`, deliberately a subset rather than equality, so adding a file to a stack does not break the test.

**Test 2 (`:210`): no unresolved placeholders in any generated file.**

```python
unresolved = [path for path, content in plan.files if "{{project_name}}" in content]
assert unresolved == []
```

Asserting on the list rather than its length means the failure message names the offending files.

**Test 3 (`:226`): Python templates actually compile.**

```python
for path, content in python_files:
    compile(content, path, "exec")
```

`compile` is stdlib and catches syntax errors in template content without executing anything.
Cheap, and it means a broken f-string in a template fails at test time rather than at a user's first run.
This runs for standard and tutorial variants both, which is where it earns its keep: tutorial templates are heavily commented and easy to break.

**Test 4 (`:254`): the `.env` gitignore rules exist for all six languages.**
This is the security regression guard from section 5.

**Test 5 (`:274`): build artifacts are ignored.**
`bin/` and `*.test` for go, `build/` and `CMakeCache.txt` for cpp.
Guards against someone dropping a branch from `render_gitignore`.

**Test 6 (`:286`): a missing template raises.**

```python
with pytest.raises(ScaffoldError, match="Missing packaged template"):
    load_template("go/gin/does-not-exist.go")
```

Tiny, and it pins the design decision from bug 3 in place.
Without it, someone could restore the silent-fallback behavior and no test would object.

**Test 7 (`:291`): the README placeholder test** from bug 2.

### `tests/test_cli.py`

Argument validation and plan shape.
Most tests construct an `argparse.Namespace` directly and call `build_spec` or `validate_mode_args`, which is why those functions were written as pure and side-effect-free.

The interactive prompt tests patch two things at once:

```python
with patch("sys.stdin.isatty", return_value=True):
    with patch("builtins.input", side_effect=["express"]):
        filled = fill_missing_args_interactively(args)
```

`side_effect` as a list feeds answers in order.
This tests the interactive path with no terminal involved.

`PlanTests` at the bottom covers the plan-level behaviors: `--no-install` on express, `--skip-install` on next, the Django rejection.

### `tests/test_ops.py`

This used to be the thinnest part of the suite: two dry-run tests asserting the result dict shape and that no directory was created.
Everything `ops.py` actually does - writing files, running subprocesses, git, `gh`, VS Code - was covered only by CI smoke tests and manual verification.
Measured with the stdlib `trace` module, that left roughly 48% of the module's statements unexecuted.

It now covers the real path in five groups:

- **`ScaffoldToDiskTests`** scaffolds into a `tmp_path` and asserts the files exist with rendered content, including nested paths and the `--license` extra. It also pins the external-initializer branch: `next`/`rails`/`springboot` must run their commands in `spec.path.parent`, and must raise if the third-party tool does not create the directory.
- **`EnsureTargetDirectoryTests`** covers the never-overwrite guarantee from both sides, including a test that a pre-existing file survives a refused scaffold.
- **`RunCommandTests`** covers every `except` clause: missing executable, timeout, failure with and without captured output, interrupt, and the re-raise of unrelated `OSError`s.
- **`InitGitRepoTests`** pins the `.git`-already-exists skip and the "author identity unknown" remapping, including that *other* commit failures pass through unchanged.
- **`GithubRepoTests`** / **`OpenInVscodeTests`** cover the `gh`-missing error, public-vs-private argv, and the three VS Code launch branches.

Coverage of `ops.py` went from ~48% to ~99%.

Writing them found a bug worth knowing about.
The last two uncovered lines were an `if exc.errno == 4:  # EINTR` branch inside `except OSError`.
It is unreachable: Python instantiates `OSError(EINTR, ...)` as `InterruptedError`, which the preceding `except (KeyboardInterrupt, InterruptedError)` clause already catches.
The branch had presumably been correct before `InterruptedError` was added to that tuple, and nothing noticed when it stopped being.
That is the general lesson: a coverage gap on a line you believe is reachable is worth reading, not just filling.

### CI

`.github/workflows/ci.yml` runs on Python 3.10, 3.11, and 3.12, with `fail-fast: false` so one version failing does not hide the others.

Then seven dry-run smoke tests through the real CLI:

```bash
python initra.py demo-python python aiohttp --dry-run --no-git
python initra.py demo-node node koa --dry-run --no-git
python initra.py demo-ruby ruby sinatra --dry-run --no-git
python initra.py demo-java java javalin --dry-run --no-git
python initra.py demo-next node next --dry-run --no-git
python initra.py demo-go go gin --dry-run --no-git
python initra.py demo-cpp cpp cmake --dry-run --no-git
```

These exercise the full path from argv to plan, catching integration breakage that unit tests on individual functions would miss.
`--dry-run` keeps them fast and hermetic.

---

## 10. Two stacks in detail

Useful when the audience wants to see what a generated project actually looks like.

### `initra myapp go gin`

15 files.
Layered, idiomatic Go using the `internal/` convention.

```
myapp/
  go.mod                            module myapp, go 1.22, gin v1.10.0
  main.go                           http.Server plus graceful shutdown
  internal/config/config.go         PORT and APP_ENV with defaults
  internal/router/router.go         gin.New, middleware, 6 route registrations
  internal/middleware/logger.go     request logging
  internal/models/user.go           User plus request structs with binding tags
  internal/store/user_store.go      RWMutex-guarded slice, ErrNotFound
  internal/handlers/health.go
  internal/handlers/users.go        List, Get, Create, Update, Delete
  internal/handlers/users_test.go   3 httptest tests
  Dockerfile                        golang:1.22-alpine to distroless/static
  .dockerignore
  .env.example
  .gitignore                        generated
  README.md                         generated
```

Three things to point out.

**Validation is declarative, via gin's binding tags:**

```go
type CreateUserRequest struct {
    Name  string `json:"name"  binding:"required,min=2"`
    Email string `json:"email" binding:"required,email"`
}
```

`c.ShouldBindJSON(&req)` returns an error if these fail, and the handler answers 400 with gin's message.
No hand-written validation code.

**Graceful shutdown in `main.go`:**

```go
go func() {
    if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
        log.Fatalf("server error: %v", err)
    }
}()

quit := make(chan os.Signal, 1)
signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
<-quit

ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()
server.Shutdown(ctx)
```

The server runs in a goroutine, the main goroutine blocks on a signal channel, then drains connections with a 10 second budget.
The `errors.Is(err, http.ErrServerClosed)` check matters: `Shutdown` causes `ListenAndServe` to return that specific error, and treating it as fatal would log a spurious error on every clean exit.

**The Dockerfile handles a chicken-and-egg problem:**

```dockerfile
COPY go.mod go.sum* ./
```

The `*` is intentional.
`go.sum` does not exist until `go mod tidy` runs, so `COPY go.sum ./` would fail on a fresh scaffold with `--no-install`.
The glob matches zero files without erroring.

The final image is `distroless/static:nonroot`: no shell, no package manager, non-root by default.

### `initra myapp cpp cmake`

15 files.
CMake with C++20 and no system dependencies.

```
myapp/
  CMakeLists.txt         FetchContent, myapp_lib STATIC plus myapp exe
  src/main.cpp           signal handling, logger, listen
  src/server.h / .cpp    Config, LoadConfig, RegisterRoutes, 6 routes
  src/user_store.h / .cpp  std::mutex, std::optional returns
  tests/CMakeLists.txt   two add_test targets
  tests/test_user_store.cpp
  tests/test_server.cpp  binds an ephemeral port, makes real HTTP requests
  .clang-format          Google style, C++20, 100 columns
  Dockerfile             gcc:13 to debian:bookworm-slim
  .dockerignore
  .env.example
  .gitignore / README.md generated
```

**Dependencies come from `FetchContent`, pinned by tag:**

```cmake
FetchContent_Declare(httplib
  GIT_REPOSITORY https://github.com/yhirose/cpp-httplib.git
  GIT_TAG v0.15.3
  GIT_SHALLOW TRUE)
FetchContent_Declare(nlohmann_json
  GIT_REPOSITORY https://github.com/nlohmann/json.git
  GIT_TAG v3.11.3
  GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(httplib nlohmann_json)
```

No vcpkg, no Conan, no `apt install`.
Pinned tags rather than branches, so the build is reproducible.
`GIT_SHALLOW` keeps the clone small.

The tradeoff, documented in the generated README: the first configure needs network access.
That is the same tradeoff as `npm install` or `go mod tidy`, just less familiar in C++.

**The library-plus-executable split is the key structural decision:**

```cmake
add_library(myapp_lib STATIC src/server.cpp src/user_store.cpp)
target_include_directories(myapp_lib PUBLIC src)
target_link_libraries(myapp_lib PUBLIC httplib::httplib nlohmann_json::nlohmann_json)

add_executable(myapp src/main.cpp)
target_link_libraries(myapp PRIVATE myapp_lib)
```

Only `main.cpp` is in the executable.
All logic lives in `myapp_lib`, which the tests link directly.
Without this split, tests would have to recompile the sources or resort to `#include`ing `.cpp` files.
This is the standard solution and worth explaining, because it is the first thing people get wrong in C++ projects.

`PUBLIC` on `target_include_directories` and `target_link_libraries` means anything linking `myapp_lib` inherits the include path and the dependencies.
That is why `tests/CMakeLists.txt` is only three lines per test.

**Tests use plain `<cassert>`, no framework:**

```cmake
add_executable(test_user_store test_user_store.cpp)
target_link_libraries(test_user_store PRIVATE myapp_lib)
add_test(NAME user_store COMMAND test_user_store)
```

No gtest, no Catch2.
An `assert` that aborts gives a non-zero exit code, which is all `ctest` needs.
One fewer dependency to fetch, and one fewer API to learn before writing the second test.

`test_server.cpp` is the more interesting of the two: it starts the real server on an ephemeral port and makes actual HTTP requests against it.
That is an integration test, not a unit test, and it verifies the routing and JSON layers that a store-only unit test cannot reach.

**Signal handling in `main.cpp`** uses a file-scope pointer:

```cpp
namespace {
httplib::Server* g_server = nullptr;
void HandleSignal(int) {
  if (g_server != nullptr) { g_server->stop(); }
}
}  // namespace
```

A global is the honest solution here.
C signal handlers cannot capture state, so there is no closure to pass the server through.
The anonymous namespace limits it to this translation unit.

---

## 11. How to add a new stack

The concrete recipe.
Following the go/gin approach, this is roughly an hour of work.

**1. Write the template files.**
Put them in `initra/templates/<language>/<framework>/`.
The relative path inside that directory becomes the relative path in the generated project.
Use `{{project_name}}` wherever the name belongs.
Keep them as real source files so your editor, formatter, and linter all work on them.

**2. Register the stack** in `core.py:22`:

```python
SUPPORTED_LANGUAGES = {..., "rust"}
SUPPORTED_FRAMEWORKS = {..., "rust": {"axum"}}
```

**3. Write the plan function,** copying `generate_go_plan`:

```python
RUST_AXUM_FILES = ["Cargo.toml", "src/main.rs", ...]

def generate_rust_plan(spec):
    files = [
        (path, render_template(load_template(f"rust/axum/{path}"), {"project_name": spec.name}))
        for path in RUST_AXUM_FILES
    ]
    post_commands = [] if spec.no_install else [["cargo", "fetch"]]
    return FrameworkPlan(files=files, commands=[], post_commands=post_commands,
                         readme_summary=..., readme_run=..., readme_install=...,
                         project_notes=[...])
```

`load_template` takes no fallback: a missing template is a loud error, which is what you want when the cause is a packaging mistake.
If a template is genuinely optional, branch on `template_exists` at the call site so the choice is visible.

**4. Add the dispatch branch** in `generate_framework_plan` (`core.py:109`).

**5. Add a `render_gitignore` branch** (`core.py:1047`) for that language's build artifacts.

**6. Update `cli.py`:** the positional help strings at `:303` and `:308`, and a `run_hint_for` entry at `:588`.

**7. Add tests:** one `pytest.param` in `STACK_CASES`, one entry in `LANGUAGE_FRAMEWORKS`, and a `test_gitignore_covers_build_artifacts` case.

**8. Add a CI smoke line** in `.github/workflows/ci.yml`.

**9. Update the docs:** `README.md`, `USAGE.md`, `QUICKSTART.md`, `INSTALL.md` (prerequisites), `TESTING.md` (a verification recipe).

**10. Verify for real.**
`--dry-run` proves the plan is built.
It does not prove the generated code compiles.
Scaffold into `/tmp`, build it, run the tests, and curl every endpoint.
For go and cpp that meant `go build`, `go vet`, `gofmt -l`, `go test`, then `cmake --build`, `ctest`, and live requests against all seven behaviors including the 400 and 404 paths.

**11. Verify the built wheel.**
`python -m build`, install it into a clean virtualenv, and scaffold from there.
Bug 3 was invisible from the source tree and only appeared in the installed package.
Do not skip this step.

You never touch `ops.py`, unless the stack needs an external initializer.
In that case add it to the `external_initializer` condition at `ops.py:74`.

---

## 12. Design decisions worth defending

If someone challenges the design, these are the answers.

**Only one runtime dependency (`rich`), and it is optional at import time.**
initra is a scaffolding tool, so a dependency conflict during install is fatal to its purpose.
Everything else uses stdlib: `argparse`, `pathlib`, `subprocess`, `json`, `textwrap`, `dataclasses`.

**No templating engine.**
Literal `{{key}}` replacement, roughly five lines.
The payoff is that template files remain valid source code in their own language, so tooling works on them.
The cost is no loops or conditionals in templates.
When a stack needs conditional content, it builds the string in Python (`build_express_package_json`) or uses two files.
Correct tradeoff for this problem.

**Templates on disk rather than inline strings, for new stacks.**
Real `.go` and `.cpp` files can be compiled, linted, and formatted by their native toolchains.
That is not possible for a `textwrap.dedent` block inside a Python file, which is exactly how the older stacks accumulated drift.

**Plan as data, execution separate.**
Makes `--dry-run` free, makes tests hermetic and fast, and keeps each new stack from touching the write or git logic.

**Delegate to official scaffolders where they exist.**
Reimplementing `rails new` or `create-next-app` would mean tracking their releases forever.
initra adds a `.gitignore`, a `README.md`, and a git commit on top, which is genuine value without the maintenance liability.

**In-memory stores in generated projects.**
The teaching goal is the layering, not persistence.
Every store has a comment naming the upgrade path.
A generated project that requires a running Postgres before it will start is a worse first experience.

**Never overwrite.**
`ensure_target_directory` refuses a non-empty target.
A scaffolding tool that can destroy work is unusable.

**No `shell=True`, anywhere.**
Every subprocess call passes a list of arguments.
The project name is user input that flows into those lists, so this is the difference between a sanitizer being a nicety and being the only thing standing between a user and shell injection.

---

## 13. Teaching order

If you are explaining this to someone in about an hour:

1. **Show the product.** Run `initra demo go gin`, `cd demo`, `go run .`, curl `/health`. Five minutes, and it grounds everything that follows.
2. **Draw the three-stage diagram.** Spec, Plan, Execution. Do not move on until it lands, because everything else is detail hanging off it.
3. **Show `FrameworkPlan`.** Emphasize that `files` holds full content, and that `commands` versus `post_commands` is an ordering constraint (`npm install` needs `package.json` to exist).
4. **Trace `initra myapi go gin`.** Follow it through `cli.main`, `build_spec`, `generate_go_plan`, `scaffold_project`. This is the spine.
5. **Show `render_template`.** Five lines. Ask why it is not Jinja. The answer (templates stay valid source code) is the best single illustration of the project's taste.
6. **Show `generate_go_plan` and `generate_java_plan` side by side.** Data-driven versus hand-written, same outcome, ten times the code. This is where the audience starts having opinions of their own.
7. **Tell the three bug stories.** Save these for when the architecture is understood, because each one is a general lesson: count your tests, order your substitution passes, and never let a fallback muffle a real failure.
8. **Walk the add-a-stack recipe.** Best done as a live exercise if there is time.

The two ideas most worth having someone leave with:

**Separating "what to do" from "doing it" makes everything downstream easier.**
Dry-run, testing, and extension all became cheap because of one decision made early.

**A fallback that hides failure is worse than no fallback.**
Three releases shipped a broken wheel because a defensive default was doing its job too well.
Removing the safety net is what made the problem visible.
