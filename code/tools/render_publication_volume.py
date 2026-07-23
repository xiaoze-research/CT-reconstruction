"""Render an annotated publication-style view of a reconstructed RAW volume."""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import matplotlib
import numpy as np
import pyvista as pv
import vtk
from matplotlib import pyplot as plt
from matplotlib.colorbar import ColorbarBase
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle
from scipy import ndimage


matplotlib.use("Agg")


BACKGROUND = "#c8c8c8"
SHELL_COLOR = "#176f79"
DEFECT_COLOR = "#b5bf3f"
ANNOTATION_COLOR = "#d7191c"


def parse_dims(value: str) -> tuple[int, int, int]:
    parts = tuple(int(part.strip()) for part in value.split(","))
    if len(parts) != 3 or any(part <= 0 for part in parts):
        raise argparse.ArgumentTypeError("dimensions must be Z,Y,X positive integers")
    return parts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-raw", type=Path, required=True)
    parser.add_argument("--dims", type=parse_dims, required=True, help="Z,Y,X")
    parser.add_argument("--output-prefix", type=Path, required=True)
    parser.add_argument("--outer-threshold", type=float, required=True)
    parser.add_argument("--defect-percentile", type=float, required=True)
    parser.add_argument("--erosion-iterations", type=int, required=True)
    parser.add_argument("--spacing-mm", type=float, required=True)
    return parser.parse_args()


def make_grid(array_zyx: np.ndarray, spacing_mm: float, name: str) -> pv.ImageData:
    array_xyz = np.transpose(array_zyx, (2, 1, 0))
    grid = pv.ImageData(dimensions=array_xyz.shape)
    grid.spacing = (spacing_mm, spacing_mm, spacing_mm)
    grid.point_data[name] = np.ascontiguousarray(array_xyz).ravel(order="F")
    return grid


def largest_component(mask: np.ndarray) -> tuple[np.ndarray, int]:
    labels, count = ndimage.label(mask)
    if count == 0:
        raise ValueError("No internal high-density candidate was found")
    sizes = np.bincount(labels.ravel())
    label = int(np.argmax(sizes[1:]) + 1)
    component = labels == label
    return component, int(sizes[label])


