import argparse
import sys
from pathlib import Path

from aicheck.analyzer import Analyzer
from aicheck.reporters.console import get_reporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aicheck",
        description="Catch AI-generated code issues before they catch you",
    )
    sub = parser.add_subparsers(dest="command")

    check = sub.add_parser("check", help="Analyze Python files for AI code issues")
    check.add_argument("path", type=str, nargs="?", default=".",
                       help="File or directory to check")
    check.add_argument("--format", choices=["console", "json"], default="console",
                       help="Output format")

    sub.add_parser("version", help="Show version")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "version" or not args.command:
        from aicheck import __version__
        print(f"aicheck v{__version__}")
        return 0

    if args.command == "check":
        target = Path(args.path).resolve()
        if not target.exists():
            print(f"Error: path '{target}' does not exist", file=sys.stderr)
            return 1
        analyzer = Analyzer()
        results = analyzer.check_path(target)
        reporter = get_reporter(args.format)
        output = reporter.report(results)
        print(output)
        all_passed = all(r.passed for r in results)
        return 0 if all_passed else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
