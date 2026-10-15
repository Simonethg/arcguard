"""Rule metadata for ARC-001..ARC-008.

The wording of every rule follows the public Arc docs. Cite these pages from
detector output instead of paraphrasing a new rule:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps

Arc testnet only. These detectors do not certify a contract and do not replace
an audit.
"""

from __future__ import annotations

from dataclasses import dataclass

EVM_DIFFERENCES = "https://docs.arc.io/arc/references/evm-differences"
PORTING = "https://docs.arc.io/arc/tutorials/porting-contracts-to-arc"
COMPAT_GUIDE = "https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps"

VALUE_TRANSFER = EVM_DIFFERENCES + "#value-transfer-rules"
NATIVE_GAS = EVM_DIFFERENCES + "#usdc-as-the-native-gas-token"
OPCODES = EVM_DIFFERENCES + "#execution-and-opcode-differences"
SELFDESTRUCT = EVM_DIFFERENCES + "#selfdestruct"

# Canonical ERC-20 interface for native USDC on Arc (6 decimals). The native
# balance and msg.value use 18 decimals over the same asset.
USDC_ERC20_ADDRESS = int("3600000000000000000000000000000000000000", 16)
SCALE_1E12 = 10**12
FACTOR_1E6 = 10**6
FACTOR_1E18 = 10**18


@dataclass(frozen=True)
class Rule:
    """One Arc detector: id, Slither argument, severity, and the doc links."""

    rule_id: str
    argument: str
    severity: str
    title: str
    description: str
    recommendation: str
    primary_doc: str

    @property
    def docs(self) -> str:
        """Space-separated official URLs. Slither additional fields are strings."""

        links = [self.primary_doc, PORTING, COMPAT_GUIDE]
        unique: list[str] = []
        for link in links:
            if link not in unique:
                unique.append(link)
        return " ".join(unique)


RULES: dict[str, Rule] = {
    "ARC-001": Rule(
        rule_id="ARC-001",
        argument="arc-msg-value-vs-balanceof-mix",
        severity="High",
        title="Native value mixed with ERC-20 USDC amounts",
        description=(
            "msg.value and address.balance use 18 decimals. USDC balanceOf and "
            "transfer amounts use 6 decimals. Comparing, adding, or subtracting "
            "them without scaling by 1e12 is off by 10^12. A call that passes "
            "raw msg.value into that mix is the same bug. A parameter named like "
            "msgValue mixed only with balanceOf is reported at Medium."
        ),
        recommendation=(
            "Scale with UsdcUnits.SCALE (1e12) or Usdc.nativeCoversErc20 before "
            "comparing or moving value. Do not pass raw msg.value as an ERC-20 amount."
        ),
        primary_doc=VALUE_TRANSFER,
    ),
    "ARC-002": Rule(
        rule_id="ARC-002",
        argument="arc-usdc-decimals-hardcoded",
        severity="High",
        title="Hardcoded USDC decimals on the wrong representation",
        description=(
            "Native USDC has 18 decimals and the ERC-20 interface has 6. "
            "Dividing or comparing native value by 1e6, multiplying an ERC-20 "
            "amount by 1e18, transferring 10**18 as an ERC-20 amount, or treating "
            "USDC decimals() as 18 applies the wrong scale."
        ),
        recommendation=(
            "Keep 6 for ERC-20 amounts and 18 for native amounts. Convert with "
            "10 ** (18 - 6), which is 1e12, or with 10 ** (18 - usdc.decimals()). "
            "Do not assume decimals() is 18."
        ),
        primary_doc=NATIVE_GAS,
    ),
    "ARC-003": Rule(
        rule_id="ARC-003",
        argument="arc-native-erc20-dual-asset-pool",
        severity="High",
        title="Native USDC and ERC-20 USDC treated as two assets",
        description=(
            "Native USDC and the ERC-20 interface are one balance. Adding them, "
            "or storing both as reserves, double-counts the same USDC in a pool, "
            "LTV, or oracle."
        ),
        recommendation=(
            "Account for the balance once. If both views are read, scale one "
            "into the other with 1e12 before combining them."
        ),
        primary_doc=VALUE_TRANSFER,
    ),
    "ARC-004": Rule(
        rule_id="ARC-004",
        argument="arc-weth-pattern",
        severity="Medium",
        title="WETH deposit, withdraw, or wrapper constant",
        description=(
            "Arc has no WETH-style wrapper. deposit()/withdraw() and WETH or "
            "WUSDC constants wrap an asset that is already USDC."
        ),
        recommendation=(
            "Delete the wrapper. Use the ERC-20 USDC interface at "
            "0x3600000000000000000000000000000000000000, or native value, "
            "and scale if a path mixes both."
        ),
        primary_doc=PORTING,
    ),
    "ARC-005": Rule(
        rule_id="ARC-005",
        argument="arc-value-to-zero-address",
        severity="High",
        title="Native value sent to the zero address",
        description=(
            "A value-bearing native transfer to address(0) reverts with "
            "'Zero address not allowed'. A zero-value transfer is allowed. "
            "Burns go through the native-coin precompile, not a send to 0x0."
        ),
        recommendation=(
            "Do not send native USDC to address(0). Reject the zero address "
            "before a value transfer, and burn only through the precompile."
        ),
        primary_doc=VALUE_TRANSFER,
    ),
    "ARC-006": Rule(
        rule_id="ARC-006",
        argument="arc-unchecked-native-send",
        severity="Medium",
        title="Native send assumed to succeed",
        description=(
            "call{value:}, transfer, and send can revert even when the balance "
            "is enough: the blocklist, a burn, or address(0) all reject native "
            "USDC. Ignoring the boolean, or using transfer, assumes the "
            "Ethereum success model."
        ),
        recommendation=(
            "Use call{value:} and require the returned boolean. A balance "
            "check does not prove the send will succeed."
        ),
        primary_doc=VALUE_TRANSFER,
    ),
    "ARC-007": Rule(
        rule_id="ARC-007",
        argument="arc-selfdestruct-moves-usdc",
        severity="High",
        title="SELFDESTRUCT moves the contract USDC",
        description=(
            "On Arc, SELFDESTRUCT transfers the contract's native USDC to the "
            "beneficiary. It reverts when the beneficiary is the contract "
            "itself or address(0) and the balance is non-zero. A later "
            "non-zero send to an account destroyed in the same transaction "
            "also reverts."
        ),
        recommendation=(
            "Do not use selfdestruct to move or burn USDC. Transfer to an "
            "explicit recipient and do not send value to an account destroyed "
            "in the same transaction."
        ),
        primary_doc=SELFDESTRUCT,
    ),
    "ARC-008": Rule(
        rule_id="ARC-008",
        argument="arc-prevrandao-randomness",
        severity="High",
        title="PREVRANDAO or difficulty used as randomness",
        description=(
            "Arc PREVRANDAO is always 0. block.difficulty is the same opcode "
            "after Paris, so lottery, shuffle, or relay logic that reads it "
            "always receives 0."
        ),
        recommendation=(
            "Replace block.prevrandao and block.difficulty with a VRF or a "
            "randomness oracle. Do not use them as a seed."
        ),
        primary_doc=OPCODES,
    ),
}
