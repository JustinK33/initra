# Usage Guide

## Basic Command Format

```bash
newproj <name> <language> <framework> [options]
```

### Required Arguments

- **`<name>`** – Project directory name (lowercase, hyphens allowed)
- **`<language>`** – Programming language: `python`, `node`, `ruby`, or `java`
- **`<framework>`** – Framework for the language (see Supported Stacks below)

### Options

- **`--ts`** – Use TypeScript for Node.js Express projects
- **`--gh`** – Create a GitHub repository (requires GitHub CLI and authentication)
- **`--public`** – Make the GitHub repository public (only with `--gh`)
- **`--open`** – Open the generated project in VS Code
- **`--no-install`** – Skip dependency/package installation steps
- **`--no-git`** – Skip git initialization and initial commit
- **`--dry-run`** – Preview commands/files without creating anything
- **`--output-dir`** – Set the base directory for project creation
- **`--json`** – Print machine-readable JSON output
- **`--list`** – Show all supported language/framework combos and exit

## Supported Stacks

### Python

| Framework | Command | Use Case |
|-----------|---------|----------|
| Flask     | `newproj myapp python flask` | Lightweight, flexible web API |
| FastAPI   | `newproj myapp python fastapi` | Modern, async web API |
| Django    | `newproj myapp python django` | Full-featured web framework |
| Aiohttp   | `newproj myapp python aiohttp` | Async web service framework |

**Example:**
```bash
newproj myapi python fastapi
cd myapi
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

### Node.js

| Framework | Command | Use Case |
|-----------|---------|----------|
| Express   | `newproj myapp node express` | Lightweight HTTP server |
| Express + TS | `newproj myapp node express --ts` | Type-safe Express server |
| Next.js   | `newproj myapp node next` | Full-stack React/SSR |
| Koa       | `newproj myapp node koa` | Minimal middleware-based server |

**Example with Express (JavaScript):**
```bash
newproj myserver node express
cd myserver
npm install
npm run dev
```

**Example with Express (TypeScript):**
```bash
newproj myserver node express --ts
cd myserver
npm install
npm run dev
```

**Example with Next.js:**
```bash
newproj myapp node next
cd myapp
npm run dev
```

### Ruby

| Framework | Command | Use Case |
|-----------|---------|----------|
| Rails     | `newproj myapp ruby rails` | Full-featured web framework |
| Sinatra   | `newproj myapp ruby sinatra` | Lightweight Ruby service framework |

**Example:**
```bash
newproj myblog ruby rails
cd myblog
bundle install
bin/rails server
```

### Java

| Framework | Command | Use Case |
|-----------|---------|----------|
| Spring Boot | `newproj myapp java springboot` | Enterprise-grade framework |
| Javalin | `newproj myapp java javalin` | Lightweight Java service framework |

**Example:**
```bash
newproj myapp java springboot
cd myapp
./mvnw spring-boot:run
```

## Common Examples

### Create a FastAPI REST API

```bash
newproj backend python fastapi
cd backend
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn src.main:app --reload
# Visit http://localhost:8000
```

### Create a TypeScript Express API with GitHub Integration

```bash
newproj api-service node express --ts --gh --public --open
cd api-service
npm install
npm run dev
```

This will:
1. Create an Express API with TypeScript
2. Initialize git and create a GitHub repository
3. Make the repo public
4. Open the project in VS Code

### Create a Django Blog with Full Setup

```bash
newproj blog-app python django
cd blog-app
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Create a Rails Full-Stack App

```bash
newproj ecommerce ruby rails
cd ecommerce
bundle install
bin/rails server
# Visit http://localhost:3000
```

### Create a Sinatra API

```bash
newproj micro ruby sinatra
cd micro
bundle install
bundle exec ruby app.rb
```

### Create a Spring Boot Microservice

```bash
newproj user-service java springboot
cd user-service
./mvnw spring-boot:run
# Visit http://localhost:8080/
```

### Create a Javalin Microservice

```bash
newproj edge java javalin
cd edge
mvn compile exec:java
# Visit http://localhost:7000/
```

### Create a Koa API

```bash
newproj gateway node koa
cd gateway
npm install
npm run dev
```

## Interactive Mode

If you run `newproj` with no arguments, it enters interactive mode:

```bash
$ newproj
No arguments supplied. Enter project details interactively.
Project name: myapp
Language options: java, node, python, ruby
Language: node
Framework options: express, express-ts, next
Framework: express
Create a GitHub repo with gh? [y/N] n
Open the project in VS Code? [Y/n] y
```

## Testing Generated Projects

### Python (Flask)

```bash
newproj testapp python flask
cd testapp
source .venv/bin/activate
python -m unittest discover -s tests
```

