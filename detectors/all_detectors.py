"""Slither detector classes for ARC-001..ARC-008.

``slither --detect arc-...`` selects these by ``ARGUMENT``. Each class carries
the rule id, severity, description, recommendation, and the official Arc doc
section. See ``arcguard.rules`` for the URLs.
"""

from __future__ import annotations

from slither.detectors.abstract_detector import DetectorClassification

from arcguard.rules import RULES
from arcguard.slither_base import ArcDetector

_HIGH = DetectorClassification.HIGH
_MEDIUM = DetectorClassification.MEDIUM


class MsgValueVsBalanceOfMix(ArcDetector):
    """ARC-001. Native 18-decimal value mixed with 6-decimal USDC amounts."""

    RULE_ID = RULES["ARC-001"].rule_id
    ARGUMENT = RULES["ARC-001"].argument
    HELP = (
        "ARC-001 (High, Medium if only a msgValue name meets balanceOf): "
        "msg.value or balance mixed with USDC amounts without 1e12"
    )
    IMPACT = _HIGH
    CONFIDENCE = _MEDIUM
    SEVERITY = RULES["ARC-001"].severity
    WIKI = RULES["ARC-001"].primary_doc
    DOCS = RULES["ARC-001"].docs
    WIKI_TITLE = RULES["ARC-001"].title
    WIKI_DESCRIPTION = RULES["ARC-001"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A payable function does `require(msg.value >= priceUsdc)` or "
        "`usdc.transfer(to, msg.value)`. The native side is 10^12 larger than "
        "the ERC-20 side, so the contract accepts or pays the wrong amount of USDC."
    )
    WIKI_RECOMMENDATION = RULES["ARC-001"].recommendation


class UsdcDecimalsHardcoded(ArcDetector):
    """ARC-002. Hardcoded 6-decimal native scale or 18-decimal ERC-20 scale."""

    RULE_ID = RULES["ARC-002"].rule_id
    ARGUMENT = RULES["ARC-002"].argument
    HELP = "ARC-002 (High): hardcoded 6 decimals on native value or 18 on ERC-20 USDC"
    IMPACT = _HIGH
    CONFIDENCE = _MEDIUM
    SEVERITY = RULES["ARC-002"].severity
    WIKI = RULES["ARC-002"].primary_doc
    DOCS = RULES["ARC-002"].docs
    WIKI_TITLE = RULES["ARC-002"].title
    WIKI_DESCRIPTION = RULES["ARC-002"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A port does `msg.value / 1e6` or `erc20Balance * 1e18`, or requires "
        "`usdc.decimals() == 18`. Credits and debits no longer match the USDC "
        "that actually moved."
    )
    WIKI_RECOMMENDATION = RULES["ARC-002"].recommendation


class NativeErc20DualAssetPool(ArcDetector):
    """ARC-003. Pool, LTV, or total that treats both USDC views as two assets."""

    RULE_ID = RULES["ARC-003"].rule_id
    ARGUMENT = RULES["ARC-003"].argument
    HELP = "ARC-003 (High): native USDC and ERC-20 USDC counted as two assets"
    IMPACT = _HIGH
    CONFIDENCE = _MEDIUM
    SEVERITY = RULES["ARC-003"].severity
    WIKI = RULES["ARC-003"].primary_doc
    DOCS = RULES["ARC-003"].docs
    WIKI_TITLE = RULES["ARC-003"].title
    WIKI_DESCRIPTION = RULES["ARC-003"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A pool returns `address(this).balance + usdc.balanceOf(address(this))` "
        "as total assets. Both reads are the same USDC, so LTV and pricing "
        "double-count the balance."
    )
    WIKI_RECOMMENDATION = RULES["ARC-003"].recommendation


class WethPattern(ArcDetector):
    """ARC-004. WETH deposit/withdraw or a wrapped-native constant."""

    RULE_ID = RULES["ARC-004"].rule_id
    ARGUMENT = RULES["ARC-004"].argument
    HELP = "ARC-004 (Medium): WETH deposit/withdraw, wrapper constant, or wrap/unwrap"
    IMPACT = _MEDIUM
    CONFIDENCE = _HIGH
    SEVERITY = RULES["ARC-004"].severity
    WIKI = RULES["ARC-004"].primary_doc
    DOCS = RULES["ARC-004"].docs
    WIKI_TITLE = RULES["ARC-004"].title
    WIKI_DESCRIPTION = RULES["ARC-004"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A router still calls `WETH.deposit{value: msg.value}()` and "
        "`WETH.withdraw`. On Arc that wraps USDC into a second token and "
        "splits liquidity from the canonical ERC-20 interface."
    )
    WIKI_RECOMMENDATION = RULES["ARC-004"].recommendation


