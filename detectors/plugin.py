"""Slither plugin entry point for ArcGuard.

Slither discovers third-party plugins through the ``slither_analyzer.plugin``
entry-point group and calls ``make_plugin``. The callable must return
``(detectors, printers)``. With Slither installed, the detectors are
ARC-001..ARC-008. Without it, both lists stay empty so the base install
does not import Slither.

Official references for the rules this plugin will implement:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
"""

from __future__ import annotations


def make_plugin() -> tuple[list[type], list[type]]:
    """Return ArcGuard detector classes and printer classes.

    Slither calls this when the ``detectors`` extra is installed. Without
    Slither the import fails and both lists stay empty, so ``pip install -e .``
    still imports the package. With Slither, ``slither --detect arc-...`` runs
    ARC-001..ARC-008.
    """

    try:
        from arcguard.all_detectors import DETECTORS
    except ImportError:
        return [], []
    return list(DETECTORS), []
