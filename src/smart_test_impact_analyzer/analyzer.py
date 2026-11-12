
from dataclasses import dataclass
from pathlib import Path

from smart_test_impact_analyzer.dependency_graph import (
    build_dependency_graph,
    discover_python_files,
    find_dependents,
    path_to_module,
)
from smart_test_impact_analyzer.git_diff import ChangedFile


FULL_SUITE_CONFIG_FILES = {
    "pyproject.toml",
    "pytest.ini",
    "setup.cfg",
    "tox.ini",
    "setup.py",
    "noxfile.py",
    "requirements.txt",
    "requirements-dev.txt",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
}

DOCUMENTATION_SUFFIXES = {
    ".md",
    ".rst",
    ".adoc",
}


@dataclass
class AnalysisResult:
    mode: str
    changed_files: list[str]
    selected_tests: list[str]
    reasons: dict[str, list[str]]
    total_tests: int
    fallback_reason: str | None = None


def is_test_file(path: Path) -> bool:
    return (
        path.name.startswith("test_")
        or path.name.endswith("_test.py")
    )


def analyze_changes(
    repo_path: Path,
    changed_files: list[ChangedFile],
) -> AnalysisResult:
    repo_path = repo_path.resolve()

    all_python_files = discover_python_files(repo_path)

    test_files = sorted(
        path.relative_to(repo_path).as_posix()
        for path in all_python_files
        if is_test_file(path.relative_to(repo_path))
    )

    changed_paths = [item.path for item in changed_files]

    def full_suite(reason: str) -> AnalysisResult:
        return AnalysisResult(
            mode="full",
            changed_files=changed_paths,
            selected_tests=test_files,
            reasons={
                test: [f"Full-suite fallback: {reason}"]
                for test in test_files
            },
            total_tests=len(test_files),
            fallback_reason=reason,
        )

    if not changed_files:
        return full_suite("No changed files were supplied")

    for item in changed_files:
        path = Path(item.path)
        filename = path.name

        if item.status.startswith(("D", "R", "C")):
            return full_suite(
                f"Deleted, renamed, or copied file: {item.path}"
            )

        if (
            filename in FULL_SUITE_CONFIG_FILES
            or filename.startswith("requirements")
            and filename.endswith(".txt")
            or filename == "conftest.py"
            or item.path.startswith(".github/workflows/")
        ):
            return full_suite(
                f"Test configuration or CI configuration changed: {item.path}"
            )

        if path.suffix != ".py" and path.suffix not in DOCUMENTATION_SUFFIXES:
            return full_suite(
                f"Unrecognized non-Python file changed: {item.path}"
            )

    try:
        graph = build_dependency_graph(repo_path)
    except ValueError as error:
        return full_suite(str(error))

    reasons: dict[str, list[str]] = {}

    for item in changed_files:
        changed_path = Path(item.path)

        # Documentation changes do not affect Python dependencies.
        if changed_path.suffix in DOCUMENTATION_SUFFIXES:
            continue

        if changed_path.suffix != ".py":
            continue

        relative_path = changed_path
        module = path_to_module(
            repo_path / relative_path,
            repo_path,
        )

        if is_test_file(relative_path):
            if item.path not in test_files:
                return full_suite(
                    f"Changed test could not be mapped: {item.path}"
                )

            reasons.setdefault(item.path, []).append(
                f"Test file changed directly: {item.path}"
            )
            continue

        if module not in graph:
            return full_suite(
                f"Changed Python module could not be analyzed: {item.path}"
            )

        impacted_modules = find_dependents(graph, module)

        for test in test_files:
            test_module = path_to_module(
                repo_path / test,
                repo_path,
            )

            if test_module in impacted_modules:
                reasons.setdefault(test, []).append(
                    f"Depends directly or transitively on {item.path}"
                )

    if not reasons:
        return full_suite(
            "No impacted tests could be confidently identified"
        )

    selected_tests = sorted(reasons)

    return AnalysisResult(
        mode="targeted",
        changed_files=changed_paths,
        selected_tests=selected_tests,
        reasons=reasons,
        total_tests=len(test_files),
    )
