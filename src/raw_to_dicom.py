"""Convert an 8-bit RAW volume to a DICOM series."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import SimpleITK as sitk


def parse_triplet(text: str, cast):
    parts = [cast(p.strip()) for p in text.replace("x", ",").split(",")]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("Use X,Y,Z")
    return parts[0], parts[1], parts[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-raw", required=True)
    parser.add_argument("--output-dir", default="outputs/dicom_series")
    parser.add_argument("--dims", type=lambda s: parse_triplet(s, int), required=True)
    parser.add_argument("--spacing", type=lambda s: parse_triplet(s, float), default=(0.011, 0.011, 0.011))
    parser.add_argument("--patient-name", default="Industrial Object")
    parser.add_argument("--patient-id", default="Case_001")
    parser.add_argument("--series-description", default="CT Reconstruction")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    width, height, slices = args.dims
    raw_data = np.fromfile(args.input_raw, dtype=np.uint8)
    expected = width * height * slices
    if raw_data.size != expected:
        raise ValueError(f"Voxel count mismatch: expected {expected}, found {raw_data.size}")

    volume = raw_data.reshape((slices, height, width)).astype(np.uint16) * 257
    image = sitk.GetImageFromArray(volume)
    image.SetSpacing(args.spacing)
    image.SetOrigin((0.0, 0.0, 0.0))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()

    timestamp = time.strftime("%Y%m%d%H%M%S")
    series_uid = f"1.2.826.0.1.3680043.2.1125.{timestamp}"
    series_tags = [
        ("0008|0060", "CT"),
        ("0010|0010", args.patient_name),
        ("0010|0020", args.patient_id),
        ("0020|000e", series_uid),
        ("0008|103e", args.series_description),
        ("0028|0100", "16"),
        ("0028|0101", "16"),
        ("0028|0102", "15"),
        ("0028|0103", "0"),
    ]

    for i in range(slices):
        slice_img = image[:, :, i]
        z_pos = i * args.spacing[2]
        slice_img.SetOrigin((0.0, 0.0, z_pos))
        for tag, value in series_tags:
            slice_img.SetMetaData(tag, value)
        slice_img.SetMetaData("0020|0032", f"0.0\\0.0\\{z_pos}")
        slice_img.SetMetaData("0020|0013", str(i + 1))
        writer.SetFileName(str(output_dir / f"slice_{i:04d}.dcm"))
        writer.Execute(slice_img)

    print(f"Saved DICOM series: {output_dir}")


if __name__ == "__main__":
    main()
