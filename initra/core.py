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

TEMPLATES_DIR = Path(__file__).with_name("templates")

SUPPORTED_LANGUAGES = {"python", "node", "ruby", "java", "go", "cpp"}
SUPPORTED_FRAMEWORKS = {
    "python": {"flask", "fastapi", "django", "aiohttp"},
    "node": {"express", "express-ts", "next", "koa"},
    "ruby": {"rails", "sinatra"},
    "java": {"springboot", "javalin"},
    "go": {"gin"},
    "cpp": {"cmake"},
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
    if spec.language == "cpp":
        return generate_cpp_plan(spec)
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
        t = spec.tutorial
        files.extend([
            ("src/config.py", load_template("python/flask/src/config.py", tutorial=t)),
            ("src/db.py", load_template("python/flask/src/db.py", tutorial=t)),
            ("src/routes.py", render_template(load_template("python/flask/src/routes.py", tutorial=t), {"project_name": spec.name})),
            (".env.example", DEFAULT_PYTHON_ENV),
        ])
        files.append(("src/app.py", render_template(load_template("python/flask/app.py", tutorial=t), {
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
        t = spec.tutorial
        files.extend([
            ("src/core/__init__.py", ""),
            ("src/core/config.py", load_template("python/fastapi/src/core/config.py", tutorial=t)),
            ("src/db.py", load_template("python/fastapi/src/db.py", tutorial=t)),
            ("src/api/__init__.py", ""),
            ("src/api/routes/__init__.py", ""),
            ("src/api/routes/health.py", render_template(load_template("python/fastapi/src/api/routes/health.py", tutorial=t), {"project_name": spec.name})),
            ("src/api/routes/users.py", render_template(load_template("python/fastapi/src/api/routes/users.py", tutorial=t), {"project_name": spec.name})),
            (".env.example", DEFAULT_PYTHON_ENV),
        ])
        files.append(("src/main.py", render_template(load_template("python/fastapi/main.py", tutorial=t), {
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
        t = spec.tutorial
        files.extend([
            ("src/config.py", load_template("python/aiohttp/src/config.py", tutorial=t)),
            ("src/db.py", load_template("python/aiohttp/src/db.py", tutorial=t)),
            ("src/routes.py", render_template(load_template("python/aiohttp/src/routes.py", tutorial=t), {"project_name": spec.name})),
            (".env.example", DEFAULT_PYTHON_ENV),
        ])
        files.append(("src/main.py", render_template(load_template("python/aiohttp/main.py", tutorial=t), {
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
        files = [
            ("Gemfile", load_template("ruby/sinatra/Gemfile")),
            ("app.rb", render_template(load_template("ruby/sinatra/app.rb"), {"project_name": spec.name})),
            ("config.ru", load_template("ruby/sinatra/config.ru")),
            ("lib/config.rb", load_template("ruby/sinatra/lib/config.rb")),
            ("lib/db.rb", load_template("ruby/sinatra/lib/db.rb")),
            ("test/test_app.rb", render_template(load_template("ruby/sinatra/test/test_app.rb"), {"project_name": spec.name})),
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
        files = [
            ("pom.xml", render_template(load_template("java/javalin/pom.xml"), {"project_name": spec.name})),
            ("Dockerfile", render_template(load_template("java/javalin/Dockerfile"), {"project_name": spec.name})),
            (".env.example", render_template(load_template("java/javalin/.env.example"), {"project_name": spec.name})),
            ("src/main/resources/application.properties", render_template(load_template("java/javalin/src/main/resources/application.properties"), {"project_name": spec.name})),
            ("src/main/java/com/example/App.java", render_template(load_template("java/javalin/src/main/java/com/example/App.java"), {"project_name": spec.name})),
            ("src/main/java/com/example/config/AppConfig.java", render_template(load_template("java/javalin/src/main/java/com/example/config/AppConfig.java"), {"project_name": spec.name})),
            ("src/main/java/com/example/routes/HealthRoutes.java", load_template("java/javalin/src/main/java/com/example/routes/HealthRoutes.java")),
            ("src/main/java/com/example/routes/UserRoutes.java", load_template("java/javalin/src/main/java/com/example/routes/UserRoutes.java")),
            ("src/main/java/com/example/controllers/HealthController.java", render_template(load_template("java/javalin/src/main/java/com/example/controllers/HealthController.java"), {"project_name": spec.name})),
            ("src/main/java/com/example/controllers/UserController.java", load_template("java/javalin/src/main/java/com/example/controllers/UserController.java")),
            ("src/main/java/com/example/services/UserService.java", load_template("java/javalin/src/main/java/com/example/services/UserService.java")),
            ("src/main/java/com/example/models/User.java", load_template("java/javalin/src/main/java/com/example/models/User.java")),
            ("src/main/java/com/example/dto/CreateUserRequest.java", load_template("java/javalin/src/main/java/com/example/dto/CreateUserRequest.java")),
            ("src/main/java/com/example/dto/UpdateUserRequest.java", load_template("java/javalin/src/main/java/com/example/dto/UpdateUserRequest.java")),
            ("src/main/java/com/example/dto/UserResponse.java", load_template("java/javalin/src/main/java/com/example/dto/UserResponse.java")),
            ("src/main/java/com/example/exceptions/ApiException.java", load_template("java/javalin/src/main/java/com/example/exceptions/ApiException.java")),
            ("src/main/java/com/example/exceptions/NotFoundException.java", load_template("java/javalin/src/main/java/com/example/exceptions/NotFoundException.java")),
            ("src/main/java/com/example/exceptions/ValidationException.java", load_template("java/javalin/src/main/java/com/example/exceptions/ValidationException.java")),
            ("src/main/java/com/example/middleware/ExceptionMapper.java", load_template("java/javalin/src/main/java/com/example/middleware/ExceptionMapper.java")),
            ("src/main/java/com/example/middleware/RequestLoggingMiddleware.java", load_template("java/javalin/src/main/java/com/example/middleware/RequestLoggingMiddleware.java")),
            ("src/main/java/com/example/utils/ValidationUtils.java", load_template("java/javalin/src/main/java/com/example/utils/ValidationUtils.java")),
            ("src/main/java/com/example/repository/UserRepository.java", load_template("java/javalin/src/main/java/com/example/repository/UserRepository.java")),
            ("src/main/java/com/example/repository/InMemoryUserRepository.java", load_template("java/javalin/src/main/java/com/example/repository/InMemoryUserRepository.java")),
            ("src/test/java/com/example/services/UserServiceTest.java", load_template("java/javalin/src/test/java/com/example/services/UserServiceTest.java")),
            ("src/test/java/com/example/integration/HealthRoutesIntegrationTest.java", render_template(load_template("java/javalin/src/test/java/com/example/integration/HealthRoutesIntegrationTest.java"), {"project_name": spec.name})),
            ("src/test/java/com/example/integration/UserRoutesIntegrationTest.java", load_template("java/javalin/src/test/java/com/example/integration/UserRoutesIntegrationTest.java")),
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


CPP_CMAKE_FILES = [
    "CMakeLists.txt",
    "Dockerfile",
    ".dockerignore",
    ".clang-format",
    ".env.example",
    "src/main.cpp",
    "src/server.h",
    "src/server.cpp",
    "src/user_store.h",
    "src/user_store.cpp",
    "tests/CMakeLists.txt",
    "tests/test_user_store.cpp",
    "tests/test_server.cpp",
]


def generate_cpp_plan(spec: ProjectSpec) -> FrameworkPlan:
    # ponytail: on-disk templates only, same as go/gin. See generate_go_plan.
    files = [
        (path, render_template(load_template(f"cpp/cmake/{path}"), {"project_name": spec.name}))
        for path in CPP_CMAKE_FILES
    ]
    # The configure step is what downloads the FetchContent dependencies.
    post_commands = [] if spec.no_install else [["cmake", "-S", ".", "-B", "build"]]
    return FrameworkPlan(
        files=files,
        commands=[],
        post_commands=post_commands,
        readme_summary="A CMake C++20 HTTP API starter with a linkable core library and ctest coverage.",
        readme_run=(
            "Build with `cmake --build build`, run `./build/{{project_name}}`, "
            "then visit http://localhost:8080/health. Run tests with `ctest --test-dir build`."
        ),
        readme_install=(
            "Install CMake 3.20+ and a C++20 compiler, then run `cmake -S . -B build`. "
            "The first configure downloads cpp-httplib and nlohmann/json, so it needs network access."
        ),
        project_notes=[
            "Includes `/health` plus CRUD routes for `/users` and `/users/:id`.",
            "Application logic lives in the `{{project_name}}_lib` target so tests link it directly.",
            "`src/user_store.cpp` keeps users in memory behind a mutex and can be swapped for a database later.",
            "Dependencies are pinned by tag via CMake `FetchContent`; no system packages are required.",
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

    files = [
        ("package.json", build_express_package_json(project_name, is_ts, include_license=include_license)),
        (".env.example", DEFAULT_NODE_ENV_EXAMPLE),
        ("Dockerfile", DEFAULT_NODE_DOCKERFILE),
        (".dockerignore", DEFAULT_NODE_DOCKERIGNORE),
        (".eslintrc.json", DEFAULT_NODE_ESLINTRC),
        (".prettierrc", DEFAULT_NODE_PRETTIERRC),
        (app_file, render_template(load_template(f"{template_root}/{app_file}"), {"project_name": project_name})),
        (server_file, render_template(load_template(f"{template_root}/{server_file}"), {"project_name": project_name})),
        (config_file, load_template(f"{template_root}/{config_file}")),
        (route_file, render_template(load_template(f"{template_root}/{route_file}"), {"project_name": project_name})),
        (health_file, render_template(load_template(f"{template_root}/{health_file}"), {"project_name": project_name})),
        (user_file, render_template(load_template(f"{template_root}/{user_file}"), {"project_name": project_name})),
        (controller_file, render_template(load_template(f"{template_root}/{controller_file}"), {"project_name": project_name})),
        (service_file, render_template(load_template(f"{template_root}/{service_file}"), {"project_name": project_name})),
        (model_file, render_template(load_template(f"{template_root}/{model_file}"), {"project_name": project_name})),
        (middleware_file, load_template(f"{template_root}/{middleware_file}")),
        (logger_file, load_template(f"{template_root}/{logger_file}")),
        (utils_file, load_template(f"{template_root}/{utils_file}")),
        (tests_file, render_template(load_template(f"{template_root}/{tests_file}"), {"project_name": project_name})),
    ]
    if is_ts:
        files.append(("tsconfig.json", load_template(f"{template_root}/tsconfig.json")))
    return files


def build_simple_koa_files(
    project_name: str,
    tutorial: bool = False,
    include_license: bool = False,
) -> list[tuple[str, str]]:
    template_root = "node/koa"

    # Select tutorial or regular templates

    return [
        ("package.json", build_koa_package_json(project_name, include_license=include_license)),
        (".env.example", DEFAULT_NODE_ENV_EXAMPLE),
        ("Dockerfile", DEFAULT_NODE_DOCKERFILE),
        (".dockerignore", DEFAULT_NODE_DOCKERIGNORE),
        (".eslintrc.json", DEFAULT_NODE_ESLINTRC),
        (".prettierrc", DEFAULT_NODE_PRETTIERRC),
        ("src/app.js", render_template(load_template(f"{template_root}/src/app.js"), {"project_name": project_name})),
        ("src/server.js", render_template(load_template(f"{template_root}/src/server.js"), {"project_name": project_name})),
        ("src/config/index.js", load_template(f"{template_root}/src/config/index.js")),
        ("src/routes/index.js", render_template(load_template(f"{template_root}/src/routes/index.js"), {"project_name": project_name})),
        ("src/routes/health.js", render_template(load_template(f"{template_root}/src/routes/health.js"), {"project_name": project_name})),
        ("src/routes/users.js", render_template(load_template(f"{template_root}/src/routes/users.js"), {"project_name": project_name})),
        ("src/controllers/userController.js", render_template(load_template(f"{template_root}/src/controllers/userController.js"), {"project_name": project_name})),
        ("src/services/userService.js", render_template(load_template(f"{template_root}/src/services/userService.js"), {"project_name": project_name})),
        ("src/models/userStore.js", render_template(load_template(f"{template_root}/src/models/userStore.js"), {"project_name": project_name})),
        ("src/middleware/errorHandler.js", load_template(f"{template_root}/src/middleware/errorHandler.js")),
        ("src/middleware/logger.js", load_template(f"{template_root}/src/middleware/logger.js")),
        ("src/utils/validation.js", load_template(f"{template_root}/src/utils/validation.js")),
        ("tests/app.test.js", render_template(load_template(f"{template_root}/tests/app.test.js"), {"project_name": project_name})),
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




























DEFAULT_RUBY_ENV = textwrap.dedent(
        """
        APP_ENV=development
        PORT=4567
        DATABASE_URL=sqlite://data/app.db
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
















































































def load_template(relative_path: str, tutorial: bool = False) -> str:
    """Read a packaged template from ``initra/templates``.

    A missing file is a packaging bug, so it raises rather than silently
    producing an empty project. Callers that want an optional template must
    check :func:`template_exists` first.
    """
    if tutorial:
        # Tutorial variants mirror the standard tree under templates/tutorial/,
        # e.g. tutorial/python/fastapi/main.py. Stacks without one fall through
        # to the standard template.
        tutorial_candidate = TEMPLATES_DIR / "tutorial" / relative_path
        if tutorial_candidate.exists():
            return tutorial_candidate.read_text(encoding="utf-8")
    candidate = TEMPLATES_DIR / relative_path
    if not candidate.exists():
        raise ScaffoldError(f"Missing packaged template: {relative_path}")
    return candidate.read_text(encoding="utf-8")


def template_exists(relative_path: str) -> bool:
    return (TEMPLATES_DIR / relative_path).exists()


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
    elif spec.language == "cpp":
        common.extend([
            "build/",
            "cmake-build-*/",
            "CMakeCache.txt",
            "CMakeFiles/",
            "compile_commands.json",
            "*.o",
            "*.a",
            "*.so",
            "*.dylib",
        ])
    return "\n".join(common) + "\n"


def render_readme(spec: ProjectSpec, plan: FrameworkPlan) -> str:
    # A stack may ship its own README; otherwise every stack shares one.
    framework_template = f"{spec.language}/{spec.framework}/README.md"
    template = load_template(framework_template if template_exists(framework_template) else "shared/README.md")
    body = render_template(
        template,
        {
            "summary": plan.readme_summary,
            "install": plan.readme_install,
            "run": plan.readme_run,
            "notes": format_notes(plan.project_notes),
        },
    )
    # Plan text may itself contain {{project_name}}, so substitute names last.
    return render_template(
        body,
        {
            "project_name": spec.name,
            "language": spec.language,
            "framework": spec.framework,
        },
    )


def render_license(spec: ProjectSpec) -> str:
    template = load_template("shared/LICENSE")
    return render_template(
        template,
        {
            "year": str(datetime.now().year),
            "project_name": spec.name,
        },
    )






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




























