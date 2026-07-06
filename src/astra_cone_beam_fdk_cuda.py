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
    parser.add_argument("--output-raw", default="outputs/cone_beam_reconstruction.raw")
    parser.add_argument("--start-number", type=int, default=None)
    parser.add_argument("--stop-number", type=int, default=None)
    parser.add_argument("--number-step", type=int, default=1)
    parser.add_argument("--degrees", type=float, default=360.0)
    parser.add_argument("--pixel-size-mm", type=float, default=0.011)
    parser.add_argument("--sod-mm", type=float, default=70.0, help="Source-to-object distance")
    parser.add_argument("--odd-mm", type=float, default=42.0, help="Object-to-detector distance")
    parser.add_argument("--vol-cols", type=int, default=800)
    parser.add_argument("--vol-rows", type=int, default=800)
    parser.add_argument("--vol-slices", type=int, default=300)
    parser.add_argument("--epsilon", type=float, default=1e-5)
    parser.add_argument("--invert", action="store_true")
    return parser.parse_args()


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

    dist_source_origin = args.sod_mm / args.pixel_size_mm
    dist_origin_det = args.odd_mm / args.pixel_size_mm
    print(f"Loaded {len(paths)} projections with shape {img_w}x{img_h}")
    print(f"SOD={dist_source_origin:.2f} px, ODD={dist_origin_det:.2f} px")

    proj_data_astra = np.ascontiguousarray(np.transpose(projections, (1, 0, 2)))
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
    vol_geom = astra.create_vol_geom(args.vol_cols, args.vol_rows, args.vol_slices)

    proj_id = astra.data3d.create("-proj3d", proj_geom, proj_data_astra)
    rec_id = astra.data3d.create("-vol", vol_geom)
    cfg = astra.astra_dict("FDK_CUDA")
    cfg["ProjectionDataId"] = proj_id
    cfg["ReconstructionDataId"] = rec_id

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
