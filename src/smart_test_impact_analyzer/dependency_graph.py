
import ast
from collections import defaultdict
from pathlib import Path

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    "build",
    "dist",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
}


def discover_python_files(repo_path: Path) -> list[Path]:
    repo_path = repo_path.resolve()

    return sorted(
        path
        for path in repo_path.rglob("*.py")
        if not any(
            part in IGNORED_DIRS
            for part in path.relative_to(repo_path).parts
        )
    )


def path_to_module(path: Path, repo_path: Path) -> str:
    relative = path.relative_to(repo_path)
    parts = list(relative.with_suffix("").parts)

    if parts and parts[0] == "src":
        parts.pop(0)

    if parts and parts[-1] == "__init__":
        parts.pop()

    return ".".join(parts)


def resolve_import(
    node: ast.ImportFrom,
    current_module: str,
    is_package: bool,
) -> str:
    if node.level == 0:
        return node.module or ""

    parts = current_module.split(".")

    if not is_package:
        parts = parts[:-1]

    remove_count = node.level - 1

    if remove_count:
        parts = parts[:-remove_count] if remove_count < len(parts) else []

    if node.module:
        parts.extend(node.module.split("."))

    return ".".join(parts)


def add_known_module_prefixes(
    imported: str,
    known_modules: set[str],
    dependencies: set[str],
) -> None:
    parts = imported.split(".")

    for index in range(1, len(parts) + 1):
        candidate = ".".join(parts[:index])

        if candidate in known_modules:
            dependencies.add(candidate)


def build_dependency_graph(repo_path: Path) -> dict[str, set[str]]:
    repo_path = repo_path.resolve()
    files = discover_python_files(repo_path)

    module_to_path = {
        path_to_module(path, repo_path): path
        for path in files
    }

    known_modules = set(module_to_path)

    # Include every discovered module, even modules with no imports.
    graph = {
        module: set()
        for module in module_to_path
    }

    for module, path in module_to_path.items():
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as error:
            raise ValueError(
                f"Could not analyze Python file {path}: {error}"
            ) from error

        is_package = path.name == "__init__.py"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    add_known_module_prefixes(
                        alias.name,
                        known_modules,
                        graph[module],
                    )

            elif isinstance(node, ast.ImportFrom):
                base = resolve_import(node, module, is_package)

                if base:
                    add_known_module_prefixes(
                        base,
                        known_modules,
                        graph[module],
                    )

                for alias in node.names:
                    if alias.name == "*":
                        continue

                    candidate = (
                        f"{base}.{alias.name}"
                        if base
                        else alias.name
                    )

                    add_known_module_prefixes(
                        candidate,
                        known_modules,
                        graph[module],
                    )

    return graph


def find_dependents(
    graph: dict[str, set[str]],
    changed_module: str,
) -> set[str]:
    reverse_graph = defaultdict(set)

    for module, dependencies in graph.items():
        for dependency in dependencies:
            reverse_graph[dependency].add(module)

    impacted = set()
    visited = {changed_module}
    queue = [changed_module]

    while queue:
        current = queue.pop(0)

        for dependent in reverse_graph[current]:
            if dependent not in visited:
                visited.add(dependent)
                impacted.add(dependent)
                queue.append(dependent)

    return impacted
