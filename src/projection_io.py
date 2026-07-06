"""Projection image loading utilities for CT reconstruction scripts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def find_projection_files(
    input_dir: str | Path,
    start_number: int | None = None,
    stop_number: int | None = None,
    number_step: int = 1,
) -> list[Path]:
    """Find projection images, optionally by numeric acquisition sequence."""
    root = Path(input_dir)
    if not root.exists():
        raise FileNotFoundError(f"Input directory does not exist: {root}")

    files = sorted(
        p for p in root.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )
    if start_number is None or stop_number is None:
        return files

    selected: list[Path] = []
    for number in range(start_number, stop_number + 1, number_step):
        token = str(number)
        match = next((p for p in files if token in p.name), None)
        if match is not None:
            selected.append(match)

    return selected


def load_projection_stack(
    input_dir: str | Path,
    start_number: int | None = None,
    stop_number: int | None = None,
    number_step: int = 1,
    log_transform: bool = True,
    invert: bool = False,
    epsilon: float = 1e-5,
) -> tuple[np.ndarray, list[Path]]:
    """Load grayscale projection images as [angle, row, column]."""
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
    stack = np.zeros((len(paths), height, width), dtype=np.float32)

    for i, path in enumerate(paths):
        arr = np.asarray(Image.open(path).convert("L"), dtype=np.float32)
        if arr.shape != (height, width):
            raise ValueError(
                f"Projection size mismatch in {path}: "
                f"expected {(height, width)}, got {arr.shape}"
            )
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
