# =============================================================================
# Code Ocean environment for the CT reconstruction capsule.
#
# One image serves both execution paths:
#   * CPU-only hosts  -> scikit-image filtered back-projection (default fallback)
#   * GPU hosts       -> ASTRA FDK_CUDA / FBP_CUDA cone-beam reconstruction
#
# ASTRA is installed from the astra-toolbox conda channel, which bundles the
# CUDA runtime libraries. The package imports on CPU-only machines; its CUDA
# algorithms run only when an NVIDIA GPU and driver are present, which is why
# `code/run` auto-detects the GPU and falls back to the CPU FBP when absent.
#
# Inside the Code Ocean environment editor you may instead start from a
# Code Ocean base image (e.g. registry.codeocean.com/codeocean/miniconda3:...)
# and add the same conda packages through the GUI. This Dockerfile is written to
# also build as-is with `docker build`.
# =============================================================================
FROM continuumio/miniconda3:24.9.2-0

# Keep conda quiet and deterministic.
ENV PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    CONDA_ALWAYS_YES=true

# Core reconstruction stack (CPU + GPU capable).
#
# Version notes:
#   * astra-toolbox >= 2.3.0 is REQUIRED: FilterType support for FDK_CUDA
#     (used by code/run via --filter-type hann) was added in 2.3.0.
#   * libastra is pinned to the cuda_12_0 variant explicitly — the channel
#     publishes many CUDA variants at equal build numbers, and an unpinned
#     solve picks one nondeterministically. CUDA 12 covers Pascal (GTX 10xx)
#     through Hopper GPUs and needs a host driver >= 525.
#   * 2.5.0 / Python 3.11 matches the configuration the capsule was tested with.
RUN conda install -n base \
        -c astra-toolbox -c nvidia -c conda-forge \
        python=3.11 \
        "astra-toolbox=2.5.0" \
        "libastra=2.5.0=cuda_12_0" \
        "numpy>=1.24" \
        pillow \
        scikit-image \
        matplotlib-base \
        simpleitk \
        scipy \
    && conda clean -afy

# ---------------------------------------------------------------------------
# Optional: the 3-D publication renderer in code/tools/render_publication_volume.py
# needs pyvista + VTK and off-screen OpenGL. It is NOT used by the default
# reproducible run. Uncomment the two blocks below if you want to run it.
# ---------------------------------------------------------------------------
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         libgl1 libglu1-mesa libxrender1 libxext6 libsm6 xvfb \
#     && rm -rf /var/lib/apt/lists/*
# RUN pip install --no-cache-dir "pyvista>=0.43" "vtk>=9.2"

WORKDIR /code
