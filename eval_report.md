# FreshGuard End‑to‑End Evaluation Report

All metrics computed on the cluster‑disjoint **test split** frozen by notebook 1.

## Classifier‑only (ground‑truth full images, 24 classes)

- **Macro F1: 0.8115**
- Top‑1 accuracy: 0.8412

### Per‑class F1 (sorted ascending — minority classes first)

| Class | F1 | Precision | Recall | Support |
|---|---:|---:|---:|---:|
| okra_rotten | 0.331 | 0.228 | 0.605 | 43 |
| okra_fresh | 0.600 | 0.429 | 1.000 | 21 |
| carrot_rotten | 0.699 | 1.000 | 0.537 | 363 |
| banana_fresh | 0.710 | 0.556 | 0.984 | 319 |
| orange_rotten | 0.722 | 0.890 | 0.608 | 665 |
| bellpepper_rotten | 0.735 | 0.770 | 0.703 | 333 |
| apple_fresh | 0.744 | 0.613 | 0.945 | 289 |
| bellpepper_fresh | 0.751 | 0.673 | 0.850 | 353 |
| banana_rotten | 0.753 | 0.978 | 0.612 | 729 |
| potato_fresh | 0.763 | 0.784 | 0.744 | 39 |
| mango_rotten | 0.775 | 0.647 | 0.966 | 89 |
| apple_rotten | 0.815 | 0.966 | 0.705 | 847 |
| orange_fresh | 0.851 | 0.802 | 0.906 | 1294 |
| tomato_rotten | 0.861 | 0.870 | 0.852 | 1114 |
| carrot_fresh | 0.914 | 0.845 | 0.997 | 1496 |
| strawberry_fresh | 0.916 | 0.845 | 1.000 | 71 |
| cucumber_rotten | 0.922 | 0.975 | 0.875 | 311 |
| tomato_fresh | 0.924 | 0.974 | 0.879 | 1675 |
| cucumber_fresh | 0.929 | 0.888 | 0.974 | 308 |
| bitter_gourd_rotten | 0.929 | 1.000 | 0.868 | 53 |
| potato_rotten | 0.930 | 0.885 | 0.979 | 237 |
| strawberry_rotten | 0.947 | 1.000 | 0.899 | 89 |
| bitter_gourd_fresh | 0.972 | 0.946 | 1.000 | 53 |
| mango_fresh | 0.984 | 0.979 | 0.989 | 94 |

## Detector (YOLO26s) at multiple operating points

| Conf | Precision | Recall | mAP50 | mAP50‑95 |
|---:|---:|---:|---:|---:|
| 0.15 | 0.859 | 0.733 | 0.789 | 0.766 |
| 0.25 | 0.864 | 0.729 | 0.752 | 0.735 |
| 0.35 | 0.867 | 0.727 | 0.729 | 0.714 |

## End‑to‑end pipeline (detector → classifier fallback → unknown)

- Joint accuracy (excluding abstentions): **0.8341**
- Macro F1 (excluding abstentions): **0.7766**
- Abstention rate: 0.0409
- Source breakdown: {'detector': 9305, 'classifier': 1135, 'unknown': 445}

## How to use these numbers

- **Macro F1 is the headline.** Top‑1 accuracy hides minority‑class failure under the 41:1 imbalance — don't quote top‑1 in isolation.
- The end‑to‑end joint accuracy is the user‑visible quality of the local app on test images. The classifier‑only number is the ceiling that perfect detection would deliver.
- The detector‑only block shows the recall/precision tradeoff. Pick a conf threshold for `configs/inference.toml` based on whether your demo prefers misses (high conf) or false positives (low conf).