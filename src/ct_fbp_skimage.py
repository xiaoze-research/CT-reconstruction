"""CPU filtered back-projection reconstruction from projection images."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from skimage.transform import iradon

from projection_io import load_projection_stack


def _layer_bounds(
    image_height: int,
    mode: str,
    center_window: int,
    layer_start: int | None,
    layer_stop: int | None,
) -> tuple[int, int]:
    if mode == "all":
        return 0, image_height
    if mode == "range":
        if layer_start is None or layer_stop is None:
            raise ValueError("--layer-start and --layer-stop are required for range mode")
        return max(0, layer_start), min(image_height, layer_stop)

    if center_window is None:
        raise ValueError("--center-window is required for center mode")

    half = center_window // 2
    center = image_height // 2
    return max(0, center - half), min(image_height, center + half)


def reconstruct_volume(args: argparse.Namespace) -> np.ndarray:
    projections, paths = load_projection_stack(
        input_dir=args.input_dir,
        start_number=args.start_number,
        stop_number=args.stop_number,
        number_step=args.number_step,
        log_transform=not args.no_log_transform,
        invert=args.invert,
        epsilon=args.epsilon,
    )
    n_angles, image_height, image_width = projections.shape
    theta = np.linspace(0.0, args.degrees, n_angles, endpoint=False)
    start, stop = _layer_bounds(
        image_height=image_height,
        mode=args.layer_mode,
        center_window=args.center_window,
        layer_start=args.layer_start,
        layer_stop=args.layer_stop,
    )

    print(f"Loaded {len(paths)} projections with shape {image_width}x{image_height}")
    print(f"Reconstructing layers [{start}, {stop}) using {args.filter_name} filter")

    reconstructed: list[np.ndarray] = []
    t0 = time.time()
    total = stop - start
    for index, z in enumerate(range(start, stop), start=1):
        sinogram = projections[:, z, :].T
        reco_slice = iradon(sinogram, theta=theta, filter_name=args.filter_name)
        reconstructed.append(reco_slice.astype(np.float32))
        if index % args.progress_every == 0 or index == total:
            print(f"Layer {index}/{total}, elapsed {time.time() - t0:.1f}s")

    return np.asarray(reconstructed, dtype=np.float32)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="Directory of projection images")
    parser.add_argument("--output", required=True)
    parser.add_argument("--start-number", type=int, required=True)
    parser.add_argument("--stop-number", type=int, required=True)
    parser.add_argument("--number-step", type=int, required=True)
    parser.add_argument("--degrees", type=float, required=True)
    parser.add_argument("--layer-mode", choices=["center", "range", "all"], required=True)
    parser.add_argument("--center-window", type=int)
    parser.add_argument("--layer-start", type=int)
    parser.add_argument("--layer-stop", type=int)
    parser.add_argument("--filter-name", required=True)
    parser.add_argument("--epsilon", type=float, required=True)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--no-log-transform", action="store_true")
    parser.add_argument("--show-preview", action="store_true")
    parser.add_argument("--progress-every", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    volume = reconstruct_volume(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.save(output, volume)
    print(f"Saved volume: {output} shape={volume.shape} dtype={volume.dtype}")

    if args.show_preview and volume.size:
        plt.figure(figsize=(6, 6))
        plt.imshow(volume[len(volume) // 2], cmap="gray")
        plt.axis("off")
        plt.show()


if __name__ == "__main__":
    main()
