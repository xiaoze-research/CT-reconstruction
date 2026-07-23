"""Cone-beam CT reconstruction using ASTRA FDK_CUDA."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import astra
import numpy as np

from projection_io import load_projection_stack


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="Directory of projection images")
    parser.add_argument("--output-raw", required=True)
    parser.add_argument("--start-number", type=int, required=True)
    parser.add_argument("--stop-number", type=int, required=True)
    parser.add_argument("--number-step", type=int, required=True)
    parser.add_argument("--degrees", type=float, required=True)
    parser.add_argument("--pixel-size-mm", type=float, required=True)
    parser.add_argument("--sod-mm", type=float, required=True, help="Source-to-object distance")
    parser.add_argument("--odd-mm", type=float, required=True, help="Object-to-detector distance")
    parser.add_argument("--vol-cols", type=int, required=True)
    parser.add_argument("--vol-rows", type=int, required=True)
    parser.add_argument("--vol-slices", type=int, required=True)
    parser.add_argument("--epsilon", type=float, required=True)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument(
        "--filter-type",
        help="ASTRA FDK filter name (e.g. hann, hamming); library default when omitted",
    )
    parser.add_argument(
        "--center-offset-px",
        type=int,
        help="Horizontal detector-centre correction in pixels; positive shifts "
        "projection content toward higher column indices",
    )
    return parser.parse_args()


def shift_columns(stack: np.ndarray, offset: int) -> np.ndarray:
    """Shift projection columns by ``offset`` pixels, replicating the edge column.

    Edge replication (rather than wrap-around) keeps object pixels from one
    detector edge from appearing at the opposite edge after the shift.
    """
    if offset == 0:
        return stack
    if abs(offset) >= stack.shape[2]:
        raise ValueError(f"Centre offset {offset} exceeds detector width {stack.shape[2]}")
    shifted = np.empty_like(stack)
    if offset > 0:
        shifted[:, :, offset:] = stack[:, :, :-offset]
        shifted[:, :, :offset] = stack[:, :, :1]
    else:
        shifted[:, :, :offset] = stack[:, :, -offset:]
        shifted[:, :, offset:] = stack[:, :, -1:]
    return shifted


def main() -> None:
    args = parse_args()
    projections, paths = load_projection_stack(
        input_dir=args.input_dir,
        start_number=args.start_number,
        stop_number=args.stop_number,
        number_step=args.number_step,
        log_transform=True,
        invert=args.invert,
        epsilon=args.epsilon,
    )
    n_angles, img_h, img_w = projections.shape
    angles = np.linspace(0, np.deg2rad(args.degrees), n_angles, endpoint=False)

    if args.center_offset_px:
        projections = shift_columns(projections, args.center_offset_px)
        print(f"Applied detector-centre correction: {args.center_offset_px:+d} px")

    dist_source_origin = args.sod_mm / args.pixel_size_mm
    dist_origin_det = args.odd_mm / args.pixel_size_mm
    print(f"Loaded {len(paths)} projections with shape {img_w}x{img_h}")
    print(f"SOD={dist_source_origin:.2f} px, ODD={dist_origin_det:.2f} px")

    proj_data_astra = np.ascontiguousarray(np.transpose(projections, (1, 0, 2)))
    del projections  # drop the untransposed copy (~stack-sized) before ASTRA copies again
    proj_geom = astra.create_proj_geom(
        "cone",
        1.0,
        1.0,
        img_h,
        img_w,
        angles,
        dist_source_origin,
        dist_origin_det,
    )
    # ASTRA's 3D signature is (GridRowCount, GridColCount, GridSliceCount).
    vol_geom = astra.create_vol_geom(args.vol_rows, args.vol_cols, args.vol_slices)

    proj_id = astra.data3d.create("-proj3d", proj_geom, proj_data_astra)
    del proj_data_astra  # ASTRA holds its own copy now
    rec_id = astra.data3d.create("-vol", vol_geom)
    cfg = astra.astra_dict("FDK_CUDA")
    cfg["ProjectionDataId"] = proj_id
    cfg["ReconstructionDataId"] = rec_id
    if args.filter_type:
        cfg["FilterType"] = args.filter_type
        print(f"FDK filter: {args.filter_type}")

    alg_id = astra.algorithm.create(cfg)
    t0 = time.time()
    astra.algorithm.run(alg_id)
    print(f"FDK_CUDA elapsed {time.time() - t0:.2f}s")

    rec_data = astra.data3d.get(rec_id).astype(np.float32)
    output = Path(args.output_raw)
    output.parent.mkdir(parents=True, exist_ok=True)
    rec_data.tofile(output)

    astra.algorithm.delete(alg_id)
    astra.data3d.delete(proj_id)
    astra.data3d.delete(rec_id)
    astra.clear()

    print(f"Saved raw float32 volume: {output}")
    print(f"Dimensions: width={args.vol_cols}, height={args.vol_rows}, slices={args.vol_slices}")


if __name__ == "__main__":
    main()
