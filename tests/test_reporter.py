
import json

from smart_test_impact_analyzer.analyzer import AnalysisResult
from smart_test_impact_analyzer.reporter import (
    build_report,
    render_json,
    render_markdown,
    render_text,
)


def sample_result():
    return AnalysisResult(
        mode="targeted",
        changed_files=["src/payments/calculator.py"],
        selected_tests=[
            "tests/test_calculator.py",
            "tests/test_payment_service.py",
        ],
        reasons={
            "tests/test_calculator.py": [
                "Depends directly or transitively on src/payments/calculator.py"
            ],
            "tests/test_payment_service.py": [
                "Depends directly or transitively on src/payments/calculator.py"
            ],
        },
        total_tests=5,
    )


def test_build_report_contains_selection_metrics():
    report = build_report(sample_result())

    assert report["schema_version"] == "1.0"
    assert report["mode"] == "targeted"
    assert report["selected_test_count"] == 2
    assert report["total_test_count"] == 5
    assert report["selection_ratio"] == 0.4


def test_json_report_is_valid_json():
    output = render_json(sample_result())
    report = json.loads(output)

    assert report["selected_tests"] == [
        "tests/test_calculator.py",
        "tests/test_payment_service.py",
    ]


def test_text_report_contains_selection_summary():
    output = render_text(sample_result())

    assert "Selection mode: TARGETED" in output
    assert "Selected tests: 2 / 5" in output
    assert "tests/test_calculator.py" in output


def test_markdown_report_contains_changed_files_and_tests():
    output = render_markdown(sample_result())

    assert "# Test Impact Analysis" in output
    assert "src/payments/calculator.py" in output
    assert "tests/test_payment_service.py" in output


def test_empty_test_suite_has_zero_selection_ratio():
    result = AnalysisResult(
        mode="full",
        changed_files=[],
        selected_tests=[],
        reasons={},
        total_tests=0,
        fallback_reason="No tests discovered",
    )

    report = build_report(result)

    assert report["selection_ratio"] == 0.0
