# CT Workflow

1. Place projection images in `data/projections/`.
2. Run either the CPU FBP script or an ASTRA CUDA reconstruction script.
3. Write generated volumes or slices to `outputs/`.
4. Convert reconstructed float RAW volumes to uint8 only when needed for
   visualization or downstream DICOM export.
5. Convert uint8 RAW volumes to DICOM with explicit dimensions and spacing.

The original local workflow used sequence numbers from 129 to 579 with step 2,
360 degrees, 0.011 mm pixel spacing, 70 mm source-to-object distance, and
42 mm object-to-detector distance. These are now command-line parameters.
