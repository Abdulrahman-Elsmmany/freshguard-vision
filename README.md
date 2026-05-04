# FreshGuard Vision

Single-stage **24-class produce freshness detection** with an EfficientNetV2-S
fallback. Local Streamlit demo, honest cluster-disjoint metrics, reproducible
training pipeline on Kaggle.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit 1.56](https://img.shields.io/badge/streamlit-1.56-FF4B4B.svg)](https://streamlit.io)
[![PyTorch](https://img.shields.io/badge/pytorch-2.8-EE4C2C.svg)](https://pytorch.org)
[![Ultralytics YOLO26](https://img.shields.io/badge/ultralytics-YOLO26s-111111.svg)](https://docs.ultralytics.com/models/yolo26/)

---

## Headline results

> Cluster-disjoint test split (no near-duplicate ever crosses train / val / test).

| Metric                                  | Value      |
| --------------------------------------- | ---------: |
| **Classifier macro F1** (24-class)      | **0.8115** |
| Classifier top-1 accuracy               |   0.8412   |
| **End-to-end joint accuracy**           | **0.8341** |
| End-to-end macro F1 (excl. abstain)     |   0.7766   |
| Detector mAP@50 (conf 0.25)             |   0.7516   |
| Detector mAP@50–95 (conf 0.25)          |   0.7351   |
| Detector precision / recall (conf 0.25) | 0.864 / 0.729 |
| Abstention rate (end-to-end)            |   4.09 %   |

Macro F1 is the headline because top-1 accuracy hides minority-class
failure under the **41 : 1** class imbalance baked into the source dataset.
Numbers come from `eval_report.json`, produced by
[`notebooks/kaggle_05_evaluate_end_to_end.ipynb`](notebooks/kaggle_05_evaluate_end_to_end.ipynb).

---

## Architecture

```
   ┌──────────────────┐     ┌──────────────────────┐
   │  uploaded image  │────▶│  YOLO26s · 24-class  │── one or more
   └──────────────────┘     │   single forward     │   detections (label,
                            │   pass               │   freshness, box, conf)
                            └──────────┬───────────┘
                                       │ no boxes
                                       ▼
                            ┌──────────────────────┐
                            │  EfficientNetV2-S    │── full-image prediction
                            │  · 24-class          │   (no localization)
                            │  fallback classifier │
                            └──────────┬───────────┘
                                       │ confidence < 0.40
                                       ▼
                              "unknown / n_a"
```

The 24-class label space is `{12 produce types} × {fresh, rotten}` — so
the detector and the fallback classifier emit interchangeable labels.
Apples and oranges are not compared with bananas: the joint label
prevents the cascade-error class of bug where the type model and the
freshness model disagree about what they're looking at.

---

## Quickstart

```powershell
git clone https://github.com/Abdulrahman-Elsmmany/freshguard-vision.git
cd freshguard-vision
uv sync
python scripts/download_artifacts.py     # pulls .pt files from the GitHub Release
uv run streamlit run app.py
```

Requires Python 3.12, [`uv`](https://docs.astral.sh/uv/), and ~140 MB of
model weights downloaded from the v0.2.0 release. Inference is local
PyTorch only — no cloud APIs, no ONNX, no remote services.

---

## Per-class performance

Best-performing classes (classifier macro F1):

| Class                | F1    | Support |
| -------------------- | ----: | ------: |
| `mango_fresh`        | 0.984 |      94 |
| `bitter_gourd_fresh` | 0.972 |      53 |
| `strawberry_rotten`  | 0.947 |      89 |
| `potato_rotten`      | 0.930 |     237 |
| `bitter_gourd_rotten`| 0.929 |      53 |

Weakest:

| Class           | F1    | Support |
| --------------- | ----: | ------: |
| `okra_rotten`   | 0.331 |      43 |
| `okra_fresh`    | 0.600 |      21 |
| `carrot_rotten` | 0.699 |     363 |
| `banana_fresh`  | 0.710 |     319 |
| `orange_rotten` | 0.722 |     665 |

The `okra_*` weakness reflects the source data — Okra is one of the
smallest classes (~973 raw images total) and the rotten subset is
particularly noisy. Most other off-diagonal mass clusters at the
**fresh ↔ rotten** boundary within a single produce type rather than
crossing produce types — the failure mode you'd want. See
[`eval/classifier_confusion_matrix.png`](eval/classifier_confusion_matrix.png)
for the full picture.

---

## Training pipeline

Every step runs on Kaggle. The five notebooks under `notebooks/` chain
their outputs through Kaggle Datasets — each notebook publishes a
dataset that the next one attaches as input.

| # | Notebook                                              | What it does |
|---|-------------------------------------------------------|--------------|
| 1 | `kaggle_01_dataset_audit_and_split.ipynb`             | Audits 71,322 raw images from `ulnnproject/food-freshness-dataset`. Drops corrupt files, merges the verified-duplicate `Bellpepper`/`Capciscum` folders, normalizes typo'd folder names, deduplicates with `imagehash.phash` (Hamming ≤ 5), and freezes a **cluster-disjoint** 70/15/15 split stratified by `produce_type × freshness`. |
| 2 | `kaggle_02_pseudolabel_grounding_dino.ipynb`          | Generates YOLO-format bounding boxes for ~14k stratified images via Grounding DINO (`IDEA-Research/grounding-dino-tiny`), with a per-class floor of 300 boxes for minority classes. Output: 24-class detection dataset. |
| 3 | `kaggle_03_train_detector_yolo26s.ipynb`              | Fine-tunes **YOLO26s** with MuSGD, 150 epochs, multi-GPU (2× T4), `cls_pw=1.0` for the severe imbalance. The 10.5-hour wall-time cap leaves headroom inside Kaggle's 12-hour limit. |
| 4 | `kaggle_04_train_classifier_efficientnetv2s.ipynb`    | Trains **EfficientNetV2-S** (`tf_efficientnetv2_s.in21k_ft_in1k`) on the deduplicated full split. Three layers of imbalance handling stack: `WeightedRandomSampler`, class-weighted CE, and macro F1 as the model-selection metric. RandAugment + mixup; EMA decay 0.9999. |
| 5 | `kaggle_05_evaluate_end_to_end.ipynb`                 | Three independent eval blocks — classifier on ground-truth full images, detector at three confidence operating points, end-to-end pipeline simulation. Emits `eval_report.json` and `eval_report.md`. |

---

## Project layout

```
freshguard-vision/
├── app.py                         · Streamlit entrypoint
├── configs/inference.toml         · Runtime config (thresholds, paths)
├── .streamlit/config.toml         · Theme tokens
├── notebooks/                     · The five Kaggle training notebooks
├── scripts/
│   └── download_artifacts.py      · Pulls .pt weights from GitHub Release
├── src/freshness/
│   ├── inference/                 · Pipeline + detector + classifier wrappers
│   ├── ui/                        · Streamlit pages, theming, components
│   ├── utils/                     · Image I/O, label normalization
│   ├── config.py
│   └── constants.py               · 24-class label space, Latin binomials
├── eval/                          · Curated training evidence (this repo)
├── PRD.md                         · Product brief — scope, goals, non-goals
├── eval_report.md                 · Headline metrics, human-readable
└── eval_report.json               · Same metrics, machine-readable
```

---

## What's in the repo, what's in the release

The `.pt` checkpoints are large (~140 MB combined) and don't belong in
git. They live on the
[v0.2.0 GitHub Release](https://github.com/Abdulrahman-Elsmmany/freshguard-vision/releases/tag/v0.2.0):

- `yolo26s_food_freshness.pt` — detector, 60 MB
- `efficientnetv2s_food_freshness.pt` — classifier, 80 MB

`scripts/download_artifacts.py` resolves the latest release via the
GitHub API and drops both files into `artifacts/` automatically.

---

## Honest limitations

- **`okra_*` is the weakest class** (F1 0.33 / 0.60). Source data is
  small and noisy; documented rather than papered over.
- **`bitter_gourd_*` has only 684 raw examples** and trains on
  ~250 each per split. Per-class metrics there should be read with
  that floor in mind, even though F1 ends up high (0.97 fresh, 0.93
  rotten).
- **Detection ground truth is Grounding-DINO pseudo-labels** with
  programmatic area filters, not manual annotation. Per-class noise
  was sampled visually during the QA pass, but absolute box-quality
  numbers should be treated as conservative.
- **Out-of-distribution images** (cluttered scenes, novel varieties,
  non-produce subjects) trigger the classifier fallback or the
  `unknown` abstain — the system would rather refuse than confidently
  hallucinate.
- **Binary freshness only.** No shelf-life forecast, no "medium" /
  partial-ripeness label.

---

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · PyTorch 2.8 ·
[Ultralytics 8.3 / YOLO26s](https://docs.ultralytics.com/models/yolo26/) ·
[timm](https://huggingface.co/docs/timm) ·
[Streamlit 1.56](https://streamlit.io) ·
[Grounding DINO](https://huggingface.co/IDEA-Research/grounding-dino-tiny)
(training only).

## License

[MIT](LICENSE) — © 2026 Abdulrahman Elsmmany.
