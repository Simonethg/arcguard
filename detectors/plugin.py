"""Slither plugin entry point for ArcGuard.

Slither discovers third-party plugins through the ``slither_analyzer.plugin``
entry-point group and calls ``make_plugin``. The callable must return
``(detectors, printers)``. Both lists stay empty until the Arc detectors land.

Official references for the rules this plugin will implement:

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
"""

from __future__ import annotations


def make_plugin() -> tuple[list[type], list[type]]:
    """Return ArcGuard detector classes and printer classes.

    Empty lists are valid: Slither's ``all()`` check over an empty plugin
    passes, and no Arc detector is advertised before it is implemented.
    Imports of ``AbstractDetector`` stay inside future detector modules so
    ``pip install -e .`` does not require Slither.
    """

    return [], []
