# Demo Projection Dataset

The complete projection sequence used to exercise the reconstruction scripts is
published separately from Git history:

- Release: [`demo-data-v1`](https://github.com/xiaoze-research/CT-reconstruction/releases/tag/demo-data-v1)
- Asset: [`ct-reconstruction-demo-data-v1.zip`](https://github.com/xiaoze-research/CT-reconstruction/releases/download/demo-data-v1/ct-reconstruction-demo-data-v1.zip)
- Archive size: 466,332,710 bytes (444.73 MiB)
- SHA-256: `ee10b7ce3e851f96d094a8c014096ad2a61b29a03c348fb5eaefe8d51025abba`
- Data license: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

The archive includes a per-image `manifest.csv`, dataset README, license notice,
and all 226 original projections. The images contain no EXIF metadata.

## Parameters

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
acquisition order (endpoint excluded, i.e. ~1.5929 degrees per selected frame).

Flat-field and dark-field reference images are not included. The original
reconstruction used a horizontal center correction of +30 detector pixels; the
quick-start command below does not apply it, so centering and artifact levels
may differ. The reconstruction scripts accept `--center-offset-px 30` (and
`--filter-type hann`) to reproduce the publication settings — the Code Ocean
capsule's `run` script applies both by default.

## Download and verify

```powershell
gh release download demo-data-v1 `
  --repo xiaoze-research/CT-reconstruction `
  --pattern ct-reconstruction-demo-data-v1.zip

Get-FileHash -Algorithm SHA256 ct-reconstruction-demo-data-v1.zip
```

The hash must match the SHA-256 value listed above.

## Reconstruct a 256-cubed volume

Extract the ZIP, install the repository requirements, and run:

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

The output is a little-endian float32 RAW volume with dimensions
`256 x 256 x 256`.

## Attribution

When redistributing or using the data, cite:

> xiaoze-research, "CT Reconstruction Demo Projection Dataset v1",
> `xiaoze-research/CT-reconstruction`, demo-data-v1.

The dataset is intended for software demonstration and method development, not
clinical or diagnostic use.
