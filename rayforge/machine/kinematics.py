from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np
from raygeo.geo.types import Point3D
from raygeo.ops.axis import Axis

from ..core.model import Model
from .assembly import Assembly, JointType, Link, LinkRole
from .models.axis import AxisSet

if TYPE_CHECKING:
    from ..simulator.machine_state import MachineState

HeadSpec = Tuple[Optional[Model], np.ndarray]


def _axis_direction(axis_letter: Axis) -> Tuple[float, float, float]:
    mapping = {
        Axis.X: (1.0, 0.0, 0.0),
        Axis.Y: (0.0, 1.0, 0.0),
        Axis.Z: (0.0, 0.0, 1.0),
    }
    return mapping.get(axis_letter, (0.0, 0.0, 0.0))


def build_assembly(
    axis_set: AxisSet,
    head_specs: Optional[List[HeadSpec]] = None,
) -> Assembly:
    if head_specs is None:
        head_specs = [(None, np.eye(4, dtype=np.float64))]
    links = [
        Link("base", parent=None, joint_type=JointType.FIXED),
    ]

    _gantry_axes = {Axis.X, Axis.Y}

    parent = "base"
    for axis_letter in _gantry_axes:
        cfg = axis_set.get(axis_letter)
        if cfg is None:
            continue
        name = f"gantry_{axis_letter.label}"
        links.append(
            Link(
                name,
                parent=parent,
                joint_type=JointType.PRISMATIC,
                joint_axis=_axis_direction(axis_letter),
                driver_axis=axis_letter,
            )
        )
        parent = name

    for i, (model, transform) in enumerate(head_specs):
        links.append(
            Link(
                f"head_{i}",
                parent=parent,
                joint_type=JointType.PRISMATIC,
                joint_axis=(0.0, 0.0, 1.0),
                driver_axis=Axis.Z,
                role=LinkRole.HEAD,
                model=model,
                model_transform=transform.copy(),
            )
        )

    return Assembly(links)


class Kinematics:
    """Translates MachineState into spatial data via an Assembly."""

    def __init__(self, assembly: Assembly):
        self._assembly = assembly

    def head_positions(self, state: "MachineState") -> Dict[str, Point3D]:
        return self._assembly.head_positions(state)


def create_kinematics(
    axis_set: AxisSet,
    head_specs: Optional[List[HeadSpec]] = None,
) -> Kinematics:
    return Kinematics(build_assembly(axis_set, head_specs))
