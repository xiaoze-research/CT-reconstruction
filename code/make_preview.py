"""Render preview images and a run summary for the Code Ocean capsule.

This helper is capsule glue, not part of the reusable reconstruction library.
It turns whatever ``run`` produced (a float32 RAW volume from the GPU FDK path,
or a stack of central slices from the CPU FBP path) into human-readable PNGs and
a ``RESULTS.md`` note so the reproducible run leaves inspectable outputs behind.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _normalize(slice_2d: np.ndarray) -> np.ndarray:
    finite = slice_2d[np.isfinite(slice_2d)]
    if finite.size == 0:
        return np.zeros_like(slice_2d, dtype=np.uint8)
    low, high = np.percentile(finite, [1.0, 99.0])
    if high <= low:
        low, high = float(finite.min()), float(finite.max()) + 1e-9
    scaled = np.clip((slice_2d - low) / (high - low), 0.0, 1.0)
    return (scaled * 255.0).astype(np.uint8)


def _save_gray(slice_2d: np.ndarray, path: Path, title: str) -> None:
    fig, axis = plt.subplots(figsize=(5, 5))
    axis.imshow(_normalize(slice_2d), cmap="gray")
    axis.set_title(title, fontsize=10)
    axis.axis("off")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def preview_raw(raw_path: Path, dims: tuple[int, int, int], out_prefix: Path) -> list[Path]:
    """Save orthogonal central slices (axial/coronal/sagittal) of a RAW volume."""
    volume = np.fromfile(raw_path, dtype=np.float32)
    expected = int(np.prod(dims))
    if volume.size != expected:
        raise ValueError(f"Voxel count mismatch: expected {expected}, found {volume.size}")
    volume = volume.reshape(dims)  # (Z, Y, X)
    zc, yc, xc = (d // 2 for d in dims)

    written: list[Path] = []
    planes = [
        (volume[zc, :, :], "axial", f"Axial z={zc}"),
        (volume[:, yc, :], "coronal", f"Coronal y={yc}"),
        (volume[:, :, xc], "sagittal", f"Sagittal x={xc}"),
    ]
    for data, tag, title in planes:
        path = out_prefix.with_name(f"{out_prefix.name}_{tag}.png")
        _save_gray(data, path, title)
        written.append(path)

    # Combined MPR figure.
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for axis, (data, _, title) in zip(axes, planes):
        axis.imshow(_normalize(data), cmap="gray")
        axis.set_title(title, fontsize=11)
        axis.axis("off")
    mpr_path = out_prefix.with_name(f"{out_prefix.name}_mpr.png")
    fig.suptitle("Cone-beam FDK reconstruction — orthogonal central slices", fontsize=12)
    fig.savefig(mpr_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    written.append(mpr_path)
    return written


def preview_npy(npy_path: Path, out_prefix: Path) -> list[Path]:
    """Save the central slice and a montage from a stack of reconstructed slices."""
    stack = np.load(npy_path)  # (n_slices, H, W)
    if stack.ndim != 3 or stack.shape[0] == 0:
        raise ValueError(f"Unexpected slice-stack shape: {stack.shape}")
    mid = stack.shape[0] // 2

    written: list[Path] = []
    center_path = out_prefix.with_name(f"{out_prefix.name}_slice.png")
    _save_gray(stack[mid], center_path, f"Central slice {mid} / {stack.shape[0]}")
    written.append(center_path)

    n_show = min(4, stack.shape[0])
    picks = np.linspace(0, stack.shape[0] - 1, n_show).astype(int)
    fig, axes = plt.subplots(1, n_show, figsize=(5 * n_show, 5))
    axes = np.atleast_1d(axes)
    for axis, idx in zip(axes, picks):
        axis.imshow(_normalize(stack[idx]), cmap="gray")
        axis.set_title(f"slice {idx}", fontsize=11)
        axis.axis("off")
    montage_path = out_prefix.with_name(f"{out_prefix.name}_montage.png")
    fig.suptitle("CPU FBP central slices (parallel-beam approximation)", fontsize=12)
    fig.savefig(montage_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    written.append(montage_path)
    return written


def write_summary(
    results_dir: Path,
    mode: str,
    artifacts: list[Path],
    volume_file: Path,
    dims: tuple[int, int, int] | None,
) -> None:
    lines = ["# Reproducible run results", ""]
    if mode == "fdk_gpu":
        size = " x ".join(str(d) for d in dims) if dims else "see run log"
        lines += [
            "Reconstruction: ASTRA cone-beam **FDK_CUDA** (GPU).",
            "",
            f"- `{volume_file.name}` — {size} little-endian float32 volume.",
            "- `*_axial.png`, `*_coronal.png`, `*_sagittal.png` — orthogonal central slices.",
            "- `*_mpr.png` — combined multiplanar view.",
            "",
            "Reconstruction settings (filter, detector-centre correction, volume size)",
            "are printed in the run log; the defaults in `code/run` reproduce the",
            "publication reconstruction.",
        ]
    else:
        lines += [
            "Reconstruction: scikit-image **filtered back-projection** on CPU.",
            "",
            f"- `{volume_file.name}` — stack of central slices (float32).",
            "- `*_slice.png` — central slice preview.",
            "- `*_montage.png` — several central slices.",
            "",
            "> Note: the CPU path uses a parallel-beam filtered back-projection as a",
            "> GPU-free fallback, so geometry and artefact levels differ from the",
            "> cone-beam FDK result. Run on a GPU machine (or set `RECON_MODE=fdk_gpu`)",
            "> to reproduce the exact cone-beam volume.",
        ]
    lines += ["", "## Generated files", ""]
    for path in artifacts:
        lines.append(f"- `{path.name}`")
    lines.append("")
    (results_dir / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def parse_dims(text: str) -> tuple[int, int, int]:
    parts = [int(p.strip()) for p in text.replace("x", ",").split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Use Z,Y,X")
    return parts[0], parts[1], parts[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["fdk_gpu", "fbp_cpu"])
    parser.add_argument("--raw", type=Path)
    parser.add_argument("--dims", type=parse_dims)
    parser.add_argument("--npy", type=Path)
    parser.add_argument("--out-prefix", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()

    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "fdk_gpu":
        if args.raw is None or args.dims is None:
            parser.error("--raw and --dims are required for fdk_gpu mode")
        artifacts = preview_raw(args.raw, args.dims, args.out_prefix)
        volume_file = args.raw
    else:
        if args.npy is None:
            parser.error("--npy is required for fbp_cpu mode")
        artifacts = preview_npy(args.npy, args.out_prefix)
        volume_file = args.npy

    write_summary(args.results, args.mode, artifacts, volume_file, args.dims)
    for path in artifacts:
        print(f"Saved preview: {path}")
    print(f"Saved summary: {args.results / 'RESULTS.md'}")


if __name__ == "__main__":
    main()
