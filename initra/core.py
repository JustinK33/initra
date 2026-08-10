"""Project specs, framework plans, and the file/template content initra writes.

Each supported stack has a ``generate_*_plan`` function that returns a
:class:`FrameworkPlan`: the files to write, the commands to run, and the text
that ends up in the generated README. ``ops`` consumes that plan to do the
actual scaffolding.
"""
from __future__ import annotations

import json
import platform
import sys
import textwrap
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path.cwd()
TEMPLATES_DIR = Path(__file__).with_name("templates")

SUPPORTED_LANGUAGES = {"python", "node", "ruby", "java", "go"}
SUPPORTED_FRAMEWORKS = {
    "python": {"flask", "fastapi", "django", "aiohttp"},
    "node": {"express", "express-ts", "next", "koa"},
    "ruby": {"rails", "sinatra"},
    "java": {"springboot", "javalin"},
    "go": {"gin"},
}


@dataclass
class ProjectSpec:
    name: str
    language: str
    framework: str
    path: Path
    gh: bool = False
    public: bool = False
    open_in_vscode: bool = False
    typescript: bool = False
    no_install: bool = False
    no_git: bool = False
    dry_run: bool = False
    output_json: bool = False
    tutorial: bool = False
    include_license: bool = False


@dataclass
class FrameworkPlan:
    files: list[tuple[str, str]]
    commands: list[list[str]]
    post_commands: list[list[str]]
    readme_summary: str
    readme_run: str
    readme_install: str
    project_notes: list[str]


class ScaffoldError(RuntimeError):
    pass


class CommandError(ScaffoldError):
    pass


def format_supported_stacks() -> str:
    lines = ["Supported stacks:"]
    for language in sorted(SUPPORTED_FRAMEWORKS):
        frameworks = ", ".join(sorted(SUPPORTED_FRAMEWORKS[language]))
        lines.append(f"- {language}: {frameworks}")
    return "\n".join(lines)


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


def sanitize_python_module_name(value: str) -> str:
    name = []
    for char in value.strip().lower():
        if char.isalnum() or char == "_":
            name.append(char)
        else:
            name.append("_")
    result = "".join(name).strip("_")
    if not result:
        result = "app"
    if result[0].isdigit():
        result = f"app_{result}"
    return result


def generate_framework_plan(spec: ProjectSpec) -> FrameworkPlan:
    if spec.language == "python":
        return generate_python_plan(spec)
    if spec.language == "node":
        return generate_node_plan(spec)
    if spec.language == "ruby":
        return generate_ruby_plan(spec)
    if spec.language == "java":
        return generate_java_plan(spec)
    if spec.language == "go":
        return generate_go_plan(spec)
    raise ScaffoldError(f"Unsupported language: {spec.language}")


def generate_python_plan(spec: ProjectSpec) -> FrameworkPlan:
    module_name = sanitize_python_module_name(spec.name)
    venv_path = spec.path / ".venv"
    pip = venv_executable(venv_path, "pip")
    django_admin = venv_executable(venv_path, "django-admin")
    requirements: list[str]
    files: list[tuple[str, str]] = [
        ("src/__init__.py", ""),
        ("tests/__init__.py", ""),
    ]
    commands = [[sys.executable, "-m", "venv", str(venv_path)]]
    post_commands: list[list[str]]

    if spec.framework == "flask":
        requirements = ["Flask>=3.0,<4.0"]
        flask_config = TUTORIAL_PYTHON_CONFIG if spec.tutorial else DEFAULT_PYTHON_CONFIG
        flask_db = TUTORIAL_PYTHON_DB if spec.tutorial else DEFAULT_PYTHON_DB
        flask_routes = TUTORIAL_FLASK_ROUTES if spec.tutorial else DEFAULT_FLASK_ROUTES
        flask_app = TUTORIAL_FLASK_TEMPLATE if spec.tutorial else DEFAULT_FLASK_TEMPLATE
        t = spec.tutorial
        files.extend([
            ("src/config.py", load_template("python/flask/src/config.py", flask_config, t)),
            ("src/db.py", load_template("python/flask/src/db.py", flask_db, t)),
            ("src/routes.py", render_template(load_template("python/flask/src/routes.py", flask_routes, t), {"project_name": spec.name})),
            (".env.example", DEFAULT_PYTHON_ENV),
        ])
        files.append(("src/app.py", render_template(load_template("python/flask/app.py", flask_app, t), {
            "project_name": spec.name,
            "module_name": module_name,
        })))
        files.append(("tests/test_health.py", render_template(DEFAULT_FLASK_TEST, {"module_name": module_name})))
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        post_commands = [] if spec.no_install else [[pip, "install", "--upgrade", "pip"], [pip, "install", "-r", "requirements.txt"]]
        summary = "A Flask starter with app factory, route module, and sqlite-ready db helper."
        install_text = (
            "Install the virtual environment and Flask dependencies with `python -m venv .venv` and `pip install -r requirements.txt`."
            if not spec.no_install
            else "Dependency installation was skipped due to `--no-install`."
        )
        run_text = "Activate the virtual environment and run `flask --app src.app:create_app run --debug`."
        notes = [
            "The project uses a local `.venv` that is ignored by git.",
            "Database path and runtime settings are environment-driven in `src/config.py`.",
        ]
    elif spec.framework == "fastapi":
        requirements = ["fastapi>=0.110,<1.0", "uvicorn[standard]>=0.30,<1.0"]
        fastapi_config = TUTORIAL_PYTHON_CONFIG if spec.tutorial else DEFAULT_PYTHON_CONFIG
        fastapi_db = TUTORIAL_PYTHON_DB if spec.tutorial else DEFAULT_PYTHON_DB
        fastapi_health = TUTORIAL_FASTAPI_HEALTH_ROUTES if spec.tutorial else DEFAULT_FASTAPI_HEALTH_ROUTES
        fastapi_users = TUTORIAL_FASTAPI_USERS_ROUTES if spec.tutorial else DEFAULT_FASTAPI_USERS_ROUTES
        fastapi_main = TUTORIAL_FASTAPI_TEMPLATE if spec.tutorial else DEFAULT_FASTAPI_TEMPLATE
        t = spec.tutorial
        files.extend([
            ("src/core/__init__.py", ""),
            ("src/core/config.py", load_template("python/fastapi/src/core/config.py", fastapi_config, t)),
            ("src/db.py", load_template("python/fastapi/src/db.py", fastapi_db, t)),
            ("src/api/__init__.py", ""),
            ("src/api/routes/__init__.py", ""),
            ("src/api/routes/health.py", render_template(load_template("python/fastapi/src/api/routes/health.py", fastapi_health, t), {"project_name": spec.name})),
            ("src/api/routes/users.py", render_template(load_template("python/fastapi/src/api/routes/users.py", fastapi_users, t), {"project_name": spec.name})),
            (".env.example", DEFAULT_PYTHON_ENV),
        ])
        files.append(("src/main.py", render_template(load_template("python/fastapi/main.py", fastapi_main, t), {
            "project_name": spec.name,
            "module_name": module_name,
        })))
        files.append(("tests/test_health.py", render_template(DEFAULT_FASTAPI_TEST, {"project_name": spec.name})))
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        post_commands = [] if spec.no_install else [[pip, "install", "--upgrade", "pip"], [pip, "install", "-r", "requirements.txt"]]
        summary = "A FastAPI starter with modular routes, settings, and sqlite-ready db helper."
        install_text = (
            "Create a virtual environment and install dependencies with `python -m venv .venv` and `pip install -r requirements.txt`."
            if not spec.no_install
            else "Dependency installation was skipped due to `--no-install`."
        )
        run_text = "Activate the virtual environment and run `uvicorn src.main:app --reload`."
        notes = [
            "The app is ready for Uvicorn out of the box.",
            "Route handlers are organized under `src/api/routes`.",
        ]
    elif spec.framework == "django":
        if spec.no_install:
            raise ScaffoldError("`--no-install` is not supported for Django because project generation requires installed Django tooling.")
        requirements = ["Django>=5.0,<6.0"]
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        files.append(("tests/.gitkeep", ""))
        post_commands = [
            [pip, "install", "--upgrade", "pip"],
            [pip, "install", "-r", "requirements.txt"],
            [django_admin, "startproject", module_name, "."],
        ]
        summary = "An official Django project generated with django-admin startproject."
        install_text = "Create a virtual environment and install Django with `python -m venv .venv` and `pip install -r requirements.txt`."
        run_text = "Activate the virtual environment and run `python manage.py runserver`."
        notes = ["The Django project is generated with the official Django CLI."]
    else:
        requirements = ["aiohttp>=3.10,<4.0"]
        aiohttp_config = TUTORIAL_PYTHON_CONFIG if spec.tutorial else DEFAULT_PYTHON_CONFIG
        aiohttp_db = TUTORIAL_PYTHON_DB if spec.tutorial else DEFAULT_PYTHON_DB
        aiohttp_routes = TUTORIAL_AIOHTTP_ROUTES if spec.tutorial else DEFAULT_AIOHTTP_ROUTES
        aiohttp_main = TUTORIAL_AIOHTTP_TEMPLATE if spec.tutorial else DEFAULT_AIOHTTP_TEMPLATE
        t = spec.tutorial
        files.extend([
            ("src/config.py", load_template("python/aiohttp/src/config.py", aiohttp_config, t)),
            ("src/db.py", load_template("python/aiohttp/src/db.py", aiohttp_db, t)),
            ("src/routes.py", render_template(load_template("python/aiohttp/src/routes.py", aiohttp_routes, t), {"project_name": spec.name})),
            (".env.example", DEFAULT_PYTHON_ENV),
        ])
        files.append(("src/main.py", render_template(load_template("python/aiohttp/main.py", aiohttp_main, t), {
            "project_name": spec.name,
            "module_name": module_name,
        })))
        files.append(("tests/test_health.py", render_template(DEFAULT_AIOHTTP_TEST, {"project_name": spec.name})))
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        post_commands = [] if spec.no_install else [[pip, "install", "--upgrade", "pip"], [pip, "install", "-r", "requirements.txt"]]
        summary = "An aiohttp starter with separated routes, config, and sqlite-ready db helper."
        install_text = (
            "Create a virtual environment and install dependencies with `python -m venv .venv` and `pip install -r requirements.txt`."
            if not spec.no_install
            else "Dependency installation was skipped due to `--no-install`."
        )
        run_text = "Activate the virtual environment and run `python -m src.main`."
        notes = [
            "The app is built with aiohttp and ready for async request handling.",
            "Database utilities are intentionally lightweight for easy replacement with Postgres later.",
        ]
    return FrameworkPlan(
        files=files,
        commands=commands,
        post_commands=post_commands,
        readme_summary=summary,
        readme_run=run_text,
        readme_install=install_text,
        project_notes=notes,
    )


def generate_node_plan(spec: ProjectSpec) -> FrameworkPlan:
    if spec.framework == "next":
        command = [
            "npx",
            "create-next-app@latest",
            spec.name,
            "--yes",
            "--use-npm",
            "--eslint",
            "--app",
            "--src-dir",
            "--import-alias",
            "@/*",
        ]
        if spec.typescript:
            command.append("--typescript")
        else:
            command.append("--javascript")
        command.append("--no-tailwind")
        if spec.no_install:
            command.append("--skip-install")
        install_text = (
            "Dependencies are installed automatically by create-next-app."
            if not spec.no_install
            else "Dependencies were skipped due to `--no-install`; run `npm install` before starting the app."
        )
        return FrameworkPlan(
            files=[],
            commands=[command],
            post_commands=[],
            readme_summary="A Next.js starter created with create-next-app.",
            readme_run="Run `npm run dev`.",
            readme_install=install_text,
            project_notes=["The project was generated with the official Next.js scaffold."],
        )

    if spec.framework == "koa":
        files = build_simple_node_files(spec.name, "koa", spec.tutorial, include_license=spec.include_license)
        post_commands = [] if spec.no_install else [["npm", "install"]]
        install_text = "Install dependencies with `npm install`." if not spec.no_install else "Dependency installation was skipped due to `--no-install`."
        return FrameworkPlan(
            files=files,
            commands=[],
            post_commands=post_commands,
            readme_summary="A beginner-friendly Koa starter with routes, controllers, services, and in-memory users.",
            readme_run="Run `npm run dev` during development or `npm start` in production.",
            readme_install=install_text,
            project_notes=["The project keeps data in memory and separates route, controller, and service code."] ,
        )

    use_ts = spec.framework == "express-ts"
    files = build_simple_node_files(
        spec.name,
        "express-ts" if use_ts else "express",
        spec.tutorial,
        include_license=spec.include_license,
    )

    post_commands = [] if spec.no_install else [["npm", "install"]]
    install_text = "Install dependencies with `npm install`." if not spec.no_install else "Dependency installation was skipped due to `--no-install`."

    return FrameworkPlan(
        files=files,
        commands=[],
        post_commands=post_commands,
        readme_summary="A beginner-friendly Express starter with routes, controllers, services, and in-memory users.",
        readme_run="Run `npm run dev` during development or `npm start` in production.",
        readme_install=install_text,
        project_notes=["The project keeps data in memory and separates route, controller, and service code."],
    )


