from __future__ import annotations

import json
import platform
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path.cwd()
TEMPLATES_DIR = Path(__file__).with_name("templates")

SUPPORTED_LANGUAGES = {"python", "node", "ruby", "java"}
SUPPORTED_FRAMEWORKS = {
    "python": {"flask", "fastapi", "django", "aiohttp"},
    "node": {"express", "express-ts", "next", "koa"},
    "ruby": {"rails", "sinatra"},
    "java": {"springboot", "javalin"},
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
        files.append(("src/app.py", render_template(load_template("python/flask/app.py", DEFAULT_FLASK_TEMPLATE), {
            "project_name": spec.name,
            "module_name": module_name,
        })))
        files.append(("tests/test_app.py", render_template(DEFAULT_FLASK_TEST, {"module_name": module_name})))
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        post_commands = [] if spec.no_install else [[pip, "install", "--upgrade", "pip"], [pip, "install", "-r", "requirements.txt"]]
        summary = "A Flask starter with a single JSON health endpoint."
        install_text = (
            "Install the virtual environment and Flask dependencies with `python -m venv .venv` and `pip install -r requirements.txt`."
            if not spec.no_install
            else "Dependency installation was skipped due to `--no-install`."
        )
        run_text = "Activate the virtual environment and run `flask --app src.app run`."
        notes = ["The project uses a local `.venv` that is ignored by git."]
    elif spec.framework == "fastapi":
        requirements = ["fastapi>=0.110,<1.0", "uvicorn[standard]>=0.30,<1.0"]
        files.append(("src/main.py", render_template(load_template("python/fastapi/main.py", DEFAULT_FASTAPI_TEMPLATE), {
            "project_name": spec.name,
            "module_name": module_name,
        })))
        files.append(("tests/test_app.py", render_template(DEFAULT_FASTAPI_TEST, {"project_name": spec.name})))
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        post_commands = [] if spec.no_install else [[pip, "install", "--upgrade", "pip"], [pip, "install", "-r", "requirements.txt"]]
        summary = "A FastAPI starter with typed models and a health endpoint."
        install_text = (
            "Create a virtual environment and install dependencies with `python -m venv .venv` and `pip install -r requirements.txt`."
            if not spec.no_install
            else "Dependency installation was skipped due to `--no-install`."
        )
        run_text = "Activate the virtual environment and run `uvicorn src.main:app --reload`."
        notes = ["The app is ready for Uvicorn out of the box."]
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
        files.append(("src/main.py", render_template(load_template("python/aiohttp/main.py", DEFAULT_AIOHTTP_TEMPLATE), {
            "project_name": spec.name,
            "module_name": module_name,
        })))
        files.append(("tests/test_app.py", render_template(DEFAULT_AIOHTTP_TEST, {"project_name": spec.name})))
        files.append(("requirements.txt", "\n".join(requirements) + "\n"))
        post_commands = [] if spec.no_install else [[pip, "install", "--upgrade", "pip"], [pip, "install", "-r", "requirements.txt"]]
        summary = "An aiohttp starter for async Python web services with a JSON health endpoint."
        install_text = (
            "Create a virtual environment and install dependencies with `python -m venv .venv` and `pip install -r requirements.txt`."
            if not spec.no_install
            else "Dependency installation was skipped due to `--no-install`."
        )
        run_text = "Activate the virtual environment and run `python -m src.main`."
        notes = ["The app is built with aiohttp and ready for async request handling."]
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
        files = [
            ("package.json", build_koa_package_json(spec.name)),
            ("src/index.js", render_template(load_template("node/koa/src/index.js", DEFAULT_KOA_TEMPLATE), {"project_name": spec.name})),
            ("tests/app.test.js", render_template(DEFAULT_KOA_TEST, {"project_name": spec.name})),
        ]
        post_commands = [] if spec.no_install else [["npm", "install"]]
        install_text = "Install dependencies with `npm install`." if not spec.no_install else "Dependency installation was skipped due to `--no-install`."
        return FrameworkPlan(
            files=files,
            commands=[],
            post_commands=post_commands,
            readme_summary="A Koa starter with a health endpoint and clean source layout.",
            readme_run="Run `npm run dev` during development or `npm start` in production.",
            readme_install=install_text,
            project_notes=["The project uses Koa with @koa/router for simple API routing."],
        )

    use_ts = spec.framework == "express-ts"
    package_json = build_express_package_json(spec.name, use_ts)
    files = [
        ("package.json", package_json),
        (
            "src/index.ts" if use_ts else "src/index.js",
            render_template(
                load_template("node/express-ts/src/index.ts", DEFAULT_EXPRESS_TS_TEMPLATE)
                if use_ts
                else load_template("node/express-js/src/index.js", DEFAULT_EXPRESS_JS_TEMPLATE),
                {"project_name": spec.name, "port": "PORT"},
            ),
        ),
        (
            "tests/app.test.ts" if use_ts else "tests/app.test.js",
            render_template(
                DEFAULT_EXPRESS_TS_TEST if use_ts else DEFAULT_EXPRESS_JS_TEST,
                {"project_name": spec.name},
            ),
        ),
    ]
    if use_ts:
        files.append(("tsconfig.json", EXPRESS_TS_CONFIG))

    post_commands = [] if spec.no_install else [["npm", "install"]]
    install_text = "Install dependencies with `npm install`." if not spec.no_install else "Dependency installation was skipped due to `--no-install`."

    return FrameworkPlan(
        files=files,
        commands=[],
        post_commands=post_commands,
        readme_summary="An Express starter with a health endpoint and clean source layout.",
        readme_run="Run `npm run dev` during development or `npm start` in production.",
        readme_install=install_text,
        project_notes=[
            "TypeScript support is enabled when the Express TypeScript variant is selected."
            if use_ts
            else "The project uses plain JavaScript and Node's standard runtime."
        ],
    )


def generate_ruby_plan(spec: ProjectSpec) -> FrameworkPlan:
    if spec.framework == "sinatra":
        files = [
            ("Gemfile", DEFAULT_SINATRA_GEMFILE),
            ("app.rb", render_template(DEFAULT_SINATRA_APP, {"project_name": spec.name})),
            ("config.ru", DEFAULT_SINATRA_RACKUP),
            ("test/test_app.rb", DEFAULT_SINATRA_TEST),
        ]
        post_commands = [] if spec.no_install else [["bundle", "install"]]
        install_text = "Run `bundle install` to install Ruby gems." if not spec.no_install else "Gem installation was skipped due to `--no-install`."
        return FrameworkPlan(
            files=files,
            commands=[],
            post_commands=post_commands,
            readme_summary="A Sinatra starter with a simple JSON health endpoint.",
            readme_run="Run `bundle exec ruby app.rb`.",
            readme_install=install_text,
            project_notes=["The generated app includes a minimal Rack setup and Minitest example."],
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
            ("pom.xml", build_javalin_pom(spec.name)),
            ("src/main/java/com/example/App.java", render_template(DEFAULT_JAVALIN_APP, {"project_name": spec.name})),
            ("src/test/java/com/example/AppTest.java", DEFAULT_JAVALIN_TEST),
        ]
        return FrameworkPlan(
            files=files,
            commands=[],
            post_commands=[],
            readme_summary="A Javalin starter with an HTTP health endpoint.",
            readme_run="Run `mvn compile exec:java`.",
            readme_install="Dependencies are defined in `pom.xml`; run `mvn clean package` to fetch and build.",
            project_notes=["The project uses Maven with JUnit and Javalin 6."],
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


def build_express_package_json(project_name: str, use_ts: bool) -> str:
    data = {
        "name": project_name,
        "version": "1.0.0",
        "private": True,
        "description": f"{project_name} Express application",
        "main": "dist/index.js" if use_ts else "src/index.js",
        "scripts": {
            "dev": "tsx watch src/index.ts" if use_ts else "node src/index.js",
            "start": "node dist/index.js" if use_ts else "node src/index.js",
            "build": "tsc -p tsconfig.json" if use_ts else "echo \"No build step required\"",
            "test": "tsx --test tests/app.test.ts" if use_ts else "node --test",
        },
        "keywords": ["express", "scaffold"],
        "license": "MIT",
    }
    data["dependencies"] = {"express": "^5.0.0"}
    if use_ts:
        data["type"] = "commonjs"
        data["devDependencies"] = {
            "@types/express": "^5.0.0",
            "@types/node": "^22.0.0",
            "tsx": "^4.16.0",
            "typescript": "^5.7.0",
        }
    return json.dumps(data, indent=2) + "\n"


def build_koa_package_json(project_name: str) -> str:
    data = {
        "name": project_name,
        "version": "1.0.0",
        "private": True,
        "description": f"{project_name} Koa application",
        "main": "src/index.js",
        "scripts": {
            "dev": "node src/index.js",
            "start": "node src/index.js",
            "test": "node --test",
        },
        "keywords": ["koa", "scaffold"],
        "license": "MIT",
        "dependencies": {
            "koa": "^2.15.0",
            "@koa/router": "^12.0.1",
        },
    }
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
    import os

    from flask import Flask, jsonify

    app = Flask(__name__)


    @app.get("/")
    def health():
        return jsonify(status="ok", project="{{project_name}}")


    if __name__ == "__main__":
        app.run(debug=os.getenv("FLASK_DEBUG") == "1")
    """
).strip() + "\n"


DEFAULT_FASTAPI_TEMPLATE = textwrap.dedent(
    """
    from fastapi import FastAPI

    app = FastAPI(title="{{project_name}}")


    @app.get("/")
    def health() -> dict[str, str]:
        return {"status": "ok", "project": "{{project_name}}"}
    """
).strip() + "\n"


DEFAULT_FLASK_TEST = textwrap.dedent(
    """
    import unittest

    from src.app import app


    class AppImportTest(unittest.TestCase):
        def test_app_exists(self):
            self.assertEqual(app.name, "src.app")


    if __name__ == "__main__":
        unittest.main()
    """
).strip() + "\n"


DEFAULT_FASTAPI_TEST = textwrap.dedent(
    """
    import unittest

    from src.main import app


    class AppImportTest(unittest.TestCase):
        def test_title_exists(self):
            self.assertEqual(app.title, "{{project_name}}")


    if __name__ == "__main__":
        unittest.main()
    """
).strip() + "\n"


DEFAULT_EXPRESS_JS_TEMPLATE = textwrap.dedent(
    """
    const express = require('express');

    const app = express();
    const port = process.env.PORT || 3000;

    app.get('/', (req, res) => {
      res.json({ status: 'ok', project: '{{project_name}}' });
    });

    if (require.main === module) {
      app.listen(port, () => {
        console.log(`{{project_name}} listening on port ${port}`);
      });
    }

    module.exports = app;
    """
).strip() + "\n"


DEFAULT_EXPRESS_TS_TEMPLATE = textwrap.dedent(
    """
    import express, { Request, Response } from 'express';

    const app = express();
    const port = Number(process.env.PORT || 3000);

    app.get('/', (req: Request, res: Response) => {
      res.json({ status: 'ok', project: '{{project_name}}' });
    });

    app.listen(port, () => {
      console.log(`{{project_name}} listening on port ${port}`);
    });

    export default app;
    """
).strip() + "\n"


DEFAULT_EXPRESS_JS_TEST = textwrap.dedent(
    """
        const assert = require('node:assert/strict');
        const test = require('node:test');

        const app = require('../src/index');

        test('loads the Express app', () => {
            assert.equal(typeof app, 'function');
        });
    """
).strip() + "\n"


DEFAULT_EXPRESS_TS_TEST = textwrap.dedent(
    """
        import assert from 'node:assert/strict';
        import test from 'node:test';

        import app from '../src/index';

        test('loads the Express app', () => {
            assert.equal(typeof app, 'function');
        });
    """
).strip() + "\n"


DEFAULT_AIOHTTP_TEMPLATE = textwrap.dedent(
        """
        from aiohttp import web


        async def health(request: web.Request) -> web.Response:
                return web.json_response({"status": "ok", "project": "{{project_name}}"})


        def create_app() -> web.Application:
                app = web.Application()
                app.router.add_get("/", health)
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
        const Koa = require('koa');
        const Router = require('@koa/router');

        const app = new Koa();
        const router = new Router();
        const port = process.env.PORT || 3000;

        router.get('/', (ctx) => {
            ctx.body = { status: 'ok', project: '{{project_name}}' };
        });

        app.use(router.routes());
        app.use(router.allowedMethods());

        if (require.main === module) {
            app.listen(port, () => {
                console.log(`{{project_name}} listening on port ${port}`);
            });
        }

        module.exports = app;
        """
).strip() + "\n"


DEFAULT_KOA_TEST = textwrap.dedent(
        """
                const assert = require('node:assert/strict');
                const test = require('node:test');

                const app = require('../src/index');

                test('loads the Koa app', () => {
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

        set :bind, '0.0.0.0'
        set :port, ENV.fetch('PORT', 4567)

        get '/' do
            content_type :json
            { status: 'ok', project: '{{project_name}}' }.to_json
        end
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
                    <groupId>org.junit.jupiter</groupId>
                    <artifactId>junit-jupiter</artifactId>
                    <version>5.10.2</version>
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


DEFAULT_JAVALIN_APP = textwrap.dedent(
        """
        package com.example;

        import io.javalin.Javalin;

        public final class App {
                private App() {}

                public static void main(String[] args) {
                        int port = Integer.parseInt(System.getenv().getOrDefault("PORT", "7000"));
                        Javalin app = Javalin.create();
                        app.get("/", ctx -> ctx.json(new HealthResponse("ok", "{{project_name}}")));
                        app.start(port);
                }

                public record HealthResponse(String status, String project) {}
        }
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


def load_template(relative_path: str, fallback: str) -> str:
    candidate = TEMPLATES_DIR / relative_path
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
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
            ".env",
            ".env.*",
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
    return "\n".join(common) + "\n"


def render_readme(spec: ProjectSpec, plan: FrameworkPlan) -> str:
    template = load_template("shared/README.md", DEFAULT_README_TEMPLATE)
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


def format_notes(notes: Iterable[str]) -> str:
    items = list(notes)
    if not items:
        return "- No additional notes."
    return "\n".join(f"- {item}" for item in items)


def venv_executable(venv_path: Path, executable: str) -> str:
    if platform.system() == "Windows":
        return str(venv_path / "Scripts" / f"{executable}.exe")
    return str(venv_path / "bin" / executable)
