# CT Reconstruction Algorithms

This repository contains cleaned CT reconstruction scripts derived from a local
experimental workflow. The upload-ready version keeps algorithm code only and
does not include raw scans, DICOM series, reconstructed volumes, literature
PDF/CAJ files, archives, or generated TIFF slices.

## Repository contents

- `src/projection_io.py` - projection-image discovery and loading utilities.
- `src/ct_fbp_skimage.py` - CPU filtered back-projection using scikit-image.
- `src/astra_slice_fbp_cuda.py` - GPU slice-by-slice FBP using ASTRA CUDA.
- `src/astra_cone_beam_fdk_cuda.py` - cone-beam FDK reconstruction using ASTRA CUDA.
- `src/raw_to_uint8.py` - convert float RAW volumes to 8-bit RAW volumes.
- `src/raw_to_dicom.py` - convert 8-bit RAW volumes to DICOM series.
- `data/` - place local input data here; files are ignored by Git.
- `outputs/` - generated outputs; files are ignored by Git.
- `docs/` - workflow and provenance notes.

## Install

ASTRA CUDA support is easiest to install with conda. The remaining packages are
listed in `requirements.txt`.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If `astra-toolbox` is not available through pip on your platform, install it in
a conda environment following the ASTRA documentation, then run these scripts
from that environment.

## Example commands

CPU filtered back-projection for the middle 100 layers:

```powershell
python src\ct_fbp_skimage.py `
  --input-dir data\projections `
  --output outputs\reconstructed_volume.npy `
  --start-number 129 `
  --stop-number 579 `
  --number-step 2
```

ASTRA CUDA slice-by-slice FBP:

```powershell
python src\astra_slice_fbp_cuda.py `
  --input-dir data\projections `
  --output-dir outputs\gpu_slices `
  --start-number 129 `
  --stop-number 579 `
  --number-step 2
```

ASTRA CUDA cone-beam FDK:

```powershell
python src\astra_cone_beam_fdk_cuda.py `
  --input-dir data\projections `
  --output-raw outputs\cone_beam_reconstruction.raw `
  --start-number 129 `
  --stop-number 579 `
  --number-step 2 `
  --pixel-size-mm 0.011 `
  --sod-mm 70 `
  --odd-mm 42 `
  --vol-cols 800 `
  --vol-rows 800 `
  --vol-slices 300
```

Convert a float32 RAW volume to uint8:

```powershell
python src\raw_to_uint8.py `
  --input-raw outputs\cone_beam_reconstruction.raw `
  --output-raw outputs\final_uint8_model.raw `
  --dims 800,800,300 `
  --auto-invert
```

Convert an 8-bit RAW volume to DICOM:

```powershell
python src\raw_to_dicom.py `
  --input-raw outputs\final_uint8_model.raw `
  --output-dir outputs\dicom_series `
  --dims 800,800,300 `
  --spacing 0.011,0.011,0.011
```

## Data policy

Do not commit experimental projection images, DICOM files, RAW volumes, vendor
archives, literature PDFs/CAJ files, or manuscript drafts. Share large datasets
through a data repository or release asset after checking ownership and privacy.
