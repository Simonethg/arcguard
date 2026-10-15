"""Celo-specific rules (CELO-*).

Text-pattern heuristics over Solidity and TypeScript/JavaScript sources. ``scan_path``
returns the shared ``arcguard.finding.Finding`` (chain ``celo``) and is run by
``arcaudit scan --chain celo|all`` through ``arcguard.registry``. Not a Slither
detector.

A finding is a hint for review, not proof of a bug. An empty result does not
mean code is safe. ArcGuard does not certify security and does not replace an audit.

Every rule cites official Celo documentation (docs.celo.org) in
``docs/rules/celo/CELO-*.md``.
"""

from __future__ import annotations

from arcguard.celo.rules import RULES, Finding, Rule, scan_path, scan_text

__all__ = ["RULES", "Finding", "Rule", "scan_path", "scan_text"]
