"""
Parametric CAD & Design Studio components for Pires Forge.

This module provides the CAD-first UI architecture:
- CadToolPalette: Left-hand vector CAD tool palette (Select, Nodes, Shapes, Curves, Offset, Measure).
- CadRibbon: Contextual top ribbon for alignment, distribution, boolean ops, and parametric constraints.
- CadInspectorTab: Dedicated inspector tab for geometric constraints, laser kerf offset, tabs, and lead-in/out.
- OperationsTimelineWidget: Dockable timeline view showing passes and operations in cutting sequence.
"""

from .cad_palette import CadToolPalette
from .cad_ribbon import CadRibbon
from .cad_inspector import CadInspectorTab
from .operations_timeline import OperationsTimelineWidget

__all__ = [
    "CadToolPalette",
    "CadRibbon",
    "CadInspectorTab",
    "OperationsTimelineWidget",
]