def generate_ruby_plan(spec: ProjectSpec) -> FrameworkPlan:
    if spec.framework == "sinatra":
        sinatra_app = TUTORIAL_SINATRA_APP if spec.tutorial else DEFAULT_SINATRA_APP
        files = [
            ("Gemfile", load_template("ruby/sinatra/Gemfile", DEFAULT_SINATRA_GEMFILE)),
            ("app.rb", render_template(load_template("ruby/sinatra/app.rb", sinatra_app), {"project_name": spec.name})),
            ("config.ru", load_template("ruby/sinatra/config.ru", DEFAULT_SINATRA_RACKUP)),
            ("lib/config.rb", load_template("ruby/sinatra/lib/config.rb", DEFAULT_SINATRA_CONFIG)),
            ("lib/db.rb", load_template("ruby/sinatra/lib/db.rb", DEFAULT_SINATRA_DB)),
            ("test/test_app.rb", render_template(load_template("ruby/sinatra/test/test_app.rb", DEFAULT_SINATRA_TEST), {"project_name": spec.name})),
            (".env.example", DEFAULT_RUBY_ENV),
        ]
        post_commands = [] if spec.no_install else [["bundle", "install"]]
        install_text = "Run `bundle install` to install Ruby gems." if not spec.no_install else "Gem installation was skipped due to `--no-install`."
        return FrameworkPlan(
            files=files,
            commands=[],
            post_commands=post_commands,
            readme_summary="A Sinatra starter with modular config, db helper, and JSON health endpoint.",
            readme_run="Run `bundle exec ruby app.rb`.",
            readme_install=install_text,
            project_notes=[
                "The generated app includes a minimal Rack setup and Minitest example.",
                "Database configuration is isolated in `lib/db.rb` for easy adapter swaps.",
            ],
        )

    post_commands = [] if spec.no_install else [["bundle", "install"]]
    install_text = "Run `bundle install` to install Ruby gems." if not spec.no_install else "Gem installation was skipped due to `--no-install`."
    return FrameworkPlan(
        files=[],
        commands=[["rails", "new", spec.name, "--skip-bundle"]],
        post_commands=post_commands,
        readme_summary="A Rails application generated with rails new.",
        readme_run="Run `bin/rails server`.",
        readme_install=install_text,
        project_notes=["Rails generated the framework files and Bundler installs dependencies on demand."],
    )


def generate_java_plan(spec: ProjectSpec) -> FrameworkPlan:
    if spec.framework == "javalin":
        javalin_app = TUTORIAL_JAVALIN_APP if spec.tutorial else DEFAULT_JAVALIN_APP
        files = [
            ("pom.xml", render_template(load_template("java/javalin/pom.xml", build_javalin_pom(spec.name)), {"project_name": spec.name})),
            ("Dockerfile", render_template(load_template("java/javalin/Dockerfile", DEFAULT_JAVALIN_DOCKERFILE), {"project_name": spec.name})),
            (".env.example", render_template(load_template("java/javalin/.env.example", DEFAULT_JAVA_ENV), {"project_name": spec.name})),
            ("src/main/resources/application.properties", render_template(load_template("java/javalin/src/main/resources/application.properties", DEFAULT_JAVALIN_PROPERTIES), {"project_name": spec.name})),
            ("src/main/java/com/example/App.java", render_template(load_template("java/javalin/src/main/java/com/example/App.java", javalin_app), {"project_name": spec.name})),
            ("src/main/java/com/example/config/AppConfig.java", render_template(load_template("java/javalin/src/main/java/com/example/config/AppConfig.java", DEFAULT_JAVALIN_CONFIG), {"project_name": spec.name})),
            ("src/main/java/com/example/routes/HealthRoutes.java", load_template("java/javalin/src/main/java/com/example/routes/HealthRoutes.java", DEFAULT_JAVALIN_HEALTH_ROUTES)),
            ("src/main/java/com/example/routes/UserRoutes.java", load_template("java/javalin/src/main/java/com/example/routes/UserRoutes.java", DEFAULT_JAVALIN_USER_ROUTES)),
            ("src/main/java/com/example/controllers/HealthController.java", render_template(load_template("java/javalin/src/main/java/com/example/controllers/HealthController.java", DEFAULT_JAVALIN_HEALTH_CONTROLLER), {"project_name": spec.name})),
            ("src/main/java/com/example/controllers/UserController.java", load_template("java/javalin/src/main/java/com/example/controllers/UserController.java", DEFAULT_JAVALIN_USER_CONTROLLER)),
            ("src/main/java/com/example/services/UserService.java", load_template("java/javalin/src/main/java/com/example/services/UserService.java", DEFAULT_JAVALIN_USER_SERVICE)),
            ("src/main/java/com/example/models/User.java", load_template("java/javalin/src/main/java/com/example/models/User.java", DEFAULT_JAVALIN_USER_MODEL)),
            ("src/main/java/com/example/dto/CreateUserRequest.java", load_template("java/javalin/src/main/java/com/example/dto/CreateUserRequest.java", DEFAULT_JAVALIN_CREATE_DTO)),
            ("src/main/java/com/example/dto/UpdateUserRequest.java", load_template("java/javalin/src/main/java/com/example/dto/UpdateUserRequest.java", DEFAULT_JAVALIN_UPDATE_DTO)),
            ("src/main/java/com/example/dto/UserResponse.java", load_template("java/javalin/src/main/java/com/example/dto/UserResponse.java", DEFAULT_JAVALIN_USER_RESPONSE_DTO)),
            ("src/main/java/com/example/exceptions/ApiException.java", load_template("java/javalin/src/main/java/com/example/exceptions/ApiException.java", DEFAULT_JAVALIN_API_EXCEPTION)),
            ("src/main/java/com/example/exceptions/NotFoundException.java", load_template("java/javalin/src/main/java/com/example/exceptions/NotFoundException.java", DEFAULT_JAVALIN_NOT_FOUND_EXCEPTION)),
            ("src/main/java/com/example/exceptions/ValidationException.java", load_template("java/javalin/src/main/java/com/example/exceptions/ValidationException.java", DEFAULT_JAVALIN_VALIDATION_EXCEPTION)),
            ("src/main/java/com/example/middleware/ExceptionMapper.java", load_template("java/javalin/src/main/java/com/example/middleware/ExceptionMapper.java", DEFAULT_JAVALIN_EXCEPTION_MAPPER)),
            ("src/main/java/com/example/middleware/RequestLoggingMiddleware.java", load_template("java/javalin/src/main/java/com/example/middleware/RequestLoggingMiddleware.java", DEFAULT_JAVALIN_REQUEST_LOGGING)),
            ("src/main/java/com/example/utils/ValidationUtils.java", load_template("java/javalin/src/main/java/com/example/utils/ValidationUtils.java", DEFAULT_JAVALIN_VALIDATION_UTILS)),
            ("src/main/java/com/example/repository/UserRepository.java", load_template("java/javalin/src/main/java/com/example/repository/UserRepository.java", DEFAULT_JAVALIN_USER_REPOSITORY)),
            ("src/main/java/com/example/repository/InMemoryUserRepository.java", load_template("java/javalin/src/main/java/com/example/repository/InMemoryUserRepository.java", DEFAULT_JAVALIN_INMEMORY_REPOSITORY)),
            ("src/test/java/com/example/services/UserServiceTest.java", load_template("java/javalin/src/test/java/com/example/services/UserServiceTest.java", DEFAULT_JAVALIN_SERVICE_TEST)),
            ("src/test/java/com/example/integration/HealthRoutesIntegrationTest.java", render_template(load_template("java/javalin/src/test/java/com/example/integration/HealthRoutesIntegrationTest.java", DEFAULT_JAVALIN_HEALTH_IT), {"project_name": spec.name})),
            ("src/test/java/com/example/integration/UserRoutesIntegrationTest.java", load_template("java/javalin/src/test/java/com/example/integration/UserRoutesIntegrationTest.java", DEFAULT_JAVALIN_USER_IT)),
        ]
        return FrameworkPlan(
            files=files,
            commands=[],
            post_commands=[],
            readme_summary="A production-style Javalin API starter with layered architecture, DTOs, middleware, and tests.",
            readme_run="Run `mvn compile exec:java`. Run tests with `mvn test`. Build an image with `docker build -t {{project_name}} .`.",
            readme_install="Install Java 21 and Maven, then run `mvn clean package` to resolve dependencies.",
            project_notes=[
                "Includes `/health` plus CRUD routes for `/users` and `/users/{id}`.",
                "Persistence is in-memory via `InMemoryUserRepository` and can be replaced by a database-backed implementation later.",
                "Centralized exception handling and request logging middleware are wired at startup.",
            ],
        )

    command = [
        "spring",
        "init",
        "--build",
        "maven",
        "--java-version",
        "21",
        "--dependencies",
        "web,actuator",
        spec.name,
    ]
    return FrameworkPlan(
        files=[],
        commands=[command],
        post_commands=[],
        readme_summary="A Spring Boot application created with the Spring Initializr CLI.",
        readme_run="Run `./mvnw spring-boot:run` or `mvn spring-boot:run`.",
        readme_install="The Maven dependencies are already defined in the generated `pom.xml`.",
        project_notes=["The project uses Spring Initializr with web and actuator starters."],
    )


GO_GIN_FILES = [
    "go.mod",
    "main.go",
    "Dockerfile",
    ".dockerignore",
    ".env.example",
    "internal/config/config.go",
    "internal/router/router.go",
    "internal/middleware/logger.go",
    "internal/models/user.go",
    "internal/store/user_store.go",
    "internal/handlers/health.go",
    "internal/handlers/users.go",
    "internal/handlers/users_test.go",
]


def generate_go_plan(spec: ProjectSpec) -> FrameworkPlan:
    # ponytail: templates live on disk only (no inline fallback), so load_template
    # raises if one is missing instead of writing an empty file. No tutorial
    # variants yet -- `-t` falls through to the standard templates.
    files = [
        (path, render_template(load_template(f"go/gin/{path}"), {"project_name": spec.name}))
        for path in GO_GIN_FILES
    ]
    post_commands = [] if spec.no_install else [["go", "mod", "tidy"]]
    return FrameworkPlan(
        files=files,
        commands=[],
        post_commands=post_commands,
        readme_summary="A Gin API starter with layered handlers, an in-memory store, and graceful shutdown.",
        readme_run="Run `go run .`, then visit http://localhost:8080/health. Run tests with `go test ./...`.",
        readme_install="Install Go 1.22 or newer, then run `go mod tidy` to download dependencies.",
        project_notes=[
            "Includes `/health` plus CRUD routes for `/users` and `/users/:id`.",
            "Request bodies are validated by Gin binding tags on the structs in `internal/models`.",
            "`internal/store` keeps users in memory behind a mutex and can be swapped for a database later.",
            "`main.go` runs an `http.Server` with graceful shutdown on SIGINT/SIGTERM.",
        ],
    )


def build_express_package_json(project_name: str, use_ts: bool, include_license: bool = False) -> str:
    data = {
        "name": project_name,
        "version": "1.0.0",
        "private": True,
        "description": f"{project_name} beginner-friendly Express application",
        "main": "dist/index.js" if use_ts else "src/index.js",
        "scripts": {
            "dev": "tsx watch src/server.ts" if use_ts else "nodemon src/server.js",
            "start": "tsx src/server.ts" if use_ts else "node src/server.js",
            "test": "node --test" if not use_ts else "tsx --test tests/app.test.ts",
            "lint": "eslint .",
            "format": "prettier --write .",
        },
        "keywords": ["express", "beginner", "users"],
    }
    if include_license:
        data["license"] = "MIT"
    data["dependencies"] = {"express": "^5.0.0", "dotenv": "^16.4.5", "supertest": "^7.1.1"}
    if use_ts:
        data["type"] = "commonjs"
        data["devDependencies"] = {
            "@types/express": "^5.0.0",
            "@types/node": "^22.0.0",
            "@types/supertest": "^6.0.2",
            "nodemon": "^3.1.4",
            "tsx": "^4.16.0",
            "eslint": "^9.9.0",
            "prettier": "^3.3.3",
            "typescript": "^5.7.0",
        }
    else:
        data["devDependencies"] = {
            "nodemon": "^3.1.4",
            "eslint": "^9.9.0",
            "prettier": "^3.3.3",
        }
    return json.dumps(data, indent=2) + "\n"


def build_simple_node_files(
    project_name: str,
    variant: str,
    tutorial: bool = False,
    include_license: bool = False,
) -> list[tuple[str, str]]:
    if variant == "koa":
        return build_simple_koa_files(project_name, tutorial, include_license=include_license)

    is_ts = variant == "express-ts"
    template_root = "node/express-ts" if is_ts else "node/express-js"
    app_file = "src/app.ts" if is_ts else "src/app.js"
    server_file = "src/server.ts" if is_ts else "src/server.js"
    route_file = "src/routes/index.ts" if is_ts else "src/routes/index.js"
    health_file = "src/routes/health.ts" if is_ts else "src/routes/health.js"
    user_file = "src/routes/users.ts" if is_ts else "src/routes/users.js"
    controller_file = "src/controllers/userController.ts" if is_ts else "src/controllers/userController.js"
    service_file = "src/services/userService.ts" if is_ts else "src/services/userService.js"
    model_file = "src/models/userStore.ts" if is_ts else "src/models/userStore.js"
    middleware_file = "src/middleware/errorHandler.ts" if is_ts else "src/middleware/errorHandler.js"
    logger_file = "src/middleware/logger.ts" if is_ts else "src/middleware/logger.js"
    config_file = "src/config/index.ts" if is_ts else "src/config/index.js"
    utils_file = "src/utils/validation.ts" if is_ts else "src/utils/validation.js"
    tests_file = "tests/app.test.ts" if is_ts else "tests/app.test.js"

    # Select tutorial or regular templates
    server_template = TUTORIAL_EXPRESS_SERVER if tutorial else (DEFAULT_NODE_SERVER_TEMPLATE_TS if is_ts else DEFAULT_NODE_SERVER_TEMPLATE_JS)
    health_template = TUTORIAL_EXPRESS_HEALTH_ROUTE if tutorial else (DEFAULT_NODE_HEALTH_ROUTE_TS if is_ts else DEFAULT_NODE_HEALTH_ROUTE_JS)

    files = [
        ("package.json", build_express_package_json(project_name, is_ts, include_license=include_license)),
        (".env.example", DEFAULT_NODE_ENV_EXAMPLE),
        ("Dockerfile", DEFAULT_NODE_DOCKERFILE),
        (".dockerignore", DEFAULT_NODE_DOCKERIGNORE),
        (".eslintrc.json", DEFAULT_NODE_ESLINTRC),
        (".prettierrc", DEFAULT_NODE_PRETTIERRC),
        (app_file, render_template(load_template(f"{template_root}/{app_file}", DEFAULT_NODE_APP_TEMPLATE_TS if is_ts else DEFAULT_NODE_APP_TEMPLATE_JS), {"project_name": project_name})),
        (server_file, render_template(load_template(f"{template_root}/{server_file}", server_template), {"project_name": project_name})),
        (config_file, load_template(f"{template_root}/{config_file}", DEFAULT_NODE_CONFIG_TS if is_ts else DEFAULT_NODE_CONFIG_JS)),
        (route_file, render_template(load_template(f"{template_root}/{route_file}", DEFAULT_NODE_ROUTE_INDEX_TS if is_ts else DEFAULT_NODE_ROUTE_INDEX_JS), {"project_name": project_name})),
        (health_file, render_template(load_template(f"{template_root}/{health_file}", health_template), {"project_name": project_name})),
        (user_file, render_template(load_template(f"{template_root}/{user_file}", DEFAULT_NODE_USERS_ROUTE_TS if is_ts else DEFAULT_NODE_USERS_ROUTE_JS), {"project_name": project_name})),
        (controller_file, render_template(load_template(f"{template_root}/{controller_file}", DEFAULT_NODE_USER_CONTROLLER_TS if is_ts else DEFAULT_NODE_USER_CONTROLLER_JS), {"project_name": project_name})),
        (service_file, render_template(load_template(f"{template_root}/{service_file}", DEFAULT_NODE_USER_SERVICE_TS if is_ts else DEFAULT_NODE_USER_SERVICE_JS), {"project_name": project_name})),
        (model_file, render_template(load_template(f"{template_root}/{model_file}", DEFAULT_NODE_USER_STORE_TS if is_ts else DEFAULT_NODE_USER_STORE_JS), {"project_name": project_name})),
        (middleware_file, load_template(f"{template_root}/{middleware_file}", DEFAULT_NODE_ERROR_HANDLER_TS if is_ts else DEFAULT_NODE_ERROR_HANDLER_JS)),
        (logger_file, load_template(f"{template_root}/{logger_file}", DEFAULT_NODE_LOGGER_TS if is_ts else DEFAULT_NODE_LOGGER_JS)),
        (utils_file, load_template(f"{template_root}/{utils_file}", DEFAULT_NODE_VALIDATION_TS if is_ts else DEFAULT_NODE_VALIDATION_JS)),
        (tests_file, render_template(load_template(f"{template_root}/{tests_file}", DEFAULT_NODE_TEST_TS if is_ts else DEFAULT_NODE_TEST_JS), {"project_name": project_name})),
    ]
    if is_ts:
        files.append(("tsconfig.json", load_template(f"{template_root}/tsconfig.json", DEFAULT_NODE_TSCONFIG)))
    return files


