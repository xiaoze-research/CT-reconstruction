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

The scripts do not embed acquisition geometry, scan range, image dimensions, or
metadata defaults. Replace each placeholder with values from your own dataset.

CPU filtered back-projection:

```powershell
python src\ct_fbp_skimage.py `
  --input-dir <PROJECTION_DIR> `
  --output <OUTPUT_NPY> `
  --start-number <FIRST_INDEX> `
  --stop-number <LAST_INDEX> `
  --number-step <INDEX_STEP> `
  --degrees <SCAN_DEGREES> `
  --layer-mode <LAYER_MODE> `
  --filter-name <FILTER_NAME> `
  --epsilon <EPSILON> `
  --progress-every <PROGRESS_INTERVAL>
```

ASTRA CUDA slice-by-slice FBP:

```powershell
python src\astra_slice_fbp_cuda.py `
  --input-dir <PROJECTION_DIR> `
  --output-dir <OUTPUT_SLICE_DIR> `
  --start-number <FIRST_INDEX> `
  --stop-number <LAST_INDEX> `
  --number-step <INDEX_STEP> `
  --degrees <SCAN_DEGREES> `
  --slice-start <FIRST_SLICE> `
  --slice-stop <LAST_SLICE> `
  --epsilon <EPSILON>
```

ASTRA CUDA cone-beam FDK:

```powershell
python src\astra_cone_beam_fdk_cuda.py `
  --input-dir <PROJECTION_DIR> `
  --output-raw <OUTPUT_RAW> `
  --start-number <FIRST_INDEX> `
  --stop-number <LAST_INDEX> `
  --number-step <INDEX_STEP> `
  --degrees <SCAN_DEGREES> `
  --pixel-size-mm <PIXEL_SIZE_MM> `
  --sod-mm <SOURCE_TO_OBJECT_DISTANCE_MM> `
  --odd-mm <OBJECT_TO_DETECTOR_DISTANCE_MM> `
  --vol-cols <VOLUME_COLUMNS> `
  --vol-rows <VOLUME_ROWS> `
  --vol-slices <VOLUME_SLICES> `
  --epsilon <EPSILON>
```

Convert a RAW volume to uint8:

```powershell
python src\raw_to_uint8.py `
  --input-raw <INPUT_RAW> `
  --output-raw <OUTPUT_UINT8_RAW> `
  --dims <WIDTH,HEIGHT,SLICES> `
  --source-dtype <SOURCE_DTYPE> `
  --lower-percentile <LOWER_PERCENTILE> `
  --upper-percentile <UPPER_PERCENTILE>
```

Convert an 8-bit RAW volume to DICOM:

```powershell
python src\raw_to_dicom.py `
  --input-raw <INPUT_UINT8_RAW> `
  --output-dir <OUTPUT_DICOM_DIR> `
  --dims <WIDTH,HEIGHT,SLICES> `
  --spacing <SPACING_X,SPACING_Y,SPACING_Z> `
  --patient-name <DICOM_PATIENT_NAME> `
  --patient-id <DICOM_PATIENT_ID> `
  --series-description <DICOM_SERIES_DESCRIPTION>
```

## Data policy

Do not commit experimental projection images, DICOM files, RAW volumes, vendor
archives, literature PDFs/CAJ files, or manuscript drafts. Share large datasets
through a data repository or release asset after checking ownership and privacy.
