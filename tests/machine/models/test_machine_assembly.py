from raygeo.ops.axis import Axis

from rayforge.context import RayforgeContext
from rayforge.machine.assembly import LinkRole
from rayforge.machine.models.laser import Laser
from rayforge.machine.models.machine import Machine
from rayforge.simulator.machine_state import MachineState


def _make_machine():
    ctx = RayforgeContext()
    return Machine(ctx)


class TestAssemblyCaching:
    def test_assembly_cached_on_repeated_access(self):
        machine = _make_machine()
        asm1 = machine.assembly
        asm2 = machine.assembly
        assert asm1 is asm2

    def test_invalidate_forces_rebuild(self):
        machine = _make_machine()
        asm1 = machine.assembly
        machine.invalidate_assembly()
        asm2 = machine.assembly
        assert asm1 is not asm2


class TestAssemblyHeadLinks:
    def test_single_head(self):
        machine = _make_machine()
        asm = machine.assembly
        heads = asm.get_links_by_role(LinkRole.HEAD)
        assert len(heads) == 1
        assert heads[0].name == "head_0"

    def test_head_positions(self):
        machine = _make_machine()
        state = MachineState()
        state.axes[Axis.X] = 10.0
        state.axes[Axis.Y] = 20.0
        state.axes[Axis.Z] = 5.0
        positions = machine.assembly.head_positions(state)
        assert "head_0" in positions
        assert positions["head_0"] == (10.0, 20.0, 5.0)


class TestAssemblyInvalidation:
    def test_add_head_invalidates(self):
        machine = _make_machine()
        asm_before = machine.assembly

        machine.add_head(Laser())
        asm_after = machine.assembly
        assert asm_after is not asm_before
        heads = asm_after.get_links_by_role(LinkRole.HEAD)
        assert len(heads) == 2

    def test_remove_head_invalidates(self):
        machine = _make_machine()

        extra = Laser()
        machine.add_head(extra)
        asm_before = machine.assembly
        machine.remove_head(extra)
        asm_after = machine.assembly
        assert asm_after is not asm_before
        heads = asm_after.get_links_by_role(LinkRole.HEAD)
        assert len(heads) == 1
