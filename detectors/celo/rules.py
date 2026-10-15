# ruff: noqa: E501  (long address tables and regexes)
"""Heuristic Celo rules. Sources are listed per rule in docs/rules/celo/."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

SOL = (".sol",)
OFFCHAIN = (".ts", ".tsx", ".js", ".mjs", ".cjs")

# Addresses from https://docs.celo.org/build/tools/contracts/fee-currencies (mainnet + Celo Sepolia).
# Non-18-decimal tokens are allowlisted for gas through an adapter with a different address.
TOKEN_TO_ADAPTER = {
    # mainnet
    "0xceba9300f2b948710d2653dd7b07f33a8b32118c": "0x2f25deb3848c207fc8e0c34035b3ba7fc157602b",  # USDC
    "0x48065fbbe25f71c9282ddf5e1cd6d6a887483d5e": "0x0e2a3e05bc9a16f5292a6170456a710cb89c6f72",  # USDT
    "0xd2ab3c9a02dbbab236bfec45d1d755df4267f771": "0x0357ee22278c922e1d36cfe6b899269b161880c4",  # USAT
    # Celo Sepolia
    "0x01c5c0122039549ad1493b8220cabedd739bc44e": "0xbf1441ea57f43f35f713431001f35742c88071c7",  # USDC
    "0xd077a400968890eacc75cdc901f0356c943e4fdb": "0xe19447b12cb0d0220b2a501d8382be2f61ccf92a",  # USDT
}
SIX_DEC_TOKENS = set(TOKEN_TO_ADAPTER)
ADAPTERS = set(TOKEN_TO_ADAPTER.values())
CELO_TOKEN = "0x471ece3750da237f93b8e339c536989b8978a438"  # GoldToken (CELO ERC-20 view)


@dataclass(frozen=True)
class Finding:
    rule_id: str
    slug: str
    severity: str
    path: str
    line: int
    message: str


@dataclass(frozen=True)
class Rule:
    rule_id: str
    slug: str
    severity: str
    extensions: tuple[str, ...]
    check: Callable[[str], list[tuple[int, str]]]
    doc: str


def _line(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _strip_comments(text: str) -> str:
    """Blank out // and /* */ comments, keeping offsets and line numbers."""

    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return re.sub(r"//[^\n]*|/\*.*?\*/", blank, text, flags=re.S)


_ASSIGN = re.compile(
    r"""\b([A-Za-z_$][\w$]*)\s*(?::\s*[^=;\n]+)?=\s*(?:address\()?["']?(0x[0-9a-fA-F]{40})"""
)


def _aliases(text: str, targets: set[str]) -> set[str]:
    """Identifiers assigned one of the target addresses in this file."""
    return {m.group(1) for m in _ASSIGN.finditer(text) if m.group(2).lower() in targets}


def _mentions(expr: str, targets: set[str], names: set[str]) -> bool:
    low = expr.lower()
    if any(t in low for t in targets):
        return True
    return any(re.search(rf"(?<![\w$]){re.escape(n)}(?![\w$])", expr) for n in names)


# CELO-001 -------------------------------------------------------------------
_SIX_NAME = re.compile(r"usdc|usdt|usd₮|usa₮|usat\b|usdt0", re.I)
_EIGHTEEN = re.compile(
    r"parseUnits\s*\([^()\n]*(?:\([^()\n]*\)[^()\n]*)*,\s*18\s*\)|parseEther\s*\(|\b1e18\b|10\s*\*\*\s*18|formatEther\s*\("
    r"|formatUnits\s*\([^()\n]*,\s*18\s*\)|\bether\b"
)


def check_usdc_wrong_decimals(text: str) -> list[tuple[int, str]]:
    names = _aliases(text, SIX_DEC_TOKENS)
    out = []
    for i, line in enumerate(text.splitlines(), 1):
        if not _EIGHTEEN.search(line):
            continue
        if _SIX_NAME.search(line) or _mentions(line, SIX_DEC_TOKENS, names):
            out.append(
                (
                    i,
                    "18-decimal scaling applied to USDC/USDT/USA₮, which use 6 decimals on Celo "
                    "(off by 10^12). Use parseUnits(x, 6) or read decimals() from the token.",
                )
            )
    return out


# CELO-002 -------------------------------------------------------------------
_FEE = re.compile(r"""feeCurrency["']?\s*[:=]\s*([^,}\n;]+)""")


def check_feecurrency_token_not_adapter(text: str) -> list[tuple[int, str]]:
    names = _aliases(text, SIX_DEC_TOKENS)
    out = []
    for m in _FEE.finditer(text):
        if _mentions(m.group(1), SIX_DEC_TOKENS, names):
            out.append(
                (
                    _line(text, m.start()),
                    "feeCurrency points at the USDC/USDT/USA₮ token address. Non-18-decimal tokens "
                    "pay gas through their adapter address (see FeeCurrencyDirectory).",
                )
            )
    return out


