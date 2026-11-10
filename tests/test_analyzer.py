
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
