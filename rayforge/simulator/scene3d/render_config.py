from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np


@dataclass
class RenderConfig3D:
    world_to_visual: np.ndarray

    def to_dict(self) -> Dict:
        d: Dict[str, object] = {
            "world_to_visual": self.world_to_visual.astype(
                np.float32
            ).tobytes(),
        }
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderConfig3D":
        w2v = (
            np.frombuffer(data["world_to_visual"], dtype=np.float32)
            .reshape(4, 4)
            .copy()
        )
        return cls(world_to_visual=w2v)
