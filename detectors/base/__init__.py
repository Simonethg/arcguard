"""Base-specific rules (BASE-*, BASE-OFF-*).

Text-pattern heuristics over Solidity and TypeScript/JavaScript sources.
``scan_path(path)`` returns the shared :class:`arcguard.finding.Finding`
(``chain="base"``, lowercase severity, ``doc_url``) and runs through
``arcaudit scan --chain base``. They are not part of the Slither plugin.

A finding is a hint for review, not proof of a bug. An empty result does not
mean code is safe. ArcGuard does not certify security and does not replace an audit.

Every rule cites official Base documentation in ``docs/rules/BASE-*.md``.
"""

from __future__ import annotations

from arcguard.base.rules import RULES, Finding, Rule, scan_path, scan_text

__all__ = ["RULES", "Finding", "Rule", "scan_path", "scan_text"]
