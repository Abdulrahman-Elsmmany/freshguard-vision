# Product Requirements Document

## Product

Local Food Freshness Detector — a Streamlit app that accepts a fruit or
vegetable image and reports produce type and freshness for every detected
item.

## Goal

Build a reproducible local demo that classifies 24 fine-grained labels
(12 produce types × {fresh, rotten}) honestly, with leakage-controlled
metrics and a single-stage architecture that doesn't compound errors.

## Runtime Artifacts

The app uses local PyTorch artifacts only:

- Detector: `artifacts/yolo26s_food_freshness.pt` (YOLO26s, 24 classes)
- Fallback classifier: `artifacts/efficientnetv2s_food_freshness.pt`
  (EfficientNetV2-S, 24 classes)

No ONNX path, no cloud inference. Runtime config lives in
`configs/inference.toml`.

## Supported Labels

12 canonical produce types:

`apple`, `banana`, `bellpepper`, `bitter_gourd`, `carrot`, `cucumber`,
`mango`, `okra`, `orange`, `potato`, `strawberry`, `tomato`

Folder-name typos and synonyms in the source dataset (`bittergroud`,
`okara`, `capciscum`, `capsicum`) are normalized to the canonical names
above. `Bellpepper` and `Capciscum` source folders are merged into one
`bellpepper` class — verified to be the same vegetable.

Two freshness levels: `fresh`, `rotten`.

The detector and classifier both predict the joint 24-class label
(`<produce>_<freshness>`), so their outputs are interchangeable.

Runtime abstention labels surface in the UI when both stages refuse:
`unknown / n_a`.

## User Flow

1. User uploads an image.
2. **Detector first.** YOLO26s runs at conf 0.25 and returns 0..N boxes,
   each with a 24-class label and confidence.
3. **Fallback if detector finds nothing.** EfficientNetV2-S runs on the
   full image. If its top-1 confidence ≥ 0.4, the app surfaces that
   single guess (no box).
4. **Abstain otherwise.** Both stages refusing yields `unknown / n_a`.
5. UI renders **all** detections (not just the top one), labeled with
   produce, freshness, confidence, and source badge (`detector` /
   `classifier` / `unknown`).

## Functional Requirements

- Predict page accepts one image upload at a time.
- Predict page draws one bounding box per detection plus a per-detection
  card with produce, freshness, confidence, and source.
- Model card lists the 24 supported classes, the architecture, the
  cluster-disjoint dataset preparation, and the headline metrics.
- App boots with `uv run streamlit run app.py`.
- App size guard rejects images whose longest side exceeds 4096 px.

## Dataset And Training Notes

Source: Kaggle `ulnnproject/food-freshness-dataset`, a merge of three
upstream Kaggle multiclass datasets. Raw size: 71,322 images across 26
folders (12 produce types + the duplicated Bellpepper/Capciscum pair) ×
fresh/rotten.

- After dropping unreadable files and applying the Bellpepper/Capciscum
  merge, the post-decode set is **70,762 images / 24 classes**.
- Class imbalance is severe: ratio ≈ 41:1 between FreshTomato and
  FreshBittergroud. Training compensates with class-weighted loss
  (`cls_pw=1.0` for YOLO; weighted CE + WeightedRandomSampler for the
  classifier) and reports macro F1 as the headline metric.
- **Perceptual-hash deduplication is applied** (`imagehash.phash`,
  Hamming distance ≤ 5, Union-Find clustering). Train/val/test splits
  are cluster-disjoint at a 70/15/15 ratio, stratified by
  `produce_type × freshness`. No near-duplicate ever spans two splits.
- Detector training data: ~13,871 images stratified across the 24
  classes, with bounding boxes pseudo-labeled by Grounding DINO
  (`IDEA-Research/grounding-dino-tiny`) using the known produce type as
  the prompt. Per-class minimum 300 boxes for minority classes
  (Bittergroud, Okra, Mango, Strawberry).
- Classifier training data: the full deduplicated split (~50k train).

## Headline Metrics

Computed on the cluster-disjoint test split. Full breakdown in
`eval_report.md`.

| Block | Metric | Value |
|---|---|---:|
| Classifier (ground-truth full image, 24 classes) | Macro F1 | **0.81** |
| Classifier (ground-truth full image, 24 classes) | Top-1 accuracy | 0.84 |
| Detector @ conf 0.25 | Precision / Recall | 0.86 / 0.73 |
| Detector @ conf 0.25 | mAP50 / mAP50-95 | 0.75 / 0.74 |
| End-to-end pipeline | Joint accuracy (excl. abstain) | **0.83** |
| End-to-end pipeline | Macro F1 (excl. abstain) | 0.78 |
| End-to-end pipeline | Abstention rate | 4.1% |

**Macro F1 is the headline.** Top-1 hides minority-class failure under
41:1 imbalance. Detector recall of 0.73 is a substantial lift over the
previous 0.438.

## Non-Goals

- Cloud deployment, hosted API, mobile packaging.
- ONNX export or alternative inference runtimes.
- Shelf-life forecasting or multi-stage ripeness (`medium`, `partial`).
- Training an `unknown` class — abstention is a runtime threshold, not
  a learned label.

## Quality Targets

- App boots locally with `uv run streamlit run app.py`.
- `python scripts/download_artifacts.py` pulls both checkpoints from a
  GitHub Release on a fresh clone.
- Detector loads from `artifacts/yolo26s_food_freshness.pt` and
  classifier loads from `artifacts/efficientnetv2s_food_freshness.pt`.
- Known fresh and known rotten test images render readable boxes plus a
  per-detection card.
- Photos with no produce return `unknown / n_a`.

## Known Limitations

- Detection ground truth is Grounding-DINO pseudo-labels with
  programmatic area filters, not full manual annotation. Per-class
  noise was sampled visually in notebook 2's QA report.
- `okra_rotten` (33) and `okra_fresh` (60) classifier F1 are weak
  because raw counts are small (~973 total) and the rotten subset is
  particularly noisy. Treat these predictions skeptically.
- Bittergroud has only 684 raw examples — the model is trained on it
  but per-class metrics should be read with that floor in mind.
- Out-of-distribution photos (cluttered scenes, unusual angles, novel
  varieties) trigger the classifier fallback or surface `unknown`
  rather than a confident wrong answer.
- Binary freshness only.

## References

- Kaggle Food Freshness Dataset: https://www.kaggle.com/datasets/ulnnproject/food-freshness-dataset
- Streamlit docs: https://docs.streamlit.io/
- Ultralytics YOLO26 docs: https://docs.ultralytics.com/models/yolo26/
- timm EfficientNetV2: https://huggingface.co/docs/timm/models/efficientnetv2
- Grounding DINO: https://huggingface.co/IDEA-Research/grounding-dino-tiny