def build_simple_koa_files(
    project_name: str,
    tutorial: bool = False,
    include_license: bool = False,
) -> list[tuple[str, str]]:
    template_root = "node/koa"

    # Select tutorial or regular templates
    server_template = TUTORIAL_KOA_SERVER if tutorial else DEFAULT_KOA_SIMPLE_SERVER
    health_template = TUTORIAL_KOA_HEALTH_ROUTE if tutorial else DEFAULT_KOA_SIMPLE_HEALTH_ROUTE

    return [
        ("package.json", build_koa_package_json(project_name, include_license=include_license)),
        (".env.example", DEFAULT_NODE_ENV_EXAMPLE),
        ("Dockerfile", DEFAULT_NODE_DOCKERFILE),
        (".dockerignore", DEFAULT_NODE_DOCKERIGNORE),
        (".eslintrc.json", DEFAULT_NODE_ESLINTRC),
        (".prettierrc", DEFAULT_NODE_PRETTIERRC),
        ("src/app.js", render_template(load_template(f"{template_root}/src/app.js", DEFAULT_KOA_SIMPLE_APP), {"project_name": project_name})),
        ("src/server.js", render_template(load_template(f"{template_root}/src/server.js", server_template), {"project_name": project_name})),
        ("src/config/index.js", load_template(f"{template_root}/src/config/index.js", DEFAULT_NODE_CONFIG_JS)),
        ("src/routes/index.js", render_template(load_template(f"{template_root}/src/routes/index.js", DEFAULT_KOA_SIMPLE_ROUTE_INDEX), {"project_name": project_name})),
        ("src/routes/health.js", render_template(load_template(f"{template_root}/src/routes/health.js", health_template), {"project_name": project_name})),
        ("src/routes/users.js", render_template(load_template(f"{template_root}/src/routes/users.js", DEFAULT_KOA_SIMPLE_USERS_ROUTE), {"project_name": project_name})),
        ("src/controllers/userController.js", render_template(load_template(f"{template_root}/src/controllers/userController.js", DEFAULT_KOA_SIMPLE_USER_CONTROLLER), {"project_name": project_name})),
        ("src/services/userService.js", render_template(load_template(f"{template_root}/src/services/userService.js", DEFAULT_KOA_SIMPLE_USER_SERVICE), {"project_name": project_name})),
        ("src/models/userStore.js", render_template(load_template(f"{template_root}/src/models/userStore.js", DEFAULT_NODE_USER_STORE_JS), {"project_name": project_name})),
        ("src/middleware/errorHandler.js", load_template(f"{template_root}/src/middleware/errorHandler.js", DEFAULT_KOA_SIMPLE_ERROR_HANDLER)),
        ("src/middleware/logger.js", load_template(f"{template_root}/src/middleware/logger.js", DEFAULT_KOA_SIMPLE_LOGGER)),
        ("src/utils/validation.js", load_template(f"{template_root}/src/utils/validation.js", DEFAULT_KOA_SIMPLE_VALIDATION)),
        ("tests/app.test.js", render_template(load_template(f"{template_root}/tests/app.test.js", DEFAULT_KOA_SIMPLE_TEST), {"project_name": project_name})),
    ]


def build_koa_package_json(project_name: str, include_license: bool = False) -> str:
    data = {
        "name": project_name,
        "version": "1.0.0",
        "private": True,
        "description": f"{project_name} beginner-friendly Koa application",
        "main": "src/index.js",
        "scripts": {
            "dev": "nodemon src/server.js",
            "start": "node src/server.js",
            "test": "node --test",
            "lint": "eslint .",
            "format": "prettier --write .",
        },
        "keywords": ["koa", "beginner", "users"],
        "dependencies": {
            "koa": "^2.15.0",
            "@koa/router": "^12.0.1",
            "koa-bodyparser": "^4.4.1",
            "dotenv": "^16.4.5",
            "supertest": "^7.1.1",
        },
        "devDependencies": {
            "nodemon": "^3.1.4",
            "eslint": "^9.9.0",
            "prettier": "^3.3.3",
        },
    }
    if include_license:
        data["license"] = "MIT"
    return json.dumps(data, indent=2) + "\n"


def build_javalin_pom(project_name: str) -> str:
    return render_template(
        DEFAULT_JAVALIN_POM,
        {
            "project_name": project_name,
        },
    )


EXPRESS_TS_CONFIG = textwrap.dedent(
    """
    {
      "compilerOptions": {
        "target": "ES2020",
        "module": "CommonJS",
        "moduleResolution": "Node",
        "rootDir": "src",
        "outDir": "dist",
        "strict": true,
        "esModuleInterop": true,
        "skipLibCheck": true,
        "forceConsistentCasingInFileNames": true,
        "types": ["node"]
      },
      "include": ["src/**/*.ts", "tests/**/*.ts"],
      "exclude": ["node_modules", "dist"]
    }
    """
).strip() + "\n"


DEFAULT_FLASK_TEMPLATE = textwrap.dedent(
    """
    from flask import Flask

    from src.routes import health_bp


    def create_app() -> Flask:
        app = Flask(__name__)
        app.register_blueprint(health_bp)
        return app


    app = create_app()


    if __name__ == "__main__":
        app.run(debug=True)
    """
).strip() + "\n"


DEFAULT_FASTAPI_TEMPLATE = textwrap.dedent(
    """
    from fastapi import FastAPI

    from src.api.routes.health import router as health_router
    from src.api.routes.users import router as users_router

    app = FastAPI(title="{{project_name}}")
    app.include_router(health_router)
    app.include_router(users_router)


    @app.get("/readyz")
    def ready() -> dict[str, str]:
        return {"status": "ready", "project": "{{project_name}}"}
    """
).strip() + "\n"


DEFAULT_PYTHON_CONFIG = textwrap.dedent(
    """
    import os
    from dataclasses import dataclass


    @dataclass(frozen=True)
    class Settings:
        env: str = os.getenv("APP_ENV", "development")
        db_url: str = os.getenv("DATABASE_URL", "sqlite:///data/app.db")


    settings = Settings()
    """
).strip() + "\n"


DEFAULT_PYTHON_DB = textwrap.dedent(
    """
    from pathlib import Path
    import sqlite3

    from src.config import settings


    def _sqlite_path() -> Path:
        raw = settings.db_url
        if raw.startswith("sqlite:///"):
            return Path(raw.replace("sqlite:///", "", 1))
        return Path("data/app.db")


    def get_connection() -> sqlite3.Connection:
        db_path = _sqlite_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection
    """
).strip() + "\n"


DEFAULT_FLASK_ROUTES = textwrap.dedent(
    """
    from flask import Blueprint, jsonify

    from src.config import settings


    health_bp = Blueprint("health", __name__)
    users: list[dict[str, object]] = []
    next_id = 1


    @health_bp.get("/")
    def health() -> tuple[dict[str, str], int]:
        return jsonify(status="ok", project="{{project_name}}", env=settings.env), 200


    @health_bp.get("/users")
    def list_users() -> tuple[dict[str, object], int]:
        return jsonify(users=users), 200


    @health_bp.get("/users/<int:user_id>")
    def get_user(user_id: int) -> tuple[dict[str, object], int]:
        for user in users:
            if user["id"] == user_id:
                return jsonify(user), 200
        return jsonify(error="User not found"), 404


    @health_bp.post("/users")
    def create_user() -> tuple[dict[str, object], int]:
        global next_id
        from flask import request

        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        if len(name) < 2 or "@" not in email:
            return jsonify(error="Invalid name or email"), 400

        user = {"id": next_id, "name": name, "email": email.lower()}
        next_id += 1
        users.append(user)
        return jsonify(user), 201


    @health_bp.put("/users/<int:user_id>")
    def update_user(user_id: int) -> tuple[dict[str, object], int]:
        from flask import request

        payload = request.get_json(silent=True) or {}
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        if len(name) < 2 or "@" not in email:
            return jsonify(error="Invalid name or email"), 400

        for user in users:
            if user["id"] == user_id:
                user["name"] = name
                user["email"] = email.lower()
                return jsonify(user), 200
        return jsonify(error="User not found"), 404


    @health_bp.delete("/users/<int:user_id>")
    def delete_user(user_id: int) -> tuple[dict[str, str], int]:
        for index, user in enumerate(users):
            if user["id"] == user_id:
                users.pop(index)
                return jsonify(status="deleted"), 200
        return jsonify(error="User not found"), 404
    """
).strip() + "\n"


DEFAULT_FASTAPI_HEALTH_ROUTES = textwrap.dedent(
    """
    from fastapi import APIRouter

    from src.config import settings


    router = APIRouter()


    @router.get("/")
    def health() -> dict[str, str]:
        return {"status": "ok", "project": "{{project_name}}", "env": settings.env}
    """
).strip() + "\n"


DEFAULT_FASTAPI_USERS_ROUTES = textwrap.dedent(
    """
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel, EmailStr


    class UserCreate(BaseModel):
        name: str
        email: EmailStr


    class User(UserCreate):
        id: int


    router = APIRouter(prefix="/users", tags=["users"])
    users: list[User] = []
    next_id = 1


    @router.get("/", response_model=list[User])
    def list_users() -> list[User]:
        return users


    @router.get("/{user_id}", response_model=User)
    def get_user(user_id: int) -> User:
        for user in users:
            if user.id == user_id:
                return user
        raise HTTPException(status_code=404, detail="User not found")


    @router.post("/", response_model=User, status_code=201)
    def create_user(payload: UserCreate) -> User:
        global next_id
        user = User(id=next_id, name=payload.name.strip(), email=payload.email)
        next_id += 1
        users.append(user)
        return user


    @router.put("/{user_id}", response_model=User)
    def update_user(user_id: int, payload: UserCreate) -> User:
        for index, user in enumerate(users):
            if user.id == user_id:
                updated = User(id=user_id, name=payload.name.strip(), email=payload.email)
                users[index] = updated
                return updated
        raise HTTPException(status_code=404, detail="User not found")


    @router.delete("/{user_id}", status_code=200)
    def delete_user(user_id: int) -> dict[str, str]:
        for index, user in enumerate(users):
            if user.id == user_id:
                users.pop(index)
                return {"status": "deleted"}
        raise HTTPException(status_code=404, detail="User not found")
    """
).strip() + "\n"


DEFAULT_AIOHTTP_ROUTES = textwrap.dedent(
    """
    from aiohttp import web

    from src.config import settings


    users: list[dict[str, object]] = []
    next_id = 1


    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok", "project": "{{project_name}}", "env": settings.env})


    async def list_users(request: web.Request) -> web.Response:
        return web.json_response({"users": users})


    async def get_user(request: web.Request) -> web.Response:
        user_id = int(request.match_info["user_id"])
        for user in users:
            if user["id"] == user_id:
                return web.json_response(user)
        return web.json_response({"error": "User not found"}, status=404)


    async def create_user(request: web.Request) -> web.Response:
        global next_id
        payload = await request.json()
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        if len(name) < 2 or "@" not in email:
            return web.json_response({"error": "Invalid name or email"}, status=400)

        user = {"id": next_id, "name": name, "email": email.lower()}
        next_id += 1
        users.append(user)
        return web.json_response(user, status=201)


    async def update_user(request: web.Request) -> web.Response:
        user_id = int(request.match_info["user_id"])
        payload = await request.json()
        name = str(payload.get("name", "")).strip()
        email = str(payload.get("email", "")).strip()
        if len(name) < 2 or "@" not in email:
            return web.json_response({"error": "Invalid name or email"}, status=400)

        for user in users:
            if user["id"] == user_id:
                user["name"] = name
                user["email"] = email.lower()
                return web.json_response(user)
        return web.json_response({"error": "User not found"}, status=404)


    async def delete_user(request: web.Request) -> web.Response:
        user_id = int(request.match_info["user_id"])
        for index, user in enumerate(users):
            if user["id"] == user_id:
                users.pop(index)
                return web.json_response({"status": "deleted"})
        return web.json_response({"error": "User not found"}, status=404)


    def register_routes(app: web.Application) -> None:
        app.router.add_get("/", health)
        app.router.add_get("/users", list_users)
        app.router.add_get("/users/{user_id}", get_user)
        app.router.add_post("/users", create_user)
        app.router.add_put("/users/{user_id}", update_user)
        app.router.add_delete("/users/{user_id}", delete_user)
    """
).strip() + "\n"


