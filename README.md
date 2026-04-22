# newproj

**A cross-platform CLI for scaffolding production-ready starter projects.**

Instantly create fully-configured projects for Python, Node.js, Ruby, and Java with one command. Includes git initialization, framework boilerplate, dependency installation, optional GitHub integration, and VS Code launch.

## Features

✅ **Multiple Languages & Frameworks**
- Python: Flask, FastAPI, Django, Aiohttp  
- Node.js: Express (JS/TS), Next.js, Koa
- Ruby: Rails, Sinatra
- Java: Spring Boot, Javalin

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

## Quick Start

### Install

```bash
pipx install .
```

See [INSTALL.md](INSTALL.md) for detailed installation options.

### Create a Project

```bash
# FastAPI REST API with automatic virtual environment
newproj myapi python fastapi
cd myapi && source .venv/bin/activate

# Express server with TypeScript and VS Code
newproj server node express --ts --open

# Full-stack Next.js with GitHub repo
newproj app node next --gh --public

# Rails app
newproj blog ruby rails

# Spring Boot microservice
newproj service java springboot
```

## Command Format

```bash
newproj <name> <language> <framework> [options]
```

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

## Examples

**Python FastAPI with auto-installed dependencies:**
```bash
newproj myapi python fastapi
cd myapi
source .venv/bin/activate  # Auto-created
pip install -r requirements.txt
uvicorn src.main:app --reload
```

**TypeScript Express with GitHub and VS Code:**
```bash
newproj api node express --ts --gh --public --open
cd api
npm install
npm run dev
```

**Next.js with GitHub:**
```bash
newproj webapp node next --gh --open
cd webapp
npm run dev
```

**Django full-stack:**
```bash
newproj blog python django
cd blog
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

**Rails:**
```bash
newproj store ruby rails
cd store
bundle install
bin/rails server
```

**Spring Boot:**
```bash
newproj users java springboot
cd users
./mvnw spring-boot:run
```

**Koa:**
```bash
newproj service node koa
cd service
npm install
npm run dev
```

**Sinatra:**
```bash
newproj web ruby sinatra
cd web
bundle install
bundle exec ruby app.rb
```

**Javalin:**
```bash
newproj api java javalin
cd api
mvn compile exec:java
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
newproj myapp python fastapi
cd myapp
source .venv/bin/activate
python -m unittest discover -s tests
```

### Node.js (TypeScript) Tests
```bash
newproj myapp node express --ts
cd myapp
npm install
npm test
```

### Node.js (JavaScript) Tests
```bash
newproj myapp node express
cd myapp
npm install
npm test
```

### Ruby Tests
```bash
newproj myapp ruby rails
cd myapp
bundle install
bin/rails test
```

### Java Tests
```bash
newproj myapp java springboot
cd myapp
./mvnw test
```

## Installation & Setup Details

See [INSTALL.md](INSTALL.md) for:
- Framework prerequisites
- Alternative installation methods
- Troubleshooting
- Detailed verification steps

See [USAGE.md](USAGE.md) for:
- Complete command reference
- Framework-specific examples
- Interactive mode walkthrough
- Advanced usage patterns

## Local Development

```bash
# Run directly without installation
python3 newproj.py myapp python flask

# Install in editable mode
pip install -e .
newproj myapp python fastapi

# Run automated CLI tests
python -m unittest discover -s tests
```

## Prerequisites

- **Python 3.10+** – For running the CLI
- **Git** – For repository initialization
- **Framework CLIs** – Rails, Spring, etc. (installed separately)

Optional:
- **GitHub CLI** (`gh`) – For `--gh` flag
- **VS Code** – For `--open` flag

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make focused changes
4. Open a pull request

## License

MIT
