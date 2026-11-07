import numpy as np
import pytest

from rayforge.simulator.scene3d.render_config import RenderConfig3D


class TestRenderConfig3D:
    @pytest.fixture
    def sample_config(self):
        w2v = np.eye(4, dtype=np.float32)
        w2v[0, 3] = -10.0
        w2v[1, 3] = -5.0

        return RenderConfig3D(world_to_visual=w2v)

    def test_round_trip(self, sample_config):
        d = sample_config.to_dict()
        restored = RenderConfig3D.from_dict(d)

        np.testing.assert_allclose(
            sample_config.world_to_visual, restored.world_to_visual
        )

    def test_round_trip_preserves_matrices(self, sample_config):
        d = sample_config.to_dict()
        restored = RenderConfig3D.from_dict(d)
        np.testing.assert_allclose(
            sample_config.world_to_visual, restored.world_to_visual
        )

    def test_missing_field_raises(self):
        with pytest.raises(KeyError):
            RenderConfig3D.from_dict({})
