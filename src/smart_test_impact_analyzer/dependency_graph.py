
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
}


def discover_python_files(repo_path: Path) -> list[Path]:
    return [
        path
        for path in repo_path.rglob("*.py")
        if not any(part in IGNORED_DIRS for part in path.parts)
    ]

def path_to_module(path: Path, repo_path: Path) -> str:
    relative = path.relative_to(repo_path)
    parts = list(relative.with_suffix("").parts)

    if parts[0] == "src":
        parts.pop(0)

    if parts[-1] == "__init__":
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
        parts = parts[:-remove_count]

    if node.module:
        parts.extend(node.module.split("."))

    return ".".join(parts)


def build_dependency_graph(
    repo_path: Path,
) -> dict[str, set[str]]:
    files = discover_python_files(repo_path)

    module_to_path = {
        path_to_module(path, repo_path): path
        for path in files
    }

    known_modules = set(module_to_path)
    graph = {module: set() for module in module_to_path}

    for module, path in module_to_path.items():
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeError, SyntaxError) as error:
            raise ValueError(
                f"Could not analyze Python file {path}: {error}"
            ) from error

        is_package = path.name == "__init__.py"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported = alias.name

                    if imported in known_modules:
                        graph[module].add(imported)

            elif isinstance(node, ast.ImportFrom):
                base = resolve_import(
                    node,
                    module,
                    is_package,
                )

                if base in known_modules:
                    graph[module].add(base)

                for alias in node.names:
                    candidate = (
                        f"{base}.{alias.name}"
                        if base
                        else alias.name
                    )

                    if candidate in known_modules:
                        graph[module].add(candidate)

    return dict(graph)


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