def project_bounds(
    renderer: pv.Renderer,
    bounds: tuple[float, float, float, float, float, float],
    image_height: int,
) -> tuple[float, float, float, float]:
    coordinate = vtk.vtkCoordinate()
    coordinate.SetCoordinateSystemToWorld()
    points: list[tuple[float, float]] = []
    for x, y, z in product(
        (bounds[0], bounds[1]),
        (bounds[2], bounds[3]),
        (bounds[4], bounds[5]),
    ):
        coordinate.SetValue(x, y, z)
        display_x, display_y = coordinate.GetComputedDoubleDisplayValue(renderer)
        points.append((float(display_x), float(image_height - display_y)))
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def render_base(
    density: np.ndarray,
    object_mask: np.ndarray,
    interior: np.ndarray,
    defect: np.ndarray,
    spacing_mm: float,
    output_path: Path,
) -> tuple[tuple[float, float, float, float], tuple[float, float]]:
    object_grid = make_grid(object_mask.astype(np.float32), spacing_mm, "mask")
    shell = object_grid.contour([0.5], scalars="mask").smooth(
        n_iter=25,
        relaxation_factor=0.08,
    )

    defect_grid = make_grid(defect.astype(np.float32), spacing_mm, "mask")
    defect_mesh = defect_grid.contour([0.5], scalars="mask").smooth(
        n_iter=20,
        relaxation_factor=0.08,
    )

    internal_density = np.where(interior, density, 0.0).astype(np.float32)
    density_grid = make_grid(internal_density, spacing_mm, "density")
    finite_values = density[interior]
    low, high = (float(value) for value in np.percentile(finite_values, [2.0, 99.8]))

    opacity = np.zeros(256, dtype=float)
    opacity[65:150] = np.linspace(0.0, 0.035, 85)
    opacity[150:220] = np.linspace(0.035, 0.12, 70)
    opacity[220:] = np.linspace(0.12, 0.28, 36)
    colormap = LinearSegmentedColormap.from_list(
        "ct_reference",
        [DEFECT_COLOR, "#176f79", "#d9e1e3"],
    )

    width, height = 900, 1100
    plotter = pv.Plotter(off_screen=True, window_size=(width, height))
    plotter.set_background(BACKGROUND)
    plotter.enable_anti_aliasing("ssaa")
    plotter.add_mesh(
        shell,
        color=SHELL_COLOR,
        opacity=0.25,
        smooth_shading=True,
        ambient=0.35,
        diffuse=0.65,
        specular=0.18,
        specular_power=18,
    )
    plotter.add_volume(
        density_grid,
        scalars="density",
        cmap=colormap,
        clim=(low, high),
        opacity=opacity,
        shade=True,
        ambient=0.28,
        diffuse=0.62,
        specular=0.12,
        blending="composite",
        show_scalar_bar=False,
    )
    plotter.add_mesh(
        defect_mesh,
        color=DEFECT_COLOR,
        opacity=0.92,
        smooth_shading=True,
        ambient=0.45,
        diffuse=0.75,
        specular=0.22,
        specular_power=22,
    )

    bounds = shell.bounds
    center = np.array(shell.center)
    size_x = bounds[1] - bounds[0]
    size_y = bounds[3] - bounds[2]
    size_z = bounds[5] - bounds[4]
    distance = max(size_x, size_y, size_z) * 3.2
    plotter.camera_position = [
        (
            center[0] + 0.95 * distance,
            center[1] - distance,
            center[2] + 0.28 * distance,
        ),
        tuple(center),
        (0.0, 0.0, 1.0),
    ]
    plotter.camera.zoom(1.42)
    plotter.render()

    defect_bounds = tuple(float(value) for value in defect_mesh.bounds)
    projected_bounds = project_bounds(
        plotter.renderer,
        defect_bounds,
        image_height=height,
    )
    plotter.screenshot(str(output_path))
    plotter.close()
    return projected_bounds, (low, high)


def annotate(
    base_path: Path,
    output_path: Path,
    projected_bounds: tuple[float, float, float, float],
    scalar_range: tuple[float, float],
    show_defect: bool,
) -> None:
    image = plt.imread(base_path)
    image_height, image_width = image.shape[:2]
    fig = plt.figure(figsize=(7.0, 8.2), facecolor=BACKGROUND)
    grid = fig.add_gridspec(1, 2, width_ratios=(5.4, 0.55), wspace=0.12)
    axis = fig.add_subplot(grid[0, 0])
    axis.imshow(image)
    axis.set_xlim(0, image_width)
    axis.set_ylim(image_height, 0)
    axis.axis("off")
    axis.text(
        0.035,
        0.965,
        "j",
        transform=axis.transAxes,
        fontsize=22,
        fontweight="bold",
        va="top",
        color="black",
    )

    if show_defect:
        x0, y0, x1, y1 = projected_bounds
        padding_x = max(16.0, (x1 - x0) * 0.16)
        padding_y = max(18.0, (y1 - y0) * 0.10)
        rectangle_x = max(0.0, x0 - padding_x)
        rectangle_y = max(0.0, y0 - padding_y)
        rectangle_width = min(image_width - rectangle_x, x1 - x0 + 2.0 * padding_x)
        rectangle_height = min(
            image_height - rectangle_y,
            y1 - y0 + 2.0 * padding_y,
        )
        axis.add_patch(
            Rectangle(
                (rectangle_x, rectangle_y),
                rectangle_width,
                rectangle_height,
                fill=False,
                edgecolor=ANNOTATION_COLOR,
                linewidth=2.2,
                linestyle=(0, (3, 3)),
            )
        )
        axis.text(
            rectangle_x,
            min(image_height - 6.0, rectangle_y + rectangle_height + 32.0),
            "Defect",
            color=ANNOTATION_COLOR,
            fontsize=18,
            ha="left",
            va="top",
        )

    color_axis = fig.add_subplot(grid[0, 1])
    colormap = LinearSegmentedColormap.from_list(
        "ct_reference",
        [DEFECT_COLOR, "#176f79", "#d9e1e3"],
    )
    colorbar = ColorbarBase(
        color_axis,
        cmap=colormap,
        norm=Normalize(vmin=scalar_range[0], vmax=scalar_range[1]),
        orientation="vertical",
    )
    colorbar.set_ticks([])
    colorbar.outline.set_linewidth(1.5)
    color_axis.set_ylabel("Pixel value", fontsize=18, rotation=90, labelpad=12)
    color_axis.text(
        0.5,
        1.025,
        "High",
        transform=color_axis.transAxes,
        ha="center",
        va="bottom",
        fontsize=17,
    )
    color_axis.text(
        0.5,
        -0.03,
        "Low",
        transform=color_axis.transAxes,
        ha="center",
        va="top",
        fontsize=17,
    )
    fig.savefig(output_path, dpi=220, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)


