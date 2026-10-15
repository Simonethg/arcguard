"""Shared Slither detector base for ARC-001..ARC-008."""

from __future__ import annotations

from slither.detectors.abstract_detector import AbstractDetector
from slither.utils.output import Output

from arcguard.engine import findings_for


class ArcDetector(AbstractDetector):
    """Detector that reports one Arc rule with its id, severity, and docs."""

    RULE_ID = ""
    DOCS = ""
    SEVERITY = ""

    def _detect(self) -> list[Output]:
        results: list[Output] = []
        for finding in findings_for(self.compilation_unit, self.RULE_ID):
            severity = finding.severity or self.SEVERITY
            info = [finding.anchor, " ", finding.message, "\n"]
            output = self.generate_result(
                info,
                {
                    "id": self.RULE_ID,
                    "severity": severity,
                    "recommendation": self.WIKI_RECOMMENDATION,
                    "docs": self.DOCS,
                },
            )
            # Class IMPACT stays High. Name-only msgValue/balanceOf hits are Medium.
            output.data["impact"] = severity
            results.append(output)
        return results
