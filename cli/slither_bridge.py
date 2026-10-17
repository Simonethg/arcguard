"""Run ArcGuard Slither detectors when the plugin actually exposes some.

The scaffold plugin returns empty lists. This bridge does nothing in that
case, so a scan cannot pretend Solidity was analyzed. Detector classes run
only for a scan that includes Arc, and only if Slither imports. A missing
compiler or a missing Slither install becomes a note; off-chain rules still run.

A detector that raises is an error, not a note. The remaining detectors still
run, and the error is returned separately so the CLI fails closed (exit 2)
instead of reporting a crashed scan as clean.
"""

from __future__ import annotations

from pathlib import Path

from arcguard.finding import Finding, canonical_severity
from arcguard.plugin import make_plugin

_DOC = "https://docs.arc.io/arc/references/evm-differences"


def slither_findings(root: Path) -> tuple[list[Finding], list[str], list[str]]:
    """Return ``(findings, notes, errors)``. Any error means the scan is incomplete."""

    detectors, _printers = make_plugin()
    if not detectors:
        return [], [], []
    try:
        from slither.slither import Slither
    except ImportError:
        return (
            [],
            [
                "Slither is not installed; Arc detector classes were not executed. "
                "Off-chain rules still ran."
            ],
            [],
        )
    try:
        analyzer = Slither(str(root))
    except Exception as exc:
        return [], [f"Slither did not analyze this target ({type(exc).__name__})."], []

    wanted = {detector.ARGUMENT for detector in detectors if hasattr(detector, "ARGUMENT")}
    registered = {type(detector) for detector in analyzer.detectors}
    for detector_cls in detectors:
        if detector_cls not in registered:
            analyzer.register_detector(detector_cls)

    findings: list[Finding] = []
    errors: list[str] = []
    for detector in analyzer.detectors:
        argument = getattr(detector, "ARGUMENT", None)
        if argument not in wanted and type(detector) not in detectors:
            continue
        try:
            results = detector.detect() or []
        except Exception as exc:
            detail = str(exc).strip().splitlines()[0][:200] if str(exc).strip() else ""
            suffix = f": {detail}" if detail else ""
            errors.append(
                f"Slither detector {argument} failed ({type(exc).__name__}{suffix}). "
                "Its rule did not run, so this scan is incomplete."
            )
            continue
        for result in results:
            findings.append(_convert(detector, result, root))
    return findings, [], errors


def _location(result: object, root: Path) -> tuple[str, int]:
    elements = result.get("elements") if isinstance(result, dict) else None
    if not elements:
        return root.as_posix(), 1
    source = elements[0].get("source_mapping") if isinstance(elements[0], dict) else None
    if not isinstance(source, dict):
        return root.as_posix(), 1
    filename = source.get("filename_relative") or source.get("filename_absolute") or ""
    if isinstance(filename, dict):
        filename = filename.get("relative") or filename.get("short") or ""
    lines = source.get("lines") or [1]
    line = int(lines[0]) if lines else 1
    return str(filename), max(line, 1)


def _convert(detector: object, result: object, root: Path) -> Finding:
    if isinstance(result, dict):
        message = str(result.get("description") or getattr(detector, "HELP", "") or "Arc detector")
        impact = result.get("impact") or getattr(detector, "IMPACT", "High")
        extra = result.get("additional_fields")
        fields = extra if isinstance(extra, dict) else {}
        rule_id = str(
            fields.get("id") or result.get("check") or getattr(detector, "ARGUMENT", "arc-detector")
        )
        filename, line = _location(result, root)
    else:
        message = str(getattr(result, "description", "") or getattr(detector, "HELP", ""))
        impact = getattr(detector, "IMPACT", "High")
        rule_id = str(getattr(detector, "ARGUMENT", "arc-detector"))
        filename, line = root.as_posix(), 1
    wiki = str(getattr(detector, "WIKI", "") or "")
    doc_url = wiki if wiki.startswith(("https://", "http://")) else _DOC
    return Finding(
        rule_id=rule_id,
        chain="arc",
        severity=canonical_severity(impact),
        file=filename,
        line=line,
        message=message.strip() or "Arc Slither detector reported a finding.",
        doc_url=doc_url,
    )
