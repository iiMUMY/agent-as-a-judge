# Benchmark Test Folders

This directory contains curated, reusable benchmark test setups created during local validation.

## Kept Folders

- `task39_black_box_smoke`
  - Purpose: single-task smoke test for Task 39 using black-box mode.
  - What it contains:
    - one instance (`39_Drug_Response_Prediction_SVM_GDSC_ML`)
    - matching workspace snapshot
    - matching trajectory
    - generated judgment artifacts
  - Why kept: reproduces the original "run one task" validation path.

- `task01_english_gray_baseline`
  - Purpose: English baseline for Task 01 in gray-box mode.
  - What it contains:
    - one instance (`01_fmnist`) in English
    - workspace with task files
    - trajectory evidence
    - judgment output used as baseline labels
  - Why kept: reference baseline for agreement-rate comparison.

- `task01_arabic_gray_final`
  - Purpose: final Arabic evaluation setup for Task 01 in gray-box mode.
  - What it contains:
    - one instance (`01_fmnist`) translated to Arabic
    - Arabic trajectory evidence
    - workspace snapshot
    - final Arabic judgment output (UTF-8 readable Arabic text)
  - Why kept: validates Arabic prompt/evaluation flow and enables English-vs-Arabic comparison.

## Removed Folders

The following temporary/intermediate directories were deleted as they were superseded:

- `benchmark_single_01`
- `benchmark_single_01_ar`
- `benchmark_single_01_comp`

These were staging folders used for iterative debugging and were replaced by the finalized folders above.