### Python (FastAPI)

```bash
newproj testapp python fastapi
cd testapp
source .venv/bin/activate
python -m unittest discover -s tests
```

### Node.js (Express - JavaScript)

```bash
newproj testapp node express
cd testapp
npm install
npm test
```

### Node.js (Express - TypeScript)

```bash
newproj testapp node express --ts
cd testapp
npm install
npm test
# Or run with tsx
npm run build
npm test
```

### Node.js (Next.js)

```bash
newproj testapp node next
cd testapp
npm run dev
# If generated with --no-install, run npm install first
```

### Automated CLI Test Suite

```bash
python -m unittest discover -s tests
```

### Ruby (Rails)

```bash
newproj testapp ruby rails
cd testapp
bundle install
bin/rails test
```

### Java (Spring Boot)

```bash
newproj testapp java springboot
cd testapp
./mvnw test
```

## Advanced Usage

### Using with Version Control

Generate a project and push to GitHub:

```bash
newproj myapp node express --ts --gh --open
cd myapp
git log --oneline  # View the initial commit
git remote -v      # View the GitHub remote
```

### Chaining Commands

```bash
newproj api python fastapi && \
cd api && \
source .venv/bin/activate && \
pip install -r requirements.txt && \
uvicorn src.main:app --reload
```

### Preview Without Creating Files

```bash
newproj demo node express --dry-run
```

### Create Projects in Another Directory

```bash
newproj api python fastapi --output-dir ~/workspaces
```

### JSON Output for Automation

```bash
newproj api node koa --dry-run --json --no-git
```

### List Supported Stacks

```bash
newproj --list
```

### Skip Dependency Installation

```bash
newproj backend python fastapi --no-install
# Later: activate .venv and run pip install -r requirements.txt
```

### Skip Git Initialization

```bash
newproj sandbox node express --no-git
```

### Creating Multiple Projects

```bash
# Create a frontend and backend
newproj frontend node next --open
newproj backend python fastapi --open

# Then work on both
ls -la frontend backend
```

## What Gets Created

Each generated project includes:

- **Source code** – Minimal working starter
- **Dependencies file** – `requirements.txt`, `package.json`, `pom.xml`, or `Gemfile`
- **Tests directory** – Basic test structure and example tests
- **.gitignore** – Language-appropriate ignores
- **README.md** – Project-specific documentation
- **.git** directory – Initial git repository with one commit

### Directory Structure Examples

**Python (FastAPI):**
```
myapi/
├── .venv/           # Virtual environment (auto-created)
├── src/
│   ├── __init__.py
│   └── main.py      # FastAPI app
├── tests/
│   ├── __init__.py
│   └── test_app.py
├── .gitignore
├── README.md
└── requirements.txt
```

**Node.js (Express + TypeScript):**
```
myserver/
├── node_modules/    # Dependencies (auto-installed)
├── src/
│   └── index.ts     # Express app
├── dist/            # Compiled output
├── tests/
│   └── app.test.ts
├── .gitignore
├── README.md
├── package.json
└── tsconfig.json
```

**Node.js (Next.js):**
```
myapp/
├── node_modules/
├── src/
│   └── app/         # App Router
├── .gitignore
├── .next/           # Build output
├── package.json
└── tsconfig.json
```

## Tips and Best Practices

1. **Use TypeScript for Express** – Better type safety and IDE support:
   ```bash
   newproj myserver node express --ts
   ```

2. **Activate Python virtualenv immediately:**
   ```bash
   newproj myapi python fastapi
   cd myapi
   source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
   ```

3. **Use `--gh` for easy GitHub integration:**
   ```bash
   newproj myapp python flask --gh --public
   ```

4. **Open in VS Code for instant editing:**
   ```bash
   newproj myapp node express --open
   ```

5. **Check the generated README:**
   ```bash
   newproj myapp ruby rails
   cd myapp
   cat README.md
   ```

## Troubleshooting

### Project Already Exists
```
error: Target directory already exists and is not empty: /path/to/myapp
```
Solution: Use a different project name or delete the existing directory.

### Missing Framework CLI
```
error: Required command not found: rails
```
Solution: Install the missing tool (e.g., `gem install rails` for Ruby).

### Git Author Not Configured
```
error: Git commit failed because user.name and user.email are not configured.
```
Solution:
```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

### GitHub CLI Not Found
```
error: `gh` was not found. Install GitHub CLI or omit --gh.
```
Solution: Install from https://cli.github.com or omit `--gh`.

### VS Code Not Found
```
error: VS Code was not found on PATH.
```
Solution: Install VS Code or open the project manually with `code myapp`.

## Support

For issues, questions, or feature requests, open an issue on GitHub or check the main [README.md](README.md).
