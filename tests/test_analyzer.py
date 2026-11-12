
from pathlib import Path

from smart_test_impact_analyzer.analyzer import analyze_changes
from smart_test_impact_analyzer.git_diff import ChangedFile


def create_file(root: Path, relative: str, content: str):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def create_sample_repo(root: Path):
    create_file(
        root,
        "src/payments/calculator.py",
        "def calculate(): pass",
    )
    create_file(
        root,
        "src/payments/service.py",
        "from payments.calculator import calculate",
    )
    create_file(
        root,
        "tests/test_payment.py",
        "from payments.service import process",
    )
    create_file(
        root,
        "tests/test_other.py",
        "def test_other(): pass",
    )


def test_selects_transitively_impacted_tests(tmp_path):
    create_sample_repo(tmp_path)

    result = analyze_changes(
        tmp_path,
        [
            ChangedFile(
                path="src/payments/calculator.py",
                status="M",
            )
        ],
    )

    assert result.mode == "targeted"
    assert result.selected_tests == ["tests/test_payment.py"]
    assert result.total_tests == 2


def test_selects_changed_test_directly(tmp_path):
    create_sample_repo(tmp_path)

    result = analyze_changes(
        tmp_path,
        [
            ChangedFile(
                path="tests/test_other.py",
                status="M",
            )
        ],
    )

    assert result.mode == "targeted"
    assert result.selected_tests == ["tests/test_other.py"]


def test_configuration_change_selects_full_suite(tmp_path):
    create_sample_repo(tmp_path)

    result = analyze_changes(
        tmp_path,
        [
            ChangedFile(
                path="pyproject.toml",
                status="M",
            )
        ],
    )

    assert result.mode == "full"
    assert result.total_tests == 2
    assert len(result.selected_tests) == 2


def test_deleted_file_selects_full_suite(tmp_path):
    create_sample_repo(tmp_path)

    result = analyze_changes(
        tmp_path,
        [
            ChangedFile(
                path="src/payments/calculator.py",
                status="D",
            )
        ],
    )

    assert result.mode == "full"
    assert len(result.selected_tests) == 2


def test_unparseable_file_selects_full_suite(tmp_path):
    create_sample_repo(tmp_path)
    create_file(
        tmp_path,
        "src/payments/broken.py",
        "def invalid syntax(",
    )

    result = analyze_changes(
        tmp_path,
        [
            ChangedFile(
                path="src/payments/calculator.py",
                status="M",
            )
        ],
    )

    assert result.mode == "full"
    assert result.fallback_reason is not None


from smart_test_impact_analyzer.analyzer import (
    analyze_changes,
    is_test_file,
)
from smart_test_impact_analyzer.git_diff import ChangedFile


def test_does_not_count_tests_init_as_a_test():
    assert not is_test_file(Path("tests/__init__.py"))


def test_recognizes_pytest_test_filenames():
    assert is_test_file(Path("tests/test_payment.py"))
    assert is_test_file(Path("tests/payment_test.py"))


def test_unknown_non_python_change_selects_full_suite(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()

    (tmp_path / "src" / "calculator.py").write_text(
        "def add(a, b):\n    return a + b\n"
    )
    (tmp_path / "tests" / "test_calculator.py").write_text(
        "from calculator import add\n"
    )

    result = analyze_changes(
        tmp_path,
        [ChangedFile("Dockerfile", "M")],
    )

    assert result.mode == "full"
    assert "Dockerfile" in result.fallback_reason


def test_documentation_change_uses_safe_fallback_when_no_tests_are_impacted(
    tmp_path,
):
    (tmp_path / "tests").mkdir()

    (tmp_path / "tests" / "test_example.py").write_text(
        "def test_example():\n    assert True\n"
    )

    result = analyze_changes(
        tmp_path,
        [ChangedFile("README.md", "M")],
    )

    assert result.mode == "full"
    assert result.total_tests == 1