# CELO-003 -------------------------------------------------------------------
_MOVE = re.compile(r"""\b(transfer|transferFrom|approve)\b""")


def check_adapter_used_for_transfer(text: str) -> list[tuple[int, str]]:
    names = _aliases(text, ADAPTERS)
    if not names and not any(a in text.lower() for a in ADAPTERS):
        return []
    out = []
    seen: set[int] = set()
    for m in _MOVE.finditer(text):
        window = text[max(0, m.start() - 250) : m.end() + 250]
        # Ignore the alias definitions themselves; only usages near the call count.
        window = _ASSIGN.sub("", window)
        if _mentions(window, ADAPTERS, names):
            ln = _line(text, m.start())
            if ln in seen:
                continue
            seen.add(ln)
            out.append(
                (
                    ln,
                    f"`{m.group(1)}` near a fee-currency adapter address. Adapters are only for the "
                    "feeCurrency field; transfers and approvals must use the token address.",
                )
            )
    return out


# CELO-006 -------------------------------------------------------------------
_WALLET = re.compile(r"isMetaMask|metaMask\s*\(|MetaMask|window\.ethereum|injected\s*\(")
_HONOR_CHECK = re.compile(
    r"isMiniPay|feeCurrency\s*(?:!==?|===?)|receipt\.feeCurrency|getTransaction\s*\("
)


def check_feecurrency_assumed_honored(text: str) -> list[tuple[int, str]]:
    if "feeCurrency" not in text or not _WALLET.search(text) or _HONOR_CHECK.search(text):
        return []
    m = re.search(r"feeCurrency", text)
    assert m
    return [
        (
            _line(text, m.start()),
            "feeCurrency is set for a transaction signed by an injected wallet (MetaMask drops the "
            "field and charges CELO; MiniPay may replace it). Detect the wallet and do not assume "
            "the chosen fee currency was used.",
        )
    ]


# CELO-008 -------------------------------------------------------------------
_TRANSFER_EVT = re.compile(
    r"""eventName\s*:\s*["']Transfer["']|["']Transfer\(address,address,uint256\)["']|\.Transfer\s*\("""
)
_NATIVE_TRACK = re.compile(r"getBalance\s*\(|\btx\.value\b|transaction\.value|traces?|debug_trace")


def check_celo_native_erc20_duality(text: str) -> list[tuple[int, str]]:
    names = _aliases(text, {CELO_TOKEN})
    if not _mentions(text, {CELO_TOKEN}, names) or _NATIVE_TRACK.search(text):
        return []
    return [
        (
            _line(text, m.start()),
            "Tracks CELO only through ERC-20 Transfer events. CELO also moves as native value "
            "(no Transfer event); both views are the same balance. Also track native transfers.",
        )
        for m in _TRANSFER_EVT.finditer(text)
    ]


# CELO-009 -------------------------------------------------------------------
_DOUBLE = re.compile(
    r"\.balance\s*\+\s*[^;]*\bbalanceOf\s*\(|\bbalanceOf\s*\([^;]*\)\s*\+\s*[^;]*\.balance\b"
)


def check_double_count(text: str) -> list[tuple[int, str]]:
    return [
        (
            _line(text, m.start()),
            "Adds a native balance and an ERC-20 balanceOf. On Celo, address.balance and "
            "GoldToken.balanceOf are the same CELO; summing them double counts.",
        )
        for m in _DOUBLE.finditer(text)
    ]


# CELO-010 -------------------------------------------------------------------
_BLOCKTIME = re.compile(
    r"\b\w*(?:BLOCK_?TIME|SECONDS_?PER_?BLOCK|blockTime|secondsPerBlock)\w*\s*(?::\s*\w+\s*)?=\s*(5|12)(?:n|_?000)?\b"
    r"|\b(17_?280|7_?200|6_?307_?200|2_?628_?000|518_?400|216_?000)\b",
    re.I,
)


def check_block_time_assumption(text: str) -> list[tuple[int, str]]:
    return [
        (
            _line(text, m.start()),
            "Block-time constant from Celo L1 (5 s) or Ethereum (12 s). Celo L2 produces 1 s "
            "blocks: block-count timelocks/vesting will run 5-12x faster. Prefer timestamps.",
        )
        for m in _BLOCKTIME.finditer(text)
    ]


# CELO-011 -------------------------------------------------------------------
_PRECOMPILE = re.compile(
    r"address\s*\(\s*0xff\s*-\s*(\d+)\s*\)"
    r"|\b0x0{38}(f[0-9a-c]|e[0-9a-f])\b"
    r"|\b(fractionMulExp|getEpochSize|numberValidatorsInSet|validatorSignerAddressFromSet"
    r"|validatorSignerAddressFromCurrentSet|getVerifiedSealBitmapFromHeader|getParentSealBitmap"
    r"|checkProofOfPossession|getBlockNumberFromHeader|hashHeader|minQuorumSize)\s*\(",
    re.I,
)


