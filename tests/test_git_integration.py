
import subprocess
from pathlib import Path

from smart_test_impact_analyzer.analyzer import analyze_changes
from smart_test_impact_analyzer.git_diff import get_changed_files


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_real_git_change_selects_impacted_tests(tmp_path):
    repo = tmp_path

    run_git(repo, "init", "-b", "main")
    run_git(repo, "config", "user.email", "test@example.com")
    run_git(repo, "config", "user.name", "Test User")

    calculator = repo / "src" / "payments" / "calculator.py"
    service = repo / "src" / "payments" / "service.py"
    calculator_test = repo / "tests" / "test_calculator.py"
    service_test = repo / "tests" / "test_service.py"

    for path in [calculator, service, calculator_test, service_test]:
        path.parent.mkdir(parents=True, exist_ok=True)

    calculator.write_text(
        "def add(a, b):\n    return a + b\n"
    )
    service.write_text(
        "from payments.calculator import add\n\n"
        "def total(a, b):\n    return add(a, b)\n"
    )
    calculator_test.write_text(
        "from payments.calculator import add\n"
    )
    service_test.write_text(
        "from payments.service import total\n"
    )

    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "Initial test repository")

    base_commit = run_git(repo, "rev-parse", "HEAD")

    calculator.write_text(
        "def add(a, b):\n    return a + b + 0\n"
    )

    run_git(repo, "add", ".")
    run_git(repo, "commit", "-m", "Change calculator")

    head_commit = run_git(repo, "rev-parse", "HEAD")

    changed_files = get_changed_files(
        repo,
        base_commit,
        head_commit,
    )

    assert len(changed_files) == 1
    assert changed_files[0].path == "src/payments/calculator.py"

    result = analyze_changes(repo, changed_files)

    assert result.mode == "targeted"
    assert result.selected_tests == [
        "tests/test_calculator.py",
        "tests/test_service.py",
    ]
