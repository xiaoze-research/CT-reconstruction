"""Convert a float RAW CT volume to an 8-bit RAW volume."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def parse_dims(text: str) -> tuple[int, int, int]:
    parts = [int(p.strip()) for p in text.replace("x", ",").split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Use WIDTH,HEIGHT,SLICES")
    return parts[0], parts[1], parts[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-raw", required=True)
    parser.add_argument("--output-raw", required=True)
    parser.add_argument("--dims", type=parse_dims, required=True, help="Use WIDTH,HEIGHT,SLICES")
    parser.add_argument("--source-dtype", required=True)
    parser.add_argument("--invert", action="store_true")
    parser.add_argument("--auto-invert", action="store_true")
    parser.add_argument("--lower-percentile", type=float, required=True)
    parser.add_argument("--upper-percentile", type=float, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = np.fromfile(args.input_raw, dtype=np.dtype(args.source_dtype))
    expected = args.dims[0] * args.dims[1] * args.dims[2]
    if data.size != expected:
        raise ValueError(f"Voxel count mismatch: expected {expected}, found {data.size}")

    data = data.astype(np.float32, copy=False)
    if args.auto_invert:
        bg_mean = float(np.mean(data[: min(1000, data.size)]))
        obj_mean = float(np.mean(data))
        if bg_mean > obj_mean:
            data = float(data.max()) - data
            print("Applied auto inversion")
    elif args.invert:
        data = float(data.max()) - data
        print("Applied inversion")

    low = np.percentile(data, args.lower_percentile)
    high = np.percentile(data, args.upper_percentile)
    clipped = np.clip(data, low, high)
    scaled = (clipped - low) / (high - low + 1e-12) * 255.0
    output_data = scaled.astype(np.uint8)

    output = Path(args.output_raw)
    output.parent.mkdir(parents=True, exist_ok=True)
    output_data.tofile(output)
    print(f"Saved uint8 raw volume: {output}")
    print(f"Dimensions: width={args.dims[0]}, height={args.dims[1]}, slices={args.dims[2]}")


if __name__ == "__main__":
    main()
