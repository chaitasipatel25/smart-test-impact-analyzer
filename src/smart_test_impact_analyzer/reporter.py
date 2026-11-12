
import json

from smart_test_impact_analyzer.analyzer import AnalysisResult


def build_report(result: AnalysisResult) -> dict:
    selected_count = len(result.selected_tests)

    return {
        "schema_version": "1.0",
        "mode": result.mode,
        "changed_files": result.changed_files,
        "selected_tests": result.selected_tests,
        "selected_test_count": selected_count,
        "total_test_count": result.total_tests,
        "selection_ratio": (
            round(selected_count / result.total_tests, 3)
            if result.total_tests
            else 0.0
        ),
        "fallback_reason": result.fallback_reason,
        "reasons": result.reasons,
    }


def render_json(result: AnalysisResult) -> str:
    return json.dumps(build_report(result), indent=2)


def render_text(result: AnalysisResult) -> str:
    report = build_report(result)

    lines = [
        "Smart Test Impact Analyzer",
        "=" * 50,
        "",
        f"Selection mode: {report['mode'].upper()}",
        f"Changed files: {len(report['changed_files'])}",
        (
            f"Selected tests: {report['selected_test_count']} "
            f"/ {report['total_test_count']}"
        ),
        f"Selection ratio: {report['selection_ratio']:.1%}",
    ]

    if report["fallback_reason"]:
        lines.extend([
            "",
            f"Fallback reason: {report['fallback_reason']}",
        ])

    lines.extend([
        "",
        "Selected Tests",
        "-" * 50,
    ])

    if not result.selected_tests:
        lines.append("No tests discovered.")
    else:
        for test in result.selected_tests:
            lines.append(f"\n{test}")

            for reason in result.reasons.get(test, []):
                lines.append(f"  Reason: {reason}")

    return "\n".join(lines)


def render_markdown(result: AnalysisResult) -> str:
    report = build_report(result)

    lines = [
        "# Test Impact Analysis",
        "",
        f"**Selection mode:** `{report['mode'].upper()}`",
        "",
        f"**Changed files:** {len(report['changed_files'])}",
        f"**Selected tests:** {report['selected_test_count']} / "
        f"{report['total_test_count']}",
        f"**Selection ratio:** {report['selection_ratio']:.1%}",
        "",
    ]

    if report["fallback_reason"]:
        lines.extend([
            "## Safety fallback",
            "",
            report["fallback_reason"],
            "",
        ])

    lines.extend([
        "## Changed files",
        "",
    ])

    if report["changed_files"]:
        lines.extend(f"- `{path}`" for path in report["changed_files"])
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Selected tests",
        "",
    ])

    if not result.selected_tests:
        lines.append("No tests discovered.")
    else:
        for test in result.selected_tests:
            lines.append(f"### `{test}`")

            for reason in result.reasons.get(test, []):
                lines.append(f"- {reason}")

            lines.append("")

    return "\n".join(lines)
