"""Shared test helper for scene compiler tests."""

import numpy as np

from rayforge.simulator.scene3d.render_config import RenderConfig3D


def make_test_config():
    return RenderConfig3D(
        world_to_visual=np.eye(4, dtype=np.float32),
    )


def make_assembled_ops(step_ops_list):
    """Assemble per-step ops into full job ops with markers.

    step_ops_list: list of (layer_uid, ops) tuples.
    Returns a single Ops with JobStart/End and LayerStart/End markers.
    """
    from raygeo.ops import Ops

    assembled = Ops()
    assembled.job_start()
    for layer_uid, step_ops in step_ops_list:
        assembled.layer_start(layer_uid)
        assembled.extend(step_ops)
        assembled.layer_end(layer_uid)
    assembled.job_end()
    return assembled