def check_removed_precompiles(text: str) -> list[tuple[int, str]]:
    out = []
    for m in _PRECOMPILE.finditer(text):
        if m.group(1) == "2":  # 0xff - 2 = 0xfd, the transfer precompile, still exists
            continue
        out.append(
            (
                _line(text, m.start()),
                "Uses a Celo L1 precompile. All Celo precompiles were removed in the L2 migration "
                "except the transfer precompile (0xfd).",
            )
        )
    return out


# CELO-012 -------------------------------------------------------------------
_RANDOM = re.compile(
    r"\bIRandom\b|getAddressFor\w*\s*\(\s*[^)]*[\"']Random[\"']|\b(revealAndCommit|getBlockRandomness)\s*\("
    r"|\bRANDOM_REGISTRY_ID\b"
)


def check_random_contract(text: str) -> list[tuple[int, str]]:
    return [
        (
            _line(text, m.start()),
            "Uses the Celo `Random` contract, which was deactivated with the L2 migration. "
            "Use block.prevrandao (and remember it is not secure randomness either).",
        )
        for m in _RANDOM.finditer(text)
    ]


# CELO-013 -------------------------------------------------------------------
_TYPE = re.compile(r"""\btype\s*:\s*["']?(0x7c|124|cip42|legacy|0x0|0)\b["']?""")


def check_deprecated_tx_types(text: str) -> list[tuple[int, str]]:
    out = []
    for m in _TYPE.finditer(text):
        val = m.group(1)
        window = text[max(0, m.start() - 300) : m.end() + 300]
        if val in {"0x7c", "124", "cip42"} or "feeCurrency" in window:
            out.append(
                (
                    _line(text, m.start()),
                    f"Transaction type `{val}` is deprecated on Celo (type 124, or type 0 with "
                    "feeCurrency). Use CIP-64 (type 123, `cip64` in viem) for fee abstraction.",
                )
            )
    return out


RULES: tuple[Rule, ...] = (
    Rule("CELO-001", "usdc-wrong-decimals", "Critical", SOL + OFFCHAIN,
         check_usdc_wrong_decimals, "docs/rules/celo/CELO-001.md"),
    Rule("CELO-002", "feecurrency-token-not-adapter", "High", OFFCHAIN,
         check_feecurrency_token_not_adapter, "docs/rules/celo/CELO-002.md"),
    Rule("CELO-003", "adapter-used-for-transfer", "High", SOL + OFFCHAIN,
         check_adapter_used_for_transfer, "docs/rules/celo/CELO-003.md"),
    Rule("CELO-006", "feecurrency-assumed-honored", "High", OFFCHAIN,
         check_feecurrency_assumed_honored, "docs/rules/celo/CELO-006.md"),
    Rule("CELO-008", "celo-native-erc20-duality", "High", OFFCHAIN,
         check_celo_native_erc20_duality, "docs/rules/celo/CELO-008.md"),
    Rule("CELO-009", "msgvalue-plus-erc20-double-count", "High", SOL,
         check_double_count, "docs/rules/celo/CELO-009.md"),
    Rule("CELO-010", "block-time-assumption", "Medium", SOL + OFFCHAIN,
         check_block_time_assumption, "docs/rules/celo/CELO-010.md"),
    Rule("CELO-011", "removed-precompiles", "High", SOL,
         check_removed_precompiles, "docs/rules/celo/CELO-011.md"),
    Rule("CELO-012", "random-contract", "High", SOL + OFFCHAIN,
         check_random_contract, "docs/rules/celo/CELO-012.md"),
    Rule("CELO-013", "deprecated-tx-types", "Medium", OFFCHAIN,
         check_deprecated_tx_types, "docs/rules/celo/CELO-013.md"),
)  # fmt: skip


def scan_text(text: str, path: str = "<memory>", rules: Iterable[Rule] = RULES) -> list[Finding]:
    clean = _strip_comments(text)
    suffix = Path(path).suffix
    findings = []
    for rule in rules:
        if path != "<memory>" and suffix not in rule.extensions:
            continue
        for line, message in rule.check(clean):
            findings.append(Finding(rule.rule_id, rule.slug, rule.severity, path, line, message))
    return findings


def scan_path(root: str | Path, rules: Iterable[Rule] = RULES) -> list[Finding]:
    root = Path(root)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.is_file())
    findings: list[Finding] = []
    for f in files:
        if any(part in {"node_modules", ".git", "lib", "cache"} for part in f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text(text, str(f), rules))
    return findings
