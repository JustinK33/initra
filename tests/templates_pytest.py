from __future__ import annotations

from pathlib import Path

import pytest

from initra.core import ProjectSpec, generate_framework_plan, render_gitignore


STACK_CASES = [
    pytest.param(
        "python",
        "flask",
        False,
        {
            "src/app.py",
            "src/config.py",
            "src/db.py",
            "src/routes.py",
            "tests/test_health.py",
        },
        id="python-flask",
    ),
    pytest.param(
        "python",
        "fastapi",
        False,
        {
            "src/main.py",
            "src/core/config.py",
            "src/db.py",
            "src/api/routes/health.py",
            "src/api/routes/users.py",
            "tests/test_health.py",
        },
        id="python-fastapi",
    ),
    pytest.param(
        "python",
        "aiohttp",
        False,
        {
            "src/main.py",
            "src/config.py",
            "src/db.py",
            "src/routes.py",
            "tests/test_health.py",
        },
        id="python-aiohttp",
    ),
    pytest.param(
        "node",
        "express",
        False,
        {
            "src/app.js",
            "src/server.js",
            "src/routes/health.js",
            "src/routes/users.js",
            "src/controllers/userController.js",
            "tests/app.test.js",
        },
        id="node-express",
    ),
    pytest.param(
        "node",
        "express-ts",
        False,
        {
            "src/app.ts",
            "src/server.ts",
            "src/routes/health.ts",
            "src/routes/users.ts",
            "src/controllers/userController.ts",
            "tests/app.test.ts",
            "tsconfig.json",
        },
        id="node-express-ts",
    ),
    pytest.param(
        "node",
        "koa",
        False,
        {
            "src/app.js",
            "src/server.js",
            "src/routes/health.js",
            "src/routes/users.js",
            "src/controllers/userController.js",
            "tests/app.test.js",
        },
        id="node-koa",
    ),
    pytest.param(
        "ruby",
        "sinatra",
        False,
        {
            "app.rb",
            "config.ru",
            "Gemfile",
            "lib/config.rb",
            "lib/db.rb",
            "test/test_app.rb",
        },
        id="ruby-sinatra",
    ),
    pytest.param(
        "java",
        "javalin",
        False,
        {
            "pom.xml",
            ".env.example",
            "src/main/java/com/example/App.java",
            "src/main/java/com/example/config/AppConfig.java",
            "src/main/resources/application.properties",
            "src/test/java/com/example/services/UserServiceTest.java",
        },
        id="java-javalin",
    ),
]


PYTHON_CASES = [
    pytest.param("python", "flask", False, id="python-flask"),
    pytest.param("python", "fastapi", False, id="python-fastapi"),
    pytest.param("python", "aiohttp", False, id="python-aiohttp"),
]


def build_spec(
    tmp_path: Path,
    language: str,
    framework: str,
    *,
    tutorial: bool,
    typescript: bool = False,
) -> ProjectSpec:
    return ProjectSpec(
        name="demo-template",
        language=language,
        framework=framework,
        path=tmp_path / "demo-template",
        typescript=typescript,
        no_install=True,
        no_git=True,
        tutorial=tutorial,
    )


@pytest.mark.parametrize("tutorial", [False, True], ids=["standard", "tutorial"])
@pytest.mark.parametrize("language,framework,typescript,expected_files", STACK_CASES)
def test_template_plans_include_expected_files(
    tmp_path: Path,
    language: str,
    framework: str,
    typescript: bool,
    expected_files: set[str],
    tutorial: bool,
) -> None:
    spec = build_spec(tmp_path, language, framework, tutorial=tutorial, typescript=typescript)
    plan = generate_framework_plan(spec)

    generated_files = {path for path, _ in plan.files}
    assert expected_files.issubset(generated_files)


@pytest.mark.parametrize("language,framework,typescript,expected_files", STACK_CASES)
def test_standard_template_plans_render_project_name_placeholders(
    tmp_path: Path,
    language: str,
    framework: str,
    typescript: bool,
    expected_files: set[str],
) -> None:
    spec = build_spec(tmp_path, language, framework, tutorial=False, typescript=typescript)
    plan = generate_framework_plan(spec)

    unresolved = [path for path, content in plan.files if "{{project_name}}" in content]
    assert unresolved == []


@pytest.mark.parametrize("tutorial", [False, True], ids=["standard", "tutorial"])
@pytest.mark.parametrize("language,framework,typescript", PYTHON_CASES)
def test_python_template_files_compile(
    tmp_path: Path,
    language: str,
    framework: str,
    typescript: bool,
    tutorial: bool,
) -> None:
    spec = build_spec(tmp_path, language, framework, tutorial=tutorial, typescript=typescript)
    plan = generate_framework_plan(spec)

    python_files = [(path, content) for path, content in plan.files if path.endswith(".py")]
    assert python_files

    for path, content in python_files:
        compile(content, path, "exec")


@pytest.mark.parametrize("language", ["python", "node", "ruby", "java"])
def test_gitignore_includes_env_rules_for_all_languages(tmp_path: Path, language: str) -> None:
    framework = {
        "python": "flask",
        "node": "express",
        "ruby": "sinatra",
        "java": "javalin",
    }[language]
    spec = ProjectSpec(
        name="demo-template",
        language=language,
        framework=framework,
        path=tmp_path / "demo-template",
    )
    content = render_gitignore(spec)
    assert ".env\n" in content
    assert ".env.*\n" in content
    assert "!.env.example\n" in content
