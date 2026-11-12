
import argparse
import sys
from pathlib import Path

from smart_test_impact_analyzer.analyzer import analyze_changes
from smart_test_impact_analyzer.git_diff import get_changed_files
from smart_test_impact_analyzer.reporter import (
    render_json,
    render_markdown,
    render_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze Git changes and select the tests most likely "
            "to be impacted."
        )
    )

    parser.add_argument(
        "--repo",
        type=Path,
        default=Path("."),
        help="Repository path (default: current directory)",
    )

    parser.add_argument(
        "--base",
        default="origin/main",
        help="Base Git reference (default: origin/main)",
    )

    parser.add_argument(
        "--head",
        default="HEAD",
        help="Head Git reference (default: HEAD)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Report format (default: text)",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the report",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        changed_files = get_changed_files(
            args.repo,
            args.base,
            args.head,
        )

        result = analyze_changes(args.repo, changed_files)

        renderers = {
            "text": render_text,
            "json": render_json,
            "markdown": render_markdown,
        }

        output = renderers[args.format](result)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + "\n", encoding="utf-8")
            print(f"Report written to {args.output}")
        else:
            print(output)

    except Exception as error:
        print(f"Error analyzing repository: {error}", file=sys.stderr)
        raise SystemExit(2) from error


if __name__ == "__main__":
    main()
