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
        if "arc" in ran:
            extra, slither_notes = slither_findings(root)
            findings.extend(extra)
            notes.extend(slither_notes)
        findings.sort(key=lambda item: (item.file, item.line, item.rule_id, item.chain))
        return ScanReport(
            target=target,
            chains_requested=chain,
            chains_ran=ran,
            threshold=threshold,
            findings=findings,
            notes=notes,
        )
    finally:
        cleanup()


def exit_code(findings: list[Finding], threshold: str) -> int:
    """1 when any finding is at least ``threshold``; otherwise 0."""

    if any(meets_threshold(finding.severity, threshold) for finding in findings):
        return 1
    return 0


__all__ = ["ChainModuleError", "TargetError", "execute", "exit_code"]
