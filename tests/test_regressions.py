"""Regressions found by scanning public Arc projects (October 2026).

1. A call to another contract's public state-variable getter made the shared
   engine raise ``AttributeError`` (``StateVariable`` has no ``is_implemented``).
2. A detector crash used to end the scan with exit 0 and a single note, which
   CI read as clean. Now the remaining detectors run, the error is reported,
   and the CLI exits 2.
3. ARC-002 read a native-wei reserve named ``realUsdc`` as a 6-decimal ERC-20
   amount because of its name.
4. ARC-OFF-1 reported fee values in tests and mocks.

The fixtures are minimal reproductions written for this repository.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from arcguard.arc.max_fee import is_test_path, scan_path
from arcguard.cli import engine as cli_engine
from arcguard.cli import slither_bridge
from arcguard.cli.main import main
from arcguard.rules import RULES
from test_detectors import ALL_ARGUMENTS, FIXTURES, run_slither

ROOT = Path(__file__).resolve().parents[1]


def _ids(findings: list[dict]) -> set[str]:
    return {item["additional_fields"]["id"] for item in findings}


def _lines(findings: list[dict], rule_id: str) -> set[int]:
    return {
        line
        for item in findings
        if item["additional_fields"]["id"] == rule_id
        for element in item["elements"]
        for line in element["source_mapping"]["lines"]
    }


# 1. Public getter callee -------------------------------------------------------


def test_public_getter_call_does_not_crash_any_detector() -> None:
    # run_slither raises when Slither reports an error, so this asserts no crash.
    findings = run_slither(FIXTURES / "regress_public_getter_call.sol", ALL_ARGUMENTS)
    assert findings == []


def test_callee_destructs_ignores_state_variables() -> None:
    from slither.core.variables.state_variable import StateVariable

    from arcguard import engine

    getter = StateVariable()
    getter.name = "totalSupply"
    assert engine._callee_destructs(getter, set()) is False


# 2. Fail closed -----------------------------------------------------------------


class _Ok:
    ARGUMENT = "arc-ok"

    def detect(self) -> list:
        return []


class _Boom:
    ARGUMENT = "arc-boom"

    def detect(self) -> list:
        raise AttributeError("'StateVariable' object has no attribute 'is_implemented'")


class _AfterBoom:
    ARGUMENT = "arc-after"
    ran = False

    def detect(self) -> list:
        type(self).ran = True
        return []


def test_bridge_keeps_running_after_a_detector_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import slither.slither as slither_module

    class FakeSlither:
        def __init__(self, _target: str) -> None:
            self.detectors = [_Ok(), _Boom(), _AfterBoom()]

        def register_detector(self, _cls: type) -> None:
            return None

    monkeypatch.setattr(slither_bridge, "make_plugin", lambda: ([_Ok, _Boom, _AfterBoom], []))
    monkeypatch.setattr(slither_module, "Slither", FakeSlither)
    findings, notes, errors = slither_bridge.slither_findings(tmp_path)
    assert findings == []
    assert notes == []
    assert len(errors) == 1
    assert "arc-boom" in errors[0]
    assert "AttributeError" in errors[0]
    assert "incomplete" in errors[0]
    assert _AfterBoom.ran, "detectors after the failing one must still run"


@pytest.fixture
def crashed_scan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli_engine,
        "slither_findings",
        lambda _root: ([], [], ["Slither detector arc-boom failed (AttributeError)."]),
    )


@pytest.mark.parametrize("threshold", ["low", "critical"])
def test_cli_exits_2_and_never_says_clean_on_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    crashed_scan: None,
    threshold: str,
) -> None:
    status = main(["scan", str(tmp_path), "--chain", "arc", "--threshold", threshold])
    captured = capsys.readouterr()
    assert status == 2
    assert "No findings" not in captured.out
    assert "Scan incomplete" in captured.out
    assert "arc-boom" in captured.err


def test_error_wins_over_findings_exit_code() -> None:
    from arcguard.finding import Finding

    finding = Finding(
        rule_id="ARC-005",
        chain="arc",
        severity="high",
        file="a.sol",
        line=1,
        message="m",
        doc_url="",
    )
    assert cli_engine.exit_code([finding], "low", ["boom"]) == 2
    assert cli_engine.exit_code([finding], "low", []) == 1
    assert cli_engine.exit_code([], "low", []) == 0


def test_json_sarif_and_markdown_mark_the_scan_incomplete(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], crashed_scan: None
) -> None:
    assert main(["scan", str(tmp_path), "--chain", "arc", "--format", "json"]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["complete"] is False
    assert payload["errors"]

    assert main(["scan", str(tmp_path), "--chain", "arc", "--format", "sarif"]) == 2
    sarif = json.loads(capsys.readouterr().out)
    invocation = sarif["runs"][0]["invocations"][0]
    assert invocation["executionSuccessful"] is False
    levels = {item["level"] for item in invocation["toolExecutionNotifications"]}
    assert "error" in levels

    assert main(["scan", str(tmp_path), "--chain", "arc", "--format", "markdown"]) == 2
    markdown = capsys.readouterr().out
    assert "Scan incomplete" in markdown
    assert "No findings" not in markdown


def _action_engine():
    path = ROOT / "action" / "engine.py"
    spec = importlib.util.spec_from_file_location("arcguard_action_engine_regress", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["arcguard_action_engine_regress"] = module
    spec.loader.exec_module(module)
    return module


def test_action_reads_sarif_errors_and_comment_is_not_clean() -> None:
    action = _action_engine()
    payload = {
        "runs": [
            {
                "results": [],
                "invocations": [
                    {
                        "executionSuccessful": False,
                        "toolExecutionNotifications": [
                            {"level": "error", "message": {"text": "detector arc-boom failed"}},
                            {"level": "note", "message": {"text": "just a note"}},
                        ],
                    }
                ],
            }
        ]
    }
    errors = action.errors_from_sarif(payload)
    assert errors == ["detector arc-boom failed"]
    summary = action.build_markdown([], ".", "arcaudit", "", errors=errors)
    assert "Scan incomplete" in summary
    assert "No findings from the rules this run applied." not in summary
    clean = action.build_markdown([], ".", "arcaudit", "")
    assert "No findings from the rules this run applied." in clean
    succeeded = {"runs": [{"invocations": [{"executionSuccessful": True}]}]}
    assert action.errors_from_sarif(succeeded) == []


def test_action_manifests_fail_on_incomplete_scans() -> None:
    for manifest in (ROOT / "action.yml", ROOT / "action" / "action.yml"):
        text = manifest.read_text(encoding="utf-8")
        assert "incomplete:" in text
        assert 'if [ "${INCOMPLETE}" = "true" ]' in text


# 3. ARC-002 and native reserves named "usdc" ----------------------------------


def test_native_wei_reserve_named_usdc_is_not_arc002() -> None:
    path = FIXTURES / "regress_native_named_usdc.sol"
    findings = run_slither(path, RULES["ARC-002"].argument)
    lines = _lines(findings, "ARC-002")
    source = path.read_text(encoding="utf-8").splitlines()
    price_line = next(i for i, text in enumerate(source, 1) if "* 1e18 / (virtualTokens" in text)
    control_line = next(i for i, text in enumerate(source, 1) if "usdcAmount * 1e18" in text)
    assert price_line not in lines, findings
    assert control_line in lines, "name-only usdc without native value must stay ARC-002"


def test_native_reserve_fixture_has_no_other_rule_hits() -> None:
    findings = run_slither(FIXTURES / "regress_native_named_usdc.sol", ALL_ARGUMENTS)
    assert _ids(findings) <= {"ARC-002"}


# 4. ARC-OFF-1 skips tests and mocks -------------------------------------------


@pytest.mark.parametrize(
    "relative",
    [
        "test/send.ts",
        "apps/api/test/support/fakes.ts",
        "src/features/bridge/bridge.test.ts",
        "src/bridge.spec.tsx",
        "test/Deploy.t.sol",
        "script/Fee.t.sol",
        "src/mocks/rpc.ts",
        "src/__mocks__/viem.ts",
        "packages/sdk/src/mock-sdk.ts",
        "src/MockProvider.ts",
    ],
)
def test_test_and_mock_paths_are_recognized(relative: str) -> None:
    assert is_test_path(relative)


@pytest.mark.parametrize(
    "relative",
    ["src/send.ts", "script/Deploy.s.sol", "scripts/testnet.ts", "src/hammock.ts", "contest/a.ts"],
)
def test_real_paths_are_not_test_paths(relative: str) -> None:
    assert not is_test_path(relative)


def test_arc_off_1_skips_tests_by_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARCGUARD_INCLUDE_TESTS", raising=False)
    low = "export const tx = { maxFeePerGas: 1n }\n"
    (tmp_path / "src").mkdir()
    (tmp_path / "test").mkdir()
    (tmp_path / "src" / "send.ts").write_text(low, encoding="utf-8")
    (tmp_path / "test" / "send.ts").write_text(low, encoding="utf-8")
    (tmp_path / "src" / "send.test.ts").write_text(low, encoding="utf-8")
    (tmp_path / "src" / "MockWallet.ts").write_text(low, encoding="utf-8")

    default = sorted(item.file for item in scan_path(tmp_path))
    assert default == ["src/send.ts"]

    everything = sorted(item.file for item in scan_path(tmp_path, include_tests=True))
    assert everything == ["src/MockWallet.ts", "src/send.test.ts", "src/send.ts", "test/send.ts"]

    # A file passed directly is always scanned.
    assert len(scan_path(tmp_path / "test" / "send.ts")) == 1


def test_cli_include_tests_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("ARCGUARD_INCLUDE_TESTS", raising=False)
    monkeypatch.setattr(cli_engine, "slither_findings", lambda _root: ([], [], []))
    (tmp_path / "test").mkdir()
    (tmp_path / "test" / "send.ts").write_text(
        "export const tx = { maxFeePerGas: 1n }\n", encoding="utf-8"
    )
    assert main(["scan", str(tmp_path), "--chain", "arc"]) == 0
    capsys.readouterr()
    assert main(["scan", str(tmp_path), "--chain", "arc", "--include-tests"]) == 1
    assert "ARC-OFF-1" in capsys.readouterr().out
