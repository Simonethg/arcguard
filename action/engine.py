"""Text rules and SARIF/Markdown reports for the ArcGuard action.

Official sources for every rule in this module:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps

These checks run only when ``arcaudit scan`` does not emit SARIF yet.
They are heuristics over source text, not the Slither plugin, and they do
not certify that a contract is safe.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

EVM_DIFFERENCES = "https://docs.arc.io/arc/references/evm-differences"
PORTING = "https://docs.arc.io/arc/tutorials/porting-contracts-to-arc"
COMPAT_GUIDE = "https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps"
TOOL_URI = "https://github.com/Simonethg/arcguard"
DISCLAIMER = "ArcGuard does not certify security and does not replace an audit. Arc testnet only."
DISCLAIMER_ES = "ArcGuard no certifica seguridad y no reemplaza una auditoría. Solo Arc testnet."

# 20 Gwei, in wei. Arc drops a transaction whose max fee is below this floor.
FEE_FLOOR_WEI = 20 * 10**9

SEVERITY_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3}
SARIF_LEVEL = {"info": "note", "low": "note", "medium": "warning", "high": "error"}
SECURITY_SEVERITY = {"info": "1.0", "low": "3.0", "medium": "5.0", "high": "8.0"}

CODE_SUFFIXES = {".sol", ".ts", ".tsx", ".js", ".mjs", ".cjs", ".toml"}
SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".arcguard-test",
    "cache",
    "artifacts",
    "broadcast",
    "out",
    "coverage",
}


@dataclass(frozen=True)
class Rule:
    """Static metadata for one Arc rule."""

    rule_id: str
    slug: str
    severity: str
    short_en: str
    message_en: str
    message_es: str
    help_uri: str


@dataclass(frozen=True)
class Finding:
    """One location that matched a rule."""

    rule: Rule
    path: str
    line: int


RULES: dict[str, Rule] = {
    "ARC-001": Rule(
        rule_id="ARC-001",
        slug="msg-value-vs-balanceof-mix",
        severity="high",
        short_en="Native value mixed with ERC-20 USDC amounts without scaling.",
        message_en=(
            "This function uses msg.value or address.balance together with an ERC-20 "
            "balanceOf or transfer and no 18-to-6 scale factor. On Arc those units differ "
            "by 1e12."
        ),
        message_es=(
            "Esta función usa msg.value o address.balance junto con balanceOf o transfer "
            "del ERC-20 y no escala entre 18 y 6 decimales. En Arc esas unidades difieren "
            "por 1e12."
        ),
        help_uri=EVM_DIFFERENCES,
    ),
    "ARC-004": Rule(
        rule_id="ARC-004",
        slug="weth-pattern",
        severity="medium",
        short_en="WETH wrap or unwrap copied from Ethereum.",
        message_en=(
            "WETH deposit, withdraw, or a WETH constant assumes native ETH wrapped into "
            "another ERC-20. On Arc the native asset is already USDC."
        ),
        message_es=(
            "deposit, withdraw o una constante WETH asumen ETH nativo envuelto en otro "
            "ERC-20. En Arc el activo nativo ya es USDC."
        ),
        help_uri=PORTING,
    ),
    "ARC-005": Rule(
        rule_id="ARC-005",
        slug="value-to-zero-address",
        severity="high",
        short_en="Native value sent to the zero address.",
        message_en=(
            "Native value is sent to address(0). On Arc that transfer reverts because the "
            "zero address is not allowed, so an Ethereum-style native burn does not burn."
        ),
        message_es=(
            "Se envía valor nativo a address(0). En Arc esa transferencia revierte porque "
            "la dirección cero no está permitida: un burn nativo al estilo Ethereum no quema."
        ),
        help_uri=EVM_DIFFERENCES,
    ),
    "ARC-006": Rule(
        rule_id="ARC-006",
        slug="unchecked-native-send",
        severity="medium",
        short_en="Native send whose success is not checked.",
        message_en=(
            "A native call{value:} or send ignores its success flag. On Arc a native "
            "transfer can revert even when the balance is enough, for example because of "
            "a blocklist."
        ),
        message_es=(
            "Un call{value:} o send nativo ignora el indicador de éxito. En Arc una "
            "transferencia nativa puede revertir aunque haya saldo, por ejemplo por una "
            "blocklist."
        ),
        help_uri=EVM_DIFFERENCES,
    ),
    "ARC-007": Rule(
        rule_id="ARC-007",
        slug="selfdestruct-moves-usdc",
        severity="high",
        short_en="selfdestruct moves the contract USDC instead of burning it.",
        message_en=(
            "selfdestruct does not burn the contract's USDC on Arc. It moves that balance "
            "to the beneficiary."
        ),
        message_es=(
            "selfdestruct no quema el USDC del contrato en Arc. Mueve ese saldo al beneficiario."
        ),
        help_uri=EVM_DIFFERENCES,
    ),
    "ARC-008": Rule(
        rule_id="ARC-008",
        slug="prevrandao-randomness",
        severity="high",
        short_en="block.prevrandao or block.difficulty used as randomness.",
        message_en=(
            "block.prevrandao and block.difficulty are not entropy on Arc. The value is 0, "
            "so a draw or a branch that depends on it is fixed."
        ),
        message_es=(
            "block.prevrandao y block.difficulty no son entropía en Arc. El valor es 0, "
            "así que un sorteo o una rama que dependa de ese campo queda fijo."
        ),
        help_uri=EVM_DIFFERENCES,
    ),
    "ARC-OFF-1": Rule(
        rule_id="ARC-OFF-1",
        slug="max-fee-below-floor",
        severity="high",
        short_en="maxFeePerGas is below the 20 Gwei floor.",
        message_en=(
            "maxFeePerGas is below 20 Gwei. Arc silently drops that transaction. Set the "
            "cap to at least 20 Gwei on Arc testnet."
        ),
        message_es=(
            "maxFeePerGas está por debajo de 20 Gwei. Arc descarta esa transacción en "
            "silencio. El tope tiene que ser de al menos 20 Gwei en Arc testnet."
        ),
        help_uri=EVM_DIFFERENCES,
    ),
}


def mask_non_code(source: str) -> str:
    """Replace comments and string contents with spaces, preserving newlines."""

    chars = list(source)
    index = 0
    limit = len(chars)
    while index < limit:
        current = chars[index]
        nxt = chars[index + 1] if index + 1 < limit else ""
        if current == "/" and nxt == "/":
            chars[index] = " "
            chars[index + 1] = " "
            index += 2
            while index < limit and chars[index] != "\n":
                chars[index] = " "
                index += 1
            continue
        if current == "/" and nxt == "*":
            chars[index] = " "
            chars[index + 1] = " "
            index += 2
            while index < limit - 1 and not (chars[index] == "*" and chars[index + 1] == "/"):
                if chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < limit - 1:
                chars[index] = " "
                chars[index + 1] = " "
                index += 2
            continue
        if current in {'"', "'"}:
            quote = current
            chars[index] = " "
            index += 1
            while index < limit and chars[index] != quote:
                if chars[index] == "\\" and index + 1 < limit:
                    if chars[index] != "\n":
                        chars[index] = " "
                    index += 1
                    if chars[index] != "\n":
                        chars[index] = " "
                    index += 1
                    continue
                if chars[index] != "\n":
                    chars[index] = " "
                index += 1
            if index < limit:
                chars[index] = " "
                index += 1
            continue
        index += 1
    return "".join(chars)


def line_of(source: str, index: int) -> int:
    """Return the 1-based line number for a character index."""

    return source.count("\n", 0, index) + 1


def _function_spans(masked: str) -> list[tuple[int, str]]:
    matches = list(re.finditer(r"^\s*function\b", masked, flags=re.MULTILINE))
    if not matches:
        return [(0, masked)]
    spans: list[tuple[int, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(masked)
        spans.append((start, masked[start:end]))
    return spans


def _add(findings: list[Finding], rule_id: str, path: str, line: int) -> None:
    findings.append(Finding(rule=RULES[rule_id], path=path, line=line))


def _has_native_value(chunk: str) -> bool:
    if re.search(r"\bmsg\.value\b", chunk):
        return True
    return re.search(r"\.balance\b", chunk) is not None


def _has_erc20_amount(chunk: str) -> bool:
    return "balanceOf" in chunk or ".transfer(" in chunk


def _is_scaled(chunk: str) -> bool:
    if re.search(r"(?<![0-9A-Za-z_])1e12\b", chunk):
        return True
    if re.search(r"10\s*\*\*\s*12", chunk):
        return True
    if "1_000_000_000_000" in chunk:
        return True
    return re.search(r"\b(?:NATIVE_PER_TOKEN|USDC_SCALE)\b", chunk) is not None


def _scan_mix(masked: str, path: str, findings: list[Finding]) -> None:
    for start, chunk in _function_spans(masked):
        if not (_has_native_value(chunk) and _has_erc20_amount(chunk) and not _is_scaled(chunk)):
            continue
        marker = "msg.value" if "msg.value" in chunk else ".balance"
        local = chunk.find(marker)
        _add(findings, "ARC-001", path, line_of(masked, start + max(local, 0)))
        return


def _scan_weth(masked: str, path: str, findings: list[Finding]) -> None:
    patterns = (
        re.compile(r"\b(?:WETH9|IWETH|WETH)\b"),
        re.compile(r"\.\s*deposit\s*\{[^}]*\bvalue\b"),
    )
    seen: set[int] = set()
    for pattern in patterns:
        match = pattern.search(masked)
        if match is None:
            continue
        line = line_of(masked, match.start())
        if line in seen:
            continue
        seen.add(line)
        _add(findings, "ARC-004", path, line)
        return


def _scan_zero_value(masked: str, path: str, findings: list[Finding]) -> None:
    direct = re.compile(
        r"payable\s*\(\s*address\s*\(\s*0\s*\)\s*\)\s*\.\s*"
        r"(?:call\s*\{[^}]*\bvalue\b|send\s*\()"
        r"|address\s*\(\s*0\s*\)\s*\.\s*(?:call\s*\{[^}]*\bvalue\b|send\s*\()"
    )
    assign = re.compile(
        r"\b([A-Za-z_]\w*)\s*=\s*payable\s*\(\s*address\s*\(\s*0\s*\)\s*\)"
        r"|\b([A-Za-z_]\w*)\s*=\s*address\s*\(\s*0\s*\)"
    )
    match = direct.search(masked)
    if match is not None:
        _add(findings, "ARC-005", path, line_of(masked, match.start()))
        return
    names = {item for group in assign.findall(masked) for item in group if item}
    for name in sorted(names):
        use = re.compile(rf"\b{re.escape(name)}\s*\.\s*(?:call\s*\{{[^}}]*\bvalue\b|send\s*\()")
        used = use.search(masked)
        if used is not None:
            _add(findings, "ARC-005", path, line_of(masked, used.start()))
            return


def _checked(window: str, name: str | None) -> bool:
    if not name:
        return False
    pattern = re.compile(
        rf"require\s*\(\s*{re.escape(name)}\b"
        rf"|assert\s*\(\s*{re.escape(name)}\b"
        rf"|if\s*\(\s*!\s*{re.escape(name)}\b"
        rf"|if\s*\(\s*{re.escape(name)}\b"
    )
    return pattern.search(window) is not None


def _scan_unchecked(masked: str, path: str, findings: list[Finding]) -> None:
    call = re.compile(
        r"(?:\(\s*bool\s+([A-Za-z_]\w*)\s*(?:,[^)]*)?\)\s*=\s*)?"
        r"[A-Za-z_]\w*\s*\.\s*call\s*\{([^}]*)\}"
    )
    send = re.compile(
        r"(?:\(\s*bool\s+([A-Za-z_]\w*)\s*(?:,[^)]*)?\)\s*=\s*)?"
        r"[A-Za-z_]\w*\s*\.\s*send\s*\("
    )
    for base, chunk in _function_spans(masked):
        for pattern in (call, send):
            for match in pattern.finditer(chunk):
                if pattern is call and "value" not in match.group(2):
                    continue
                window = chunk[match.end() : match.end() + 500]
                if _checked(window, match.group(1)):
                    continue
                _add(findings, "ARC-006", path, line_of(masked, base + match.start()))
                return


def _scan_selfdestruct(masked: str, path: str, findings: list[Finding]) -> None:
    match = re.search(r"\bselfdestruct\s*\(", masked)
    if match is not None:
        _add(findings, "ARC-007", path, line_of(masked, match.start()))


def _scan_prevrandao(masked: str, path: str, findings: list[Finding]) -> None:
    match = re.search(r"\bblock\s*\.\s*(?:prevrandao|difficulty)\b", masked)
    if match is not None:
        _add(findings, "ARC-008", path, line_of(masked, match.start()))


def _parse_wei(literal: str) -> int | None:
    text = literal.replace("_", "")
    if text.endswith("n"):
        text = text[:-1]
    if re.fullmatch(r"[0-9]+", text):
        return int(text)
    scientific = re.fullmatch(r"([0-9]+)e([0-9]+)", text)
    if scientific is None:
        return None
    return int(scientific.group(1)) * 10 ** int(scientific.group(2))


def _scan_fee(masked: str, path: str, findings: list[Finding]) -> None:
    pattern = re.compile(
        r"\b(maxFeePerGas|max_fee_per_gas)\b\s*[:=]\s*([0-9][0-9_]*(?:e[0-9]+)?n?)"
    )
    for match in pattern.finditer(masked):
        value = _parse_wei(match.group(2))
        if value is None or value >= FEE_FLOOR_WEI:
            continue
        _add(findings, "ARC-OFF-1", path, line_of(masked, match.start()))
        return


def scan_source(source: str, path: str) -> list[Finding]:
    """Return findings for one source file. ``path`` is the report path."""

    suffix = Path(path).suffix.lower()
    if suffix not in CODE_SUFFIXES and Path(path).name != "foundry.toml":
        return []
    masked = mask_non_code(source)
    findings: list[Finding] = []
    if suffix == ".sol":
        _scan_mix(masked, path, findings)
        _scan_weth(masked, path, findings)
        _scan_zero_value(masked, path, findings)
        _scan_unchecked(masked, path, findings)
        _scan_selfdestruct(masked, path, findings)
        _scan_prevrandao(masked, path, findings)
    if suffix in {".ts", ".tsx", ".js", ".mjs", ".cjs", ".toml"} or path.endswith("foundry.toml"):
        _scan_fee(masked, path, findings)
    return findings


def _relative(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _ignored(relative: str, ignore: list[str], target_relative: str) -> bool:
    if target_relative == relative or relative.startswith(target_relative.rstrip("/") + "/"):
        # The caller pointed the scan at this tree. Honor that over the ignore list.
        if target_relative not in {"", "."}:
            return False
    for item in ignore:
        cleaned = item.strip().strip("/")
        if not cleaned:
            continue
        if target_relative == cleaned or target_relative.startswith(cleaned + "/"):
            continue
        if relative == cleaned or relative.startswith(cleaned + "/"):
            return True
    return False


def iter_sources(target: Path, workspace: Path, ignore: list[str]) -> list[Path]:
    """List source files under ``target`` that the text rules understand."""

    target_relative = _relative(target, workspace) if target.exists() else ""
    if target.is_file():
        relative = _relative(target, workspace)
        if _ignored(relative, ignore, target_relative):
            return []
        return [target]
    found: list[Path] = []
    for directory, dirnames, filenames in os.walk(target):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        for name in sorted(filenames):
            file_path = Path(directory) / name
            if file_path.suffix.lower() not in CODE_SUFFIXES and name != "foundry.toml":
                continue
            relative = _relative(file_path, workspace)
            if _ignored(relative, ignore, target_relative):
                continue
            found.append(file_path)
    return found


def scan_tree(target: Path, workspace: Path, ignore: list[str] | None = None) -> list[Finding]:
    """Scan Solidity and off-chain config files under ``target``."""

    findings: list[Finding] = []
    for file_path in iter_sources(target, workspace, ignore or []):
        if file_path.stat().st_size > 1_000_000:
            continue
        source = file_path.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_source(source, _relative(file_path, workspace)))
    return findings


def should_fail(findings: list[Finding], fail_on: str) -> bool:
    """Return whether ``fail_on`` is met by any finding."""

    if fail_on == "none":
        return False
    if fail_on not in SEVERITY_RANK:
        raise ValueError(f"unsupported fail-on value: {fail_on}")
    threshold = SEVERITY_RANK[fail_on]
    return any(SEVERITY_RANK[item.rule.severity] >= threshold for item in findings)


def _fingerprint(finding: Finding) -> str:
    payload = f"{finding.rule.rule_id}|{finding.path}|{finding.line}|{finding.rule.slug}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def build_sarif(findings: list[Finding], version: str, engine: str, cli_note: str) -> dict:
    """Build a SARIF 2.1.0 document GitHub Code Scanning can ingest."""

    rules = []
    for rule in RULES.values():
        rules.append(
            {
                "id": rule.rule_id,
                "name": rule.slug,
                "shortDescription": {"text": rule.short_en},
                "fullDescription": {"text": rule.message_en},
                "helpUri": rule.help_uri,
                "defaultConfiguration": {"level": SARIF_LEVEL[rule.severity]},
                "properties": {
                    "security-severity": SECURITY_SEVERITY[rule.severity],
                    "tags": ["security", "arc", rule.slug],
                },
            }
        )
    results = []
    for finding in findings:
        text = f"{finding.rule.message_en} {finding.rule.message_es}"
        results.append(
            {
                "ruleId": finding.rule.rule_id,
                "level": SARIF_LEVEL[finding.rule.severity],
                "message": {"text": text},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": finding.path},
                            "region": {"startLine": finding.line},
                        }
                    }
                ],
                "partialFingerprints": {"primaryLocationLineHash": _fingerprint(finding)},
            }
        )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ArcGuard",
                        "version": version,
                        "informationUri": TOOL_URI,
                        "rules": rules,
                    }
                },
                "results": results,
                "properties": {
                    "arcguardEngine": engine,
                    "arcguardCliNote": cli_note[:500],
                    "sources": [EVM_DIFFERENCES, PORTING, COMPAT_GUIDE],
                },
            }
        ],
    }


def summary_marker(scanned_path: str) -> str:
    """HTML marker used to update an existing pull-request comment."""

    safe = scanned_path.replace('"', "").replace("\n", " ")
    return f'<!-- arcguard-summary path="{safe}" -->'


def _counts(findings: list[Finding]) -> dict[str, int]:
    counts = {name: 0 for name in SEVERITY_RANK}
    for finding in findings:
        counts[finding.rule.severity] += 1
    return counts


def build_markdown(
    findings: list[Finding],
    scanned_path: str,
    engine: str,
    cli_note: str,
) -> str:
    """Bilingual pull-request summary. Severity is written with words."""

    counts = _counts(findings)
    lines = [
        summary_marker(scanned_path),
        "",
        "## ArcGuard",
        "",
        DISCLAIMER_ES,
        "",
        DISCLAIMER,
        "",
        f"**Ruta / Path:** `{scanned_path}`",
        f"**Motor / Engine:** `{engine}`",
        (
            "**Hallazgos / Findings:** "
            f"{len(findings)} "
            f"(high: {counts['high']}, medium: {counts['medium']}, "
            f"low: {counts['low']}, info: {counts['info']})"
        ),
        "",
    ]
    if engine == "text-rules":
        lines.extend(
            [
                "`arcaudit scan` se ejecutó. Esta versión del CLI todavía no emite SARIF, "
                "así que la Action aplicó reglas de texto sobre Solidity y sobre la config "
                "de fees. No es el plugin de Slither y no certifica el contrato.",
                "",
                "`arcaudit scan` ran. This CLI build does not emit SARIF yet, so the Action "
                "applied text rules to Solidity and to the fee config. This is not the "
                "Slither plugin and it does not certify the contract.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "El SARIF lo escribió `arcaudit`. La Action lo sube a Code Scanning.",
                "",
                "`arcaudit` wrote the SARIF. The Action uploads it to Code Scanning.",
                "",
            ]
        )
    if not findings:
        lines.extend(
            [
                "Sin hallazgos en el umbral revisado por estas reglas.",
                "",
                "No findings from the rules this run applied.",
                "",
            ]
        )
    else:
        shown = findings[:30]
        for finding in shown:
            lines.append(
                f"- **{finding.rule.rule_id}** `{finding.rule.slug}` "
                f"({finding.rule.severity}) `{finding.path}:{finding.line}`"
            )
            lines.append(f"  - ES: {finding.rule.message_es}")
            lines.append(f"  - EN: {finding.rule.message_en}")
            lines.append(f"  - Doc: {finding.rule.help_uri}")
        if len(findings) > len(shown):
            extra = len(findings) - len(shown)
            lines.append(f"- … {extra} hallazgos más en el SARIF. / {extra} more in the SARIF.")
        lines.append("")
    if cli_note:
        lines.extend(
            [
                "<details>",
                "<summary>arcaudit</summary>",
                "",
                "```text",
                cli_note[:800],
                "```",
                "",
                "</details>",
                "",
            ]
        )
    lines.extend(
        [
            "Fuentes / Sources:",
            "",
            f"- {EVM_DIFFERENCES}",
            f"- {PORTING}",
            f"- {COMPAT_GUIDE}",
            "",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: dict) -> None:
    """Write SARIF with a trailing newline."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def findings_from_sarif(payload: dict) -> list[Finding]:
    """Map a CLI SARIF document back to findings for the summary and fail-on."""

    level_to_severity = {"error": "high", "warning": "medium", "note": "low", "none": "info"}
    findings: list[Finding] = []
    for run in payload.get("runs", []):
        driver = run.get("tool", {}).get("driver", {})
        described = {item.get("id"): item for item in driver.get("rules", [])}
        for result in run.get("results", []):
            rule_id = str(result.get("ruleId", "ARC-UNKNOWN"))
            known = RULES.get(rule_id)
            level = str(result.get("level", "warning"))
            severity = (
                known.severity if known is not None else level_to_severity.get(level, "medium")
            )
            message = ""
            raw_message = result.get("message", {})
            if isinstance(raw_message, dict):
                message = str(raw_message.get("text", ""))
            locations = result.get("locations") or [{}]
            physical = locations[0].get("physicalLocation", {}) if locations else {}
            artifact = physical.get("artifactLocation", {})
            region = physical.get("region", {})
            uri = str(artifact.get("uri", "unknown"))
            line = int(region.get("startLine", 1) or 1)
            meta = described.get(rule_id, {})
            short = ""
            short_raw = meta.get("shortDescription", {})
            if isinstance(short_raw, dict):
                short = str(short_raw.get("text", ""))
            help_uri = str(meta.get("helpUri", EVM_DIFFERENCES))
            rule = known or Rule(
                rule_id=rule_id,
                slug=str(meta.get("name", rule_id.lower())),
                severity=severity,
                short_en=short or rule_id,
                message_en=message or short or rule_id,
                message_es=message or short or rule_id,
                help_uri=help_uri,
            )
            findings.append(Finding(rule=rule, path=uri, line=line))
    return findings
