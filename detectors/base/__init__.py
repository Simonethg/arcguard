"""Base-specific rules (BASE-*, BASE-OFF-*).

These are text-pattern heuristics over Solidity and TypeScript/JavaScript sources.
They are NOT wired into the Slither plugin or ``arcaudit scan`` yet: the plugin
keeps returning empty lists so no tool advertises a check through Slither that it
does not perform there. Use ``arcguard.base.scan_text`` / ``scan_path`` directly.

A finding is a hint for review, not proof of a bug. An empty result does not
mean code is safe. ArcGuard does not certify security and does not replace an audit.

Every rule cites official Base documentation in ``docs/rules/BASE-*.md``.
"""

from __future__ import annotations

from arcguard.base.rules import RULES, Finding, Rule, scan_path, scan_text

__all__ = ["RULES", "Finding", "Rule", "scan_path", "scan_text"]