DEFAULT_PYTHON_ENV = textwrap.dedent(
    """
    APP_ENV=development
    DATABASE_URL=sqlite:///data/app.db
    """
).strip() + "\n"


DEFAULT_FLASK_TEST = textwrap.dedent(
    """
    import unittest

    from src.app import create_app


    class HealthRouteTest(unittest.TestCase):
        def test_health_endpoint(self):
            client = create_app().test_client()
            response = client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "ok")


    if __name__ == "__main__":
        unittest.main()
    """
).strip() + "\n"


DEFAULT_FASTAPI_TEST = textwrap.dedent(
    """
    import unittest

    from fastapi.testclient import TestClient

    from src.main import app


    class HealthRouteTest(unittest.TestCase):
        def test_health_endpoint(self):
            client = TestClient(app)
            response = client.get("/")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "ok")


    if __name__ == "__main__":
        unittest.main()
    """
).strip() + "\n"


DEFAULT_EXPRESS_JS_TEMPLATE = textwrap.dedent(
    """
    const port = process.env.PORT || 3000;
    const { createApp } = require('./app');

    const app = createApp();

    if (require.main === module) {
      app.listen(port, () => {
        console.log(`{{project_name}} listening on port ${port}`);
      });
    }

    module.exports = app;
    """
).strip() + "\n"


DEFAULT_EXPRESS_JS_APP = textwrap.dedent(
        """
        const express = require('express');

        const { healthRouter } = require('./routes/health');

        function createApp() {
            const app = express();
            app.use(express.json());
            app.use('/', healthRouter);
            return app;
        }

        module.exports = { createApp };
        """
).strip() + "\n"


DEFAULT_EXPRESS_JS_HEALTH_ROUTE = textwrap.dedent(
        """
        const express = require('express');

        const { appConfig } = require('../config/env');

        const healthRouter = express.Router();

        healthRouter.get('/', (_req, res) => {
            res.json({ status: 'ok', project: '{{project_name}}', env: appConfig.env });
        });

        module.exports = { healthRouter };
        """
).strip() + "\n"


DEFAULT_EXPRESS_TS_TEMPLATE = textwrap.dedent(
    """
    import { createApp } from './app';

    const port = Number(process.env.PORT || 3000);

    const app = createApp();

    app.listen(port, () => {
      console.log(`{{project_name}} listening on port ${port}`);
    });

    export default app;
    """
).strip() + "\n"


DEFAULT_EXPRESS_TS_APP = textwrap.dedent(
        """
        import express from 'express';

        import { healthRouter } from './routes/health';


        export function createApp() {
            const app = express();
            app.use(express.json());
            app.use('/', healthRouter);
            return app;
        }
        """
).strip() + "\n"


DEFAULT_EXPRESS_TS_HEALTH_ROUTE = textwrap.dedent(
        """
        import { Router, type Request, type Response } from 'express';

        import { appConfig } from '../config/env';

        const healthRouter = Router();

        healthRouter.get('/', (_req: Request, res: Response) => {
            res.json({ status: 'ok', project: '{{project_name}}', env: appConfig.env });
        });

        export { healthRouter };
        """
).strip() + "\n"


DEFAULT_EXPRESS_JS_TEST = textwrap.dedent(
    """
        const assert = require('node:assert/strict');
        const test = require('node:test');

        const { createApp } = require('../src/app');

        test('loads the Express app', () => {
            const app = createApp();
            assert.equal(typeof app, 'function');
        });
    """
).strip() + "\n"


DEFAULT_EXPRESS_TS_TEST = textwrap.dedent(
    """
        import assert from 'node:assert/strict';
        import test from 'node:test';

        import { createApp } from '../src/app';

        test('loads the Express app', () => {
            const app = createApp();
            assert.equal(typeof app, 'function');
        });
    """
).strip() + "\n"


DEFAULT_AIOHTTP_TEMPLATE = textwrap.dedent(
    """
    from aiohttp import web

    from src.routes import register_routes


    def create_app() -> web.Application:
        app = web.Application()
        register_routes(app)
        return app


    def main() -> None:
        web.run_app(create_app(), port=8000)


    if __name__ == "__main__":
        main()
    """
).strip() + "\n"


DEFAULT_AIOHTTP_TEST = textwrap.dedent(
    """
    import unittest

    from src.main import create_app


    class AppImportTest(unittest.TestCase):
        def test_routes_exist(self):
            app = create_app()
            self.assertGreaterEqual(len(list(app.router.routes())), 1)


    if __name__ == "__main__":
        unittest.main()
    """
).strip() + "\n"


DEFAULT_KOA_TEMPLATE = textwrap.dedent(
        """
        const port = process.env.PORT || 3000;
        const { createApp } = require('./app');

        const app = createApp();

        if (require.main === module) {
            app.listen(port, () => {
                console.log(`{{project_name}} listening on port ${port}`);
            });
        }

        module.exports = app;
        """
).strip() + "\n"


DEFAULT_KOA_APP_TEMPLATE = textwrap.dedent(
        """
        const Koa = require('koa');

        const { registerHealthRoutes } = require('./routes/health');


        function createApp() {
            const app = new Koa();
            registerHealthRoutes(app);
            return app;
        }

        module.exports = { createApp };
        """
).strip() + "\n"


DEFAULT_KOA_HEALTH_ROUTE = textwrap.dedent(
        """
        const Router = require('@koa/router');

        const { appConfig } = require('../config/env');


        function registerHealthRoutes(app) {
            const router = new Router();
            router.get('/', (ctx) => {
                ctx.body = { status: 'ok', project: '{{project_name}}', env: appConfig.env };
            });
            app.use(router.routes());
            app.use(router.allowedMethods());
        }

        module.exports = { registerHealthRoutes };
        """
).strip() + "\n"


DEFAULT_NODE_ENV_CONFIG = textwrap.dedent(
        """
        const appConfig = {
            env: process.env.APP_ENV || 'development',
            port: Number(process.env.PORT || 3000),
            dbUrl: process.env.DATABASE_URL || 'sqlite://./data/app.db',
        };

        module.exports = { appConfig };
        """
).strip() + "\n"


DEFAULT_NODE_TS_ENV_CONFIG = textwrap.dedent(
        """
        export const appConfig = {
            env: process.env.APP_ENV ?? 'development',
            port: Number(process.env.PORT ?? 3000),
            dbUrl: process.env.DATABASE_URL ?? 'sqlite://./data/app.db',
        };
        """
).strip() + "\n"


DEFAULT_NODE_DB_CLIENT = textwrap.dedent(
        """
        const { appConfig } = require('../config/env');


        function getDbUrl() {
            return appConfig.dbUrl;
        }

        module.exports = { getDbUrl };
        """
).strip() + "\n"


DEFAULT_NODE_TS_DB_CLIENT = textwrap.dedent(
        """
        import { appConfig } from '../config/env';


        export function getDbUrl(): string {
            return appConfig.dbUrl;
        }
        """
).strip() + "\n"


DEFAULT_NODE_ENV_FILE = textwrap.dedent(
        """
        APP_ENV=development
        PORT=3000
        DATABASE_URL=sqlite://./data/app.db
        """
).strip() + "\n"


DEFAULT_KOA_TEST = textwrap.dedent(
    """
    const assert = require('node:assert/strict');
    const test = require('node:test');

    const { createApp } = require('../src/app');

    test('loads the Koa app', () => {
      const app = createApp();
      assert.equal(typeof app.callback, 'function');
    });
    """
).strip() + "\n"


DEFAULT_SINATRA_GEMFILE = textwrap.dedent(
        """
        source 'https://rubygems.org'

        gem 'sinatra', '~> 4.0'
        gem 'rackup', '~> 2.1'
        gem 'puma', '~> 6.0'
        gem 'minitest', '~> 5.22'
        gem 'rack-test', '~> 2.1'
        """
).strip() + "\n"


DEFAULT_SINATRA_APP = textwrap.dedent(
        """
        require 'sinatra'
        require 'json'

        require_relative './lib/config'
        require_relative './lib/db'

        configure do
            set :bind, '0.0.0.0'
            set :port, AppConfig.port
        end

        USERS = []
        NEXT_ID = { value: 1 }

        get '/health' do
            content_type :json
            { status: 'ok', project: '{{project_name}}', env: AppConfig.env }.to_json
        end

        get '/users' do
            content_type :json
            USERS.to_json
        end

        get '/users/:id' do
            content_type :json
            user = USERS.find { |item| item[:id] == params[:id].to_i }
            halt 404, { error: 'User not found' }.to_json if user.nil?
            user.to_json
        end

        post '/users' do
            payload = JSON.parse(request.body.read)
            name = payload['name'].to_s.strip
            email = payload['email'].to_s.strip

            halt 400, { error: 'Invalid name or email' }.to_json if name.length < 2 || !email.include?('@')

            user = { id: NEXT_ID[:value], name: name, email: email.downcase }
            NEXT_ID[:value] += 1
            USERS << user

            status 201
            content_type :json
            user.to_json
        end

        put '/users/:id' do
            payload = JSON.parse(request.body.read)
            name = payload['name'].to_s.strip
            email = payload['email'].to_s.strip
            halt 400, { error: 'Invalid name or email' }.to_json if name.length < 2 || !email.include?('@')

            user = USERS.find { |item| item[:id] == params[:id].to_i }
            halt 404, { error: 'User not found' }.to_json if user.nil?

            user[:name] = name
            user[:email] = email.downcase
            content_type :json
            user.to_json
        end

        delete '/users/:id' do
            index = USERS.find_index { |item| item[:id] == params[:id].to_i }
            halt 404, { error: 'User not found' }.to_json if index.nil?
            USERS.delete_at(index)
            content_type :json
            { status: 'deleted' }.to_json
        end
        """
).strip() + "\n"


DEFAULT_SINATRA_CONFIG = textwrap.dedent(
        """
        module AppConfig
            module_function

            def env
                ENV.fetch('APP_ENV', 'development')
            end

            def port
                ENV.fetch('PORT', 4567)
            end

            def database_url
                ENV.fetch('DATABASE_URL', 'sqlite://data/app.db')
            end
        end
        """
).strip() + "\n"


DEFAULT_SINATRA_DB = textwrap.dedent(
        """
        require_relative './config'

        module DatabaseClient
            module_function

            def url
                AppConfig.database_url
            end
        end
        """
).strip() + "\n"


DEFAULT_RUBY_ENV = textwrap.dedent(
        """
        APP_ENV=development
        PORT=4567
        DATABASE_URL=sqlite://data/app.db
        """
).strip() + "\n"


DEFAULT_SINATRA_RACKUP = "require './app'\nrun Sinatra::Application\n"


DEFAULT_SINATRA_TEST = textwrap.dedent(
        """
        require 'minitest/autorun'
        require 'rack/test'
        require_relative '../app'

        class AppTest < Minitest::Test
            include Rack::Test::Methods

            def app
                Sinatra::Application
            end

            def test_health_route
                get '/'
                assert_equal 200, last_response.status
                assert_includes last_response.body, '{{project_name}}'
            end
        end
        """
).strip() + "\n"


DEFAULT_JAVALIN_POM = textwrap.dedent(
    """
    <project xmlns="http://maven.apache.org/POM/4.0.0"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
        <modelVersion>4.0.0</modelVersion>

        <groupId>com.example</groupId>
        <artifactId>{{project_name}}</artifactId>
        <version>1.0.0-SNAPSHOT</version>

        <properties>
            <maven.compiler.source>21</maven.compiler.source>
            <maven.compiler.target>21</maven.compiler.target>
            <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
            <junit.version>5.10.2</junit.version>
        </properties>

        <dependencies>
            <dependency>
                <groupId>io.javalin</groupId>
                <artifactId>javalin</artifactId>
                <version>6.3.0</version>
            </dependency>
            <dependency>
                <groupId>org.slf4j</groupId>
                <artifactId>slf4j-simple</artifactId>
                <version>2.0.13</version>
            </dependency>
            <dependency>
                <groupId>com.fasterxml.jackson.core</groupId>
                <artifactId>jackson-databind</artifactId>
                <version>2.17.2</version>
            </dependency>
            <dependency>
                <groupId>org.junit.jupiter</groupId>
                <artifactId>junit-jupiter</artifactId>
                <version>${junit.version}</version>
                <scope>test</scope>
            </dependency>
            <dependency>
                <groupId>io.javalin</groupId>
                <artifactId>javalin-testtools</artifactId>
                <version>6.3.0</version>
                <scope>test</scope>
            </dependency>
        </dependencies>

        <build>
            <plugins>
                <plugin>
                    <groupId>org.apache.maven.plugins</groupId>
                    <artifactId>maven-compiler-plugin</artifactId>
                    <version>3.13.0</version>
                </plugin>
                <plugin>
                    <groupId>org.codehaus.mojo</groupId>
                    <artifactId>exec-maven-plugin</artifactId>
                    <version>3.3.0</version>
                    <configuration>
                        <mainClass>com.example.App</mainClass>
                    </configuration>
                </plugin>
                <plugin>
                    <groupId>org.apache.maven.plugins</groupId>
                    <artifactId>maven-surefire-plugin</artifactId>
                    <version>3.2.5</version>
                </plugin>
            </plugins>
        </build>
    </project>
    """
).strip() + "\n"


DEFAULT_JAVALIN_DOCKERFILE = textwrap.dedent(
    """
    FROM maven:3.9.8-eclipse-temurin-21 AS build
    WORKDIR /workspace
    COPY pom.xml ./
    RUN mvn -q -DskipTests dependency:go-offline
    COPY src ./src
    RUN mvn -q -DskipTests clean package

    FROM eclipse-temurin:21-jre
    WORKDIR /app
    COPY --from=build /workspace/target/{{project_name}}-1.0.0-SNAPSHOT.jar /app/app.jar
    EXPOSE 7000
    ENTRYPOINT ["java", "-jar", "/app/app.jar"]
    """
).strip() + "\n"


DEFAULT_JAVALIN_PROPERTIES = textwrap.dedent(
    """
    app.name={{project_name}}
    app.env=development
    app.port=7000
    """
).strip() + "\n"


