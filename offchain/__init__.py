"""Arc chain module (``arcguard.arc``).

``scan_path(path)`` returns the shared :class:`arcguard.finding.Finding` list.
ARC-OFF-1 lives here: TypeScript, JavaScript, Foundry config, Hardhat config,
and Foundry scripts that set ``maxFeePerGas`` or ``gasPrice`` below 20 Gwei.

Sources:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
"""

from .max_fee import DOC_URL, RULE_ID, scan_path, scan_text

__all__ = ["DOC_URL", "RULE_ID", "scan_path", "scan_text"]
