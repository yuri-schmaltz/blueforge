from raygeo.ops.axis import Axis

from rayforge.machine.kinematics import (
    Kinematics,
    create_kinematics,
)
from rayforge.machine.models.axis import (
    AxisConfig,
    AxisSet,
    AxisType,
)
from rayforge.machine.models.machine import Machine
from rayforge.simulator.machine_state import MachineState


def _make_3axis_set():
    return AxisSet(
        [
            AxisConfig(
                letter=Axis.X,
                axis_type=AxisType.LINEAR,
                extents=(0, 200),
            ),
            AxisConfig(
                letter=Axis.Y,
                axis_type=AxisType.LINEAR,
                extents=(0, 200),
            ),
            AxisConfig(
                letter=Axis.Z,
                axis_type=AxisType.LINEAR,
                extents=(-50, 50),
            ),
        ]
    )


def _make_state(x=0.0, y=0.0, z=0.0):
    state = MachineState()
    state.axes[Axis.X] = x
    state.axes[Axis.Y] = y
    state.axes[Axis.Z] = z
    return state


def test_cartesian_head_positions():
    kinematics = create_kinematics(axis_set=_make_3axis_set())
    state = _make_state(x=10.0, y=20.0, z=0.0)
    heads = kinematics.head_positions(state)
    assert heads == {"head_0": (10.0, 20.0, 0.0)}


def test_machine_kinematics():
    from rayforge.context import RayforgeContext

    ctx = RayforgeContext()
    machine = Machine(ctx)
    kin = machine.kinematics
    assert isinstance(kin, Kinematics)
