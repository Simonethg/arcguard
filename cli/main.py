"""ArcGuard CLI.

``arcaudit scan <path|github-url> --chain arc|base|celo|all`` runs the chain
modules and can emit text, JSON, SARIF 2.1.0, or Markdown. The process exits
1 when a finding's severity is at least ``--threshold``, and 2 when the scan
could not finish (bad target, a missing module, or a detector that crashed).
A crashed detector is never reported as a clean scan.

Live checks stay on public testnets. ArcGuard does not certify security and
does not replace an audit.
"""

from __future__ import annotations

import argparse
import os
import sys

from arcguard import __version__

from .engine import ChainModuleError, TargetError, execute, exit_code
from .report import render

DISCLAIMER = (
    "Multichain scanner for Arc, Base, and Celo. "
    "Live checks stay on public testnets. "
    "ArcGuard does not certify security and does not replace an audit."
)

_FORMATS = ("text", "json", "sarif", "markdown")
_THRESHOLDS = ("info", "low", "medium", "high", "critical")


def build_parser() -> argparse.ArgumentParser:
    """Build the ``arcaudit`` argument parser."""

    parser = argparse.ArgumentParser(prog="arcaudit", description=DISCLAIMER)
    parser.add_argument("--version", action="version", version=f"arcguard {__version__}")
    subparsers = parser.add_subparsers(dest="command")
    scan = subparsers.add_parser(
        "scan",
        help="Scan a local path or a public GitHub URL.",
        description=(
            "Run arcguard.arc, arcguard.base, and arcguard.celo when those modules "
            "are installed. Emit text, JSON, SARIF 2.1.0, or Markdown. " + DISCLAIMER
        ),
    )
    scan.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Local file or directory, or a public https://github.com/owner/repo URL.",
    )
    scan.add_argument(
        "--chain",
        choices=("arc", "base", "celo", "all"),
        default="all",
        help="Chain module to run. 'all' runs every installed module (default: all).",
    )
    scan.add_argument(
        "--format",
        choices=_FORMATS,
        default="text",
        help="Report format written to stdout or --output (default: text).",
    )
    scan.add_argument(
        "--threshold",
        choices=_THRESHOLDS,
        default="low",
        help=(
            "Exit 1 when a finding is at least this severity (default: low). "
            "Exit 2 means the scan did not finish; it is never a clean result."
        ),
    )
    scan.add_argument(
        "--include-tests",
        action="store_true",
        help=(
            "Also run ARC-OFF-1 on test and mock paths (test/, mocks/, *.t.sol, "
            "*.test.ts). They are skipped by default."
        ),
    )
    scan.add_argument(
        "--output",
        help="Write the report to this file as well as stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process status code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command != "scan":
        parser.print_help()
        return 0
    previous = os.environ.get("ARCGUARD_INCLUDE_TESTS")
    if args.include_tests:
        os.environ["ARCGUARD_INCLUDE_TESTS"] = "1"
    try:
        report = execute(args.target, chain=args.chain, threshold=args.threshold)
    except (TargetError, ChainModuleError) as exc:
        print(f"arcaudit: {exc}", file=sys.stderr)
        return 2
    finally:
        if args.include_tests:
            if previous is None:
                os.environ.pop("ARCGUARD_INCLUDE_TESTS", None)
            else:
                os.environ["ARCGUARD_INCLUDE_TESTS"] = previous
    rendered = render(report, args.format)
    sys.stdout.write(rendered)
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(rendered)
        except OSError as exc:
            print(f"arcaudit: could not write {args.output}: {exc}", file=sys.stderr)
            return 2
    for error in report.errors:
        print(f"arcaudit: error: {error}", file=sys.stderr)
    return exit_code(report.findings, args.threshold, report.errors)


if __name__ == "__main__":
    raise SystemExit(main())
