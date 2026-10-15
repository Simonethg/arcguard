"""ARC-OFF-1 ``max-fee-below-floor``.

Arc's mempool drops a transaction whose ``maxFeePerGas`` (or legacy
``gasPrice``) is below 20 Gwei. There is no error receipt and the
transaction never appears in a block. Priority fee is not the floor:
``maxPriorityFeePerGas`` may be 0.

Sources:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/references/gas-and-fees
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps

The check is static. A value that is not a literal, a unit expression, or a
``parseGwei`` / ``parseUnits`` / ``parseEther`` call is left alone.
``foundry.toml`` ``gas_price = 0`` is Foundry's unset default (the client
estimates). A literal ``0`` in a TypeScript or JavaScript transaction is an
explicit fee and is reported.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from arcguard.finding import Finding

RULE_ID = "ARC-OFF-1"
RULE_NAME = "max-fee-below-floor"
CHAIN = "arc"
SEVERITY = "high"
DOC_URL = "https://docs.arc.io/arc/references/evm-differences"

# 20 Gwei in wei. Equal to the floor is accepted; only a lower value is flagged.
FLOOR_WEI = Decimal(20) * (Decimal(10) ** 9)

_UNITS = {"wei": 0, "gwei": 9, "ether": 18}

_JS_SUFFIXES = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"}
_SKIP_DIRS = {
    ".git",
    ".next",
    ".venv",
    "artifacts",
    "broadcast",
    "cache",
    "coverage",
    "dist",
    "lib",
    "node_modules",
    "out",
    "typechain-types",
    "venv",
}

# ``_`` is a word character, so ``priority_gas_price`` does not match ``gas_price``.
_FEE_KEY = re.compile(
    r"""(?<!\w)(maxFeePerGas|max_fee_per_gas|gasPrice|gas_price)\??\s*(?:=(?!=)|:)\s*"""
)
_TX_GAS_PRICE = re.compile(r"""(?<!\w)txGasPrice\s*\(""")
_MEMBER_GAS_PRICE = re.compile(r"""\.\s*(gasPrice)\s*=(?!=)\s*""")

# The final "." keeps braces and other punctuation as tokens. Dropping them
# would glue the next expression onto this one and hide a low fee.
_TOKEN = re.compile(
    r"\s+"
    r"|0[xX][0-9a-fA-F_]+n?"
    r"|\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?n?"
    r'|"(?:\\.|[^"\\])*"'
    r"|'(?:\\.|[^'\\])*'"
    r"|`(?:\\.|[^`\\])*`"
    r"|\*\*"
    r"|[A-Za-z_][A-Za-z0-9_]*"
    r"|."
)

_STOP = {",", ";", ")", "}", "]", "\n", None}


class _Value:
    """A coefficient (not yet wei) or an absolute wei amount."""

    __slots__ = ("amount", "wei", "unit")

    def __init__(self, amount: Decimal, *, wei: bool, unit: str | None = None) -> None:
        self.amount = amount
        self.wei = wei
        self.unit = unit


def _mask_comments(text: str, *, hash_comments: bool) -> str:
    """Blank comments. Strings stay so fee literals inside them can be read."""

    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if ch in "\"'`":
            out.append(ch)
            i += 1
            while i < n:
                out.append(text[i])
                if text[i] == "\\":
                    i += 1
                    if i < n:
                        out.append(text[i])
                        i += 1
                    continue
                if text[i] == ch:
                    i += 1
                    break
                i += 1
            continue
        if ch == "/" and nxt == "/":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
            continue
        if ch == "/" and nxt == "*":
            out.append(" ")
            out.append(" ")
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                out.append("\n" if text[i] == "\n" else " ")
                i += 1
            if i < n:
                out.append(" ")
                out.append(" ")
                i += 2
            continue
        if hash_comments and ch == "#":
            while i < n and text[i] != "\n":
                out.append(" ")
                i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _string_spans(text: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] in "\"'`":
            start = i
            quote = text[i]
            i += 1
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == quote:
                    i += 1
                    break
                i += 1
            spans.append((start, i))
            continue
        i += 1
    return spans


def _inside(spans: list[tuple[int, int]], index: int) -> bool:
    return any(start <= index < end for start, end in spans)


def _unquote(token: str) -> str:
    body = token[1:-1]
    return body.replace(r"\'", "'").replace(r"\"", '"').replace(r"\\", "\\")


def _numeric(token: str) -> Decimal:
    raw = token[:-1] if token[-1] in "nN" else token
    raw = raw.replace("_", "")
    if raw[:2].lower() == "0x":
        return Decimal(int(raw, 16))
    return Decimal(raw)


def _is_number(token: str) -> bool:
    return token[0].isdigit() or (token[0] == "0" and len(token) > 1)


def _is_string(token: str) -> bool:
    return token[:1] in "\"'`"


def _string_value(token: str) -> _Value | None:
    text = _unquote(token).strip()
    match = re.fullmatch(
        r"(?i)(0x[0-9a-f]+|\d[\d_]*(?:\.\d+)?(?:e[+-]?\d+)?)(?:\s*(wei|gwei|ether))?",
        text,
    )
    if match is None:
        lowered = text.lower()
        if lowered in _UNITS:
            return _Value(Decimal(0), wei=False, unit=lowered)
        return None
    amount = _numeric(match.group(1))
    unit = match.group(2)
    if unit:
        return _Value(amount * (Decimal(10) ** _UNITS[unit.lower()]), wei=True)
    if match.group(1).lower().startswith("0x"):
        return _Value(amount, wei=True)
    return _Value(amount, wei=False)


class _Parser:
    def __init__(self, text: str) -> None:
        self.tokens = [tok for tok in _TOKEN.findall(text) if tok and not tok[0].isspace()]
        self.i = 0

    def peek(self) -> str | None:
        if self.i >= len(self.tokens):
            return None
        return self.tokens[self.i]

    def advance(self) -> str | None:
        tok = self.peek()
        if tok is not None:
            self.i += 1
        return tok

    def parse_expr(self) -> _Value | None:
        left = self.parse_pow()
        if left is None:
            return None
        while self.peek() == "*":
            self.advance()
            right = self.parse_pow()
            if right is None:
                return None
            left = _mul(left, right)
            if left is None:
                return None
        return left

    def parse_pow(self) -> _Value | None:
        left = self.parse_unary()
        if left is None:
            return None
        if self.peek() == "**":
            self.advance()
            right = self.parse_pow()
            if right is None or left.wei or right.wei or right.unit or left.unit:
                return None
            exponent = right.amount
            if exponent != exponent.to_integral_value() or exponent < 0 or exponent > 24:
                return None
            return _Value(left.amount ** int(exponent), wei=False)
        return left

    def parse_unary(self) -> _Value | None:
        if self.peek() == "-":
            self.advance()
            inner = self.parse_factor()
            if inner is None:
                return None
            return _Value(-inner.amount, wei=inner.wei, unit=inner.unit)
        return self.parse_factor()

    def parse_factor(self) -> _Value | None:
        tok = self.peek()
        if tok is None:
            return None
        if tok == "(":
            self.advance()
            inner = self.parse_expr()
            if inner is None or self.peek() != ")":
                return None
            self.advance()
            return inner
        if _is_string(tok):
            self.advance()
            return _string_value(tok)
        if _is_number(tok):
            self.advance()
            amount = _numeric(tok)
            wei = tok.lower().startswith("0x")
            unit = self.peek()
            if unit in _UNITS and self._unit_not_call():
                self.advance()
                return _Value(amount * (Decimal(10) ** _UNITS[unit]), wei=True)
            return _Value(amount, wei=wei)
        if tok[:1].isalpha() or tok[:1] == "_":
            name = self._dotted_name()
            if name is None:
                return None
            if self.peek() == "(":
                return self._call(name)
            return None
        return None

    def _unit_not_call(self) -> bool:
        # ``1 gwei`` is a unit. ``1 gwei(`` is not a pattern we understand.
        nxt = self.tokens[self.i + 1] if self.i + 1 < len(self.tokens) else None
        return nxt != "("

    def _dotted_name(self) -> str | None:
        parts: list[str] = []
        tok = self.advance()
        if tok is None:
            return None
        parts.append(tok)
        while self.peek() == ".":
            self.advance()
            nxt = self.peek()
            if nxt is None or not (nxt[:1].isalpha() or nxt[:1] == "_"):
                return None
            parts.append(self.advance() or "")
        return ".".join(parts)

    def _call(self, name: str) -> _Value | None:
        if self.advance() != "(":
            return None
        args: list[_Value | None] = []
        if self.peek() != ")":
            while True:
                args.append(self.parse_expr())
                if self.peek() == ",":
                    self.advance()
                    continue
                break
        if self.peek() != ")":
            return None
        self.advance()
        if any(arg is None for arg in args):
            return None
        leaf = name.split(".")[-1]
        parsed = [arg for arg in args if arg is not None]
        return _eval_call(leaf, parsed)


def _mul(left: _Value, right: _Value) -> _Value | None:
    if left.unit or right.unit:
        return None
    return _Value(left.amount * right.amount, wei=left.wei or right.wei)


def _as_coeff(value: _Value) -> Decimal | None:
    if value.unit or value.wei:
        return None
    return value.amount


def _eval_call(leaf: str, args: list[_Value]) -> _Value | None:
    if leaf == "parseGwei" and args:
        coeff = _as_coeff(args[0])
        if coeff is None:
            return None
        return _Value(coeff * (Decimal(10) ** 9), wei=True)
    if leaf == "parseEther" and args:
        coeff = _as_coeff(args[0])
        if coeff is None:
            return None
        return _Value(coeff * (Decimal(10) ** 18), wei=True)
    if leaf == "parseUnits" and len(args) >= 2:
        coeff = _as_coeff(args[0])
        if coeff is None:
            return None
        unit = args[1].unit
        if unit is None:
            if args[1].wei or args[1].amount != args[1].amount.to_integral_value():
                return None
            decimals = int(args[1].amount)
            if not 0 <= decimals <= 18:
                return None
            return _Value(coeff * (Decimal(10) ** decimals), wei=True)
        return _Value(coeff * (Decimal(10) ** _UNITS[unit]), wei=True)
    if leaf == "BigInt" and args:
        coeff = _as_coeff(args[0])
        if coeff is None:
            return None
        return _Value(coeff, wei=False)
    return None


def _wei_from(text: str) -> Decimal | None:
    parser = _Parser(text)
    value = parser.parse_expr()
    if value is None or value.unit:
        return None
    nxt = parser.peek()
    if nxt not in _STOP:
        return None
    if value.wei:
        return value.amount
    return value.amount


def _gwei_text(wei: Decimal) -> str:
    gwei = wei / (Decimal(10) ** 9)
    rendered = format(gwei, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _message(field: str, wei: Decimal) -> str:
    return (
        f"{field} is {_gwei_text(wei)} Gwei, below Arc's 20 Gwei floor. "
        "The mempool drops the transaction with no receipt and it never appears in a block. "
        "Set maxFeePerGas or gasPrice to at least 20 Gwei. "
        "maxPriorityFeePerGas may stay 0. "
        "Sources: EVM differences, porting contracts to Arc, and the Arc compatibility guide."
    )


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _consider(
    findings: list[Finding],
    seen: set[tuple[str, int, str]],
    *,
    text: str,
    index: int,
    field: str,
    wei: Decimal | None,
    file: str,
    skip_zero: bool,
) -> None:
    if wei is None or wei >= FLOOR_WEI:
        return
    if skip_zero and wei == 0:
        return
    line = _line_of(text, index)
    key = (file, line, field)
    if key in seen:
        return
    seen.add(key)
    findings.append(
        Finding(
            rule_id=RULE_ID,
            chain=CHAIN,
            severity=SEVERITY,
            file=file,
            line=line,
            message=_message(field, wei),
            doc_url=DOC_URL,
        )
    )


def scan_text(text: str, file: str = "<memory>") -> list[Finding]:
    """Scan one source buffer. ``file`` is the path reported on each finding."""

    suffix = Path(file).suffix.lower()
    name = Path(file).name
    if name == "foundry.toml":
        mode = "toml"
    elif suffix == ".sol":
        mode = "sol"
    elif suffix in _JS_SUFFIXES or name.startswith("hardhat.config."):
        mode = "js"
    else:
        return []

    masked = _mask_comments(text, hash_comments=mode == "toml")
    spans = _string_spans(masked)
    findings: list[Finding] = []
    seen: set[tuple[str, int, str]] = set()
    script = name.endswith(".s.sol") or "/script/" in Path(file).as_posix()

    patterns: list[re.Pattern[str]] = []
    if mode in {"js", "toml"} or script:
        patterns.append(_FEE_KEY)
    if mode == "sol":
        patterns.append(_TX_GAS_PRICE)
        patterns.append(_MEMBER_GAS_PRICE)

    for pattern in patterns:
        for match in pattern.finditer(masked):
            if _inside(spans, match.start()):
                continue
            field = match.group(1) if match.lastindex else "txGasPrice"
            if pattern is _TX_GAS_PRICE:
                field = "txGasPrice"
            skip_zero = mode == "toml" and field == "gas_price"
            wei = _wei_from(masked[match.end() : match.end() + 400])
            _consider(
                findings,
                seen,
                text=masked,
                index=match.start(),
                field=field,
                wei=wei,
                file=file,
                skip_zero=skip_zero,
            )
    return findings


def _interesting(path: Path) -> bool:
    name = path.name
    if name == "foundry.toml" or name.startswith("hardhat.config."):
        return True
    return path.suffix.lower() in _JS_SUFFIXES or path.suffix.lower() == ".sol"


def scan_path(root: str | Path) -> list[Finding]:
    """Scan a file or directory for ARC-OFF-1.

    The signature is ``scan_path(path)`` so the chain registry can call it
    the same way it calls ``arcguard.base.scan_path``.
    """

    root_path = Path(root)
    if root_path.is_file():
        files = [root_path]
        base = root_path.parent
    else:
        files = sorted(path for path in root_path.rglob("*") if path.is_file())
        base = root_path

    findings: list[Finding] = []
    for path in files:
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if not _interesting(path):
            continue
        try:
            if path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        try:
            reported = path.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            reported = path.as_posix()
        findings.extend(scan_text(text, reported))
    return findings
