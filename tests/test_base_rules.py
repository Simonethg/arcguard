"""Base rules: every vulnerable corpus file is flagged by its rule; every fixed file is not."""

from __future__ import annotations

from pathlib import Path

import pytest

from arcguard.base import RULES, scan_path, scan_text
from arcguard.plugin import make_plugin

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "corpus" / "base"
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
def test_every_rule_has_a_doc_page_with_official_base_sources(rule) -> None:
    page = ROOT / rule.doc
    text = page.read_text(encoding="utf-8")
    assert text.startswith(f"# {rule.rule_id} `{rule.slug}`")
    assert "## Fuentes / Sources" in text
    links = [line for line in text.splitlines() if "](https://" in line]
    assert links
    assert all("https://docs.base.org/" in line for line in links)


def test_comments_do_not_trigger_findings() -> None:
    assert scan_text("// newFlashblocks\n/* block.number + 10 */", "x.ts") == []


def test_seize_with_hasrole_guard_is_clean() -> None:
    src = """
    contract C { IB20 t;
      function f(address h) external {
        require(hasRole(SEIZE, msg.sender));
        t.seizeWithMemo(h, a, 1, bytes32("r"));
      }
    }"""
    assert [f for f in scan_text(src, "c.sol") if f.rule_id == "BASE-003"] == []


def test_base_rules_are_not_advertised_through_slither_yet() -> None:
    assert make_plugin() == ([], [])


def test_findings_use_the_shared_format() -> None:
    from arcguard.finding import Finding

    hits = scan_path(_file("BASE-001", "vulnerable"))
    assert hits and all(isinstance(f, Finding) for f in hits)
    f = hits[0]
    assert (f.chain, f.severity) == ("base", "high")
    assert f.doc_url == "https://github.com/Simonethg/arcguard/blob/main/docs/rules/BASE-001.md"


def test_cli_scan_chain_base_reports_corpus(capsys: pytest.CaptureFixture[str]) -> None:
    import json

    from arcguard.cli.main import main

    status = main(["scan", str(CORPUS), "--chain", "base", "--format", "json"])
    assert status == 1
    report = json.loads(capsys.readouterr().out)
    text = json.dumps(report)
    for rule_id in RULE_IDS:
        assert rule_id in text
    assert "/fixed." not in text


def test_cli_scan_chain_base_clean_on_fixed_files(capsys: pytest.CaptureFixture[str]) -> None:
    from arcguard.cli.main import main

    for rule_id in RULE_IDS:
        assert main(["scan", str(_file(rule_id, "fixed")), "--chain", "base"]) == 0
    capsys.readouterr()
