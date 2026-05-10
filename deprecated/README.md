# Deprecated Local Artifacts

This folder is a local archive for v1 training outputs and checkpoints that are
useful as historical evidence but should not clutter the active v2 workspace.

Ignored contents may include:

- `results/` and `results.zip` from the YOLO26s v1 detector run.
- `results_efficientnetv2/` and `results_efficientnetv2.zip` from the
  EfficientNetV2-S v1 classifier run.
- Loose v1 `.pt` checkpoints copied during earlier local testing.

The active v2 app expects these files under `artifacts/`:

- `yolo26n_produce_v2.pt`
- `dinov3_vits16_food_freshness_v2.pt`

Model checkpoints stay out of git. Publish active checkpoints as GitHub Release
assets and fetch them with `python scripts/download_artifacts.py`.
