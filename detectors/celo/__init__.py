"""Celo-specific rules (CELO-*).

Text-pattern heuristics over Solidity and TypeScript/JavaScript sources. They are
NOT wired into the Slither plugin or ``arcaudit scan`` yet (the common engine is
still a skeleton). Use ``arcguard.celo.scan_text`` / ``scan_path`` directly.

A finding is a hint for review, not proof of a bug. An empty result does not
mean code is safe. ArcGuard does not certify security and does not replace an audit.

Every rule cites official Celo documentation (docs.celo.org) in
``docs/rules/celo/CELO-*.md``.
"""

from __future__ import annotations

from arcguard.celo.rules import RULES, Finding, Rule, scan_path, scan_text

__all__ = ["RULES", "Finding", "Rule", "scan_path", "scan_text"]
