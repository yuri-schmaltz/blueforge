"""
Parametric CAD & Design Studio components for Blueforge.

This module provides the CAD-first UI architecture:
- CadToolPalette: Vector CAD tool entry points.
- CadRibbon: Alignment, distribution and geometry controls.
- CadInspectorTab: Geometry and contour settings.
- OperationsTimelineWidget: Workflow order and operation parameters.
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
