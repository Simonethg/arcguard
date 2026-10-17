"""Orchestrate chain modules, optional Slither detectors, and the exit code."""

from __future__ import annotations

from arcguard.finding import Finding, meets_threshold
from arcguard.registry import ChainModuleError, scan_chains

from .report import ScanReport
from .slither_bridge import slither_findings
from .targets import TargetError, resolve_target


def execute(
    target: str,
    *,
    chain: str,
    threshold: str,
) -> ScanReport:
    """Scan ``target`` and return a report. Raises ``TargetError`` or ``ChainModuleError``."""

    root, cleanup = resolve_target(target)
    try:
        findings, notes, ran = scan_chains(root, chain)
        errors: list[str] = []
        if "arc" in ran:
            extra, slither_notes, slither_errors = slither_findings(root)
            findings.extend(extra)
            notes.extend(slither_notes)
            errors.extend(slither_errors)
        findings.sort(key=lambda item: (item.file, item.line, item.rule_id, item.chain))
        return ScanReport(
            target=target,
            chains_requested=chain,
            chains_ran=ran,
            threshold=threshold,
            findings=findings,
            notes=notes,
            errors=errors,
        )
    finally:
        cleanup()


EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


def exit_code(findings: list[Finding], threshold: str, errors: list[str] | None = None) -> int:
    """2 when the scan hit an analysis error, 1 for a finding at ``threshold``, else 0.

    An error wins over findings: a scan that did not finish is never reported
    as clean, and CI must not read it as a normal pass or a normal failure.
    """

    if errors:
        return EXIT_ERROR
    if any(meets_threshold(finding.severity, threshold) for finding in findings):
        return EXIT_FINDINGS
    return EXIT_CLEAN


__all__ = [
    "EXIT_CLEAN",
    "EXIT_ERROR",
    "EXIT_FINDINGS",
    "ChainModuleError",
    "TargetError",
    "execute",
    "exit_code",
]
