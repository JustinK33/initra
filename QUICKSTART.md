# Quick Start

Get started with `newproj` in 5 minutes.

## Installation (Choose One)

### Option 1: Using pipx (Recommended)

```bash
pipx install /path/to/newproj
newproj --help
```

### Option 2: Direct Python

```bash
pip install -e /path/to/newproj
newproj --help
```

### Option 3: Run Directly

```bash
cd /path/to/newproj
python3 newproj.py --help
```

## Create Your First Project

### FastAPI (Recommended to Start)

```bash
newproj myapi python fastapi
cd myapi
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn src.main:app --reload
# Open http://localhost:8000
```

### Express with TypeScript

```bash
newproj myserver node express --ts
cd myserver
npm install
npm run dev
# Open http://localhost:3000
```

### Next.js Full-Stack

```bash
newproj myapp node next
cd myapp
npm run dev
# Open http://localhost:3000
```

### Rails

```bash
newproj myblog ruby rails
cd myblog
bundle install
bin/rails server
# Open http://localhost:3000
```

### Spring Boot

```bash
newproj myservice java springboot
cd myservice
./mvnw spring-boot:run
# Open http://localhost:8080
```

## Key Features

✅ **One Command** – Full project scaffolding with one line

✅ **Automatic Setup** – Virtual environments, dependencies, git repos

✅ **TypeScript Ready** – Use `--ts` with Express

✅ **GitHub Integration** – Push to GitHub with `--gh`

✅ **VS Code Ready** – Open in editor with `--open`

## Command Syntax

```bash
newproj <name> <language> <framework> [options]

# Examples:
newproj api python fastapi
newproj backend node express --ts
newproj webapp node next --gh --public --open
newproj blog ruby rails
newproj service java springboot
```

## All Supported Stacks

### Python
- `flask` – Lightweight web API
- `fastapi` – Modern async framework
- `django` – Full-featured framework

### Node.js
- `express` – HTTP server (JavaScript)
- `express --ts` – HTTP server (TypeScript)
- `next` – Full-stack React/SSR

### Ruby
- `rails` – Web framework
- `sinatra` – Lightweight API framework

### Java
- `springboot` – Enterprise framework
- `javalin` – Lightweight service framework

### More Popular Choices
- `python aiohttp` – Async Python web services
- `node koa` – Minimal async middleware APIs

## Testing Your Generated Projects

### Python
```bash
cd myapp
source .venv/bin/activate
python -m unittest discover -s tests
```

### Node.js
```bash
cd myapp
npm install
npm test
```

### Ruby
```bash
cd myapp
bundle install
bin/rails test
```

### Java
```bash
cd myapp
./mvnw test
```

## Common Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--ts` | Use TypeScript | `newproj app node express --ts` |
| `--gh` | Create GitHub repo | `newproj app python flask --gh` |
| `--public` | Make repo public | `newproj app python flask --gh --public` |
| `--open` | Open in VS Code | `newproj app node express --open` |
| `--no-install` | Skip dependency installs | `newproj app node express --no-install` |
| `--no-git` | Skip git initialization | `newproj app python fastapi --no-git` |
| `--dry-run` | Preview generated actions | `newproj app node next --dry-run` |
| `--output-dir` | Choose base output folder | `newproj app node koa --output-dir ~/work` |
| `--json` | Print JSON summary | `newproj app node koa --dry-run --json` |
| `--list` | Show supported stacks | `newproj --list` |

## What Gets Created

Every project includes:

- 📁 Source code directory (`src/`)
- 🧪 Tests directory with example tests
- 📝 `.gitignore` for your language
- 📖 `README.md` with setup instructions
- 📦 Dependency file (`requirements.txt`, `package.json`, etc.)
- 🔧 `.git` repository with initial commit
- 🐍 Python virtual environment (`.venv` for Python)

## Need Help?

- **Installation**: See [INSTALL.md](INSTALL.md)
- **Detailed Usage**: See [USAGE.md](USAGE.md)
- **Testing Guide**: See [TESTING.md](TESTING.md)
- **Main README**: See [README.md](README.md)

## Next Steps

1. ✅ Install newproj
2. ✅ Create your first project
3. ✅ Start developing
4. ✅ Push to GitHub (with `--gh`)

Happy coding! 🚀
