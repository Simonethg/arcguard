"""Text, JSON, SARIF 2.1.0, and Markdown reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.parse import quote

from arcguard import __version__
from arcguard.arc.max_fee import DOC_URL, RULE_ID, RULE_NAME
from arcguard.finding import Finding

_SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/"
    "sarif-2.1/schema/sarif-schema-2.1.0.json"
)

_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}

_SECURITY_SEVERITY = {
    "critical": "9.0",
    "high": "8.0",
    "medium": "5.0",
    "low": "3.0",
    "info": "1.0",
}

_ARC_HELP = (
    "Arc's minimum base fee is 20 Gwei. A transaction with maxFeePerGas or legacy "
    "gasPrice below that floor is silently dropped by the mempool: no error receipt "
    "and no block inclusion. Set the fee to at least 20 Gwei. maxPriorityFeePerGas "
    "may be 0. Foundry's gas_price = 0 means unset, not a submitted price of 0.\n\n"
    "Sources:\n"
    "- https://docs.arc.io/arc/references/evm-differences\n"
    "- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc\n"
    "- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps"
)


@dataclass
class ScanReport:
    target: str
    chains_requested: str
    chains_ran: tuple[str, ...]
    threshold: str
    findings: list[Finding]
    notes: list[str]


def render_text(report: ScanReport) -> str:
    lines = [
        f"arcguard {__version__}",
        f"target: {report.target}",
        f"chains: {', '.join(report.chains_ran) if report.chains_ran else '(none)'}",
        f"threshold: {report.threshold}",
        "",
    ]
    if not report.findings:
        lines.append("No findings.")
    for finding in report.findings:
        lines.append(
            f"{finding.rule_id} {finding.severity} {finding.chain} {finding.file}:{finding.line}"
        )
        lines.append(f"  {finding.message}")
        if finding.doc_url:
            lines.append(f"  doc: {finding.doc_url}")
        lines.append("")
    for note in report.notes:
        lines.append(f"note: {note}")
    lines.append(
        "ArcGuard does not certify security and does not replace an audit. "
        "Live checks stay on public testnets."
    )
    return "\n".join(lines).rstrip() + "\n"


def render_json(report: ScanReport) -> str:
    payload = {
        "tool": "arcguard",
        "version": __version__,
        "target": report.target,
        "chains_requested": report.chains_requested,
        "chains_ran": list(report.chains_ran),
        "threshold": report.threshold,
        "notes": list(report.notes),
        "findings": [finding.to_dict() for finding in report.findings],
    }
    return json.dumps(payload, indent=2) + "\n"


def render_markdown(report: ScanReport) -> str:
    lines = [
        "# ArcGuard report",
        "",
        f"- Tool version: `{__version__}`",
        f"- Target: `{report.target}`",
        f"- Chains requested: `{report.chains_requested}`",
        f"- Chains run: `{', '.join(report.chains_ran) if report.chains_ran else '(none)'}`",
        f"- Threshold: `{report.threshold}`",
        "",
    ]
    if report.findings:
        lines.extend(
            [
                "| Severity | Rule | Chain | Location | Message |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for finding in report.findings:
            message = finding.message.replace("|", "\\|")
            location = f"`{finding.file}:{finding.line}`"
            row = (
                f"| {finding.severity} | {finding.rule_id} | {finding.chain} "
                f"| {location} | {message} |"
            )
            lines.append(row)
        lines.append("")
        lines.append("## Docs")
        lines.append("")
        seen: set[str] = set()
        for finding in report.findings:
            if not finding.doc_url or finding.doc_url in seen:
                continue
            seen.add(finding.doc_url)
            lines.append(f"- {finding.rule_id}: {finding.doc_url}")
        lines.append("")
    else:
        lines.append("No findings.")
        lines.append("")
    if report.notes:
        lines.append("## Notes")
        lines.append("")
        for note in report.notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append(
        "ArcGuard does not certify security and does not replace an audit. "
        "Live checks stay on public testnets."
    )
    lines.append("")
    return "\n".join(lines)


def _sarif_uri(path: str) -> str:
    return quote(path.replace("\\", "/"), safe="/")


def _rule_objects(findings: list[Finding]) -> list[dict[str, object]]:
    ordered: list[str] = []
    by_id: dict[str, Finding] = {}
    for finding in findings:
        if finding.rule_id not in by_id:
            ordered.append(finding.rule_id)
            by_id[finding.rule_id] = finding
    if not ordered:
        ordered = [RULE_ID]
    rules: list[dict[str, object]] = []
    for rule_id in ordered:
        if rule_id == RULE_ID:
            rules.append(
                {
                    "id": RULE_ID,
                    "name": RULE_NAME,
                    "shortDescription": {
                        "text": "maxFeePerGas or gasPrice is below Arc's 20 Gwei floor."
                    },
                    "fullDescription": {"text": _ARC_HELP},
                    "help": {"text": _ARC_HELP},
                    "helpUri": DOC_URL,
                    "defaultConfiguration": {"level": "error"},
                    "properties": {
                        "tags": ["security", "arc", "gas"],
                        "security-severity": "8.0",
                        "precision": "high",
                    },
                }
            )
            continue
        sample = by_id[rule_id]
        descriptor: dict[str, object] = {
            "id": rule_id,
            "shortDescription": {"text": sample.message[:400]},
            "help": {"text": sample.message},
            "defaultConfiguration": {"level": _LEVEL.get(sample.severity, "warning")},
            "properties": {
                "tags": ["security", sample.chain],
                "security-severity": _SECURITY_SEVERITY.get(sample.severity, "5.0"),
            },
        }
        if sample.doc_url:
            descriptor["helpUri"] = sample.doc_url
        rules.append(descriptor)
    return rules


def render_sarif(report: ScanReport) -> str:
    """Build a SARIF 2.1.0 log. The result validates against the OASIS schema."""

    rules = _rule_objects(report.findings)
    index = {str(rule["id"]): position for position, rule in enumerate(rules)}
    results = []
    for finding in report.findings:
        results.append(
            {
                "ruleId": finding.rule_id,
                "ruleIndex": index[finding.rule_id],
                "level": _LEVEL.get(finding.severity, "warning"),
                "message": {"text": finding.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": _sarif_uri(finding.file)},
                            "region": {"startLine": max(finding.line, 1)},
                        }
                    }
                ],
                "properties": {
                    "chain": finding.chain,
                    "severity": finding.severity,
                    "docUrl": finding.doc_url,
                },
            }
        )
    notifications = [
        {"message": {"text": note}, "level": "note"} for note in dict.fromkeys(report.notes)
    ]
    log = {
        "$schema": _SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ArcGuard",
                        "version": __version__,
                        "informationUri": "https://github.com/Simonethg/arcguard",
                        "rules": rules,
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "commandLine": (
                            f"arcaudit scan {report.target} --chain {report.chains_requested} "
                            f"--threshold {report.threshold}"
                        ),
                        "toolExecutionNotifications": notifications,
                    }
                ],
            }
        ],
    }
    return json.dumps(log, indent=2) + "\n"


def render(report: ScanReport, fmt: str) -> str:
    if fmt == "json":
        return render_json(report)
    if fmt == "sarif":
        return render_sarif(report)
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "text":
        return render_text(report)
    raise ValueError(f"unknown format {fmt!r}")
