"""ArcGuard CLI.

``arcaudit --help`` and ``arcaudit --version`` work in the scaffold.
``arcaudit scan`` refuses to pretend a scan ran: detectors are not
implemented yet, and a green empty report would be a false assurance.
"""

from __future__ import annotations

import argparse
import sys

from arcguard import __version__

DISCLAIMER = "Arc testnet only. ArcGuard does not certify security and does not replace an audit."


def build_parser() -> argparse.ArgumentParser:
    """Build the ``arcaudit`` argument parser."""

    parser = argparse.ArgumentParser(
        prog="arcaudit",
        description=(
            "Scan Solidity sources and off-chain config for Arc-specific pitfalls. " + DISCLAIMER
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"arcguard {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command")
    scan = subparsers.add_parser(
        "scan",
        help="Scan a local path (not implemented in the scaffold).",
        description=(
            "Reserved for a later task. This scaffold does not execute detectors. " + DISCLAIMER
        ),
    )
    scan.add_argument(
        "path",
        nargs="?",
        default=".",
        help="File or directory to scan once detectors exist.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI. Returns a process status code."""

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "scan":
        print(
            "arcaudit: scan is not implemented in this scaffold. "
            "No detectors were executed and no report was produced.",
            file=sys.stderr,
        )
        return 2
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
