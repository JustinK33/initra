# Testing Guide

This guide shows how to test `initra` itself and verify that generated projects work correctly.

## Testing the initra CLI

### 0. Run Automated CLI Tests

```bash
python -m unittest discover -s tests
```

### 1. Test the CLI Directly

```bash
# Test help
python3 initra.py --help

# Test with a simple project
python3 initra.py test-app python flask
ls -la test-app
cat test-app/README.md
rm -rf test-app
```

### 2. Test Installation

```bash
# Install in editable mode
pip install -e .

# Test command is available
which initra
initra --help

# Generate a test project
initra test-install-cli python fastapi
cd test-install-cli
ls -la
```

## Testing Generated Projects

### Python (FastAPI)

```bash
initra test-fastapi python fastapi
cd test-fastapi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest discover -s tests

# Start the server
uvicorn src.main:app --reload
# Visit http://localhost:8000
# Visit http://localhost:8000/docs for API docs

# Deactivate
deactivate
cd ..
rm -rf test-fastapi
```

### Python (Flask)

```bash
initra test-flask python flask
cd test-flask

source .venv/bin/activate
pip install -r requirements.txt

# Run tests
python -m unittest discover -s tests

# Start the server
flask --app src.app run
# Visit http://localhost:5000

deactivate
cd ..
rm -rf test-flask
```

### Python (Django)

```bash
initra test-django python django
cd test-django

source .venv/bin/activate
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Run tests
python manage.py test

# Start the server
python manage.py runserver
# Visit http://localhost:8000

deactivate
cd ..
rm -rf test-django
```

### Node.js (Express - JavaScript)

```bash
initra test-express-js node express
cd test-express-js

# Install dependencies
npm install

# Verify package.json has correct structure
cat package.json

# Run tests
npm test

# Start the server
npm run dev
# Visit http://localhost:3000

cd ..
rm -rf test-express-js
```

### Node.js (Express - TypeScript)

```bash
initra test-express-ts node express --ts
cd test-express-ts

# Install dependencies
npm install

# Verify TypeScript configuration
cat tsconfig.json

# Run tests (with tsx)
npm test

# Build TypeScript
npm run build
ls -la dist/

# Start the development server (with tsx watch)
npm run dev
# Visit http://localhost:3000

# Start production server
node dist/index.js

cd ..
rm -rf test-express-ts
```

### Node.js (Next.js)

```bash
initra test-next node next
cd test-next

# If generated with --no-install
# npm install

# Verify Next.js structure
ls -la src/app/

# Start development server
npm run dev
# Visit http://localhost:3000

# Build for production
npm run build

# Start production server
npm start

cd ..
rm -rf test-next
```

### Node.js (Koa)

```bash
initra test-koa node koa
cd test-koa
npm install
npm test
npm run dev
cd ..
rm -rf test-koa
```

### Ruby (Rails)

Prerequisite: `gem install rails && gem install bundler`

```bash
initra test-rails ruby rails
cd test-rails

# Install dependencies
bundle install

# Verify structure
ls -la config/ db/ app/

# Run tests
bin/rails test

# Start the server
bin/rails server
# Visit http://localhost:3000

cd ..
rm -rf test-rails
```

### Ruby (Sinatra)

Prerequisite: `gem install bundler`

```bash
initra test-sinatra ruby sinatra
cd test-sinatra
bundle install
ruby test/test_app.rb
bundle exec ruby app.rb
cd ..
rm -rf test-sinatra
```

### Java (Spring Boot)

Prerequisite: `brew install spring-boot` (macOS) or equivalent

```bash
initra test-spring java springboot
cd test-spring

# Verify structure
ls -la src/ pom.xml

# Build and test
./mvnw clean test

# Run the application
./mvnw spring-boot:run
# Visit http://localhost:8080

cd ..
rm -rf test-spring
```

### Java (Javalin)

```bash
initra test-javalin java javalin
cd test-javalin
mvn test
mvn compile exec:java
cd ..
rm -rf test-javalin
```

## Verifying TypeScript Support

### Full TypeScript Validation

```bash
# Create a TypeScript Express project
initra ts-test node express --ts
cd ts-test

# Verify TypeScript files exist
test -f src/index.ts && echo "✓ src/index.ts"
test -f tests/app.test.ts && echo "✓ tests/app.test.ts"
test -f tsconfig.json && echo "✓ tsconfig.json"

# Verify package.json has TypeScript deps
grep '"typescript"' package.json && echo "✓ TypeScript in devDependencies"
grep '"@types/express"' package.json && echo "✓ @types/express installed"
grep '"tsx"' package.json && echo "✓ tsx installed"

# Install and compile
npm install

# Compile TypeScript
npm run build
test -f dist/index.js && echo "✓ dist/index.js compiled"

# Run tests with tsx
npm test

# Verify source maps
ls -la dist/

cd ..
echo "TypeScript validation complete!"
rm -rf ts-test
```

## Verifying Git & GitHub Integration

### Test Git Initialization

```bash
initra git-test python fastapi
cd git-test

# Verify git repo
test -d .git && echo "✓ Git repository initialized"

# Check initial commit
git log --oneline | head -1 && echo "✓ Initial commit created"

# Verify files are tracked
git status

cd ..
rm -rf git-test
```

## Success Criteria

A successful test run should:
- ✅ Show no errors during project creation
- ✅ Create all required files and directories
- ✅ Initialize a git repository with an initial commit
- ✅ Create valid dependency files (requirements.txt, package.json, etc.)
- ✅ Generate working code that can run without modification
- ✅ For TypeScript: compile without errors and pass tests
- ✅ For Python: tests pass after virtualenv activation and pip install
- ✅ For Node.js: npm install succeeds and tests pass
- ✅ For Ruby/Java: all dependencies install and tests pass
