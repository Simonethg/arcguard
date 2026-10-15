"""Positive, negative, and scaffold false-positive tests for ARC-001..ARC-008.

Each case is executed with ``slither --detect arc-...`` so the plugin entry
point is what actually runs. ``Usdc.sol`` and ``UsdcUnits.sol`` are copied
from https://github.com/Simonethg/scaffold-arc (packages/foundry/src) and must
produce zero findings. ``NaiveEthereumPort.sol`` is the known vulnerable port.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from arcguard.rules import RULES

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "detectors"
SCAFFOLD = FIXTURES / "scaffold"
ALL_ARGUMENTS = ",".join(rule.argument for rule in RULES.values())


def _path() -> dict[str, str]:
    env = os.environ.copy()
    local_bin = str(Path.home() / ".local" / "bin")
    if local_bin not in env.get("PATH", "").split(os.pathsep):
        env["PATH"] = local_bin + os.pathsep + env.get("PATH", "")
    return env


_SLITHER_CACHE: dict[tuple[str, str], list[dict]] = {}


def run_slither(path: Path, detect: str) -> list[dict]:
    """Run one ``slither --detect`` invocation and return detector results."""

    key = (str(path), detect)
    cached = _SLITHER_CACHE.get(key)
    if cached is not None:
        return cached
    completed = subprocess.run(
        [
            "slither",
            str(path),
            "--detect",
            detect,
            "--compile-force-framework",
            "solc",
            "--json",
            "-",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=_path(),
    )
    stdout = completed.stdout.strip()
    if not stdout:
        raise AssertionError(completed.stderr[-4000:])
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(completed.stderr[-4000:] or stdout[:1000]) from exc
    if not payload.get("success", False):
        raise AssertionError(payload.get("error") or completed.stderr[-4000:])
    findings = payload.get("results", {}).get("detectors", [])
    _SLITHER_CACHE[key] = findings
    return findings


@pytest.mark.parametrize("rule_id", list(RULES))
def test_positive_case_reports_rule_metadata(rule_id: str) -> None:
    rule = RULES[rule_id]
    filename = rule_id.lower().replace("-", "")
    findings = run_slither(FIXTURES / f"{filename}_positive.sol", rule.argument)
    assert findings, rule.argument
    for finding in findings:
        assert finding["check"] == rule.argument
        assert finding["impact"] == rule.severity
        fields = finding["additional_fields"]
        assert fields["id"] == rule_id
        assert fields["severity"] == rule.severity
        assert fields["recommendation"] == rule.recommendation
        assert rule.primary_doc in fields["docs"]
        assert "docs.arc.io" in fields["docs"] or rule.primary_doc.startswith("https://docs.arc.io")
        assert rule_id in finding["description"]


@pytest.mark.parametrize("rule_id", list(RULES))
def test_negative_case_is_silent(rule_id: str) -> None:
    rule = RULES[rule_id]
    filename = rule_id.lower().replace("-", "")
    findings = run_slither(FIXTURES / f"{filename}_negative.sol", rule.argument)
    assert findings == []


@pytest.mark.parametrize(
    "filename",
    ["Usdc.sol", "UsdcUnits.sol"],
)
def test_scaffold_arc_reference_has_no_false_positives(filename: str) -> None:
    findings = run_slither(SCAFFOLD / filename, ALL_ARGUMENTS)
    assert findings == []


def test_naive_ethereum_port_is_the_vulnerable_reference() -> None:
    findings = run_slither(SCAFFOLD / "NaiveEthereumPort.sol", ALL_ARGUMENTS)
    found = {item["additional_fields"]["id"] for item in findings}
    assert "ARC-001" in found
    assert "ARC-003" in found
    assert found <= {"ARC-001", "ARC-003"}


def test_arc001_call_site_with_real_msg_value_is_high() -> None:
    """A pure helper named msgValue is not enough. The caller passing msg.value is High."""

    findings = run_slither(FIXTURES / "arc001_positive.sol", RULES["ARC-001"].argument)
    call_sites = [
        item
        for item in findings
        if "passes raw msg.value" in item["description"] and item["impact"] == "High"
    ]
    assert call_sites, findings
    element = call_sites[0]["elements"][0]
    mapping = element["source_mapping"]
    assert mapping["filename_short"].endswith("arc001_positive.sol")
    assert mapping["lines"]
    assert "naiveValueCoversErc20" in call_sites[0]["description"]
    assert call_sites[0]["additional_fields"]["severity"] == "High"


def test_arc001_msgvalue_name_mixed_with_balanceof_is_medium() -> None:
    findings = run_slither(FIXTURES / "arc001_name_medium.sol", RULES["ARC-001"].argument)
    assert findings, "expected a Medium ARC-001 hit"
    assert all(item["impact"] == "Medium" for item in findings)
    assert all(item["additional_fields"]["severity"] == "Medium" for item in findings)
    assert all(item["additional_fields"]["id"] == "ARC-001" for item in findings)
    assert any("msgValue" in item["description"] for item in findings)
    assert any("balanceOf" in item["description"] for item in findings)


CORPUS = ROOT / "corpus" / "src"

# file, rule id, impact, line, snippet. Lines come from slither on the corpus
# contracts that landed in PR #5.
CORPUS_HITS = [
    ("vulnerable/NaiveCheckout.sol", "ARC-001", "High", 22, "passes raw msg.value"),
    ("vulnerable/Arc001MsgValueMix.sol", "ARC-001", "High", 25, "does not scale by 1e12"),
    ("vulnerable/Arc002HardcodedDecimals.sol", "ARC-002", "High", 24, "6-decimal unit"),
    ("vulnerable/Arc002HardcodedDecimals.sol", "ARC-002", "High", 29, "10**18"),
    ("vulnerable/Arc003DualAssetPool.sol", "ARC-003", "High", 23, "two assets"),
    ("vulnerable/Arc004WethPattern.sol", "ARC-004", "Medium", 22, "deposit or withdraw"),
    ("vulnerable/Arc005ValueToZero.sol", "ARC-005", "High", 14, "address(0)"),
    ("vulnerable/Arc006UncheckedSend.sol", "ARC-006", "Medium", 16, "lowlevelcall"),
    ("vulnerable/Arc007Selfdestruct.sol", "ARC-007", "High", 18, "SELFDESTRUCT"),
    ("vulnerable/Arc008Prevrandao.sol", "ARC-008", "High", 13, "PREVRANDAO"),
]

CORPUS_SILENT = [
    "fixed/Arc001MsgValueMix.sol",
    "fixed/Arc002HardcodedDecimals.sol",
    "fixed/Arc003DualAssetPool.sol",
    "fixed/Arc004WethPattern.sol",
    "fixed/Arc005ValueToZero.sol",
    "fixed/Arc006UncheckedSend.sol",
    "fixed/Arc007Selfdestruct.sol",
    "fixed/Arc008Prevrandao.sol",
    "fixed/SafeCheckout.sol",
    "lib/UsdcUnits.sol",
]


def _hits(findings: list[dict], rule_id: str) -> list[dict]:
    return [item for item in findings if item["additional_fields"]["id"] == rule_id]


@pytest.mark.parametrize(("relative", "rule_id", "impact", "line", "snippet"), CORPUS_HITS)
def test_corpus_contract_is_flagged(
    relative: str, rule_id: str, impact: str, line: int, snippet: str
) -> None:
    findings = _hits(run_slither(CORPUS / relative, ALL_ARGUMENTS), rule_id)
    matched = []
    for item in findings:
        if item["impact"] != impact or snippet not in item["description"]:
            continue
        for element in item["elements"]:
            mapping = element["source_mapping"]
            if mapping["filename_short"].endswith(Path(relative).name) and line in mapping["lines"]:
                matched.append(item)
    assert matched, findings


@pytest.mark.parametrize("relative", CORPUS_SILENT)
def test_corpus_fixed_reference_is_silent(relative: str) -> None:
    findings = run_slither(CORPUS / relative, ALL_ARGUMENTS)
    assert findings == [], relative


def test_corpus_zero_value_burn_is_not_arc_005() -> None:
    findings = _hits(
        run_slither(CORPUS / "vulnerable/Arc005ValueToZero.sol", ALL_ARGUMENTS),
        "ARC-005",
    )
    lines = {
        line
        for item in findings
        for element in item["elements"]
        for line in element["source_mapping"]["lines"]
    }
    assert lines == {14}


def test_slither_lists_every_arc_detector() -> None:
    completed = subprocess.run(
        ["slither", "--list-detectors"],
        check=False,
        capture_output=True,
        text=True,
        env=_path(),
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    for rule in RULES.values():
        assert rule.argument in completed.stdout
        assert rule.rule_id in completed.stdout
