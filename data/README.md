# CT Reconstruction Demo Projection Dataset v1

This release contains the complete projection sequence used to exercise the
reconstruction scripts in
[`xiaoze-research/CT-reconstruction`](https://github.com/xiaoze-research/CT-reconstruction).

## Contents

- `projections/` - 226 grayscale-compatible JPEG projection images.
- `manifest.csv` - filename, byte size, dimensions, and SHA-256 for every image.
- `LICENSE-DATA.md` - CC BY 4.0 data license and attribution instructions.

## Acquisition and reconstruction parameters

| Parameter | Value |
| --- | --- |
| Projection count | 226 |
| Image dimensions | 2048 x 2048 pixels |
| Acquisition indices | 129 through 579, step 2 |
| Angular range | 360 degrees |
| Detector pixel size | 0.011 mm |
| Source-to-object distance (SOD) | 70.0 mm |
| Object-to-detector distance (ODD) | 42.0 mm |
| Image format | 8-bit-compatible JPEG |

Projection angles are assigned as k x (360/226) degrees for k = 0..225 in
acquisition order (endpoint excluded, i.e. ~1.5929 degrees per selected frame;
the hypothetical next frame would coincide with 0 degrees).

The public files contain no EXIF metadata. Flat-field and dark-field reference
images are not included. A prior local reconstruction used a horizontal center
correction of approximately +30 detector pixels; the public command below does
not apply that correction automatically, so centering and artifact levels may
differ.

## Example reconstruction

From the repository root, after extracting this archive:

```powershell
python src\astra_cone_beam_fdk_cuda.py `
  --input-dir <EXTRACTED_DIR>\demo-data-v1\projections `
  --output-raw outputs\demo_fdk_256.raw `
  --start-number 129 `
  --stop-number 579 `
  --number-step 2 `
  --degrees 360 `
  --pixel-size-mm 0.011 `
  --sod-mm 70 `
  --odd-mm 42 `
  --vol-cols 256 `
  --vol-rows 256 `
  --vol-slices 256 `
  --epsilon 0.00390625
```

The expected output is a little-endian float32 RAW volume with dimensions
`256 x 256 x 256`. This dataset is intended for software demonstration and
method development, not clinical or diagnostic use.

## Integrity

Verify individual projections against `manifest.csv`. The release page also
publishes the SHA-256 checksum of the complete ZIP archive.

