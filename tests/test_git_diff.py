
from types import SimpleNamespace

from smart_test_impact_analyzer.git_diff import get_changed_files


def test_parses_git_diff_output(tmp_path, monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            stdout=(
                "M\tsrc/payments/calculator.py\n"
                "A\ttests/test_payment.py\n"
            )
        )

    monkeypatch.setattr(
        "smart_test_impact_analyzer.git_diff.subprocess.run",
        fake_run,
    )

    result = get_changed_files(
        tmp_path,
        "main",
        "HEAD",
    )

    assert len(result) == 2
    assert result[0].path == "src/payments/calculator.py"
    assert result[0].status == "M"
    assert result[1].path == "tests/test_payment.py"
    assert result[1].status == "A"
