"""Celo rules: every vulnerable corpus file is flagged by its rule; every fixed file is not."""

from __future__ import annotations

from pathlib import Path

import pytest

from arcguard.celo import RULES, scan_path, scan_text
from arcguard.cli.main import main
from arcguard.finding import Finding
from arcguard.plugin import make_plugin
from arcguard.registry import scan_chains

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "celo"
RULE_IDS = [r.rule_id for r in RULES]


def _file(rule_id: str, kind: str) -> Path:
    matches = sorted((CORPUS / rule_id).glob(f"{kind}.*"))
    assert len(matches) == 1, f"expected one {kind} file for {rule_id}"
    return matches[0]


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_vulnerable_example_is_flagged(rule_id: str) -> None:
    ids = {f.rule_id for f in scan_path(_file(rule_id, "vulnerable"))}
    assert rule_id in ids


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_fixed_example_is_clean(rule_id: str) -> None:
    assert scan_path(_file(rule_id, "fixed")) == []


@pytest.mark.parametrize("rule", RULES, ids=RULE_IDS)
def test_every_rule_has_a_bilingual_doc_with_official_celo_sources(rule) -> None:
    text = (ROOT / rule.doc).read_text(encoding="utf-8")
    assert text.startswith(f"# {rule.rule_id} `{rule.slug}`")
    assert "## Español" in text and "## English" in text
    assert "## Fuentes / Sources" in text
    links = [line for line in text.splitlines() if "](https://" in line]
    assert links
    assert all("https://docs.celo.org/" in line for line in links)


def test_comments_do_not_trigger_findings() -> None:
    src = "// parseUnits(usdc, 18)\n/* BLOCK_TIME = 5; IRandom */"
    assert scan_text(src, "x.ts") == []


def test_transfer_precompile_is_still_allowed() -> None:
    assert scan_text("address constant T = address(0xff - 2);", "c.sol") == []


def test_usdm_with_18_decimals_is_not_flagged() -> None:
    assert scan_text("const amt = parseUnits(x, 18); // USDm", "a.ts") == []


def test_celo_rules_are_not_slither_detectors() -> None:
    assert make_plugin() == ([], [])


def test_findings_use_the_shared_format() -> None:
    hits = scan_path(_file("CELO-001", "vulnerable"))
    assert hits and all(isinstance(f, Finding) for f in hits)
    hit = hits[0]
    assert hit.chain == "celo"
    assert hit.severity == "critical"
    assert hit.doc_url.endswith("docs/rules/celo/CELO-001.md")


@pytest.mark.parametrize("chain", ["celo", "all"])
def test_registry_runs_celo(chain: str) -> None:
    findings, _notes, ran = scan_chains(CORPUS / "CELO-002", chain)
    assert "celo" in ran
    hits = [f for f in findings if f.chain == "celo"]
    assert [(f.rule_id, f.file) for f in hits] == [("CELO-002", "vulnerable.ts")]


def test_cli_scan_chain_celo_reports_and_fails(capsys: pytest.CaptureFixture[str]) -> None:
    status = main(["scan", str(CORPUS / "CELO-010"), "--chain", "celo"])
    assert status == 1
    assert "CELO-010" in capsys.readouterr().out


def test_cli_scan_chain_celo_clean_fixture(tmp_path: Path) -> None:
    (tmp_path / "fixed.sol").write_text(
        _file("CELO-010", "fixed").read_text(encoding="utf-8"), encoding="utf-8"
    )
    assert main(["scan", str(tmp_path), "--chain", "celo"]) == 0
