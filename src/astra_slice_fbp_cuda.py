"""GPU slice-by-slice FBP reconstruction using ASTRA FBP_CUDA."""

from __future__ import annotations

import argparse
import time

import astra
import numpy as np
from PIL import Image

from projection_io import ensure_dir, load_projection_stack


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="Directory of projection images")
    parser.add_argument("--output-dir", default="outputs/gpu_slices")
    parser.add_argument("--start-number", type=int, default=None)
    parser.add_argument("--stop-number", type=int, default=None)
    parser.add_argument("--number-step", type=int, default=1)
    parser.add_argument("--degrees", type=float, default=360.0)
    parser.add_argument("--slice-start", type=int, default=0)
    parser.add_argument("--slice-stop", type=int, default=None)
    parser.add_argument("--epsilon", type=float, default=1e-5)
    parser.add_argument("--invert", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = ensure_dir(args.output_dir)
    projections, paths = load_projection_stack(
        input_dir=args.input_dir,
        start_number=args.start_number,
        stop_number=args.stop_number,
        number_step=args.number_step,
        log_transform=True,
        invert=args.invert,
        epsilon=args.epsilon,
    )
    n_angles, n_rows, n_cols = projections.shape
    slice_stop = n_rows if args.slice_stop is None else min(args.slice_stop, n_rows)
    angles = np.linspace(0, np.deg2rad(args.degrees), n_angles, endpoint=False)

    vol_geom = astra.create_vol_geom(n_cols, n_cols)
    proj_geom = astra.create_proj_geom("parallel", 1.0, n_cols, angles)

    print(f"Loaded {len(paths)} projections with shape {n_cols}x{n_rows}")
    print(f"Writing slices [{args.slice_start}, {slice_stop}) to {output_dir}")
    t0 = time.time()

    for z in range(args.slice_start, slice_stop):
        sinogram = projections[:, z, :]
        sid = astra.data2d.create("-sino", proj_geom, sinogram)
        vid = astra.data2d.create("-vol", vol_geom)

        cfg = astra.astra_dict("FBP_CUDA")
        cfg["ProjectionDataId"] = sid
        cfg["ReconstructionDataId"] = vid
        cfg["FilterType"] = "ram-lak"

        alg_id = astra.algorithm.create(cfg)
        astra.algorithm.run(alg_id)
        reco_slice = astra.data2d.get(vid)

        s_min, s_max = float(reco_slice.min()), float(reco_slice.max())
        rescaled = (reco_slice - s_min) / (s_max - s_min + 1e-7) * 255.0
        Image.fromarray(rescaled.astype(np.uint8)).save(output_dir / f"slice_{z:04d}.tif")

        astra.algorithm.delete(alg_id)
        astra.data2d.delete(sid)
        astra.data2d.delete(vid)

        done = z - args.slice_start + 1
        if done % 100 == 0 or z == slice_stop - 1:
            print(f"Slice {done}/{slice_stop - args.slice_start}, elapsed {time.time() - t0:.1f}s")

    print(f"Finished in {time.time() - t0:.2f}s")


if __name__ == "__main__":
    main()
