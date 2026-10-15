"""Shared finding type for every chain module.

Chain packages expose ``scan_path(path) -> list[Finding]``. Arc and future
modules should construct this dataclass. The Base package already published
on its own branch (``arcguard.base.scan_path``) returns a different frozen
dataclass: ``rule_id``, ``slug``, ``severity``, ``path``, ``line``, ``message``.
It has no ``chain``, no ``doc_url``, and the file field is named ``path``.
``normalize_finding`` accepts that shape without importing ``arcguard.base``.

Severity is stored in lowercase (``info``, ``low``, ``medium``, ``high``,
``critical``). Base emits title case (``High``); that is folded here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

SEVERITY_RANK = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

_SEVERITY_ALIASES = {
    "info": "info",
    "informational": "info",
    "note": "info",
    "low": "low",
    "baja": "low",
    "medium": "medium",
    "moderate": "medium",
    "media": "medium",
    "med": "medium",
    "high": "high",
    "alta": "high",
    "critical": "critical",
    "critica": "critical",
}

# Relative rule pages (Base's Rule.doc) become a stable blob URL.
_BLOB = "https://github.com/Simonethg/arcguard/blob/main/"


@dataclass(frozen=True)
class Finding:
    """One static-analysis result.

    Fields are the cross-chain contract: ``rule_id``, ``chain``, ``severity``,
    ``file``, ``line``, ``message``, ``doc_url``.
    """

    rule_id: str
    chain: str
    severity: str
    file: str
    line: int
    message: str
    doc_url: str

    def to_dict(self) -> dict[str, object]:
        return {
            "rule_id": self.rule_id,
            "chain": self.chain,
            "severity": self.severity,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "doc_url": self.doc_url,
        }


def canonical_severity(value: object) -> str:
    """Fold chain-specific labels onto the shared scale.

    Unknown labels become ``high`` so a finding is not dropped on a typo.
    """

    key = str(value).strip().lower()
    return _SEVERITY_ALIASES.get(key, "high")


def meets_threshold(severity: str, threshold: str) -> bool:
    """True when ``severity`` is at least ``threshold`` on the shared scale."""

    return (
        SEVERITY_RANK[canonical_severity(severity)] >= SEVERITY_RANK[canonical_severity(threshold)]
    )


def relativize(file: str, root: Path) -> str:
    """Prefer a path relative to the scan root, with forward slashes."""

    raw = Path(file)
    try:
        base = root.resolve()
        resolved = raw.resolve()
    except OSError:
        return raw.as_posix()
    if base.is_file():
        if resolved == base:
            return raw.name
        return raw.as_posix()
    try:
        return resolved.relative_to(base).as_posix()
    except ValueError:
        return raw.as_posix()


def _doc_from_module(module: object | None, rule_id: str) -> str:
    if module is None:
        return ""
    rules = getattr(module, "RULES", ()) or ()
    for rule in rules:
        if getattr(rule, "rule_id", None) != rule_id:
            continue
        doc = getattr(rule, "doc_url", None) or getattr(rule, "doc", None) or ""
        doc = str(doc).strip()
        if not doc:
            continue
        if doc.startswith(("https://", "http://")):
            return doc
        return _BLOB + doc.lstrip("/")
    return ""


def normalize_finding(
    raw: object,
    *,
    chain: str,
    module: object | None = None,
    root: Path | None = None,
) -> Finding:
    """Adapt this package's Finding or the Base package's Finding."""

    if isinstance(raw, Finding):
        file = relativize(raw.file, root) if root is not None else raw.file
        if file == raw.file:
            return raw
        return Finding(
            raw.rule_id,
            raw.chain,
            raw.severity,
            file,
            raw.line,
            raw.message,
            raw.doc_url,
        )

    rule_id = str(getattr(raw, "rule_id"))
    file = getattr(raw, "file", None)
    if file is None:
        file = getattr(raw, "path", "")
    file = str(file)
    if root is not None and file:
        file = relativize(file, root)
    line = int(getattr(raw, "line", 1) or 1)
    if line < 1:
        line = 1
    doc_url = getattr(raw, "doc_url", None)
    if not doc_url:
        doc_url = _doc_from_module(module, rule_id)
    reported_chain = getattr(raw, "chain", None) or chain
    return Finding(
        rule_id=rule_id,
        chain=str(reported_chain),
        severity=canonical_severity(getattr(raw, "severity", "high")),
        file=file,
        line=line,
        message=str(getattr(raw, "message", "")),
        doc_url=str(doc_url or ""),
    )
