
from pathlib import Path

from smart_test_impact_analyzer.dependency_graph import (
    build_dependency_graph,
    find_dependents,
    path_to_module,
)


def create_file(root: Path, relative: str, content: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_builds_dependency_graph(tmp_path):
    create_file(
        tmp_path,
        "src/payments/calculator.py",
        "def calculate(): pass",
    )
    create_file(
        tmp_path,
        "src/payments/service.py",
        "from payments.calculator import calculate",
    )
    create_file(
        tmp_path,
        "tests/test_payment.py",
        "from payments.service import process",
    )

    graph = build_dependency_graph(tmp_path)

    assert "payments.calculator" in graph["payments.service"]
    assert "payments.service" in graph["tests.test_payment"]


def test_finds_transitive_dependents(tmp_path):
    create_file(
        tmp_path,
        "src/payments/calculator.py",
        "def calculate(): pass",
    )
    create_file(
        tmp_path,
        "src/payments/service.py",
        "from payments.calculator import calculate",
    )
    create_file(
        tmp_path,
        "tests/test_payment.py",
        "from payments.service import process",
    )

    graph = build_dependency_graph(tmp_path)

    impacted = find_dependents(
        graph,
        "payments.calculator",
    )

    assert "payments.service" in impacted
    assert "tests.test_payment" in impacted


def test_path_to_module_strips_src_directory(tmp_path):
    path = tmp_path / "src" / "payments" / "calculator.py"

    assert path_to_module(path, tmp_path) == "payments.calculator"


def test_invalid_python_file_raises_error(tmp_path):
    create_file(
        tmp_path,
        "src/payments/broken.py",
        "def invalid syntax(",
    )

    try:
        build_dependency_graph(tmp_path)
        assert False, "Expected ValueError"
    except ValueError:
        pass
