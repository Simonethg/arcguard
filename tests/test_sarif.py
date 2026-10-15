"""SARIF 2.1.0 output validates against the OASIS schema."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from jsonschema.validators import validator_for

from arcguard.cli.main import main

SCHEMA_PATH = Path(__file__).resolve().parent / "fixtures" / "sarif-schema-2.1.0.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validator() -> jsonschema.Validator:
    """Pick the validator declared by the SARIF schema (JSON Schema draft-04)."""

    validator_cls = validator_for(SCHEMA)
    return validator_cls(SCHEMA, format_checker=validator_cls.FORMAT_CHECKER)


def _validate(document: dict[str, object]) -> None:
    _validator().validate(document)


def test_schema_fixture_is_the_sarif_2_1_0_document() -> None:
    assert SCHEMA["title"].startswith("Static Analysis Results Format (SARIF) Version 2.1.0")
    assert SCHEMA["properties"]["version"]["enum"] == ["2.1.0"]


def test_finding_report_validates(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    script = tmp_path / "send.ts"
    script.write_text(
        'export const tx = { maxFeePerGas: parseUnits("10", "gwei") }\n',
        encoding="utf-8",
    )
    status = main(["scan", str(script), "--chain", "arc", "--format", "sarif"])
    assert status == 1
    document = json.loads(capsys.readouterr().out)
    _validate(document)
    assert document["version"] == "2.1.0"
    run = document["runs"][0]
    result = run["results"][0]
    assert result["ruleId"] == "ARC-OFF-1"
    assert result["level"] == "error"
    assert result["locations"][0]["physicalLocation"]["region"]["startLine"] == 1
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "send.ts"
    rule_ids = [rule["id"] for rule in run["tool"]["driver"]["rules"]]
    assert "ARC-OFF-1" in rule_ids
    assert run["invocations"][0]["executionSuccessful"] is True


def test_clean_report_validates(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    status = main(["scan", str(tmp_path), "--chain", "arc", "--format", "sarif"])
    assert status == 0
    document = json.loads(capsys.readouterr().out)
    _validate(document)
    assert document["runs"][0]["results"] == []
