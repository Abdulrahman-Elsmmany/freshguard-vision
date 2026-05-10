# Product Requirements Document

## Product

Local Food Freshness Detector — a Streamlit app that accepts a fruit or
vegetable image and reports produce type and freshness for every detected
item.

## Goal

Build a reproducible local demo that classifies 24 fine-grained labels
(12 produce types × {fresh, rotten}) honestly, with leakage-controlled
metrics and a two-stage v2 architecture that separates localization from
classification.

## Runtime Artifacts

The v2 app uses local PyTorch artifacts only:

- Detector: `artifacts/yolo26n_produce_v2.pt` (YOLO26n, 1 class:
  `produce`)
- Classifier: `artifacts/dinov3_vits16_food_freshness_v2.pt`
  (DINOv3-S/16 + MLP head, 24 classes)

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

The classifier predicts the joint 24-class label
(`<produce>_<freshness>`). The detector predicts only produce boxes and
has no type or freshness authority.

Runtime abstention labels surface in the UI when both stages refuse:
`unknown / n_a`.

## User Flow

1. User uploads an image.
2. **Detector first.** YOLO26n runs at conf 0.40 and returns 0..N
   produce boxes with confidence.
3. **Classifier authority.** DINOv3-S/16 runs on each crop and assigns
   the 24-class type/freshness label.
4. **Full-image sanity check.** DINOv3-S/16 also runs on the full image.
   If full-image and crop predictions both commit but disagree on produce
   type, the app abstains on that box.
5. **Fallback if detector finds nothing.** The full-image classifier can
   surface a single no-box guess if it clears the abstain stack.
6. **Abstain otherwise.** Refusal yields `unknown / n_a`.
7. UI renders **all** detections (not just the top one), labeled with
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

The v2 rebuild is implemented through six `_v2` Kaggle notebooks:
official-source download, dataset audit/split, detector-data
preparation, YOLO26n detector training, DINOv3 classifier training, and
final evaluation. The v1 notebooks remain as shipped v0.2.0 evidence.

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
- v2 detector training data merges Food Freshness full-image bootstrap
  boxes, KTH GroceryStoreDataset full-image boxes, and official Open
  Images V7 produce bounding boxes into a 1-class `produce` YOLO dataset.
- v2 classifier training data keeps Food Freshness as the canonical
  24-class freshness benchmark. KTH GroceryStoreDataset is included only
  as low-weight `fresh_assumed` auxiliary training data and type-only
  external evaluation; it is not mixed into headline freshness metrics.

## Headline Metrics

Current values are from the v2 evaluation notebook. Full breakdown in
`eval_report.md`; machine-readable values are in `eval_report.json`.

| Block | Metric | Value |
|---|---|---:|
| Classifier (Food Freshness, 24 classes) | Macro F1 | **0.9478** |
| Classifier (Food Freshness, 24 classes) | Top-1 accuracy | 0.9490 |
| KTH GroceryStoreDataset external test | Type accuracy | 0.8995 |
| KTH GroceryStoreDataset external test | Count | 955 |
| Detector (1-class produce) | mAP50 / mAP50-95 | 0.8763 / 0.8249 |

**Macro F1 is the headline.** Top-1 hides minority-class failure under
41:1 imbalance. KTH is reported as a type-only external benchmark
because it has no fresh/rotten labels.

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
- Detector loads from `artifacts/yolo26n_produce_v2.pt` and classifier
  loads from `artifacts/dinov3_vits16_food_freshness_v2.pt`.
- Known fresh and known rotten test images render readable boxes plus a
  per-detection card.
- Photos with no produce return `unknown / n_a`.

## Known Limitations

- Detector supervision is mixed: Food Freshness and KTH contribute
  full-image bootstrap boxes, while Open Images contributes official
  object boxes. It is not a fully manual box-annotation benchmark.
- The weakest v2 classifier classes are `carrot_rotten` (F1 0.855),
  `orange_rotten` (0.865), and `bellpepper_fresh` (0.866). These are
  still materially stronger than the v1 minority-class floor.
- KTH GroceryStoreDataset is type-only external evidence. It improves
  the generalization story but cannot validate fresh/rotten labels.
- Out-of-distribution photos (cluttered scenes, unusual angles, novel
  varieties) trigger the classifier abstain stack, the crop/full-image
  disagreement guard, or `unknown` rather than a confident wrong answer.
- Binary freshness only.

## References

- Kaggle Food Freshness Dataset: https://www.kaggle.com/datasets/ulnnproject/food-freshness-dataset
- Streamlit docs: https://docs.streamlit.io/
- Ultralytics YOLO26 docs: https://docs.ultralytics.com/models/yolo26/
- timm DINOv3: https://huggingface.co/timm/vit_small_patch16_dinov3.lvd1689m
- Grounding DINO: https://huggingface.co/IDEA-Research/grounding-dino-tiny
