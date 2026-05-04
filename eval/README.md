# Evaluation evidence

Curated outputs from the training runs that produced the v0.2.0
checkpoints. The `.pt` weights themselves live on the GitHub Release
(too large to commit); the artifacts here are the small files that let
a reviewer confirm the headline numbers without re-running anything.

Headline metrics (cluster-disjoint test split):

| Metric | Value |
|---|---:|
| Classifier macro F1 | **0.8115** |
| Classifier top-1 accuracy | 0.8412 |
| Detector mAP@50 (conf 0.25) | 0.7516 |
| Detector mAP@50–95 (conf 0.25) | 0.7351 |
| Detector precision / recall (conf 0.25) | 0.864 / 0.729 |
| End-to-end joint accuracy | **0.8341** |
| End-to-end abstention rate | 4.09 % |

Source of truth for these numbers is `../eval_report.json` at the repo
root, produced by `notebooks/kaggle_05_evaluate_end_to_end.ipynb`.

## Artifacts

### `classifier_confusion_matrix.png`

24-class confusion matrix for the EfficientNetV2-S classifier on the
cluster-disjoint test split. Macro F1 0.812. The diagonal is dominant
across all 24 classes; the visible off-diagonal mass clusters at the
fresh ↔ rotten boundary within a produce type (e.g. orange_fresh →
orange_rotten and vice versa) rather than crossing produce types,
which is the failure mode you'd want.

### `classifier_metrics.json`

Per-class precision / recall / F1 / support for the same evaluation.
Useful when reading the README's "weakest classes" callout. The file
also lists macro / weighted / micro averages.

### `yolo_metrics_per_epoch.csv`

180 rows from the YOLO26s training run — train/val box loss, classification
loss, DFL loss, P/R/mAP50/mAP50–95 per epoch, plus per-parameter-group
learning rates from the MuSGD scheduler. Reviewable as-is in any
spreadsheet or via pandas. Final-epoch summary:

| Epoch | mAP@50 | mAP@50-95 | P | R |
|---:|---:|---:|---:|---:|
| 180 | 0.831 | 0.793 | 0.789 | 0.795 |

The run wall-time was ~10.5 hours on 2× T4 (Kaggle); the notebook caps
at that ceiling so a re-run finishes inside the platform's 12-hour
limit.

### `yolo_training_config.yaml`

Exact `args.yaml` produced by Ultralytics for the published run.
Captures every hyperparameter that produced the released weights —
optimizer, augmentation, schedule, mosaic close-out epoch, image size.
A reviewer can re-instantiate this run from this file alone.

### `yolo_label_distribution.jpg`

Auto-generated label distribution chart from the YOLO training data.
Shows the box density per class, x/y / width/height histograms, and the
corner correlation matrix. Useful for spotting the imbalance baked into
the detection subset — the minority classes (bitter_gourd, okra,
strawberry, mango) are visibly thin.

## What's not here

- `.pt` weights — published on the GitHub Release, pulled by
  `python scripts/download_artifacts.py` from the repo root.
- YOLO training-curve plots (`results.png`, `F1_curve.png`,
  `PR_curve.png`) — Ultralytics did not emit these from the canceled-
  then-recovered Kaggle run that produced `best.pt`. The `_per_epoch.csv`
  carries the same data in tabular form.
- Validation batch images and per-class detection samples — local
  artifacts only, not informative without the input images.
