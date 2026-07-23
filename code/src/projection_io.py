"""Projection image loading utilities for CT reconstruction scripts."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def find_projection_files(
    input_dir: str | Path,
    start_number: int,
    stop_number: int,
    number_step: int,
) -> list[Path]:
    """Find projection images by numeric acquisition sequence.

    Each requested number must appear in the filename as a standalone digit
    run (not embedded in a longer number), so an index such as 173 does not
    match a timestamp such as "173600" elsewhere in the name. Zero-padded
    naming schemes (e.g. "slice_0173") are also recognized. A number that
    matches several files is ambiguous and raises an error, as does a number
    that matches none: silently skipping a projection would shift the angular
    positions of every following projection during reconstruction.
    """
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")

    files = sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    selected: list[Path] = []
    missing: list[int] = []
    for number in range(start_number, stop_number + 1, number_step):
        pattern = re.compile(rf"(?<!\d)0*{number}(?!\d)")
        matches = [p for p in files if pattern.search(p.name)]
        if len(matches) > 1:
            names = ", ".join(p.name for p in matches[:5])
            raise ValueError(
                f"Projection number {number} is ambiguous; it matches "
                f"{len(matches)} files: {names}"
            )
        if matches:
            selected.append(matches[0])
        else:
            missing.append(number)

    if missing:
        shown = ", ".join(str(n) for n in missing[:10])
        suffix = ", ..." if len(missing) > 10 else ""
        raise ValueError(
            f"{len(missing)} requested projection numbers matched no file "
            f"({shown}{suffix}); a gap would corrupt the angle assignment"
        )

    return selected


def load_projection_stack(
    input_dir: str | Path,
    start_number: int,
    stop_number: int,
    number_step: int,
    log_transform: bool,
    invert: bool,
    epsilon: float,
    row_start: int | None = None,
    row_stop: int | None = None,
) -> tuple[np.ndarray, list[Path]]:
    """Load grayscale projection images as [angle, row, column].

    ``row_start``/``row_stop`` optionally crop each projection to a detector-row
    window at load time, so callers that reconstruct only a few slices do not
    need the full-resolution stack in memory.
    """
    paths = find_projection_files(
        input_dir=input_dir,
        start_number=start_number,
        stop_number=stop_number,
        number_step=number_step,
    )
    if not paths:
        raise ValueError(f"No projection images found in {input_dir}")

    first = Image.open(paths[0]).convert("L")
    width, height = first.size
    r0 = 0 if row_start is None else max(0, row_start)
    r1 = height if row_stop is None else min(height, row_stop)
    if r0 >= r1:
        raise ValueError(f"Empty row window [{r0}, {r1}) for image height {height}")
    stack = np.zeros((len(paths), r1 - r0, width), dtype=np.float32)

    for i, path in enumerate(paths):
        arr = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
        if arr.shape != (height, width):
            raise ValueError(
                f"Projection size mismatch in {path}: "
                f"expected {(height, width)}, got {arr.shape}"
            )
        arr = arr[r0:r1]
        if invert:
            arr = 255.0 - arr
        intensity = arr / 255.0
        stack[i] = -np.log(intensity + epsilon) if log_transform else intensity

    return stack, paths


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    root = Path(path)
    root.mkdir(parents=True, exist_ok=True)
    return root
