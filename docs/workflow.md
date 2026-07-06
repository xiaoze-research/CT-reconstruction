# CT Workflow

1. Place projection images in `data/projections/`.
2. Run either the CPU FBP script or an ASTRA CUDA reconstruction script.
3. Write generated volumes or slices to `outputs/`.
4. Convert reconstructed float RAW volumes to uint8 only when needed for
   visualization or downstream DICOM export.
5. Convert uint8 RAW volumes to DICOM with explicit dimensions and spacing.

The repository intentionally does not include dataset-specific scan ranges,
geometry values, image dimensions, spacing, or DICOM metadata. Set those values
explicitly from your own acquisition records when running the scripts.
