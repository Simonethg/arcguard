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


def run_slither(path: Path, detect: str) -> list[dict]:
    """Run one ``slither --detect`` invocation and return detector results."""

    completed = subprocess.run(
        ["slither", str(path), "--detect", detect, "--json", "-"],
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
    return payload.get("results", {}).get("detectors", [])


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
