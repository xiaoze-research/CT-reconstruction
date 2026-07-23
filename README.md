# CT Reconstruction — Code Ocean Capsule

Cone-beam / parallel-beam CT reconstruction pipeline for the
[`xiaoze-research/CT-reconstruction`](https://github.com/xiaoze-research/CT-reconstruction)
project, packaged as a Code Ocean capsule for one-click reproducible runs.

The capsule reconstructs a micro-CT projection sequence into a 3-D volume and
writes preview images plus a run summary to `/results`.

## What the reproducible run does

`code/run` selects a reconstruction path automatically:

| Environment | Path | Output |
| --- | --- | --- |
| **GPU** available (NVIDIA) | ASTRA cone-beam `FDK_CUDA`, Hann filter, +30 px detector-centre correction | `demo_fdk_800.raw` (800³ float32, ~2 GB) + orthogonal MPR PNGs |
| **CPU only** (fallback) | scikit-image filtered back-projection of the central slices | `demo_fbp_center.npy` + slice/montage PNGs |

The GPU defaults reproduce the reconstruction described in the manuscript
Methods: log-transformed absorbance projections, fixed detector-centre
correction, FDK with a Hann filter, and an 800 × 800 × 800-voxel volume at an
isotropic 11 µm voxel size. Optionally set `EXPORT_DICOM=1` to also export the
volume as a DICOM series with SimpleITK, matching the visualization step in the
Methods.

Environment-variable overrides:

| Variable | Default | Meaning |
| --- | --- | --- |
| `RECON_MODE` | `auto` | `fdk_gpu`, `fbp_cpu`, or `auto` (GPU detection) |
| `VOL_SIZE` | `800` | voxels per volume edge (e.g. `256` for a quick test) |
| `FILTER_TYPE` | `hann` | ASTRA FDK filter name |
| `CENTER_OFFSET_PX` | `30` | horizontal detector-centre correction; `0` disables |
| `EXPORT_DICOM` | `0` | `1` additionally writes `results/dicom/` (uint8, windowed) |

> The CPU fallback uses a **parallel-beam** filtered back-projection so the run
> always completes without a GPU. Its geometry and artefact levels differ from
> the physically correct cone-beam FDK result. Select a GPU machine (or set
> `RECON_MODE=fdk_gpu`) to reproduce the 800³ cone-beam volume described in the
> manuscript Methods.

## Capsule layout

```
LICENSE                    # MIT License for the software
code/                      # reconstruction source and the run entry point
  run                      # Code Ocean reproducible-run entry point
  make_preview.py          # renders result PNGs + RESULTS.md (capsule glue)
  src/                     # reusable, parameter-free library + CLIs
    projection_io.py       # projection discovery / loading
    ct_fbp_skimage.py      # CPU filtered back-projection (scikit-image)
    astra_slice_fbp_cuda.py    # GPU slice-by-slice FBP (ASTRA)
    astra_cone_beam_fdk_cuda.py# GPU cone-beam FDK (ASTRA)
    raw_to_uint8.py        # float RAW -> 8-bit RAW
    raw_to_dicom.py        # 8-bit RAW -> DICOM series
  tools/                   # optional 3-D publication renderer (pyvista/VTK)
  tests/                   # disclosure-policy checks + unit tests
  docs/                    # workflow, provenance, demo-data notes
  README.md, LICENSE       # code readme (parameter-free) and code license
data/                      # demo projections (mounted at /data at runtime)
  projections/             # 226 JPEG projections
  manifest.csv             # per-image SHA-256, size, dimensions
  README.md, LICENSE-DATA.md   # dataset notes and CC BY 4.0 license
environment/Dockerfile     # conda-based CPU+GPU environment
metadata/metadata.yml      # Code Ocean capsule metadata
results/                   # run outputs are written here
```

## Demo dataset (bundled)

The `data/` folder contains the complete published demo sequence, so the capsule
is self-contained.

| Parameter | Value |
| --- | --- |
| Projection count | 226 |
| Image dimensions | 2048 × 2048 pixels |
| Acquisition indices | 129 through 579, step 2 |
| Angular range | 360 degrees |
| Detector pixel size | 0.011 mm |
| Source-to-object distance (SOD) | 70.0 mm |
| Object-to-detector distance (ODD) | 42.0 mm |
| Detector-centre correction | +30 px (applied by `code/run`; set `CENTER_OFFSET_PX=0` to disable) |
| FDK filter | Hann |
| Output volume | 800 × 800 × 800 voxels, isotropic 11 µm |

These are exactly the values `code/run` passes to the reconstruction scripts and
match the manuscript Methods. Flat-field / dark-field references are not
included. The data is intended for software demonstration and method
development, not clinical or diagnostic use.

> `code/docs/demo_data.md` mirrors the GitHub release notes for the dataset,
> whose quick-start example reconstructs a smaller 256³ volume without the
> centre correction; the capsule's `code/run` supersedes that example and
> applies the full publication settings by default.

### Slimmer alternative: data as a Code Ocean data asset

The projections are ~470 MB (448 MiB). If you prefer to keep the capsule code small, delete
`data/projections/` before importing and instead attach the projections as a
Code Ocean **data asset**:

1. Create a data asset from
   [`ct-reconstruction-demo-data-v1.zip`](https://github.com/xiaoze-research/CT-reconstruction/releases/tag/demo-data-v1)
   (SHA-256 `ee10b7ce3e851f96d094a8c014096ad2a61b29a03c348fb5eaefe8d51025abba`).
2. Attach it to the capsule so its `projections/` folder is mounted under `/data`.

`code/run` reads `$DATA_DIR/projections` (default `/data/projections`), so no code
change is needed.

## Requirements

- CPU fallback: any Code Ocean machine (the loader crops projections to the
  reconstructed row window, so memory stays modest).
- GPU path: a machine type with an NVIDIA GPU (host driver ≥ 525 for the CUDA 12
  build). Recommended: ≥16 GB host RAM (peak ~8 GB while staging the projection
  stack) and ≥16 GB GPU memory — ASTRA ≥2.4 splits FDK execution automatically
  when data exceeds GPU memory, so smaller GPUs work but run slower. If memory
  is short, reduce `VOL_SIZE`.

Environment packages (see `environment/Dockerfile`): Python 3.10, `astra-toolbox`,
`numpy`, `pillow`, `scikit-image`, `matplotlib`, `SimpleITK`, `scipy`.

## Run it locally (outside Code Ocean)

```bash
cd code
DATA_DIR=../data RESULTS_DIR=../results RECON_MODE=fbp_cpu bash run
```

Set `RECON_MODE=fdk_gpu` on a CUDA machine to produce the full 800³ publication
volume (or e.g. `VOL_SIZE=256` for a faster, smaller test reconstruction).

## Individual tools

Every script is a standalone CLI with no embedded acquisition defaults — pass the
values for your own dataset. See [`code/README.md`](code/README.md) for the full
per-tool command reference and [`code/docs/`](code/docs/) for workflow and
provenance notes.

## Upload checklist

Before (or right after) importing into Code Ocean:

1. **Authorship is intentionally pseudonymous** (`xiaoze-research`) to keep the
   capsule anonymous during peer review; add the real author list and
   corresponding contact in `metadata/metadata.yml` after acceptance.
2. **The MIT copyright holder is pseudonymous** (`xiaoze-research`) for
   anonymous review. If the holder changes after acceptance, update the
   copyright notice in both `LICENSE` and `code/LICENSE`.
3. **Make the entry point executable** — Windows filesystems do not store the
   Unix executable bit. After import, either mark `code/run` as the "file to
   run" in the Code Ocean UI, or run `chmod +x /code/run` once in the capsule
   terminal. (For git-based imports: `git update-index --chmod=+x code/run`.)
4. **Pick a GPU machine type** for the reproducible run (or accept the CPU
   fallback), then run once and check `results/RESULTS.md`.

## Licensing and provenance

The CT reconstruction software is released under the
[MIT License](LICENSE), an
[Open Source Initiative (OSI)-approved](https://opensource.org/license/mit)
open-source license. A copy of the license is provided in the repository's
`LICENSE` file.

The bundled demonstration dataset is licensed separately under the Creative
Commons Attribution 4.0 International (CC BY 4.0) License; see
[`data/LICENSE-DATA.md`](data/LICENSE-DATA.md).

The reusable library and its documentation deliberately omit dataset-specific
acquisition parameters; those live with the demo dataset (`data/`), in
`code/run`, and in the dataset release notes `code/docs/demo_data.md`.
`code/tests/test_no_embedded_parameters.py` enforces this separation.
