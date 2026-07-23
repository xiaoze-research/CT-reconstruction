# Source File Notes

This upload-ready repository was curated from the local `CT` working folder.
The public version keeps algorithmic logic while removing hard-coded local
paths and excluding data-heavy or copyrighted artifacts.

Original local scripts used as references:

- `ct_reconstruction.py` - CPU scikit-image reconstruction logic.
- `GPUpingxing.py` - ASTRA CUDA slice-by-slice FBP logic.
- `zhuishu.py` and later variants - ASTRA cone-beam FDK logic.
- `zhuanhuan.py` - float RAW to uint8 RAW conversion logic.
- `DICOM2.py` - uint8 RAW to DICOM series export logic.

Excluded local artifacts:

- RAW reconstruction volumes.
- DICOM series.
- TIFF/JPEG projection and output images.
- vendor archives.
- local IDE files.
- literature PDF/CAJ files.
- Word workflow drafts.
