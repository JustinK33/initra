# Installation Guide

## Prerequisites

Before installing `initra`, make sure you have the following installed:

### Universal Requirements
- **Git** – version 2.0 or later
- **Python** – version 3.10 or later (for running the CLI)

### Framework-Specific Requirements

#### Python Projects
- **Python 3.10+** – included with the initra CLI
- Virtual environments are created automatically

#### Node.js Projects
- **Node.js** – version 16.0 or later
- **npm** – comes with Node.js

#### Ruby Projects
- **Ruby** – version 2.7 or later
- **Bundler** – install with `gem install bundler`

#### Java Projects
- **Spring CLI** – download from [spring.io](https://spring.io/tools) or install via package manager
  - **macOS** (Homebrew): `brew install spring-boot`
  - **Windows** (Chocolatey): `choco install springboot`
- **Java 21 or later** – required for Spring Boot starters
- **Maven** – optional, but recommended for building projects

### Optional

- **GitHub CLI** (`gh`) – for `--gh` flag to create GitHub repositories
  - **macOS** (Homebrew): `brew install gh`
  - **Windows** (Chocolatey): `choco install gh`
  - **Linux** (apt): `sudo apt install gh`
- **VS Code** – for `--open` flag to open projects in the editor

## Installation Methods

### 1. Recommended: Using pipx (Isolated Global Install)

`pipx` ensures the CLI runs in its own isolated virtual environment, preventing dependency conflicts:

```bash
# Install pipx if you don't have it
pip install --user pipx

# Install initra
pipx install /path/to/initra
```

Then verify the installation:
```bash
initra --help
```

To upgrade:
```bash
pipx upgrade initra
```

To uninstall:
```bash
pipx uninstall initra
```

### 2. Development / Editable Install

For contributing or testing the latest code:

```bash
cd /path/to/initra
pip install -e .
```

This installs the CLI in editable mode, so changes to `initra.py` are immediately reflected.

### 3. Manual Installation (No pip)

If you prefer, you can run the script directly:

```bash
python3 /path/to/initra/initra.py <name> <language> <framework>
```

Or add the directory to your PATH:
```bash
export PATH="/path/to/initra:$PATH"
```

Then run:
```bash
python3 initra.py myapp python fastapi
```

## Verification

### Test the Installation

```bash
# Display help
initra --help

# Create a test Flask app
initra test-flask python flask

# Check the generated project
cd test-flask
ls -la
cat README.md
```

### Test with Each Language

#### Python
```bash
initra myapi python fastapi
cd myapi
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload
```

#### Node.js (JavaScript)
```bash
initra myserver node express
cd myserver
npm install
npm run dev
```

#### Node.js (TypeScript)
```bash
initra myserver node express --ts
cd myserver
npm install
npm run dev
```

#### Node.js (Koa)
```bash
initra myservice node koa
cd myservice
npm install
npm run dev
```

#### Ruby
```bash
initra myblog ruby rails
cd myblog
bundle install
bin/rails server
```

#### Ruby (Sinatra)
```bash
initra mymicro ruby sinatra
cd mymicro
bundle install
bundle exec ruby app.rb
```

#### Java
```bash
initra myapp java springboot
cd myapp
./mvnw spring-boot:run
```

#### Java (Javalin)
```bash
initra mylight java javalin
cd mylight
mvn compile exec:java
```

### Useful Safety Flags

```bash
# Preview what would be generated without writing files
initra sample node express --dry-run

# Skip dependency installation
initra sample python fastapi --no-install

# Skip git init/add/commit
initra sample node express --no-git

# Create in custom directory and print JSON summary
initra sample node koa --output-dir ~/projects --dry-run --json

# List all supported stacks
initra --list
```

Note: Next.js projects install dependencies during generation by default. If you use `--no-install`, dependencies are skipped and you should run `npm install` manually.

## Troubleshooting

### "initra: command not found"
- Verify installation: `which initra` or `which python3`
- If using pipx, try: `pipx upgrade initra` or reinstall with `pipx install /path/to/initra`
- If using pip, try: `python3 -m pip show initra`

### "git: command not found"
- Install Git from https://git-scm.com

### "Python 3.10+ is required"
- Check your Python version: `python3 --version`
- Install a newer version from https://python.org

### "bundle: command not found" (Ruby)
- Install Bundler: `gem install bundler`

### "Spring CLI not found" (Java)
- Install Spring CLI:
  - macOS: `brew install spring-boot`
  - Windows: `choco install springboot`
  - Or download from https://spring.io/tools

### "gh: command not found" (GitHub integration)
- Install GitHub CLI: https://cli.github.com
- Alternatively, omit the `--gh` flag and create the GitHub repo manually

### ".gitignore or README not found"
- Verify the `templates/` directory exists in the initra installation
- Reinstall with: `pipx uninstall initra && pipx install /path/to/initra`

## Uninstallation

### pipx
```bash
pipx uninstall initra
```

### pip
```bash
pip uninstall initra
```

### Manual
Simply delete the initra directory or remove it from your PATH.
