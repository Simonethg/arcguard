"""Registry of per-chain scanners.

Each chain is an importable module ``arcguard.<chain>`` with
``scan_path(path) -> list[Finding]``. ``arc`` is this repository's off-chain
package. ``base`` is the module published by the Base rules branch; it is
imported only when that package is installed, and its findings are adapted.
``celo`` uses the same contract and is skipped, with a note, until it exists.

Asking for one missing chain is an error. ``--chain all`` keeps going so a
partial install does not look like a clean scan: the note is part of the report.
"""

from __future__ import annotations

import importlib
from pathlib import Path

from arcguard.finding import Finding, normalize_finding

CHAIN_MODULES: dict[str, str] = {
    "arc": "arcguard.arc",
    "base": "arcguard.base",
    "celo": "arcguard.celo",
}

CHAINS: tuple[str, ...] = tuple(CHAIN_MODULES)


class ChainModuleError(Exception):
    """The requested chain module is missing or does not expose ``scan_path``."""


def selected_chains(chain: str) -> tuple[str, ...]:
    if chain == "all":
        return CHAINS
    if chain not in CHAIN_MODULES:
        known = ", ".join((*CHAINS, "all"))
        raise ChainModuleError(f"unknown chain {chain!r}; expected one of: {known}")
    return (chain,)


def load_scanner(chain: str) -> tuple[object, object]:
    """Return ``(module, scan_path)`` for a chain, or raise ``ChainModuleError``."""

    name = CHAIN_MODULES[chain]
    try:
        module = importlib.import_module(name)
    except ModuleNotFoundError as exc:
        # A missing dependency of an installed module is a different failure
        # than "this chain has not been added yet".
        if exc.name not in {name, name.split(".", 1)[0]} and not name.startswith(str(exc.name)):
            raise
        raise ChainModuleError(
            f"{chain}: {name} is not installed, so no {chain} rules were executed"
        ) from exc
    scan = getattr(module, "scan_path", None)
    if not callable(scan):
        raise ChainModuleError(f"{chain}: {name} has no scan_path(path) function")
    return module, scan


def scan_chains(root: Path, chain: str) -> tuple[list[Finding], list[str], tuple[str, ...]]:
    """Run every selected chain module that can be imported.

    Returns findings, human-readable notes, and the chains that actually ran.
    """

    findings: list[Finding] = []
    notes: list[str] = []
    ran: list[str] = []
    explicit = chain != "all"
    for name in selected_chains(chain):
        try:
            module, scan = load_scanner(name)
        except ChainModuleError as exc:
            if explicit:
                raise
            notes.append(str(exc))
            continue
        raw_results = scan(root)
        ran.append(name)
        for raw in raw_results:
            findings.append(normalize_finding(raw, chain=name, module=module, root=root))
    findings.sort(key=lambda item: (item.file, item.line, item.rule_id, item.chain))
    return findings, notes, tuple(ran)
