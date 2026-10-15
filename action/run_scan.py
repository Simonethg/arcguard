"""Run arcaudit and write the SARIF file the GitHub Action uploads.

When ``arcaudit scan --help`` does not offer SARIF, the scaffold CLI is still
executed and text rules in ``engine.py`` produce the report. A later CLI that
accepts ``--format sarif --output <file>`` replaces those text rules.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_ENGINE_PATH = Path(__file__).resolve().parent / "engine.py"
_SPEC = importlib.util.spec_from_file_location("arcguard_action_engine", _ENGINE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_engine = importlib.util.module_from_spec(_SPEC)
sys.modules["arcguard_action_engine"] = _engine
_SPEC.loader.exec_module(_engine)


class CliError(RuntimeError):
    """``arcaudit`` claimed SARIF support but did not write a report."""


def _workspace() -> Path:
    raw = os.environ.get("GITHUB_WORKSPACE")
    if raw:
        return Path(raw).resolve()
    return Path.cwd().resolve()


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _setting(env_name: str, cli_value: str | None, default: str) -> str:
    if env_name in os.environ and os.environ[env_name] != "":
        return os.environ[env_name]
    if cli_value:
        return cli_value
    return default


def _ignore_list(cli_ignore: list[str]) -> list[str]:
    if "INPUT_IGNORE" in os.environ:
        return [line.strip() for line in os.environ["INPUT_IGNORE"].splitlines() if line.strip()]
    return cli_ignore


def _write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as handle:
        handle.write(f"{name}={value.replace(chr(10), ' ')}\n")


def _tool_version() -> str:
    try:
        completed = subprocess.run(
            ["arcaudit", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return "0.1.0"
    text = (completed.stdout or completed.stderr).strip()
    parts = text.split()
    return parts[-1] if parts else "0.1.0"


def consult_arcaudit(target: Path, sarif_path: Path, markdown_path: Path) -> tuple[str, str]:
    """Run the CLI. Return ``(sarif|text, note)``."""

    try:
        help_run = subprocess.run(
            ["arcaudit", "scan", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise CliError("arcaudit is not on PATH") from exc
    help_text = f"{help_run.stdout}\n{help_run.stderr}"
    if "--format" in help_text and "sarif" in help_text.lower():
        command = [
            "arcaudit",
            "scan",
            str(target),
            "--format",
            "sarif",
            "--output",
            str(sarif_path),
        ]
        if "--markdown-output" in help_text:
            command.extend(["--markdown-output", str(markdown_path)])
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        note = (completed.stderr or completed.stdout).strip()
        if sarif_path.is_file():
            return "sarif", note
        raise CliError(note or f"arcaudit exited {completed.returncode} without SARIF")
    completed = subprocess.run(
        ["arcaudit", "scan", str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    note = (completed.stderr or completed.stdout).strip()
    print(note, file=sys.stderr)
    return "text", note


def _resolve_target(raw: str, workspace: Path) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    resolved = candidate.resolve()
    if not _inside(resolved, workspace):
        raise CliError("scan path must stay inside the workspace")
    if not resolved.exists():
        raise CliError(f"scan path does not exist: {raw}")
    return resolved


def _resolve_output(raw: str, workspace: Path) -> Path:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = workspace / candidate
    resolved = candidate.resolve()
    if not _inside(resolved, workspace):
        raise CliError("report path must stay inside the workspace")
    return resolved


def run(argv: list[str] | None = None) -> int:
    """Execute a scan and write SARIF plus Markdown. Return a status code."""

    parser = argparse.ArgumentParser(description="Run arcaudit and write SARIF.")
    parser.add_argument("--path", default=None)
    parser.add_argument("--fail-on", default=None)
    parser.add_argument("--sarif", default=None)
    parser.add_argument("--markdown", default=None)
    parser.add_argument("--ignore", action="append", default=[])
    parser.add_argument("--engine", choices=("auto", "text"), default="auto")
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0. The Action reads should-fail from the step output.",
    )
    args = parser.parse_args(argv)

    workspace = _workspace()
    scan_raw = _setting("INPUT_PATH", args.path, ".")
    fail_on = _setting("INPUT_FAIL_ON", args.fail_on, "high")
    sarif_raw = _setting("INPUT_SARIF_FILE", args.sarif, "arcguard.sarif")
    markdown_raw = args.markdown or "arcguard-summary.md"
    ignore = _ignore_list(args.ignore)
    report_only = args.report_only or os.environ.get("ARCGUARD_REPORT_ONLY") == "1"

    try:
        target = _resolve_target(scan_raw, workspace)
        sarif_path = _resolve_output(sarif_raw, workspace)
        markdown_path = _resolve_output(markdown_raw, workspace)
        engine_name = "text-rules"
        cli_note = ""
        findings = []
        if args.engine == "auto":
            mode, cli_note = consult_arcaudit(target, sarif_path, markdown_path)
            if mode == "sarif":
                payload = json.loads(sarif_path.read_text(encoding="utf-8"))
                findings = _engine.findings_from_sarif(payload)
                engine_name = "arcaudit"
                if not markdown_path.is_file():
                    markdown_path.write_text(
                        _engine.build_markdown(findings, scan_raw, engine_name, cli_note),
                        encoding="utf-8",
                    )
            else:
                findings = _engine.scan_tree(target, workspace, ignore)
        else:
            findings = _engine.scan_tree(target, workspace, ignore)
            cli_note = "text rules only; arcaudit was not invoked"
        if engine_name == "text-rules":
            version = _tool_version() if args.engine == "auto" else "0.1.0"
            payload = _engine.build_sarif(findings, version, engine_name, cli_note)
            _engine.write_json(sarif_path, payload)
            markdown_path.write_text(
                _engine.build_markdown(findings, scan_raw, engine_name, cli_note),
                encoding="utf-8",
            )
    except (CliError, ValueError, json.JSONDecodeError, OSError) as exc:
        print(f"arcguard: {exc}", file=sys.stderr)
        return 2

    failed = _engine.should_fail(findings, fail_on)
    for finding in findings:
        print(
            f"{finding.rule.rule_id} {finding.rule.severity} "
            f"{finding.path}:{finding.line} {finding.rule.slug}"
        )
    print(
        f"arcguard-result engine={engine_name} findings={len(findings)} "
        f"should-fail={'true' if failed else 'false'}"
    )
    _write_output("sarif-file", sarif_path.relative_to(workspace).as_posix())
    _write_output("markdown-file", str(markdown_path))
    _write_output("finding-count", str(len(findings)))
    _write_output("engine", engine_name)
    _write_output("should-fail", "true" if failed else "false")
    if report_only:
        return 0
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(run())