class ValueToZeroAddress(ArcDetector):
    """ARC-005. Value-bearing native transfer to the zero address."""

    RULE_ID = RULES["ARC-005"].rule_id
    ARGUMENT = RULES["ARC-005"].argument
    HELP = "ARC-005 (High): native value sent to address(0)"
    IMPACT = _HIGH
    CONFIDENCE = _HIGH
    SEVERITY = RULES["ARC-005"].severity
    WIKI = RULES["ARC-005"].primary_doc
    DOCS = RULES["ARC-005"].docs
    WIKI_TITLE = RULES["ARC-005"].title
    WIKI_DESCRIPTION = RULES["ARC-005"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A burn path does `payable(address(0)).transfer(amount)`. On Arc the "
        "call reverts with 'Zero address not allowed' and the USDC stays put."
    )
    WIKI_RECOMMENDATION = RULES["ARC-005"].recommendation


class UncheckedNativeSend(ArcDetector):
    """ARC-006. Native call, transfer, or send that assumes success."""

    RULE_ID = RULES["ARC-006"].rule_id
    ARGUMENT = RULES["ARC-006"].argument
    HELP = "ARC-006 (Medium): native call/transfer/send assumed to succeed"
    IMPACT = _MEDIUM
    CONFIDENCE = _HIGH
    SEVERITY = RULES["ARC-006"].severity
    WIKI = RULES["ARC-006"].primary_doc
    DOCS = RULES["ARC-006"].docs
    WIKI_TITLE = RULES["ARC-006"].title
    WIKI_DESCRIPTION = RULES["ARC-006"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A forwarder uses `to.transfer(amount)` after checking the balance. "
        "The recipient is blocklisted, the send reverts, and the caller has "
        "no boolean it can handle."
    )
    WIKI_RECOMMENDATION = RULES["ARC-006"].recommendation


class SelfdestructMovesUsdc(ArcDetector):
    """ARC-007. SELFDESTRUCT moves USDC, or value is sent to a destroyed account."""

    RULE_ID = RULES["ARC-007"].rule_id
    ARGUMENT = RULES["ARC-007"].argument
    HELP = "ARC-007 (High): selfdestruct moves USDC or sends value to a destroyed account"
    IMPACT = _HIGH
    CONFIDENCE = _HIGH
    SEVERITY = RULES["ARC-007"].severity
    WIKI = RULES["ARC-007"].primary_doc
    DOCS = RULES["ARC-007"].docs
    WIKI_TITLE = RULES["ARC-007"].title
    WIKI_DESCRIPTION = RULES["ARC-007"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A contract calls `selfdestruct(payable(address(this)))` or "
        "`selfdestruct(payable(address(0)))` while it holds USDC. Arc reverts, "
        "or a selfdestruct to another account moves USDC the way an ERC-20 "
        "balance would not move on Ethereum."
    )
    WIKI_RECOMMENDATION = RULES["ARC-007"].recommendation


class PrevrandaoRandomness(ArcDetector):
    """ARC-008. block.prevrandao or block.difficulty used as randomness."""

    RULE_ID = RULES["ARC-008"].rule_id
    ARGUMENT = RULES["ARC-008"].argument
    HELP = "ARC-008 (High): block.prevrandao or block.difficulty used as randomness"
    IMPACT = _HIGH
    CONFIDENCE = _HIGH
    SEVERITY = RULES["ARC-008"].severity
    WIKI = RULES["ARC-008"].primary_doc
    DOCS = RULES["ARC-008"].docs
    WIKI_TITLE = RULES["ARC-008"].title
    WIKI_DESCRIPTION = RULES["ARC-008"].description
    WIKI_EXPLOIT_SCENARIO = (
        "A lottery sets `winner = block.prevrandao % players.length`. On Arc "
        "prevrandao is 0, so the same player wins every time."
    )
    WIKI_RECOMMENDATION = RULES["ARC-008"].recommendation


DETECTORS: list[type[ArcDetector]] = [
    MsgValueVsBalanceOfMix,
    UsdcDecimalsHardcoded,
    NativeErc20DualAssetPool,
    WethPattern,
    ValueToZeroAddress,
    UncheckedNativeSend,
    SelfdestructMovesUsdc,
    PrevrandaoRandomness,
]
