
import json

from smart_test_impact_analyzer.analyzer import AnalysisResult
from smart_test_impact_analyzer.cli import main
from smart_test_impact_analyzer.git_diff import ChangedFile


def test_cli_outputs_json(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.argv",
        ["test-impact", "--format", "json"],
    )

    monkeypatch.setattr(
        "smart_test_impact_analyzer.cli.get_changed_files",
        lambda *args: [
            ChangedFile("src/payments/calculator.py", "M")
        ],
    )

    monkeypatch.setattr(
        "smart_test_impact_analyzer.cli.analyze_changes",
        lambda *args: AnalysisResult(
            mode="targeted",
            changed_files=["src/payments/calculator.py"],
            selected_tests=["tests/test_payment.py"],
            reasons={
                "tests/test_payment.py": [
                    "Depends on changed module"
                ]
            },
            total_tests=10,
        ),
    )

    main()

    output = json.loads(capsys.readouterr().out)

    assert output["mode"] == "targeted"
    assert output["selected_test_count"] == 1
    assert output["total_test_count"] == 10
    assert output["selected_tests"] == ["tests/test_payment.py"]
