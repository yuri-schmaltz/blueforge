"""
Scene compiler: pure function that compiles assembled job Ops into
GPU-ready vertex data.

Walks the full assembled job ops (with JobStart/End, LayerStart/End
markers) to produce vertex buffers and per-command offset arrays that
are indexed 1:1 with the player's command index.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

import numpy as np
from raygeo.geo.shape.arc import linearize_arc
from raygeo.geo.shape.bezier import linearize_bezier_segment
from raygeo.image import rasterize_scanlines
from raygeo.ops import Ops
from raygeo.ops.types import CommandType

from .compiled_scene import (
    CompiledSceneArtifact,
    ScanlineOverlayLayer,
    TextureLayer,
    VertexLayer,
)
from .render_config import RenderConfig3D

logger = logging.getLogger(__name__)

MAX_TEXTURE_DIMENSION = 8192
Z_OFFSET_NON_POWERED = 0.01


def _transform_verts(verts: np.ndarray, transform: np.ndarray) -> np.ndarray:
    if verts.size == 0:
        return verts
    pts = verts.reshape(-1, 3)
    hom = np.hstack([pts, np.ones((pts.shape[0], 1), dtype=pts.dtype)])
    transformed = (transform @ hom.T).T
    return transformed[:, :3].astype(np.float32)


def _remap_offsets(
    offsets: List[int],
    pair_expansions: List[Tuple[int, "np.ndarray"]],
) -> List[int]:
    if not pair_expansions:
        return offsets
    result = []
    for pre_count in offsets:
        mapped = pre_count
        for seg_start, cum_subs in pair_expansions:
            num_input_pairs = len(cum_subs) - 1
            num_input_verts = num_input_pairs * 2
            if pre_count <= seg_start:
                continue
            if pre_count >= seg_start + num_input_verts:
                mapped += int(cum_subs[-1]) * 2 - num_input_verts
            else:
                vert_offset = pre_count - seg_start
                pair_idx = min(vert_offset // 2, num_input_pairs)
                extra_verts = vert_offset % 2
                mapped = seg_start + int(cum_subs[pair_idx]) * 2 + extra_verts
                break
        result.append(mapped)
    return result


def _to_arr(raw: List[float], cols: int) -> np.ndarray:
    if not raw:
        return np.empty((0, cols), dtype=np.float32)
    return np.array(raw, dtype=np.float32).reshape(-1, cols)


def _to_flat(raw: np.ndarray) -> np.ndarray:
    if raw.size == 0:
        return np.empty((0,), dtype=np.float32)
    return raw.ravel().astype(np.float32)


def _extract_zero_power_segments(
    ops: Ops,
    idx: int,
    start_pos: Tuple[float, float, float],
    zero_power_v: List[float],
    end_pos: Optional[Tuple[float, float, float]] = None,
) -> None:
    end = ops.endpoint(idx)
    power_mv = ops.scanline_data(idx)
    num_steps = len(power_mv)
    if num_steps == 0:
        return

    p_start = np.array(start_pos, dtype=np.float32)
    use_end = end_pos if end_pos is not None else end
    p_end = np.array(use_end, dtype=np.float32)
    line_vec = p_end - p_start

    is_zero = np.frombuffer(power_mv, dtype=np.uint8) == 0
    padded = np.concatenate(([False], is_zero, [False]))
    diffs = np.diff(padded.astype(int))
    starts = np.where(diffs == 1)[0]
    ends = np.where(diffs == -1)[0]

    for s, e in zip(starts, ends):
        t_start = s / num_steps
        t_end = e / num_steps
        chunk_start = p_start + t_start * line_vec
        chunk_end = p_start + t_end * line_vec
        zero_power_v.extend(chunk_start)
        zero_power_v.extend(chunk_end)


def _encode_overlay_segments(
    ops: Ops,
    idx: int,
    start_pos: Tuple[float, float, float],
    ov_pos: List[float],
    ov_pow: List[float],
    ov_lid: List[int],
    laser_index: int = 0,
    end_pos: Optional[Tuple[float, float, float]] = None,
) -> int:
    end = ops.endpoint(idx)
    power_mv = ops.scanline_data(idx)
    num_steps = len(power_mv)
    if num_steps == 0:
        return 0

    sx, sy, sz = start_pos
    use_end = end_pos if end_pos is not None else end
    ex, ey, ez = use_end
    dx = (ex - sx) / num_steps
    dy = (ey - sy) / num_steps
    dz = (ez - sz) / num_steps

    vertex_count = 0
    prev_power_on = False
    seg_start_x = 0.0
    seg_start_y = 0.0
    seg_start_z = 0.0
    seg_power = 0.0

    for i in range(num_steps):
        power_byte = power_mv[i]
        power_on = power_byte > 0

        if power_on and not prev_power_on:
            seg_start_x = sx + i * dx
            seg_start_y = sy + i * dy
            seg_start_z = sz + i * dz
            seg_power = power_byte / 255.0
        elif not power_on and prev_power_on:
            seg_end_x = sx + i * dx
            seg_end_y = sy + i * dy
            seg_end_z = sz + i * dz
            ov_pos.extend(
                [
                    seg_start_x,
                    seg_start_y,
                    seg_start_z,
                    seg_end_x,
                    seg_end_y,
                    seg_end_z,
                ]
            )
            ov_pow.append(seg_power)
            ov_pow.append(seg_power)
            ov_lid.append(laser_index)
            ov_lid.append(laser_index)
            vertex_count += 2

        prev_power_on = power_byte > 0

    if prev_power_on:
        ov_pos.extend([seg_start_x, seg_start_y, seg_start_z, ex, ey, ez])
        ov_pow.append(seg_power)
        ov_pow.append(seg_power)
        ov_lid.append(laser_index)
        ov_lid.append(laser_index)
        vertex_count += 2

    return vertex_count


PX_PER_MM = 50.0


def _scanline_bbox(ops: Ops) -> Optional[Tuple[float, float, float, float]]:
    current_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    has_scanlines = False
    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for i in range(ops.len()):
        ct = ops.command_type(i)
        if ct == CommandType.MOVE_TO:
            current_pos = ops.endpoint(i)
        elif ct == CommandType.SCAN_LINE:
            end = ops.endpoint(i)
            sx, sy = current_pos[0], current_pos[1]
            ex, ey = end[0], end[1]
            min_x = min(min_x, sx, ex)
            min_y = min(min_y, sy, ey)
            max_x = max(max_x, sx, ex)
            max_y = max(max_y, sy, ey)
            current_pos = end
            has_scanlines = True

    if not has_scanlines:
        return None
    return (min_x, min_y, max_x - min_x, max_y - min_y)


def _rasterize_scanlines(
    ops: Ops,
    bbox: Tuple[float, float, float, float],
) -> Optional[Tuple[np.ndarray, int, int, float]]:
    x0, y0, w_mm, h_mm = bbox
    if w_mm <= 0 or h_mm <= 0:
        return None

    px_per_mm = PX_PER_MM
    width_px = int(round(w_mm * px_per_mm))
    height_px = int(round(h_mm * px_per_mm))

    if width_px > MAX_TEXTURE_DIMENSION or height_px > MAX_TEXTURE_DIMENSION:
        scale = min(
            MAX_TEXTURE_DIMENSION / width_px,
            MAX_TEXTURE_DIMENSION / height_px,
        )
        px_per_mm *= scale
        width_px = int(round(w_mm * px_per_mm))
        height_px = int(round(h_mm * px_per_mm))

    if width_px <= 0 or height_px <= 0:
        return None

    buffer = rasterize_scanlines(
        ops,
        width_px,
        height_px,
        (px_per_mm, px_per_mm),
        origin_mm=(x0, y0),
    )
    if not np.any(buffer):
        return None

    dilated = np.zeros_like(buffer)
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            shifted = np.roll(np.roll(buffer, dy, axis=0), dx, axis=1)
            np.maximum(dilated, shifted, out=dilated)
    buffer = dilated

    return buffer, width_px, height_px, px_per_mm


@dataclass
class _WalkState:
    current_power: float = 0.0
    current_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    current_pos_vis: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    is_initial: bool = True
    current_laser_uid: str = ""
    current_laser_index: int = 0
    laser_uid_order: List[str] = field(default_factory=list)
    layer_infos: List[dict] = field(default_factory=list)
    current_layer_start: Optional[int] = None
    current_layer_has_scanlines: bool = False
    current_layer_scanline_laser: str = ""


class _LayerAccumulator:
    """Accumulates vertex data for one rendering treatment group."""

    __slots__ = (
        "pv",
        "pvv",
        "pvl",
        "tv",
        "zpv",
        "ov_pos",
        "ov_pow",
        "ov_lid",
        "pv_cum",
        "tv_cum",
        "ov_cum",
        "pv_off",
        "tv_off",
        "ov_off",
    )

    def __init__(self, total_cmds: int):
        self.pv: List[float] = []
        self.pvv: List[float] = []
        self.pvl: List[int] = []
        self.tv: List[float] = []
        self.zpv: List[float] = []
        self.ov_pos: List[float] = []
        self.ov_pow: List[float] = []
        self.ov_lid: List[int] = []
        self.pv_cum = 0
        self.tv_cum = 0
        self.ov_cum = 0
        self.pv_off = [0] * (total_cmds + 1)
        self.tv_off = [0] * (total_cmds + 1)
        self.ov_off = [0] * (total_cmds + 1)

    def record_offset(self, cmd_idx: int):
        self.pv_off[cmd_idx + 1] = self.pv_cum
        self.tv_off[cmd_idx + 1] = self.tv_cum
        self.ov_off[cmd_idx + 1] = self.ov_cum

    def has_content(self) -> bool:
        return bool(self.pv or self.tv or self.zpv or self.ov_pos)

    def finalize(
        self,
        transform: np.ndarray,
    ):
        pv_arr = _to_arr(self.pv, 3)
        pvv_arr = _to_arr(self.pvv, 1)
        pvl_arr = np.array(self.pvl, dtype=np.float32).reshape(-1, 1)
        tv_arr = _to_arr(self.tv, 3)
        zpv_arr = _to_arr(self.zpv, 3)
        ov_pos_arr = _to_arr(self.ov_pos, 3)
        ov_pow_arr = _to_arr(self.ov_pow, 1)
        ov_lid_arr = np.array(self.ov_lid, dtype=np.float32).reshape(-1, 1)

        pv_arr = _transform_verts(pv_arr, transform)
        tv_arr = _transform_verts(tv_arr, transform)
        zpv_arr = _transform_verts(zpv_arr, transform)
        ov_pos_arr = _transform_verts(ov_pos_arr, transform)

        if tv_arr.size > 0:
            tv_arr[:, 2] += Z_OFFSET_NON_POWERED
        if zpv_arr.size > 0:
            zpv_arr[:, 2] += Z_OFFSET_NON_POWERED

        return (
            pv_arr,
            pvv_arr,
            pvl_arr,
            tv_arr,
            zpv_arr,
            ov_pos_arr,
            ov_pow_arr,
            ov_lid_arr,
        )


def _pad_powers_to_vec4(pvv: np.ndarray) -> np.ndarray:
    if pvv.size == 0:
        return np.empty((0, 4), dtype=np.float32)
    flat = pvv.ravel()
    n = flat.shape[0]
    result = np.zeros((n, 4), dtype=np.float32)
    result[:, 0] = flat
    result[:, 3] = 1.0
    return result


def _extract_powers_from_vec4(pvv4: np.ndarray) -> np.ndarray:
    if pvv4.size == 0:
        return np.empty((0, 1), dtype=np.float32)
    return pvv4[:, 0:1].copy()


def _pad_power_laser_to_vec4(pvv: np.ndarray, pvl: np.ndarray) -> np.ndarray:
    if pvv.size == 0:
        return np.empty((0, 4), dtype=np.float32)
    power = pvv.ravel()
    laser = pvl.ravel()
    n = power.shape[0]
    result = np.zeros((n, 4), dtype=np.float32)
    result[:, 0] = power
    result[:, 1] = laser
    result[:, 3] = 1.0
    return result


def _extract_laser_from_vec4(pvv4: np.ndarray) -> np.ndarray:
    if pvv4.size == 0:
        return np.empty((0, 1), dtype=np.float32)
    return pvv4[:, 1:2].copy()


def _finalize_layers(
    acc: _LayerAccumulator,
    config: RenderConfig3D,
) -> Tuple[List[VertexLayer], List[ScanlineOverlayLayer]]:
    flat_transform = config.world_to_visual

    vertex_layers: List[VertexLayer] = []
    overlay_layers: List[ScanlineOverlayLayer] = []

    if acc.has_content():
        transform = flat_transform
        (
            pv_arr,
            pvv_arr,
            pvl_arr,
            tv_arr,
            zpv_arr,
            ov_pos_arr,
            ov_pow_arr,
            ov_lid_arr,
        ) = acc.finalize(transform)

        vertex_layers.append(
            VertexLayer(
                powered_verts=_to_flat(pv_arr),
                power_values=_to_flat(pvv_arr),
                laser_indices=_to_flat(pvl_arr),
                travel_verts=_to_flat(tv_arr),
                zero_power_verts=_to_flat(zpv_arr),
                powered_cmd_offsets=acc.pv_off,
                travel_cmd_offsets=acc.tv_off,
            )
        )

        overlay_layers.append(
            ScanlineOverlayLayer(
                positions=_to_flat(ov_pos_arr),
                power_values=_to_flat(ov_pow_arr),
                laser_indices=_to_flat(ov_lid_arr),
                cmd_offsets=acc.ov_off,
            )
        )

    return vertex_layers, overlay_layers


def _generate_texture_layers(
    ops: Ops,
    layer_infos: List[dict],
    config: RenderConfig3D,
) -> List[TextureLayer]:
    texture_layers: List[TextureLayer] = []

    for li in layer_infos:
        if not li["has_scanlines"]:
            continue

        layer_ops = Ops()
        for j in range(li["cmd_start"], li["cmd_end"]):
            layer_ops.copy_command_from(ops, j)

        bbox = _scanline_bbox(layer_ops)
        if bbox is None:
            continue

        raster_result = _rasterize_scanlines(layer_ops, bbox)
        if raster_result is None:
            continue

        tex_buf, w_px, h_px, actual_ppm = raster_result
        x0, y0, bw, bh = bbox

        model = np.eye(4, dtype=np.float32)
        model[0, 0] = bw
        model[1, 1] = bh
        model[0, 3] = x0
        model[1, 3] = y0
        final_model = (config.world_to_visual @ model).astype(np.float32)

        texture_layers.append(
            TextureLayer(
                power_texture=tex_buf,
                width_px=w_px,
                height_px=h_px,
                model_matrix=final_model,
                activation_cmd_idx=li["activation_cmd_idx"],
                laser_uid=li.get("scanline_laser", ""),
            )
        )

    return texture_layers


def _handle_layer_start(
    st: _WalkState,
    ops: Ops,
    idx: int,
) -> None:
    st.current_layer_start = idx + 1
    st.current_layer_has_scanlines = False
    st.current_layer_scanline_laser = ""


def _handle_layer_end(
    st: _WalkState,
    acc: _LayerAccumulator,
    cmd_idx: int,
) -> None:
    if st.current_layer_start is not None:
        st.layer_infos.append(
            {
                "cmd_start": st.current_layer_start,
                "cmd_end": cmd_idx,
                "has_scanlines": st.current_layer_has_scanlines,
                "scanline_laser": st.current_layer_scanline_laser,
                "activation_cmd_idx": cmd_idx,
            }
        )
    st.current_layer_start = None


def _handle_set_laser(
    st: _WalkState,
    ops: Ops,
    idx: int,
) -> None:
    laser_uid = ops.head_uid(idx)
    st.current_laser_uid = laser_uid
    if laser_uid not in st.laser_uid_order:
        st.laser_uid_order.append(laser_uid)
    st.current_laser_index = st.laser_uid_order.index(laser_uid)


def _update_positions(
    st: _WalkState,
    acc: _LayerAccumulator,
    ops: Ops,
    idx: int,
) -> None:
    st.current_pos_vis = ops.endpoint(idx)
    st.current_pos = ops.endpoint(idx)
    st.is_initial = False


def _handle_move_to(
    st: _WalkState,
    acc: _LayerAccumulator,
    ops: Ops,
    idx: int,
) -> None:
    vis_end = ops.endpoint(idx)
    if not st.is_initial:
        acc.tv.extend(st.current_pos_vis)
        acc.tv.extend(vis_end)
        acc.tv_cum += 2
    _update_positions(st, acc, ops, idx)


def _handle_line_to(
    st: _WalkState,
    acc: _LayerAccumulator,
    ops: Ops,
    idx: int,
) -> None:
    vis_end = ops.endpoint(idx)
    if st.current_power > 0.0:
        acc.pv.extend(st.current_pos_vis)
        acc.pv.extend(vis_end)
        acc.pvv.append(st.current_power)
        acc.pvv.append(st.current_power)
        acc.pvl.append(st.current_laser_index)
        acc.pvl.append(st.current_laser_index)
        acc.pv_cum += 2
    else:
        acc.zpv.extend(st.current_pos_vis)
        acc.zpv.extend(vis_end)
    _update_positions(st, acc, ops, idx)


def _handle_arc_to(
    st: _WalkState,
    acc: _LayerAccumulator,
    ops: Ops,
    idx: int,
) -> None:
    end = ops.endpoint(idx)
    i_val, j_val, cw = ops.arc_params(idx)
    arc_row = [
        3,
        end[0],
        end[1],
        end[2],
        i_val,
        j_val,
        0.0,
        0.0,
        0.0,
        -1.0 if cw else 1.0,
    ]
    vis_segs = linearize_arc(arc_row, st.current_pos)
    if st.current_power > 0.0:
        n_segs = len(vis_segs)
        for seg_start, seg_end in vis_segs:
            acc.pv.extend(seg_start)
            acc.pv.extend(seg_end)
            acc.pvv.append(st.current_power)
            acc.pvv.append(st.current_power)
            acc.pvl.append(st.current_laser_index)
            acc.pvl.append(st.current_laser_index)
        acc.pv_cum += n_segs * 2
    else:
        for seg_start, seg_end in vis_segs:
            acc.zpv.extend(seg_start)
            acc.zpv.extend(seg_end)
    _update_positions(st, acc, ops, idx)


def _handle_bezier_to(
    st: _WalkState,
    acc: _LayerAccumulator,
    ops: Ops,
    idx: int,
) -> None:
    end = ops.endpoint(idx)
    c1, c2 = ops.bezier_params(idx)
    vis_poly = list(
        linearize_bezier_segment(
            st.current_pos,
            c1,
            c2,
            end,
        )
    )
    if st.current_power > 0.0:
        for j in range(len(vis_poly) - 1):
            acc.pv.extend(vis_poly[j])
            acc.pv.extend(vis_poly[j + 1])
            acc.pvv.append(st.current_power)
            acc.pvv.append(st.current_power)
            acc.pvl.append(st.current_laser_index)
            acc.pvl.append(st.current_laser_index)
        acc.pv_cum += (len(vis_poly) - 1) * 2
    else:
        for j in range(len(vis_poly) - 1):
            acc.zpv.extend(vis_poly[j])
            acc.zpv.extend(vis_poly[j + 1])
    _update_positions(st, acc, ops, idx)


def _handle_scanline(
    st: _WalkState,
    acc: _LayerAccumulator,
    ops: Ops,
    idx: int,
) -> None:
    vis_end = ops.endpoint(idx)
    _extract_zero_power_segments(
        ops,
        idx,
        st.current_pos_vis,
        acc.zpv,
        end_pos=vis_end,
    )
    if not st.is_initial:
        n = _encode_overlay_segments(
            ops,
            idx,
            st.current_pos_vis,
            acc.ov_pos,
            acc.ov_pow,
            acc.ov_lid,
            laser_index=st.current_laser_index,
            end_pos=vis_end,
        )
        acc.ov_cum += n
    _update_positions(st, acc, ops, idx)
    st.current_layer_has_scanlines = True
    if not st.current_layer_scanline_laser:
        st.current_layer_scanline_laser = st.current_laser_uid


def compile_scene(
    ops: Ops,
    config: RenderConfig3D,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> CompiledSceneArtifact:
    total_cmds = ops.len()

    acc = _LayerAccumulator(total_cmds)

    st = _WalkState()

    for i in range(ops.len()):
        if cancel_check is not None and cancel_check():
            raise RuntimeError("Cancelled")

        ct = ops.command_type(i)

        if ct == CommandType.LAYER_START:
            _handle_layer_start(
                st,
                ops,
                i,
            )
        elif ct == CommandType.LAYER_END:
            _handle_layer_end(st, acc, i)
        elif ct == CommandType.SET_HEAD:
            _handle_set_laser(st, ops, i)
        elif ct == CommandType.SET_POWER:
            st.current_power = ops.power(i)
        elif ct == CommandType.MOVE_TO:
            _handle_move_to(st, acc, ops, i)
        elif ct == CommandType.LINE_TO:
            _handle_line_to(st, acc, ops, i)
        elif ct == CommandType.ARC_TO:
            _handle_arc_to(st, acc, ops, i)
        elif ct == CommandType.BEZIER_TO:
            _handle_bezier_to(st, acc, ops, i)
        elif ct == CommandType.SCAN_LINE:
            _handle_scanline(st, acc, ops, i)

        acc.record_offset(i)

    vertex_layers, overlay_layers = _finalize_layers(acc, config)

    texture_layers = _generate_texture_layers(ops, st.layer_infos, config)

    return CompiledSceneArtifact(
        generation_id=0,
        vertex_layers=vertex_layers,
        texture_layers=texture_layers,
        overlay_layers=overlay_layers,
        laser_uid_order=st.laser_uid_order,
    )
