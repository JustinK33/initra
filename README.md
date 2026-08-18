# initra
[![CI](https://github.com/JustinK33/initra/actions/workflows/ci.yml/badge.svg)](https://github.com/JustinK33/initra/actions/workflows/ci.yml)

**A cross-platform CLI for scaffolding production-ready starter projects.**

Generate fully-configured starter projects for Python, Node.js, Ruby, Java, Go, and C++ from one command.

## Install

```bash
# Recommended
pipx install initra

# Secondary option
python3 -m pip install initra
```

See [INSTALL.md](https://github.com/JustinK33/initra/blob/main/INSTALL.md) for detailed installation options.

## First Command

```bash
initra myapi python fastapi
```

## Demo

![initra CLI demo](https://raw.githubusercontent.com/JustinK33/initra/main/docs/demo.gif)

## Quick Start

```bash
# FastAPI REST API with automatic virtual environment
initra myapi python fastapi
cd myapi && source .venv/bin/activate

# Express server with TypeScript and VS Code
initra server node express --ts --open

# Full-stack Next.js with GitHub repo
initra app node next --gh --public

# Rails app
initra blog ruby rails

# Spring Boot microservice
initra service java springboot
```

## Command Format

```bash
initra <name> <language> <framework> [options]
```

## Features

✅ **Multiple Languages & Frameworks**
- Python: Flask, FastAPI, Django, Aiohttp
- Node.js: Express (JS/TS), Next.js, Koa
- Ruby: Rails, Sinatra
- Java: Spring Boot, Javalin
- Go: Gin
- C++: CMake

✅ **Automatic Setup**
- Project directory creation
- Git repository initialization
- Framework-specific boilerplate code
- Language-appropriate `.gitignore` files
- Dependency file generation and installation
- Python virtualenv creation (auto-installed)

✅ **Developer Integrations**
- Create GitHub repositories with `--gh` flag
- Open projects in VS Code with `--open` flag
- TypeScript support for Express projects
- Interactive prompts when run with no arguments

### Options

| Option | Description |
|--------|-------------|
| `--ts` | Use TypeScript for Express |
| `--gh` | Create GitHub repository |
| `--public` | Make GitHub repo public |
| `--open` | Open in VS Code |
| `--no-install` | Skip dependency installation |
| `--no-git` | Skip git initialization and commit |
| `--dry-run` | Preview actions without writing files |
| `--output-dir` | Choose a base directory for generated projects |
| `--json` | Print machine-readable scaffold summary |
| `--list` | List supported stacks and exit |

## Supported Stacks

### Python
- **Flask** – Lightweight, flexible
- **FastAPI** – Modern, async, type-safe
- **Django** – Full-featured, batteries-included
- **Aiohttp** – Async server framework for lightweight services

### Node.js
- **Express** – Simple HTTP server (JavaScript)
- **Express + TypeScript** – Type-safe Express with `--ts`
- **Next.js** – Full-stack React/SSR
- **Koa** – Minimal async middleware framework

### Ruby
- **Rails** – Full web framework
- **Sinatra** – Minimal Ruby web framework

### Java
- **Spring Boot** – Enterprise framework
- **Javalin** – Lightweight Java/Kotlin web framework

### Go
- **Gin** – Fast HTTP framework with layered handlers and graceful shutdown

### C++
- **CMake** – C++20 HTTP API with a linkable core library and `ctest` coverage

## Examples

**Python FastAPI with auto-installed dependencies:**
```bash
initra myapi python fastapi
cd myapi
source .venv/bin/activate  # Auto-created
pip install -r requirements.txt
uvicorn src.main:app --reload
```

**TypeScript Express with GitHub and VS Code:**
```bash
initra api node express --ts --gh --public --open
cd api
npm install
npm run dev
```

**Next.js with GitHub:**
```bash
initra webapp node next --gh --open
cd webapp
npm run dev
```

**Django full-stack:**
```bash
initra blog python django
cd blog
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

**Rails:**
```bash
initra store ruby rails
cd store
bundle install
bin/rails server
```

**Spring Boot:**
```bash
initra users java springboot
cd users
./mvnw spring-boot:run
```

**Koa:**
```bash
initra service node koa
cd service
npm install
npm run dev
```

**Sinatra:**
```bash
initra web ruby sinatra
cd web
bundle install
bundle exec ruby app.rb
```

**Javalin:**
```bash
initra api java javalin
cd api
mvn compile exec:java
```

## Best-Practice Command Recipes

Use these as copy/paste starters for common workflows.

**1) Safe preview first, then scaffold for real**
```bash
# Preview exactly what will be created (no files written)
initra orders-api python fastapi --dry-run --license --tutorial

# Run the same scaffold for real after preview
initra orders-api python fastapi --license --tutorial
```

**2) Multi-tag setup for a production-ready Node project**
```bash
initra billing-service node express --ts --gh --public --open --license
```

**3) Generate into a dedicated workspace folder**
```bash
initra auth-service python django --output-dir ~/dev/services
```

**4) CI/automation-friendly output**
```bash
# Get machine-readable scaffold details for scripts/pipelines
initra analytics-api node koa --json
```

**5) Faster local scaffolding when you want full manual control**
```bash
initra playground ruby sinatra --no-install --no-git
```

## What Gets Created

Each project includes:

- ✅ Working starter code with health endpoints
- ✅ Language-specific `.gitignore`
- ✅ `README.md` with setup & run instructions
- ✅ Dependency files (`requirements.txt`, `package.json`, etc.)
- ✅ Tests directory with example tests
- ✅ Git repository with initial commit
- ✅ Python virtualenv (`.venv` for Python projects)

## Testing Generated Projects

### Python Tests
```bash
initra myapp python fastapi
cd myapp
source .venv/bin/activate
python -m unittest discover -s tests
```

### Node.js (TypeScript) Tests
```bash
initra myapp node express --ts
cd myapp
npm install
npm test
```

### Node.js (JavaScript) Tests
```bash
initra myapp node express
cd myapp
npm install
npm test
```

### Ruby Tests
```bash
initra myapp ruby rails
cd myapp
bundle install
bin/rails test
```

### Java Tests
```bash
initra myapp java springboot
cd myapp
./mvnw test
```

## Installation & Setup Details

See [INSTALL.md](https://github.com/JustinK33/initra/blob/main/INSTALL.md) for:
- Framework prerequisites
- Alternative installation methods
- Troubleshooting
- Detailed verification steps

See [USAGE.md](https://github.com/JustinK33/initra/blob/main/USAGE.md) for:
- Complete command reference
- Framework-specific examples
- Interactive mode walkthrough
- Advanced usage patterns

## Local Development

```bash
# Run directly without installation
python3 initra.py myapp python flask

# Install in editable mode
python3 -m pip install -e .
initra myapp python fastapi

# Run the test suite
python3 -m pytest tests
```

Use `pytest`, not `unittest discover`. The parametrized every-stack suite lives in
`tests/templates_pytest.py`, which `unittest discover` does not collect - it would
report `OK` after running roughly half the tests.

## Prerequisites

- **Python 3.10+** – For running the CLI
- **Git** – For repository initialization
- **Framework CLIs** – Rails, Spring, etc. (installed separately)

Optional:
- **GitHub CLI** (`gh`) – For `--gh` flag
- **VS Code** – For `--open` flag

## Contributing

See [CONTRIBUTING.md](https://github.com/JustinK33/initra/blob/main/CONTRIBUTING.md) for the
workflow and the checklist for adding a new stack.

[WALKTHROUGH.md](https://github.com/JustinK33/initra/blob/main/WALKTHROUGH.md) is the
architecture reference: how `cli.py`, `core.py`, and `ops.py` divide the work, how the
template system resolves files, and the design decisions behind both.

## License

MIT
