"""Heuristic Base rules. Sources are listed per rule in docs/rules/."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

SOL = (".sol",)
OFFCHAIN = (".ts", ".tsx", ".js", ".mjs", ".cjs")


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


def _call_args(text: str, open_paren: int) -> str:
    depth = 0
    for i in range(open_paren, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1 : i]
    return text[open_paren + 1 :]


# BASE-001 -------------------------------------------------------------------
_UNION = re.compile(r"\bUNION\b|,\s*2\s*,")
_BLOCKY = re.compile(r"sanction|blocklist|blocked|denylist|deny|ofac", re.I)


def check_union_weakens_blocklist(text: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"createCompositePolicy\s*\(", text):
        args = _call_args(text, m.end() - 1)
        # Children are often built a few lines above the call; look back a short window.
        context = text[max(0, m.start() - 600) : m.start()] + args
        if _UNION.search(args) and _BLOCKY.search(context):
            out.append(
                (
                    _line(text, m.start()),
                    "UNION (OR) composite includes a blocklist/sanctions child: any other "
                    "child can authorize a blocked account. Use INTERSECT (AND).",
                )
            )
    return out


# BASE-002 -------------------------------------------------------------------
def check_policy_id_unchecked(text: str) -> list[tuple[int, str]]:
    if "policyExists" in text:
        return []
    out = []
    pattern = (
        r"""\b(updatePolicy|updateComposite)\s*\("""
        r"""|functionName\s*:\s*['"](updatePolicy|updateComposite)['"]"""
    )
    for m in re.finditer(pattern, text):
        name = m.group(1) or m.group(2)
        out.append(
            (
                _line(text, m.start()),
                f"{name} binds a policy ID without a policyExists() check in this file. "
                "A never-created INTERSECT ID authorizes everyone (ALWAYS_ALLOW behavior).",
            )
        )
    return out


# BASE-003 -------------------------------------------------------------------
_FUNC = re.compile(r"function\s+(\w+)\s*\(([^)]*)\)([^{;]*)\{", re.S)
_GUARD = re.compile(r"\bonly\w+|hasRole\s*\(|_checkRole|msg\.sender\s*==")


def _body(text: str, brace: int) -> str:
    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[brace : i + 1]
    return text[brace:]


def check_seize_unguarded(text: str) -> list[tuple[int, str]]:
    out = []
    for m in _FUNC.finditer(text):
        header = m.group(3)
        if not re.search(r"\b(public|external)\b", header):
            continue
        body = _body(text, m.end() - 1)
        if "seizeWithMemo" not in body and "SEIZE_ROLE" not in body:
            continue
        if _GUARD.search(header) or _GUARD.search(body):
            continue
        out.append(
            (
                _line(text, m.start()),
                f"public/external `{m.group(1)}` reaches seizeWithMemo or SEIZE_ROLE without an "
                "access check. Seize skips allowance and transfer policies.",
            )
        )
    for m in re.finditer(r"seizeWithMemo\s*\(", text):
        args = _call_args(text, m.end() - 1)
        if re.search(r"bytes32\s*\(\s*0\s*\)\s*$", args.strip()):
            out.append(
                (
                    _line(text, m.start()),
                    "seizeWithMemo with an empty memo (bytes32(0)): allowed, but the onchain "
                    "record loses the reason for the seizure.",
                )
            )
    return out


# BASE-004 -------------------------------------------------------------------
def check_validity_zero_storage(text: str) -> list[tuple[int, str]]:
    out = []
    for m in re.finditer(r"""type['"]?\s*:\s*['"]storage['"]""", text):
        window = text[m.start() : m.start() + 400]
        end = window.find("}", window.find("params"))
        window = window[: end if end > 0 else len(window)]
        if re.search(r"""op['"]?\s*:\s*['"]=['"]""", window) and re.search(
            r"""value['"]?\s*:\s*['"]0x0*['"]""", window
        ):
            out.append(
                (
                    _line(text, m.start()),
                    "Validity storage predicate waits for a zero slot. Docs: a zero slot does "
                    "not make a CREATE2 address, proxy, or uninitialized contract safe; keep "
                    "the critical check in the call itself.",
                )
            )
    for m in re.finditer(r"""type['"]?\s*:\s*['"]flashblock_index['"]""", text):
        ctx = text[max(0, m.start() - 300) : m.start() + 300]
        if re.search(r"random|lottery|raffle|winner|seed", ctx, re.I):
            out.append(
                (
                    _line(text, m.start()),
                    "Transaction placement (flashblock_index) used near randomness logic. "
                    "Docs: do not use placement as a source of randomness.",
                )
            )
    return out


# BASE-005 -------------------------------------------------------------------
_BLOCK_DURATION = re.compile(
    r"block\.number\s*[+-]\s*\w+|\w+\s*[+-]\s*block\.number|block\.number\s*[<>]=?\s*\w+\s*[+-]"
)


def check_block_count_duration(text: str) -> list[tuple[int, str]]:
    return [
        (
            _line(text, m.start()),
            "Duration measured in blocks. Denim moves Base to 200ms blocks: block.number "
            "advances 10x faster and this window shrinks to 1/10. Use block.timestamp.",
        )
        for m in _BLOCK_DURATION.finditer(text)
    ]


# BASE-OFF-1 -----------------------------------------------------------------
_FLASH = re.compile(
    r"""newFlashblocks|newFlashblockTransactions|pendingLogs|blockTag\s*:\s*['"]pending['"]|"""
    r"""['"]pending['"]\s*\)"""
)


def check_flashblocks_dependency(text: str) -> list[tuple[int, str]]:
    return [
        (
            _line(text, m.start()),
            f"`{m.group(0).strip()}` depends on Flashblocks / pending state, which Denim "
            "removes. Use canonical newHeads/logs/latest.",
        )
        for m in _FLASH.finditer(text)
    ]


# BASE-OFF-2 -----------------------------------------------------------------
_WRITE = re.compile(r"\b(writeContract|sendTransaction|sendCalls|useWriteContract|useSendCalls)\b")
_ON_BASE = re.compile(
    r"""import\s*\{[^}]*\bbase(Sepolia)?\b[^}]*\}\s*from\s*['"]viem/chains['"]"""
    r"""|chain\s*:\s*base(Sepolia)?\b|chainId\s*:\s*(8453|84532)\b"""
)


def check_builder_code_missing(text: str) -> list[tuple[int, str]]:
    if not _ON_BASE.search(text) or re.search(r"dataSuffix|toDataSuffix|erc8021", text):
        return []
    m = _WRITE.search(text)
    if not m:
        return []
    return [
        (
            _line(text, m.start()),
            "Writes on Base without an ERC-8021 dataSuffix (Builder Code). Not a safety "
            "bug: activity is not attributed and the app is ineligible for Builder "
            "Code-based programs.",
        )
    ]


RULES: tuple[Rule, ...] = (
    Rule("BASE-001", "b20-union-weakens-blocklist", "High", SOL + OFFCHAIN,
         check_union_weakens_blocklist, "docs/rules/BASE-001.md"),
    Rule("BASE-002", "b20-policy-id-unchecked", "Medium", SOL + OFFCHAIN,
         check_policy_id_unchecked, "docs/rules/BASE-002.md"),
    Rule("BASE-003", "b20-seize-unguarded", "High", SOL, check_seize_unguarded,
         "docs/rules/BASE-003.md"),
    Rule("BASE-004", "validity-predicate-unsafe", "Medium", OFFCHAIN + (".json",),
         check_validity_zero_storage, "docs/rules/BASE-004.md"),
    Rule("BASE-005", "block-count-duration", "High", SOL, check_block_count_duration,
         "docs/rules/BASE-005.md"),
    Rule("BASE-OFF-1", "flashblocks-pending-dependency", "Medium", OFFCHAIN,
         check_flashblocks_dependency, "docs/rules/BASE-OFF-1.md"),
    Rule("BASE-OFF-2", "builder-code-suffix-missing", "Low", OFFCHAIN,
         check_builder_code_missing, "docs/rules/BASE-OFF-2.md"),
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
