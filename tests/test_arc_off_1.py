"""ARC-OFF-1: fees below 20 Gwei are flagged; the floor and other fields are not."""

from __future__ import annotations

from pathlib import Path

import pytest

from arcguard.arc import scan_path, scan_text
from arcguard.arc.max_fee import RULE_ID

FLOOR_OK = [
    "export const tx = { maxFeePerGas: 20_000_000_000n }\n",
    'export const tx = { maxFeePerGas: parseGwei("20") }\n',
    'export const tx = { maxFeePerGas: parseGwei("40") }\n',
    'export const tx = { maxFeePerGas: ethers.parseUnits("20", "gwei") }\n',
    'export const tx = { maxFeePerGas: ethers.utils.parseUnits("20", "gwei") }\n',
    'export const tx = { maxFeePerGas: parseUnits("20", 9) }\n',
    "export const tx = { maxFeePerGas: 0x4a817c800n }\n",
    "export const tx = { maxFeePerGas: 2e10 }\n",
    "export const tx = { maxFeePerGas: 20n * 10n ** 9n }\n",
    "export const tx = { maxPriorityFeePerGas: 0n }\n",
    'export const tx = { maxPriorityFeePerGas: parseGwei("1") }\n',
    "export const tx = { gasLimit: 21000 }\n",
    'export const tx = { gasPrice: "auto" }\n',
    "const baseFee = block.baseFeePerGas\n",
    "// maxFeePerGas: 1\n/* gasPrice: 1 */\n",
    'const note = "maxFeePerGas: 1"\n',
]

FLOOR_BAD = [
    ("export const tx = { maxFeePerGas: 1_000_000_000n }\n", "maxFeePerGas"),
    (
        'await signer.sendTransaction({ gasPrice: ethers.utils.parseUnits("5", "gwei") })\n',
        "gasPrice",
    ),
    ('export const tx = { maxFeePerGas: parseGwei("19") }\n', "maxFeePerGas"),
    ('export const tx = { maxFeePerGas: "0x3b9aca00" }\n', "maxFeePerGas"),
    ("export const tx = { maxFeePerGas: 10n * 10n ** 9n }\n", "maxFeePerGas"),
    ("export const tx = { maxFeePerGas: 0n }\n", "maxFeePerGas"),
    ('export const tx = { gasPrice: parseUnits("1", "gwei") }\n', "gasPrice"),
    ('maxFeePerGas:\n  parseGwei("1"),\n', "maxFeePerGas"),
    ('export const tx = { maxFeePerGas: parseEther("0.00000001") }\n', "maxFeePerGas"),
    ("export const tx = { maxFeePerGas: 1 }\n", "maxFeePerGas"),
]


@pytest.mark.parametrize("source", FLOOR_OK)
def test_floor_and_unrelated_fields_are_clean(source: str) -> None:
    assert scan_text(source, "send.ts") == []


@pytest.mark.parametrize(("source", "field"), FLOOR_BAD)
def test_below_floor_is_flagged(source: str, field: str) -> None:
    findings = scan_text(source, "send.ts")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.rule_id == RULE_ID
    assert finding.chain == "arc"
    assert finding.severity == "high"
    assert finding.file == "send.ts"
    assert finding.line >= 1
    assert field in finding.message
    assert finding.doc_url == "https://docs.arc.io/arc/references/evm-differences"
    assert "20 Gwei" in finding.message


def test_foundry_toml_zero_is_unset_and_low_value_is_flagged() -> None:
    assert scan_text("gas_price = 0\npriority_gas_price = 1\n", "foundry.toml") == []
    assert scan_text("gas_price = 20000000000\n", "foundry.toml") == []
    findings = scan_text("[profile.ci]\ngas_price = 1000000000\n", "foundry.toml")
    assert [item.line for item in findings] == [2]
    assert findings[0].rule_id == RULE_ID


def test_hardhat_and_foundry_script(tmp_path: Path) -> None:
    hardhat = tmp_path / "hardhat.config.js"
    hardhat.write_text(
        "module.exports = { networks: { arc: { gasPrice: 2_000_000_000, chainId: 5042002 } } }\n",
        encoding="utf-8",
    )
    script = tmp_path / "Deploy.s.sol"
    script.write_text(
        "contract S { function run() external { vm.txGasPrice(1 gwei); } }\n", encoding="utf-8"
    )
    clean = tmp_path / "Safe.s.sol"
    clean.write_text(
        "contract S { function run() external { vm.txGasPrice(20 gwei); } }\n", encoding="utf-8"
    )
    ids = {(item.file, item.rule_id) for item in scan_path(tmp_path)}
    assert ids == {("hardhat.config.js", RULE_ID), ("Deploy.s.sol", RULE_ID)}


def test_contract_gas_price_state_is_not_a_transaction_fee() -> None:
    source = "contract C { uint256 gasPrice = 1 gwei; }\n"
    assert scan_text(source, "C.sol") == []


def test_member_assignment_in_a_contract_is_flagged() -> None:
    source = "contract C { function f() external { tx.gasPrice = 1 gwei; } }\n"
    findings = scan_text(source, "C.sol")
    assert len(findings) == 1
    assert findings[0].line == 1