DEFAULT_JAVALIN_APP = textwrap.dedent(
    """
    package com.example;

    import com.example.config.AppConfig;
    import com.example.controllers.HealthController;
    import com.example.controllers.UserController;
    import com.example.middleware.ExceptionMapper;
    import com.example.middleware.RequestLoggingMiddleware;
    import com.example.repository.InMemoryUserRepository;
    import com.example.repository.UserRepository;
    import com.example.routes.HealthRoutes;
    import com.example.routes.UserRoutes;
    import com.example.services.UserService;
    import io.javalin.Javalin;

    public final class App {
        private App() {}

        public static void main(String[] args) {
            AppConfig config = AppConfig.fromEnvironment();
            UserRepository userRepository = new InMemoryUserRepository();
            UserService userService = new UserService(userRepository);
            HealthController healthController = new HealthController(config);
            UserController userController = new UserController(userService);

            Javalin app = Javalin.create(javalinConfig -> javalinConfig.showJavalinBanner = false);
            RequestLoggingMiddleware.register(app);
            ExceptionMapper.register(app);

            HealthRoutes.register(app, healthController);
            UserRoutes.register(app, userController);

            app.start(config.port());
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_CONFIG = textwrap.dedent(
    """
    package com.example.config;

    import java.io.IOException;
    import java.io.InputStream;
    import java.util.Properties;

    public record AppConfig(String appName, String env, int port) {
        public static AppConfig fromEnvironment() {
            Properties properties = new Properties();
            try (InputStream in = AppConfig.class.getClassLoader().getResourceAsStream("application.properties")) {
                if (in != null) {
                    properties.load(in);
                }
            } catch (IOException ignored) {
                // Fall back to defaults and env vars.
            }

            String appName = get("APP_NAME", "app.name", "{{project_name}}", properties);
            String env = get("APP_ENV", "app.env", "development", properties);
            int port = Integer.parseInt(get("APP_PORT", "app.port", "7000", properties));

            return new AppConfig(appName, env, port);
        }

        private static String get(String envName, String propertyName, String fallback, Properties properties) {
            String fromEnv = System.getenv(envName);
            if (fromEnv != null && !fromEnv.isBlank()) {
                return fromEnv;
            }
            return properties.getProperty(propertyName, fallback);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_HEALTH_ROUTES = textwrap.dedent(
    """
    package com.example.routes;

    import com.example.controllers.HealthController;
    import io.javalin.Javalin;

    public final class HealthRoutes {
        private HealthRoutes() {}

        public static void register(Javalin app, HealthController controller) {
            app.get("/health", controller::health);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_ROUTES = textwrap.dedent(
    """
    package com.example.routes;

    import com.example.controllers.UserController;
    import io.javalin.Javalin;

    public final class UserRoutes {
        private UserRoutes() {}

        public static void register(Javalin app, UserController controller) {
            app.get("/users", controller::listUsers);
            app.get("/users/{id}", controller::getUserById);
            app.post("/users", controller::createUser);
            app.put("/users/{id}", controller::updateUser);
            app.delete("/users/{id}", controller::deleteUser);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_HEALTH_CONTROLLER = textwrap.dedent(
    """
    package com.example.controllers;

    import com.example.config.AppConfig;
    import io.javalin.http.Context;
    import java.time.Instant;

    public final class HealthController {
        private final AppConfig config;

        public HealthController(AppConfig config) {
            this.config = config;
        }

        public void health(Context ctx) {
            ctx.status(200).json(new HealthResponse("ok", config.appName(), config.env(), Instant.now().toString()));
        }

        public record HealthResponse(String status, String appName, String env, String timestamp) {}
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_CONTROLLER = textwrap.dedent(
    """
    package com.example.controllers;

    import com.example.dto.CreateUserRequest;
    import com.example.dto.UpdateUserRequest;
    import com.example.dto.UserResponse;
    import com.example.services.UserService;
    import com.example.utils.ValidationUtils;
    import io.javalin.http.Context;
    import java.util.List;

    public final class UserController {
        private final UserService userService;

        public UserController(UserService userService) {
            this.userService = userService;
        }

        public void listUsers(Context ctx) {
            List<UserResponse> users = userService.listUsers().stream().map(UserResponse::fromModel).toList();
            ctx.status(200).json(users);
        }

        public void getUserById(Context ctx) {
            long id = ValidationUtils.parseId(ctx.pathParam("id"));
            ctx.status(200).json(UserResponse.fromModel(userService.getUser(id)));
        }

        public void createUser(Context ctx) {
            CreateUserRequest request = ctx.bodyAsClass(CreateUserRequest.class);
            ValidationUtils.validateCreateRequest(request);
            UserResponse created = UserResponse.fromModel(userService.createUser(request));
            ctx.status(201).json(created);
        }

        public void updateUser(Context ctx) {
            long id = ValidationUtils.parseId(ctx.pathParam("id"));
            UpdateUserRequest request = ctx.bodyAsClass(UpdateUserRequest.class);
            ValidationUtils.validateUpdateRequest(request);
            UserResponse updated = UserResponse.fromModel(userService.updateUser(id, request));
            ctx.status(200).json(updated);
        }

        public void deleteUser(Context ctx) {
            long id = ValidationUtils.parseId(ctx.pathParam("id"));
            userService.deleteUser(id);
            ctx.status(204);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_SERVICE = textwrap.dedent(
    """
    package com.example.services;

    import com.example.dto.CreateUserRequest;
    import com.example.dto.UpdateUserRequest;
    import com.example.exceptions.NotFoundException;
    import com.example.models.User;
    import com.example.repository.UserRepository;
    import java.util.List;

    public final class UserService {
        private final UserRepository userRepository;

        public UserService(UserRepository userRepository) {
            this.userRepository = userRepository;
        }

        public List<User> listUsers() {
            return userRepository.findAll();
        }

        public User getUser(long id) {
            return userRepository.findById(id).orElseThrow(() -> new NotFoundException("User not found: " + id));
        }

        public User createUser(CreateUserRequest request) {
            User user = new User(0L, request.name().trim(), request.email().trim().toLowerCase());
            return userRepository.save(user);
        }

        public User updateUser(long id, UpdateUserRequest request) {
            User existing = getUser(id);
            String nextName = request.name() == null ? existing.name() : request.name().trim();
            String nextEmail = request.email() == null ? existing.email() : request.email().trim().toLowerCase();
            return userRepository.update(new User(existing.id(), nextName, nextEmail));
        }

        public void deleteUser(long id) {
            getUser(id);
            userRepository.delete(id);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_MODEL = textwrap.dedent(
    """
    package com.example.models;

    public record User(long id, String name, String email) {}
    """
).strip() + "\n"


DEFAULT_JAVALIN_CREATE_DTO = textwrap.dedent(
    """
    package com.example.dto;

    public record CreateUserRequest(String name, String email) {}
    """
).strip() + "\n"


DEFAULT_JAVALIN_UPDATE_DTO = textwrap.dedent(
    """
    package com.example.dto;

    public record UpdateUserRequest(String name, String email) {}
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_RESPONSE_DTO = textwrap.dedent(
    """
    package com.example.dto;

    import com.example.models.User;

    public record UserResponse(long id, String name, String email) {
        public static UserResponse fromModel(User user) {
            return new UserResponse(user.id(), user.name(), user.email());
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_API_EXCEPTION = textwrap.dedent(
    """
    package com.example.exceptions;

    public class ApiException extends RuntimeException {
        public ApiException(String message) {
            super(message);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_NOT_FOUND_EXCEPTION = textwrap.dedent(
    """
    package com.example.exceptions;

    public final class NotFoundException extends ApiException {
        public NotFoundException(String message) {
            super(message);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_VALIDATION_EXCEPTION = textwrap.dedent(
    """
    package com.example.exceptions;

    public final class ValidationException extends ApiException {
        public ValidationException(String message) {
            super(message);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_EXCEPTION_MAPPER = textwrap.dedent(
    """
    package com.example.middleware;

    import com.example.exceptions.NotFoundException;
    import com.example.exceptions.ValidationException;
    import io.javalin.Javalin;
    import java.time.Instant;

    public final class ExceptionMapper {
        private ExceptionMapper() {}

        public static void register(Javalin app) {
            app.exception(ValidationException.class, (e, ctx) ->
                ctx.status(400).json(new ErrorResponse("validation_error", e.getMessage(), Instant.now().toString())));

            app.exception(NotFoundException.class, (e, ctx) ->
                ctx.status(404).json(new ErrorResponse("not_found", e.getMessage(), Instant.now().toString())));

            app.exception(Exception.class, (e, ctx) ->
                ctx.status(500).json(new ErrorResponse("internal_error", "Unexpected server error", Instant.now().toString())));
        }

        public record ErrorResponse(String code, String message, String timestamp) {}
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_REQUEST_LOGGING = textwrap.dedent(
    """
    package com.example.middleware;

    import io.javalin.Javalin;
    import org.slf4j.Logger;
    import org.slf4j.LoggerFactory;

    public final class RequestLoggingMiddleware {
        private static final Logger logger = LoggerFactory.getLogger(RequestLoggingMiddleware.class);

        private RequestLoggingMiddleware() {}

        public static void register(Javalin app) {
            app.before(ctx -> logger.info("{} {}", ctx.method(), ctx.path()));
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_VALIDATION_UTILS = textwrap.dedent(
    """
    package com.example.utils;

    import com.example.dto.CreateUserRequest;
    import com.example.dto.UpdateUserRequest;
    import com.example.exceptions.ValidationException;

    public final class ValidationUtils {
        private ValidationUtils() {}

        public static long parseId(String rawId) {
            try {
                long value = Long.parseLong(rawId);
                if (value <= 0) {
                    throw new ValidationException("id must be greater than zero");
                }
                return value;
            } catch (NumberFormatException exception) {
                throw new ValidationException("id must be a number");
            }
        }

        public static void validateCreateRequest(CreateUserRequest request) {
            if (request == null) {
                throw new ValidationException("Request body is required");
            }
            requireName(request.name());
            requireEmail(request.email());
        }

        public static void validateUpdateRequest(UpdateUserRequest request) {
            if (request == null) {
                throw new ValidationException("Request body is required");
            }
            if (request.name() == null && request.email() == null) {
                throw new ValidationException("At least one field is required for update");
            }
            if (request.name() != null) {
                requireName(request.name());
            }
            if (request.email() != null) {
                requireEmail(request.email());
            }
        }

        private static void requireName(String value) {
            if (value == null || value.trim().length() < 2) {
                throw new ValidationException("name must be at least 2 characters");
            }
        }

        private static void requireEmail(String value) {
            if (value == null || !value.contains("@")) {
                throw new ValidationException("email must be valid");
            }
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_REPOSITORY = textwrap.dedent(
    """
    package com.example.repository;

    import com.example.models.User;
    import java.util.List;
    import java.util.Optional;

    public interface UserRepository {
        List<User> findAll();
        Optional<User> findById(long id);
        User save(User user);
        User update(User user);
        void delete(long id);
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_INMEMORY_REPOSITORY = textwrap.dedent(
    """
    package com.example.repository;

    import com.example.models.User;
    import java.util.ArrayList;
    import java.util.Comparator;
    import java.util.List;
    import java.util.Optional;
    import java.util.concurrent.ConcurrentHashMap;
    import java.util.concurrent.atomic.AtomicLong;

    public final class InMemoryUserRepository implements UserRepository {
        private final ConcurrentHashMap<Long, User> store = new ConcurrentHashMap<>();
        private final AtomicLong sequence = new AtomicLong(0);

        @Override
        public List<User> findAll() {
            List<User> users = new ArrayList<>(store.values());
            users.sort(Comparator.comparingLong(User::id));
            return users;
        }

        @Override
        public Optional<User> findById(long id) {
            return Optional.ofNullable(store.get(id));
        }

        @Override
        public User save(User user) {
            long id = sequence.incrementAndGet();
            User created = new User(id, user.name(), user.email());
            store.put(id, created);
            return created;
        }

        @Override
        public User update(User user) {
            store.put(user.id(), user);
            return user;
        }

        @Override
        public void delete(long id) {
            store.remove(id);
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVA_ENV = textwrap.dedent(
    """
    APP_NAME={{project_name}}
    APP_ENV=development
    APP_PORT=7000
    """
).strip() + "\n"


DEFAULT_JAVALIN_SERVICE_TEST = textwrap.dedent(
    """
    package com.example.services;

    import static org.junit.jupiter.api.Assertions.assertEquals;

    import com.example.dto.CreateUserRequest;
    import com.example.repository.InMemoryUserRepository;
    import com.example.repository.UserRepository;
    import org.junit.jupiter.api.Test;

    class UserServiceTest {
        @Test
        void createAndListUsers() {
            UserRepository repository = new InMemoryUserRepository();
            UserService service = new UserService(repository);

            service.createUser(new CreateUserRequest("Alex", "alex@example.com"));
            service.createUser(new CreateUserRequest("Sam", "sam@example.com"));

            assertEquals(2, service.listUsers().size());
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_HEALTH_IT = textwrap.dedent(
    """
    package com.example.integration;

    import static org.junit.jupiter.api.Assertions.assertEquals;

    import com.example.config.AppConfig;
    import com.example.controllers.HealthController;
    import com.example.middleware.ExceptionMapper;
    import com.example.middleware.RequestLoggingMiddleware;
    import com.example.routes.HealthRoutes;
    import io.javalin.Javalin;
    import io.javalin.testtools.JavalinTest;
    import org.junit.jupiter.api.Test;
    import okhttp3.Response;

    class HealthRoutesIntegrationTest {
        @Test
        void healthEndpointReturns200() {
            AppConfig config = new AppConfig("{{project_name}}", "test", 0);
            HealthController healthController = new HealthController(config);
            Javalin app = Javalin.create();
            RequestLoggingMiddleware.register(app);
            ExceptionMapper.register(app);
            HealthRoutes.register(app, healthController);

            JavalinTest.test(app, (server, client) -> {
                try (Response response = client.get("/health")) {
                    assertEquals(200, response.code());
                }
            });
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVALIN_USER_IT = textwrap.dedent(
    """
    package com.example.integration;

    import static org.junit.jupiter.api.Assertions.assertEquals;
    import static org.junit.jupiter.api.Assertions.assertTrue;

    import com.example.controllers.UserController;
    import com.example.middleware.ExceptionMapper;
    import com.example.middleware.RequestLoggingMiddleware;
    import com.example.repository.InMemoryUserRepository;
    import com.example.repository.UserRepository;
    import com.example.routes.UserRoutes;
    import com.example.services.UserService;
    import io.javalin.Javalin;
    import io.javalin.testtools.JavalinTest;
    import org.junit.jupiter.api.Test;
    import okhttp3.Response;

    class UserRoutesIntegrationTest {
        @Test
        void createAndGetUser() {
            UserRepository repository = new InMemoryUserRepository();
            UserService service = new UserService(repository);
            UserController controller = new UserController(service);

            Javalin app = Javalin.create();
            RequestLoggingMiddleware.register(app);
            ExceptionMapper.register(app);
            UserRoutes.register(app, controller);

            JavalinTest.test(app, (server, client) -> {
                try (Response createResponse = client.post("/users", "{\"name\":\"Taylor\",\"email\":\"taylor@example.com\"}")) {
                    assertEquals(201, createResponse.code());
                }

                try (Response listResponse = client.get("/users")) {
                    assertEquals(200, listResponse.code());
                    assertTrue(listResponse.body().string().contains("Taylor"));
                }
            });
        }
    }
    """
).strip() + "\n"


DEFAULT_JAVA_ENV = textwrap.dedent(
    """
    APP_ENV=development
    PORT=7000
    DATABASE_URL=sqlite://data/app.db
    """
).strip() + "\n"


DEFAULT_JAVALIN_TEST = textwrap.dedent(
        """
        package com.example;

        import static org.junit.jupiter.api.Assertions.assertTrue;

        import org.junit.jupiter.api.Test;

        class AppTest {
                @Test
                void placeholder() {
                        assertTrue(true);
                }
        }
        """
).strip() + "\n"


DEFAULT_NODE_ENV_EXAMPLE = textwrap.dedent(
        """
        PORT=3000
        NODE_ENV=development
        """
).strip() + "\n"


DEFAULT_NODE_DOCKERFILE = textwrap.dedent(
        """
        FROM node:20-alpine
        WORKDIR /app
        COPY package*.json ./
        RUN npm install
        COPY . .
        EXPOSE 3000
        CMD ["npm", "start"]
        """
).strip() + "\n"


DEFAULT_NODE_DOCKERIGNORE = textwrap.dedent(
        """
        node_modules
        coverage
        .env
        .git
        """
).strip() + "\n"


DEFAULT_NODE_ESLINTRC = textwrap.dedent(
        """
        {
            "env": {
                "node": true,
                "es2022": true
            },
            "extends": ["eslint:recommended"],
            "parserOptions": {
                "ecmaVersion": "latest",
                "sourceType": "script"
            },
            "rules": {
                "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }]
            }
        }
        """
).strip() + "\n"


DEFAULT_NODE_PRETTIERRC = textwrap.dedent(
        """
        {
            "singleQuote": true,
            "trailingComma": "es5"
        }
        """
).strip() + "\n"


DEFAULT_NODE_CONFIG_JS = textwrap.dedent(
        """
        const dotenv = require('dotenv');

        dotenv.config();

        const config = {
            port: Number(process.env.PORT || 3000),
            nodeEnv: process.env.NODE_ENV || 'development',
        };

        module.exports = { config };
        """
).strip() + "\n"


DEFAULT_NODE_CONFIG_TS = textwrap.dedent(
        """
        import dotenv from 'dotenv';

        dotenv.config();

        export const config = {
            port: Number(process.env.PORT || 3000),
            nodeEnv: process.env.NODE_ENV || 'development',
        };
        """
).strip() + "\n"


DEFAULT_NODE_APP_TEMPLATE_JS = textwrap.dedent(
        """
        const express = require('express');
        const { routes } = require('./routes');
        const { logger } = require('./middleware/logger');
        const { errorHandler } = require('./middleware/errorHandler');

        function createApp() {
            const app = express();
            app.use(express.json());
            app.use(logger);
            app.use(routes);
            app.use(errorHandler);
            return app;
        }

        module.exports = { createApp };
        """
).strip() + "\n"


DEFAULT_NODE_APP_TEMPLATE_TS = textwrap.dedent(
        """
        import express from 'express';
        import { routes } from './routes';
        import { logger } from './middleware/logger';
        import { errorHandler } from './middleware/errorHandler';

        export function createApp() {
            const app = express();
            app.use(express.json());
            app.use(logger);
            app.use(routes);
            app.use(errorHandler);
            return app;
        }
        """
).strip() + "\n"


DEFAULT_NODE_SERVER_TEMPLATE_JS = textwrap.dedent(
        """
        const { createApp } = require('./app');
        const { config } = require('./config');

        const app = createApp();

        app.listen(config.port, () => {
            console.log('{{project_name}} listening on port ' + config.port);
        });
        """
).strip() + "\n"


DEFAULT_NODE_SERVER_TEMPLATE_TS = textwrap.dedent(
        """
        import { createApp } from './app';
        import { config } from './config';

        const app = createApp();

        app.listen(config.port, () => {
            console.log('{{project_name}} listening on port ' + config.port);
        });
        """
).strip() + "\n"


DEFAULT_NODE_ROUTE_INDEX_JS = textwrap.dedent(
        """
        const express = require('express');
        const { healthRouter } = require('./health');
        const { usersRouter } = require('./users');

        const routes = express.Router();

        routes.use('/health', healthRouter);
        routes.use('/users', usersRouter);

        module.exports = { routes };
        """
).strip() + "\n"


DEFAULT_NODE_ROUTE_INDEX_TS = textwrap.dedent(
        """
        import { Router } from 'express';
        import { healthRouter } from './health';
        import { usersRouter } from './users';

        const routes = Router();

        routes.use('/health', healthRouter);
        routes.use('/users', usersRouter);

        export { routes };
        """
).strip() + "\n"


DEFAULT_NODE_HEALTH_ROUTE_JS = textwrap.dedent(
        """
        const express = require('express');

        const healthRouter = express.Router();

        healthRouter.get('/', (_req, res) => {
            res.json({ status: 'ok' });
        });

        module.exports = { healthRouter };
        """
).strip() + "\n"


DEFAULT_NODE_HEALTH_ROUTE_TS = textwrap.dedent(
        """
        import { Router } from 'express';

        const healthRouter = Router();

        healthRouter.get('/', (_req, res) => {
            res.json({ status: 'ok' });
        });

        export { healthRouter };
        """
).strip() + "\n"


DEFAULT_NODE_USERS_ROUTE_JS = textwrap.dedent(
        """
        const express = require('express');
    const { listUsers, getUserById, createUser, updateUser, deleteUser } = require('../controllers/userController');

        const usersRouter = express.Router();

        usersRouter.get('/', listUsers);
        usersRouter.get('/:id', getUserById);
        usersRouter.post('/', createUser);
        usersRouter.put('/:id', updateUser);
        usersRouter.delete('/:id', deleteUser);

        module.exports = { usersRouter };
        """
).strip() + "\n"


DEFAULT_NODE_USERS_ROUTE_TS = textwrap.dedent(
        """
        import { Router } from 'express';
    import { listUsers, getUserById, createUser, updateUser, deleteUser } from '../controllers/userController';

        const usersRouter = Router();

        usersRouter.get('/', listUsers);
        usersRouter.get('/:id', getUserById);
        usersRouter.post('/', createUser);
        usersRouter.put('/:id', updateUser);
        usersRouter.delete('/:id', deleteUser);

        export { usersRouter };
        """
).strip() + "\n"


DEFAULT_NODE_USER_CONTROLLER_JS = textwrap.dedent(
        """
        const { userService } = require('../services/userService');
    const { validateUserCreate, validateUserUpdate } = require('../utils/validation');

        function listUsers(_req, res) {
            res.json(userService.listUsers());
        }

        function getUserById(req, res, next) {
            try {
                const user = userService.getUserById(req.params.id);
                res.json(user);
            } catch (error) {
                next(error);
            }
        }

        function createUser(req, res, next) {
            try {
                validateUserCreate(req.body);
                const created = userService.createUser(req.body);
                res.status(201).json(created);
            } catch (error) {
                next(error);
            }
        }

        function updateUser(req, res, next) {
            try {
                validateUserUpdate(req.body);
                const updated = userService.updateUser(req.params.id, req.body);
                res.json(updated);
            } catch (error) {
                next(error);
            }
        }

        function deleteUser(req, res, next) {
            try {
                userService.deleteUser(req.params.id);
                res.status(204).send();
            } catch (error) {
                next(error);
            }
        }

        module.exports = { listUsers, getUserById, createUser, updateUser, deleteUser };
        """
).strip() + "\n"


DEFAULT_NODE_USER_CONTROLLER_TS = textwrap.dedent(
        """
        import { userService } from '../services/userService';
    import { validateUserCreate, validateUserUpdate } from '../utils/validation';

        export function listUsers(_req, res) {
            res.json(userService.listUsers());
        }

        export function getUserById(req, res, next) {
            try {
                const user = userService.getUserById(req.params.id);
                res.json(user);
            } catch (error) {
                next(error);
            }
        }

        export function createUser(req, res, next) {
            try {
                validateUserCreate(req.body);
                const created = userService.createUser(req.body);
                res.status(201).json(created);
            } catch (error) {
                next(error);
            }
        }

        export function updateUser(req, res, next) {
            try {
                validateUserUpdate(req.body);
                const updated = userService.updateUser(req.params.id, req.body);
                res.json(updated);
            } catch (error) {
                next(error);
            }
        }

        export function deleteUser(req, res, next) {
            try {
                userService.deleteUser(req.params.id);
                res.status(204).send();
            } catch (error) {
                next(error);
            }
        }
        """
).strip() + "\n"


DEFAULT_NODE_USER_SERVICE_JS = textwrap.dedent(
        """
        const { users, nextId } = require('../models/userStore');
        const { AppError } = require('../middleware/errorHandler');

        function listUsers() {
            return users;
        }

        function getUserById(id) {
            const user = users.find((item) => item.id === Number(id));
            if (!user) {
                throw new AppError(404, 'User not found');
            }
            return user;
        }

        function createUser(payload) {
            const user = { id: nextId(), name: payload.name.trim(), email: payload.email.trim().toLowerCase() };
            users.push(user);
            return user;
        }

        function updateUser(id, payload) {
            const user = getUserById(id);
            user.name = payload.name.trim();
            user.email = payload.email.trim().toLowerCase();
            return user;
        }

        function deleteUser(id) {
            const index = users.findIndex((item) => item.id === Number(id));
            if (index === -1) {
                throw new AppError(404, 'User not found');
            }
            users.splice(index, 1);
        }

        module.exports = { userService: { listUsers, getUserById, createUser, updateUser, deleteUser } };
        """
).strip() + "\n"


DEFAULT_NODE_USER_SERVICE_TS = textwrap.dedent(
        """
        import { users, nextId } from '../models/userStore';
        import { AppError } from '../middleware/errorHandler';

        function listUsers() {
            return users;
        }

        function getUserById(id) {
            const user = users.find((item) => item.id === Number(id));
            if (!user) {
                throw new AppError(404, 'User not found');
            }
            return user;
        }

        function createUser(payload) {
            const user = { id: nextId(), name: payload.name.trim(), email: payload.email.trim().toLowerCase() };
            users.push(user);
            return user;
        }

        function updateUser(id, payload) {
            const user = getUserById(id);
            user.name = payload.name.trim();
            user.email = payload.email.trim().toLowerCase();
            return user;
        }

        function deleteUser(id) {
            const index = users.findIndex((item) => item.id === Number(id));
            if (index === -1) {
                throw new AppError(404, 'User not found');
            }
            users.splice(index, 1);
        }

        export const userService = { listUsers, getUserById, createUser, updateUser, deleteUser };
        """
).strip() + "\n"


DEFAULT_NODE_USER_STORE_JS = textwrap.dedent(
        """
        const users = [];
        let currentId = 0;

        function nextId() {
            currentId += 1;
            return currentId;
        }

        module.exports = { users, nextId };
        """
).strip() + "\n"


DEFAULT_NODE_USER_STORE_TS = textwrap.dedent(
        """
        export const users = [];
        let currentId = 0;

        export function nextId() {
            currentId += 1;
            return currentId;
        }
        """
).strip() + "\n"


DEFAULT_NODE_ERROR_HANDLER_JS = textwrap.dedent(
        """
        class AppError extends Error {
            constructor(statusCode, message) {
                super(message);
                this.statusCode = statusCode;
            }
        }

        function errorHandler(error, _req, res, _next) {
            const statusCode = error.statusCode || 500;
            res.status(statusCode).json({ message: error.message || 'Something went wrong' });
        }

        module.exports = { AppError, errorHandler };
        """
).strip() + "\n"


DEFAULT_NODE_ERROR_HANDLER_TS = textwrap.dedent(
        """
        export class AppError extends Error {
            constructor(statusCode, message) {
                super(message);
                this.statusCode = statusCode;
            }
        }

        export function errorHandler(error, _req, res, _next) {
            const statusCode = error.statusCode || 500;
            res.status(statusCode).json({ message: error.message || 'Something went wrong' });
        }
        """
).strip() + "\n"


DEFAULT_NODE_LOGGER_JS = textwrap.dedent(
        """
        function logger(req, _res, next) {
            console.log(req.method + ' ' + req.url);
            next();
        }

        module.exports = { logger };
        """
).strip() + "\n"


DEFAULT_NODE_LOGGER_TS = textwrap.dedent(
        """
        export function logger(req, _res, next) {
            console.log(req.method + ' ' + req.url);
            next();
        }
        """
).strip() + "\n"


DEFAULT_NODE_VALIDATION_JS = textwrap.dedent(
        """
        const { AppError } = require('../middleware/errorHandler');

        function validateUserCreate(body) {
            if (!body || typeof body.name !== 'string' || body.name.trim().length < 2) {
                throw new AppError(400, 'Name must be at least 2 characters');
            }
            if (!body.email || typeof body.email !== 'string' || !body.email.includes('@')) {
                throw new AppError(400, 'Email must be valid');
            }
        }

        function validateUserUpdate(body) {
            validateUserCreate(body);
        }

        module.exports = { validateUserCreate, validateUserUpdate };
        """
).strip() + "\n"


DEFAULT_NODE_VALIDATION_TS = textwrap.dedent(
        """
        import { AppError } from '../middleware/errorHandler';

        export function validateUserCreate(body) {
            if (!body || typeof body.name !== 'string' || body.name.trim().length < 2) {
                throw new AppError(400, 'Name must be at least 2 characters');
            }
            if (!body.email || typeof body.email !== 'string' || !body.email.includes('@')) {
                throw new AppError(400, 'Email must be valid');
            }
        }

        export function validateUserUpdate(body) {
            validateUserCreate(body);
        }
        """
).strip() + "\n"


DEFAULT_NODE_TEST_JS = textwrap.dedent(
        """
        const test = require('node:test');
        const assert = require('node:assert/strict');
        const request = require('supertest');
        const { createApp } = require('../src/app');

        test('GET /health returns ok', async () => {
            const app = createApp();
            const response = await request(app).get('/health');
            assert.equal(response.status, 200);
            assert.equal(response.body.status, 'ok');
        });

        test('POST /users creates a user', async () => {
            const app = createApp();
            const response = await request(app).post('/users').send({ name: 'Ava', email: 'ava@example.com' });
            assert.equal(response.status, 201);
            assert.equal(response.body.name, 'Ava');
        });

        test('PUT /users/:id updates a user', async () => {
            const app = createApp();
            const created = await request(app).post('/users').send({ name: 'Ava', email: 'ava@example.com' });
            const response = await request(app)
                .put('/users/' + created.body.id)
                .send({ name: 'Ava Updated', email: 'ava.updated@example.com' });
            assert.equal(response.status, 200);
            assert.equal(response.body.name, 'Ava Updated');
        });
        """
).strip() + "\n"


DEFAULT_NODE_TEST_TS = textwrap.dedent(
        """
        import test from 'node:test';
        import assert from 'node:assert/strict';
        import request from 'supertest';
        import { createApp } from '../src/app';

        test('GET /health returns ok', async () => {
            const app = createApp();
            const response = await request(app).get('/health');
            assert.equal(response.status, 200);
            assert.equal(response.body.status, 'ok');
        });

        test('POST /users creates a user', async () => {
            const app = createApp();
            const response = await request(app).post('/users').send({ name: 'Ava', email: 'ava@example.com' });
            assert.equal(response.status, 201);
            assert.equal(response.body.name, 'Ava');
        });

        test('PUT /users/:id updates a user', async () => {
            const app = createApp();
            const created = await request(app).post('/users').send({ name: 'Ava', email: 'ava@example.com' });
            const response = await request(app)
                .put('/users/' + created.body.id)
                .send({ name: 'Ava Updated', email: 'ava.updated@example.com' });
            assert.equal(response.status, 200);
            assert.equal(response.body.name, 'Ava Updated');
        });
        """
).strip() + "\n"


DEFAULT_NODE_README_TEMPLATE = textwrap.dedent(
        """
        # {{project_name}}

        A beginner-friendly Node starter with routes, controllers, services, and in-memory users.

        ## Install
        npm install

        ## Run
        npm run dev

        ## Test
        npm test

        ## Lint
        npm run lint
        """
).strip() + "\n"


DEFAULT_NODE_TSCONFIG = textwrap.dedent(
        """
        {
            "compilerOptions": {
                "target": "ES2020",
                "module": "CommonJS",
                "moduleResolution": "Node",
                "strict": false,
                "esModuleInterop": true,
                "skipLibCheck": true,
                "forceConsistentCasingInFileNames": true,
                "types": ["node"]
            },
            "include": ["src/**/*.ts", "tests/**/*.ts"]
        }
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_APP = textwrap.dedent(
        """
        const Koa = require('koa');
        const bodyParser = require('koa-bodyparser');
        const { registerRoutes } = require('./routes');
        const { logger } = require('./middleware/logger');
        const { errorHandler } = require('./middleware/errorHandler');

        function createApp() {
            const app = new Koa();
            app.use(errorHandler);
            app.use(logger);
            app.use(bodyParser());
            registerRoutes(app);
            return app;
        }

        module.exports = { createApp };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_SERVER = textwrap.dedent(
        """
        const { createApp } = require('./app');
        const { config } = require('./config');

        const app = createApp();

        app.listen(config.port, () => {
            console.log('{{project_name}} listening on port ' + config.port);
        });
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_ROUTE_INDEX = textwrap.dedent(
        """
        const { registerHealthRoutes } = require('./health');
        const { registerUserRoutes } = require('./users');

        function registerRoutes(app) {
            registerHealthRoutes(app);
            registerUserRoutes(app);
        }

        module.exports = { registerRoutes };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_HEALTH_ROUTE = textwrap.dedent(
        """
        const Router = require('@koa/router');

        function registerHealthRoutes(app) {
            const router = new Router();
            router.get('/health', (ctx) => {
                ctx.body = { status: 'ok' };
            });
            app.use(router.routes());
            app.use(router.allowedMethods());
        }

        module.exports = { registerHealthRoutes };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_USERS_ROUTE = textwrap.dedent(
        """
        const Router = require('@koa/router');
        const controller = require('../controllers/userController');

        function registerUserRoutes(app) {
            const router = new Router();
            router.get('/users', controller.listUsers);
            router.get('/users/:id', controller.getUserById);
            router.post('/users', controller.createUser);
            router.put('/users/:id', controller.updateUser);
            router.delete('/users/:id', controller.deleteUser);
            app.use(router.routes());
            app.use(router.allowedMethods());
        }

        module.exports = { registerUserRoutes };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_USER_CONTROLLER = textwrap.dedent(
        """
        const { userService } = require('../services/userService');
        const { validateUserCreate, validateUserUpdate } = require('../utils/validation');

        async function listUsers(ctx) {
            ctx.body = userService.listUsers();
        }

        async function getUserById(ctx) {
            ctx.body = userService.getUserById(ctx.params.id);
        }

        async function createUser(ctx) {
            validateUserCreate(ctx.request.body);
            ctx.status = 201;
            ctx.body = userService.createUser(ctx.request.body);
        }

        async function updateUser(ctx) {
            validateUserUpdate(ctx.request.body);
            ctx.body = userService.updateUser(ctx.params.id, ctx.request.body);
        }

        async function deleteUser(ctx) {
            userService.deleteUser(ctx.params.id);
            ctx.status = 204;
        }

        module.exports = { listUsers, getUserById, createUser, updateUser, deleteUser };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_USER_SERVICE = textwrap.dedent(
        """
        const { users, nextId } = require('../models/userStore');

        class AppError extends Error {
            constructor(status, message) {
                super(message);
                this.status = status;
            }
        }

        function listUsers() {
            return users;
        }

        function getUserById(id) {
            const user = users.find((item) => item.id === Number(id));
            if (!user) {
                throw new AppError(404, 'User not found');
            }
            return user;
        }

        function createUser(payload) {
            const user = { id: nextId(), name: payload.name.trim(), email: payload.email.trim().toLowerCase() };
            users.push(user);
            return user;
        }

        function updateUser(id, payload) {
            const user = getUserById(id);
            user.name = payload.name.trim();
            user.email = payload.email.trim().toLowerCase();
            return user;
        }

        function deleteUser(id) {
            const index = users.findIndex((item) => item.id === Number(id));
            if (index === -1) {
                throw new AppError(404, 'User not found');
            }
            users.splice(index, 1);
        }

        module.exports = { userService: { listUsers, getUserById, createUser, updateUser, deleteUser }, AppError };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_ERROR_HANDLER = textwrap.dedent(
        """
        const { AppError } = require('../services/userService');

        async function errorHandler(ctx, next) {
            try {
                await next();
            } catch (error) {
                if (error instanceof AppError) {
                    ctx.status = error.status;
                    ctx.body = { message: error.message };
                    return;
                }
                ctx.status = 500;
                ctx.body = { message: 'Something went wrong' };
            }
        }

        module.exports = { errorHandler };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_LOGGER = textwrap.dedent(
        """
        async function logger(ctx, next) {
            console.log(ctx.method + ' ' + ctx.url);
            await next();
        }

        module.exports = { logger };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_VALIDATION = textwrap.dedent(
        """
        function validateUserCreate(body) {
            if (!body || typeof body.name !== 'string' || body.name.trim().length < 2) {
                throw new Error('Name must be at least 2 characters');
            }
            if (!body.email || typeof body.email !== 'string' || !body.email.includes('@')) {
                throw new Error('Email must be valid');
            }
        }

        function validateUserUpdate(body) {
            validateUserCreate(body);
        }

        module.exports = { validateUserCreate, validateUserUpdate };
        """
).strip() + "\n"


DEFAULT_KOA_SIMPLE_TEST = textwrap.dedent(
        """
        const test = require('node:test');
        const assert = require('node:assert/strict');
        const request = require('supertest');
        const { createApp } = require('../src/app');

        test('GET /health returns ok', async () => {
            const app = createApp();
            const response = await request(app.callback()).get('/health');
            assert.equal(response.status, 200);
        });
        """
).strip() + "\n"


def load_template(relative_path: str, fallback: str | None = None, tutorial: bool = False) -> str:
    """Read a packaged template, falling back to an inline default.

    Stacks that keep their templates on disk only omit ``fallback``; a missing
    file is then a packaging bug and raises instead of silently producing an
    empty project.
    """
    if tutorial:
        # Try tutorial version first (e.g., python/fastapi/tutorial/main.py)
        tutorial_candidate = TEMPLATES_DIR / "tutorial" / relative_path
        if tutorial_candidate.exists():
            return tutorial_candidate.read_text(encoding="utf-8")
    candidate = TEMPLATES_DIR / relative_path
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    if fallback is None:
        raise ScaffoldError(f"Missing packaged template: {relative_path}")
    return fallback


def render_template(template: str, values: dict[str, str]) -> str:
    rendered = template
    for key, value in values.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def render_gitignore(spec: ProjectSpec) -> str:
    common = [
        ".DS_Store",
        "Thumbs.db",
        ".vscode/",
        ".idea/",
        ".env",
        ".env.*",
        "!.env.example",
    ]
    if spec.language == "python":
        common.extend([
            "__pycache__/",
            "*.py[cod]",
            ".venv/",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            "build/",
            "dist/",
            "*.egg-info/",
        ])
    elif spec.language == "node":
        common.extend([
            "node_modules/",
            "dist/",
            "coverage/",
            ".next/",
        ])
    elif spec.language == "ruby":
        common.extend([
            "vendor/bundle/",
            ".bundle/",
            "log/",
            "tmp/",
            "storage/",
            ".byebug_history",
        ])
    elif spec.language == "java":
        common.extend([
            "target/",
            "*.class",
            ".gradle/",
            "out/",
        ])
    elif spec.language == "go":
        common.extend([
            "bin/",
            "*.exe",
            "*.test",
            "coverage.out",
            "vendor/",
        ])
    return "\n".join(common) + "\n"


def render_readme(spec: ProjectSpec, plan: FrameworkPlan) -> str:
    framework_template = f"{spec.language}/{spec.framework}/README.md"
    template = load_template(framework_template, load_template("shared/README.md", DEFAULT_README_TEMPLATE))
    return render_template(
        template,
        {
            "project_name": spec.name,
            "language": spec.language,
            "framework": spec.framework,
            "summary": plan.readme_summary,
            "install": plan.readme_install,
            "run": plan.readme_run,
            "notes": format_notes(plan.project_notes),
        },
    )


def render_license(spec: ProjectSpec) -> str:
    template = load_template("shared/LICENSE", DEFAULT_LICENSE_TEMPLATE)
    return render_template(
        template,
        {
            "year": str(datetime.now().year),
            "project_name": spec.name,
        },
    )


DEFAULT_README_TEMPLATE = textwrap.dedent(
    """
    # {{project_name}}

    {{summary}}

    ## Stack
    - Language: {{language}}
    - Framework: {{framework}}

    ## Install
    {{install}}

    ## Run
    {{run}}

    ## Notes
    {{notes}}
    """
).strip() + "\n"


DEFAULT_LICENSE_TEMPLATE = textwrap.dedent(
    """
    MIT License

    Copyright (c) {{year}} {{project_name}} contributors

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """
).strip() + "\n"


def format_notes(notes: Iterable[str]) -> str:
    items = list(notes)
    if not items:
        return "- No additional notes."
    return "\n".join(f"- {item}" for item in items)


def venv_executable(venv_path: Path, executable: str) -> str:
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / f"{executable}.exe")
    return str(venv_path / "bin" / executable)


# Tutorial-mode templates with explanatory comments for beginners
TUTORIAL_FASTAPI_TEMPLATE = textwrap.dedent(
    '''
    """Main application entry point for FastAPI."""
    from fastapi import FastAPI

    # Import route handlers (these define your API endpoints)
    from src.api.routes.health import router as health_router
    from src.api.routes.users import router as users_router

    # Create the FastAPI application instance
    # FastAPI is the web framework - it handles HTTP requests and responses
    app = FastAPI(title="{{project_name}}")

    # Register route handlers with the application
    # Each router contains related endpoints grouped together
    app.include_router(health_router)
    app.include_router(users_router)


    @app.get("/readyz")
    def ready() -> dict[str, str]:
        """Health check endpoint - returns basic status info."""
        return {"status": "ready", "project": "{{project_name}}"}
    '''
).strip() + "\n"


TUTORIAL_FLASK_TEMPLATE = textwrap.dedent(
    '''
    """Main application entry point for Flask."""
    from flask import Flask

    # Import blueprint (a blueprint groups related routes together)
    from src.routes import health_bp


    def create_app() -> Flask:
        """Application factory pattern - creates and configures the Flask app."""
        app = Flask(__name__)

        # Register the blueprint to add its routes to the app
        app.register_blueprint(health_bp)

        return app


    # Create the app instance - this is what uvicorn/gunicorn will run
    app = create_app()


    if __name__ == "__main__":
        # This runs the development server when you execute `python src/app.py`
        app.run(debug=True)
    '''
).strip() + "\n"


TUTORIAL_AIOHTTP_TEMPLATE = textwrap.dedent(
    '''
    """Main application entry point for aiohttp."""
    from aiohttp import web

    # Import route handlers
    from src.routes import health_routes, user_routes
    from src.config import settings


    def create_app() -> web.Application:
        """Creates and configures the aiohttp application."""
        app = web.Application()

        # Add route handlers - these define your API endpoints
        # Each handler is mapped to a URL path and HTTP method
        app.router.add_routes(health_routes)
        app.router.add_routes(user_routes)

        return app


    # Create the app instance
    app = create_app()


    if __name__ == "__main__":
        # Run the development server on localhost:8080
        web.run_app(app, host="0.0.0.0", port=8080)
    '''
).strip() + "\n"


TUTORIAL_PYTHON_CONFIG = textwrap.dedent(
    '''
    """Configuration settings for the application.

    This module uses environment variables to make the app flexible:
    - APP_ENV: controls whether you're in development, staging, or production
    - DATABASE_URL: specifies where your database is located
    """
    import os
    from dataclasses import dataclass


    @dataclass(frozen=True)
    class Settings:
        """Settings class - frozen=True makes it immutable (read-only)."""
        # Get from environment, default to 'development' if not set
        env: str = os.getenv("APP_ENV", "development")
        db_url: str = os.getenv("DATABASE_URL", "sqlite:///data/app.db")


    # Create a single instance that all modules can import
    settings = Settings()
    '''
).strip() + "\n"


TUTORIAL_PYTHON_DB = textwrap.dedent(
    '''
    """Database connection utilities.

    This module provides a simple way to connect to SQLite.
    SQLite is great for learning and development - no server needed!
    """
    from pathlib import Path
    import sqlite3

    from src.config import settings


    def _sqlite_path() -> Path:
        """Extract file path from DATABASE_URL (e.g., sqlite:///data/app.db -> data/app.db)."""
        raw = settings.db_url
        if raw.startswith("sqlite:///"):
            return Path(raw.replace("sqlite:///", "", 1))
        return Path("data/app.db")


    def get_connection() -> sqlite3.Connection:
        """Creates a connection to the SQLite database.

        Returns:
            sqlite3.Connection: A connection object used to execute queries

        Usage:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
        """
        db_path = _sqlite_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        return connection
    '''
).strip() + "\n"


TUTORIAL_FLASK_ROUTES = textwrap.dedent(
    '''
    """Route handlers for Flask application.

    A Blueprint is a way to organize related routes together.
    Think of it like a chapter in a book - it groups related pages.
    """
    from flask import Blueprint, jsonify, request

    from src.config import settings


    # Create a blueprint named 'health' - all routes here start with /health (if prefixed)
    health_bp = Blueprint("health", __name__)

    # In-memory storage for demo purposes
    # In a real app, you'd use a database instead
    users: list[dict[str, object]] = []
    next_id = 1


    @health_bp.get("/")
    def health() -> tuple[dict[str, str], int]:
        """Health check endpoint - returns status and environment info."""
        return jsonify(status="ok", project="{{project_name}}", env=settings.env), 200
        # 200 is the HTTP status code for "OK"


    @health_bp.get("/users")
    def list_users() -> tuple[dict[str, object], int]:
        """GET /users - List all users in the system."""
        return jsonify(users=users), 200


    @health_bp.get("/users/<int:user_id>")
    def get_user(user_id: int) -> tuple[dict[str, object], int]:
        """GET /users/:id - Get a specific user by ID.

        The <int:user_id> part tells Flask to:
        1. Match URLs like /users/1, /users/42
        2. Convert the ID to an integer
        3. Pass it to the function as user_id
        """
        for user in users:
            if user["id"] == user_id:
                return jsonify(user), 200
        return jsonify(error="User not found"), 404
        # 404 is "Not Found" - the user doesn't exist


    @health_bp.post("/users")
    def create_user() -> tuple[dict[str, object], int]:
        """POST /users - Create a new user.

        request.get_json() extracts JSON data from the request body.
        Example: {"name": "Alice"} becomes {"name": "Alice"}
        """
        global next_id
        payload = request.get_json(silent=True) or {}
        name = payload.get("name", "Anonymous")

        user = {"id": next_id, "name": name}
        users.append(user)
        next_id += 1

        return jsonify(user), 201
        # 201 is "Created" - a new resource was successfully created
    '''
).strip() + "\n"


TUTORIAL_FASTAPI_HEALTH_ROUTES = textwrap.dedent(
    '''
    """Health check routes for FastAPI application.

    FastAPI route handlers are defined with decorators like @app.get().
    The decorator specifies the HTTP method (GET, POST, etc.) and URL path.
    """
    from fastapi import APIRouter, HTTPException

    from src.core.config import settings


    # APIRouter groups related routes - think of it like a chapter for API endpoints
    router = APIRouter(tags=["health"])


    @router.get("/")
    def health() -> dict[str, str]:
        """Health check endpoint - returns status and current environment.

        Returns:
            dict: A dictionary that FastAPI automatically converts to JSON
        """
        return {"status": "ok", "env": settings.env}


    @router.get("/readyz")
    def ready() -> dict[str, str]:
        """Readiness check - used by load balancers to know if the app is ready."""
        return {"status": "ready", "project": "{{project_name}}"}
    '''
).strip() + "\n"


TUTORIAL_FASTAPI_USERS_ROUTES = textwrap.dedent(
    '''
    """User management routes for FastAPI application.

    FastAPI automatically handles:
    - Request body validation (using Pydantic models)
    - Response serialization (converting Python to JSON)
    - OpenAPI/Swagger documentation
    """
    from fastapi import APIRouter, HTTPException

    from src.core.config import settings


    router = APIRouter(tags=["users"])

    # In-memory storage (in a real app, use a database)
    users_db: list[dict] = []
    next_id = 1


    @router.get("/users")
    def list_users() -> dict[str, list]:
        """GET /users - Retrieve all users.

        The -> dict[str, list] is a type hint that FastAPI uses for:
        1. Validating the response matches this shape
        2. Generating OpenAPI documentation
        """
        return {"users": users_db}


    @router.get("/users/{user_id}")
    def get_user(user_id: int) -> dict:
        """GET /users/:id - Get a specific user by ID.

        FastAPI automatically converts the path parameter to int.
        If it can't convert (e.g., /users/abc), it returns a 422 error.
        """
        for user in users_db:
            if user["id"] == user_id:
                return user
        raise HTTPException(status_code=404, detail="User not found")
        # HTTPException is FastAPI's way to return error responses


    @router.post("/users")
    def create_user(name: str) -> dict:
        """POST /users - Create a new user.

        The 'name: str' parameter comes from the request body or query string.
        FastAPI validates the type and returns 422 if invalid.
        """
        global next_id
        user = {"id": next_id, "name": name}
        users_db.append(user)
        next_id += 1
        return user
    '''
).strip() + "\n"


TUTORIAL_AIOHTTP_ROUTES = textwrap.dedent(
    '''
    """Route handlers for aiohttp application.

    aiohttp uses plain functions as handlers, decorated with HTTP method names.
    Each handler receives the request object and returns a response.
    """
    from aiohttp import web

    from src.config import settings


    # Define routes as a list - maps URL paths to handler functions
    health_routes = [
        web.get("/", health),
        web.get("/readyz", ready),
    ]

    user_routes = [
        web.get("/users", list_users),
        web.get("/users/{user_id}", get_user),
        web.post("/users", create_user),
    ]

    # In-memory storage (use a database in production)
    users_db: list[dict] = []
    next_id = 1


    async def health(request: web.Request) -> web.Response:
        """Health check endpoint.

        Handlers are async functions - they can handle many concurrent requests.
        The 'request' parameter contains info about the HTTP request.
        """
        return web.json_response({"status": "ok", "env": settings.env})


    async def ready(request: web.Request) -> web.Response:
        """Readiness check for load balancers."""
        return web.json_response({"status": "ready"})


    async def list_users(request: web.Request) -> web.Response:
        """GET /users - List all users."""
        return web.json_response({"users": users_db})


    async def get_user(request: web.Request) -> web.Response:
        """GET /users/:id - Get a specific user.

        request.match_info extracts path parameters defined with {}.
        """
        user_id = int(request.match_info["user_id"])
        for user in users_db:
            if user["id"] == user_id:
                return web.json_response(user)
        return web.json_response({"error": "User not found"}, status=404)


    async def create_user(request: web.Request) -> web.Response:
        """POST /users - Create a new user.

        await request.json() asynchronously reads the request body.
        """
        global next_id
        data = await request.json()
        name = data.get("name", "Anonymous")

        user = {"id": next_id, "name": name}
        users_db.append(user)
        next_id += 1

        return web.json_response(user, status=201)
    '''
).strip() + "\n"


TUTORIAL_EXPRESS_SERVER = textwrap.dedent(
    '''
    """Main server file for Express/Node.js application.

    Express is the most popular Node.js web framework.
    It handles routing (matching URLs to handlers) and middleware.
    """
    const express = require("express");

    # Import route handlers
    const healthRoutes = require("./routes/health");
    const userRoutes = require("./routes/users");

    # Create an Express application instance
    const app = express();

    # Middleware: functions that run before your route handlers
    # express.json() parses JSON request bodies
    app.use(express.json());

    # Register route handlers
    # Each router handles a group of related endpoints
    app.use("/", healthRoutes);
    app.use("/api", userRoutes);

    # Start the server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
    });
    '''
).strip() + "\n"


TUTORIAL_KOA_SERVER = textwrap.dedent(
    '''
    """Main server file for Koa/Node.js application.

    Koa is a lightweight web framework by the Express team.
    It uses async/await and has a smaller core than Express.
    """
    const Koa = require("koa");
    const bodyParser = require("koa-bodyparser");

    # Import route handlers
    const healthRoutes = require("./routes/health");
    const userRoutes = require("./routes/users");

    # Create a Koa application instance
    const app = new Koa();

    # Middleware: Koa uses a "context" (ctx) object passed through each middleware
    # ctx.request has request info, ctx.response has response info

    # Error handling middleware
    app.use(async (ctx, next) => {
      try {
        await next();
      } catch (err) {
        ctx.status = err.status || 500;
        ctx.body = { error: err.message };
      }
    });

    # Body parser middleware - parses JSON request bodies
    app.use(bodyParser());

    # Register route handlers
    app.use(healthRoutes.routes());
    app.use(userRoutes.routes());

    # Start the server
    const PORT = process.env.PORT || 3000;
    app.listen(PORT, () => {
      console.log(`Server running on http://localhost:${PORT}`);
    });
    '''
).strip() + "\n"


TUTORIAL_EXPRESS_HEALTH_ROUTE = textwrap.dedent(
    '''
    """Health check routes for Express application.

    Express routes follow the pattern: app.METHOD(PATH, HANDLER)
    - METHOD: get, post, put, delete, etc.
    - PATH: the URL path to match
    - HANDLER: function that processes the request
    """
    const express = require("express");
    const router = express.Router();

    # GET / - Health check endpoint
    router.get("/", (req, res) => {
      # res.json() automatically converts objects to JSON and sets Content-Type
      res.json({ status: "ok", project: "{{project_name}}" });
    });

    # GET /readyz - Readiness check for load balancers
    router.get("/readyz", (req, res) => {
      res.json({ status: "ready" });
    });

    module.exports = router;
    '''
).strip() + "\n"


TUTORIAL_KOA_HEALTH_ROUTE = textwrap.dedent(
    '''
    """Health check routes for Koa application.

    Koa routes use @koa/router library.
    The handler receives (ctx, next):
    - ctx: context object with request/response info
    - next: function to call the next middleware
    """
    const Router = require("@koa/router");

    const router = new Router();

    # GET / - Health check endpoint
    router.get("/", (ctx, next) => {
      # ctx.body sets the response body (equivalent to res.json())
      ctx.body = { status: "ok", project: "{{project_name}}" };
    });

    # GET /readyz - Readiness check
    router.get("/readyz", (ctx, next) => {
      ctx.body = { status: "ready" };
    });

    module.exports = router;
    '''
).strip() + "\n"


TUTORIAL_SINATRA_APP = textwrap.dedent(
    '''
    """Main Sinatra application file.

    Sinatra is a Ruby DSL for creating web applications.
    Routes are defined with HTTP method names (get, post, etc.).
    """
    require "sinatra"
    require "json"

    # set :bind, "0.0.0.0"  # Uncomment to listen on all interfaces
    set :port, 9292

    # GET / - Health check endpoint
    get "/" do
      content_type :json
      { status: "ok", project: "{{project_name}}" }.to_json
    end

    # GET /readyz - Readiness check
    get "/readyz" do
      content_type :json
      { status: "ready" }.to_json
    end

    # In-memory user storage (use a database in production)
    USERS = []

    # GET /users - List all users
    get "/users" do
      content_type :json
      { users: USERS }.to_json
    end

    # GET /users/:id - Get a specific user
    get "/users/:id" do
      user = USERS.find { |u| u["id"] == params[:id].to_i }
      if user
        user.to_json
      else
        status 404
        { error: "User not found" }.to_json
      end
    end

    # POST /users - Create a new user
    post "/users" do
      data = JSON.parse(request.body.read) rescue {}
      user = { id: USERS.length + 1, name: data["name"] || "Anonymous" }
      USERS << user
      status 201
      user.to_json
    end
    '''
).strip() + "\n"


TUTORIAL_JAVALIN_APP = textwrap.dedent(
    '''
    """Main application class for Javalin.

    Javalin is a lightweight Java/Kotlin web framework.
    It combines the simplicity of Express (JS) with Java's type safety.
    """
    package com.example;

    import io.javalin.Javalin;
    import io.javalin.http.staticfiles.Location;
    import com.example.config.AppConfig;
    import com.example.routes.HealthRoutes;
    import com.example.routes.UserRoutes;

    public class App {
        public static void main(String[] args) {
            # Create and configure the Javalin app
            Javalin app = Javalin.create(config -> {
                # Serve static files from /public if needed
                config.staticFiles.add("/public", Location.CLASSPATH);
            });

            # Configure JSON serialization
            AppConfig.configure(app);

            # Register route handlers
            # Each Routes class adds related endpoints to the app
            HealthRoutes.register(app);
            UserRoutes.register(app);

            # Start the server on port 8080
            app.start(8080);
        }
    }
    '''
).strip() + "\n"
