from __future__ import annotations

from pathlib import Path

import pytest

from initra.core import (
    ProjectSpec,
    ScaffoldError,
    generate_framework_plan,
    load_template,
    render_gitignore,
    render_readme,
)


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
    pytest.param(
        "go",
        "gin",
        False,
        {
            "go.mod",
            "main.go",
            "internal/config/config.go",
            "internal/router/router.go",
            "internal/store/user_store.go",
            "internal/handlers/health.go",
            "internal/handlers/users.go",
            "internal/handlers/users_test.go",
        },
        id="go-gin",
    ),
    pytest.param(
        "cpp",
        "cmake",
        False,
        {
            "CMakeLists.txt",
            "src/main.cpp",
            "src/server.cpp",
            "src/server.h",
            "src/user_store.cpp",
            "src/user_store.h",
            "tests/CMakeLists.txt",
            "tests/test_user_store.cpp",
            "tests/test_server.cpp",
        },
        id="cpp-cmake",
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


LANGUAGE_FRAMEWORKS = {
    "python": "flask",
    "node": "express",
    "ruby": "sinatra",
    "java": "javalin",
    "go": "gin",
    "cpp": "cmake",
}


@pytest.mark.parametrize("language", sorted(LANGUAGE_FRAMEWORKS))
def test_gitignore_includes_env_rules_for_all_languages(tmp_path: Path, language: str) -> None:
    spec = ProjectSpec(
        name="demo-template",
        language=language,
        framework=LANGUAGE_FRAMEWORKS[language],
        path=tmp_path / "demo-template",
    )
    content = render_gitignore(spec)
    assert ".env\n" in content
    assert ".env.*\n" in content
    assert "!.env.example\n" in content


@pytest.mark.parametrize(
    "language,expected",
    [
        ("go", ["bin/", "*.test"]),
        ("cpp", ["build/", "CMakeCache.txt", "compile_commands.json"]),
    ],
)
def test_gitignore_covers_build_artifacts(tmp_path: Path, language: str, expected: list[str]) -> None:
    spec = ProjectSpec(
        name="demo-template",
        language=language,
        framework=LANGUAGE_FRAMEWORKS[language],
        path=tmp_path / "demo-template",
    )
    content = render_gitignore(spec)
    for rule in expected:
        assert f"{rule}\n" in content


def test_missing_packaged_template_raises(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError, match="Missing packaged template"):
        load_template("go/gin/does-not-exist.go")


@pytest.mark.parametrize("language,framework,typescript,expected_files", STACK_CASES)
def test_readme_resolves_placeholders_from_plan_text(
    tmp_path: Path,
    language: str,
    framework: str,
    typescript: bool,
    expected_files: set[str],
) -> None:
    """Plan text (readme_run, project_notes) may contain {{project_name}} too."""
    spec = build_spec(tmp_path, language, framework, tutorial=False, typescript=typescript)
    readme = render_readme(spec, generate_framework_plan(spec))

    assert "{{" not in readme
    assert spec.name in readme
