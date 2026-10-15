"""Chain registry, Base finding adapter, GitHub target parsing, and exit codes."""

from __future__ import annotations

import json
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest

from arcguard.cli.main import main
from arcguard.cli.targets import TargetError, parse_github, resolve_target
from arcguard.finding import Finding, normalize_finding
from arcguard.registry import ChainModuleError, load_scanner, scan_chains


@dataclass(frozen=True)
class _BaseFinding:
    """Shape published by arcguard.base (PR #2): path, not file; no chain; no doc_url."""

    rule_id: str
    slug: str
    severity: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class _BaseRule:
    rule_id: str
    slug: str
    severity: str
    extensions: tuple[str, ...]
    check: object
    doc: str


def test_base_shape_adapts_to_the_shared_finding() -> None:
    raw = _BaseFinding(
        "BASE-001",
        "b20-union-weakens-blocklist",
        "High",
        "pool.sol",
        4,
        "UNION weakens the blocklist",
    )
    module = types.SimpleNamespace(
        RULES=(
            _BaseRule(
                "BASE-001",
                "b20-union-weakens-blocklist",
                "High",
                (".sol",),
                None,
                "docs/rules/BASE-001.md",
            ),
        )
    )
    finding = normalize_finding(raw, chain="base", module=module)
    assert finding == Finding(
        rule_id="BASE-001",
        chain="base",
        severity="high",
        file="pool.sol",
        line=4,
        message="UNION weakens the blocklist",
        doc_url="https://github.com/Simonethg/arcguard/blob/main/docs/rules/BASE-001.md",
    )


def test_scan_all_runs_a_base_module_when_it_is_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def scan_path(path: Path) -> list[_BaseFinding]:
        assert Path(path) == tmp_path
        return [
            _BaseFinding(
                "BASE-OFF-2", "builder-code-suffix-missing", "Low", "app.ts", 2, "no suffix"
            )
        ]

    module = types.ModuleType("arcguard.base")
    module.scan_path = scan_path  # type: ignore[attr-defined]
    module.RULES = ()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "arcguard.base", module)

    findings, notes, ran = scan_chains(tmp_path, "all")
    assert "arc" in ran and "base" in ran
    assert "celo" not in ran
    assert any("arcguard.celo" in note for note in notes)
    base_hits = [item for item in findings if item.chain == "base"]
    assert len(base_hits) == 1
    assert base_hits[0].file == "app.ts"
    assert base_hits[0].severity == "low"
    assert base_hits[0].rule_id == "BASE-OFF-2"


def test_explicit_missing_chain_is_an_error() -> None:
    with pytest.raises(ChainModuleError):
        load_scanner("celo")


def test_cli_missing_chain_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    status = main(["scan", str(tmp_path), "--chain", "celo"])
    assert status == 2
    assert "arcguard.celo" in capsys.readouterr().err


def test_threshold_ignores_lower_severities(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = tmp_path / "send.ts"
    script.write_text("export const tx = { maxFeePerGas: 1_000_000_000n }\n", encoding="utf-8")
    status = main(
        ["scan", str(script), "--chain", "arc", "--threshold", "critical", "--format", "json"]
    )
    assert status == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"][0]["severity"] == "high"
    assert payload["findings"][0]["chain"] == "arc"


def test_low_fee_exits_1_for_default_threshold(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    script = tmp_path / "send.ts"
    script.write_text("export const tx = { gasPrice: 1 }\n", encoding="utf-8")
    status = main(["scan", str(script), "--chain", "arc", "--format", "markdown"])
    assert status == 1
    report = capsys.readouterr().out
    assert "ARC-OFF-1" in report
    assert "does not replace an audit" in report


def test_github_url_parser_rejects_credentials_and_accepts_a_tree() -> None:
    clone, ref, sub = parse_github("https://github.com/Simonethg/scaffold-arc")
    assert clone == "https://github.com/Simonethg/scaffold-arc.git"
    assert ref is None and sub is None
    clone, ref, sub = parse_github(
        "https://github.com/Simonethg/scaffold-arc/tree/main/packages/foundry"
    )
    assert ref == "main"
    assert sub == "packages/foundry"
    clone, ref, sub = parse_github("git@github.com:Simonethg/scaffold-arc.git")
    assert clone == "git@github.com:Simonethg/scaffold-arc.git"
    with pytest.raises(TargetError):
        parse_github("https://user:embedded@github.com/Simonethg/scaffold-arc")


def test_resolve_target_clones_without_using_the_network(tmp_path: Path) -> None:
    cloned: list[tuple[str, str | None]] = []

    def cloner(url: str, ref: str | None, dest: Path) -> None:
        cloned.append((url, ref))
        dest.mkdir(parents=True)
        (dest / "send.ts").write_text("export const tx = { maxFeePerGas: 1n }\n", encoding="utf-8")

    root, cleanup = resolve_target("https://github.com/acme/widgets", cloner=cloner)
    try:
        assert cloned == [("https://github.com/acme/widgets.git", None)]
        assert (root / "send.ts").is_file()
    finally:
        cleanup()
    assert not root.exists()


def test_slither_bridge_skips_when_the_plugin_is_empty(tmp_path: Path) -> None:
    from arcguard.cli.slither_bridge import slither_findings

    findings, notes = slither_findings(tmp_path)
    assert findings == []
    assert notes == []