def main() -> None:
    args = parse_args()
    expected_values = int(np.prod(args.dims))
    expected_bytes = expected_values * np.dtype(np.float32).itemsize
    actual_bytes = args.input_raw.stat().st_size
    if actual_bytes != expected_bytes:
        raise ValueError(
            f"RAW size mismatch: expected {expected_bytes}, got {actual_bytes}"
        )

    raw = np.memmap(args.input_raw, dtype=np.float32, mode="r", shape=args.dims)
    density = float(np.max(raw)) - np.asarray(raw, dtype=np.float32)
    object_mask = density >= args.outer_threshold
    interior = ndimage.binary_erosion(
        object_mask,
        iterations=args.erosion_iterations,
    )
    if not interior.any():
        raise ValueError("Object threshold and erosion produced an empty interior")

    defect_threshold = float(
        np.percentile(density[interior], args.defect_percentile)
    )
    candidate_mask = interior & (density >= defect_threshold)
    defect, defect_voxels = largest_component(candidate_mask)
    defect = ndimage.binary_closing(defect, iterations=2)
    defect = ndimage.binary_dilation(defect, iterations=1)

    output_prefix = args.output_prefix
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    base_path = output_prefix.with_name(output_prefix.name + "_render.png")
    clean_path = output_prefix.with_name(output_prefix.name + "_clean.png")
    annotated_path = output_prefix.with_name(output_prefix.name + "_annotated.png")
    metadata_path = output_prefix.with_name(output_prefix.name + "_metadata.json")

    projected_bounds, scalar_range = render_base(
        density=density,
        object_mask=object_mask,
        interior=interior,
        defect=defect,
        spacing_mm=args.spacing_mm,
        output_path=base_path,
    )
    annotate(
        base_path=base_path,
        output_path=clean_path,
        projected_bounds=projected_bounds,
        scalar_range=scalar_range,
        show_defect=False,
    )
    annotate(
        base_path=base_path,
        output_path=annotated_path,
        projected_bounds=projected_bounds,
        scalar_range=scalar_range,
        show_defect=True,
    )

    coordinates = np.argwhere(defect)
    metadata = {
        "input_raw": str(args.input_raw),
        "dimensions_zyx": args.dims,
        "spacing_mm": args.spacing_mm,
        "outer_threshold": args.outer_threshold,
        "defect_percentile": args.defect_percentile,
        "defect_threshold": defect_threshold,
        "defect_voxels": defect_voxels,
        "defect_bounds_zyx": {
            "min": coordinates.min(axis=0).tolist(),
            "max": coordinates.max(axis=0).tolist(),
        },
        "scalar_range": scalar_range,
        "outputs": {
            "render": str(base_path),
            "clean": str(clean_path),
            "annotated": str(annotated_path),
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(metadata, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
