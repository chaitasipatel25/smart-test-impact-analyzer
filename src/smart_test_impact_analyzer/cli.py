
import argparse
import json
from pathlib import Path

from smart_test_impact_analyzer.analyzer import analyze_changes
from smart_test_impact_analyzer.git_diff import get_changed_files


def main():
    parser = argparse.ArgumentParser(
        description="Select tests impacted by Git changes."
    )

    parser.add_argument(
        "--repo",
        default=".",
        help="Repository path",
    )
    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base Git reference",
    )
    parser.add_argument(
        "--head",
        default="HEAD",
        help="Head Git reference",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )

    args = parser.parse_args()
    repo_path = Path(args.repo).resolve()

    try:
        changed_files = get_changed_files(
            repo_path,
            args.base,
            args.head,
        )

        result = analyze_changes(repo_path, changed_files)

    except Exception as error:
        parser.exit(
            2,
            f"Error analyzing repository: {error}\n",
        )

    report = {
        "mode": result.mode,
        "changed_files": result.changed_files,
        "selected_tests": result.selected_tests,
        "selected_test_count": len(result.selected_tests),
        "total_test_count": result.total_tests,
        "fallback_reason": result.fallback_reason,
        "reasons": result.reasons,
    }

    if args.format == "json":
        print(json.dumps(report, indent=2))
        return

    print("Smart Test Impact Analyzer")
    print("=" * 50)
    print(f"Selection mode: {result.mode.upper()}")
    print(f"Changed files: {len(result.changed_files)}")
    print(
        f"Selected tests: {len(result.selected_tests)}"
        f" / {result.total_tests}"
    )

    if result.fallback_reason:
        print(f"Fallback reason: {result.fallback_reason}")

    print("\nSelected Tests")
    print("-" * 50)

    for test in result.selected_tests:
        print(f"\n{test}")

        for reason in result.reasons.get(test, []):
            print(f"  Reason: {reason}")

    if not result.selected_tests:
        print("No tests selected.")


if __name__ == "__main__":
    main()
