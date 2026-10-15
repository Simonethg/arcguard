"""Smoke tests for the scaffold CLI and the Slither plugin hook."""

from __future__ import annotations

import re
from importlib.metadata import entry_points
from pathlib import Path

import pytest

from arcguard import __version__
from arcguard.cli.main import main
from arcguard.plugin import make_plugin

ROOT = Path(__file__).resolve().parents[1]


def test_help_describes_scope(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--help"])
    assert raised.value.code == 0
    output = capsys.readouterr().out
    assert "arcaudit" in output
    assert "testnet" in output.lower()
    assert "audit" in output.lower()


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["--version"])
    assert raised.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_scan_clean_directory_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = main(["scan", str(tmp_path), "--chain", "arc"])
    assert status == 0
    output = capsys.readouterr().out
    assert "No findings" in output
    assert "audit" in output.lower()


def test_plugin_registers_arc_detectors() -> None:
    detectors, printers = make_plugin()
    assert printers == []
    assert [detector.RULE_ID for detector in detectors] == [
        "ARC-001",
        "ARC-002",
        "ARC-003",
        "ARC-004",
        "ARC-005",
        "ARC-006",
        "ARC-007",
        "ARC-008",
    ]
    for detector in detectors:
        assert detector.ARGUMENT.startswith("arc-")
        assert detector.WIKI.startswith("https://")
        assert detector.WIKI_DESCRIPTION
        assert detector.WIKI_RECOMMENDATION
        assert "arc.io" in detector.DOCS


def test_version_matches_project_metadata() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)
    assert match is not None
    assert match.group(1) == __version__


def test_slither_and_console_entry_points() -> None:
    plugins = {item.name: item.value for item in entry_points(group="slither_analyzer.plugin")}
    scripts = {item.name: item.value for item in entry_points(group="console_scripts")}
    assert plugins["arcguard"] == "arcguard.plugin:make_plugin"
    assert scripts["arcaudit"] == "arcguard.cli.main:main"
