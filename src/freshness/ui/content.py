"""Static content + headline metrics consumed by the Field Guide page.

Headline metrics are sourced from `eval_report.json` at module-import time
so the model card never drifts from the most recent run.
"""

from __future__ import annotations

import json
from pathlib import Path

# ----------------------------------------------------------------------
# Headline metrics — loaded once from eval_report.json. If the file is
# absent (e.g. fresh clone before notebook 5 has run), fall back to the
# latest v2 Kaggle report values.
# ----------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVAL_PATH = _REPO_ROOT / "eval_report.json"

_FALLBACK = {
    "macro_f1": 0.9478,
    "top1_accuracy": 0.9490,
    "kth_type_accuracy": 0.8995,
    "kth_count": 955.0,
    "detector_map50": 0.8693,
    "detector_map5095": 0.8190,
    "detector_conf": 0.40,
    "open_world_false_accept": 0.0873,
    "open_world_positive_retention": 0.5951,
}


def _load_metrics() -> dict[str, float]:
    if not _EVAL_PATH.exists():
        return dict(_FALLBACK)
    try:
        data = json.loads(_EVAL_PATH.read_text())
    except json.JSONDecodeError:
        return dict(_FALLBACK)

    classifier = data.get("classifier_only", {})
    grocery = data.get("grocery_external_type_only", {})
    detector_blocks = data.get("detector", {})
    detector_conf = 0.40 if "conf_0.40" in detector_blocks else 0.25
    detector = detector_blocks.get(f"conf_{detector_conf:.2f}", {}).get("overall", {})
    open_world = data.get("open_world", {})

    def metric(value: object, fallback: float) -> float:
        return float(value) if isinstance(value, int | float) else fallback

    return {
        "macro_f1": metric(classifier.get("macro_f1"), _FALLBACK["macro_f1"]),
        "top1_accuracy": metric(classifier.get("top1_accuracy"), _FALLBACK["top1_accuracy"]),
        "kth_type_accuracy": metric(grocery.get("type_accuracy"), _FALLBACK["kth_type_accuracy"]),
        "kth_count": metric(grocery.get("count"), _FALLBACK["kth_count"]),
        "detector_map50": metric(detector.get("mAP50"), _FALLBACK["detector_map50"]),
        "detector_map5095": metric(detector.get("mAP50_95"), _FALLBACK["detector_map5095"]),
        "detector_conf": detector_conf,
        "open_world_false_accept": metric(
            open_world.get("detector_false_accept_rate"),
            _FALLBACK["open_world_false_accept"],
        ),
        "open_world_positive_retention": metric(
            open_world.get("positive_retention"),
            _FALLBACK["open_world_positive_retention"],
        ),
    }


HEADLINE_METRICS: dict[str, float] = _load_metrics()


# ----------------------------------------------------------------------
# Field Guide chapters — almanac voice, no marketing copy.
# Each value is HTML so the page can drop it into <div class="fg-prose">…</div>.
# ----------------------------------------------------------------------
PROCEDURE_HTML = """
<p>
The v2 pipeline separates localization from classification.
<strong>YOLO26n</strong> predicts one class — produce — and returns only
boxes plus confidence. A <strong>DINOv3-S/16</strong> classifier assigns
the 24-class label to each crop, so produce type and freshness come from
one authority instead of from the detector.
</p>
<p>
The classifier also runs once on the full image as a sanity check. If the
crop classifier and full-image classifier both commit but disagree on
produce type, the system answers honestly: <code>unknown / n_a</code>.
Near-full-image detector boxes are treated as scene context when smaller
produce boxes exist, and no-box uploads are rejected instead of being
forced through the closed-set freshness classifier.
</p>
"""

PROVENANCE_HTML = """
<p>
Source dataset: Kaggle <code>ulnnproject/food-freshness-dataset</code>, a
merge of three upstream multiclass datasets. The raw set has 26 folders;
the <code>Bellpepper</code> and <code>Capciscum</code> folders are the
same vegetable (visually verified) and merge to one canonical
<code>bellpepper</code> class. Folder typos
<code>bittergroud</code> and <code>okara</code> normalize to
<code>bitter_gourd</code> and <code>okra</code>.
</p>
<p>
After deduplication via perceptual hashing
(<code>imagehash.phash</code>, Hamming ≤ 5, Union-Find) and
<strong>cluster-disjoint</strong> 70 / 15 / 15 splits stratified on
<code>produce_type × freshness</code>, the working set is
<strong>70,762 images / 24 classes</strong>. Class imbalance is
severe — about <strong>41 : 1</strong> between FreshTomato and
FreshBittergroud. Training compensates with class-weighted loss
(<code>cls_pw=1.0</code> for YOLO; weighted CE +
<code>WeightedRandomSampler</code> for the classifier). Macro F1 is the
reporting metric; top-1 hides minority-class failure under that
imbalance.
</p>
"""

LIMITATIONS_HTML = """
<ul>
  <li>
    Detector supervision is mixed: Food Freshness and KTH contribute
    full-image bootstrap boxes, while Open Images contributes official
    object boxes plus negative/background examples. Runtime scene-box
    suppression reduces the visible impact, but it is not a fully manual
    box-annotation benchmark.
  </li>
  <li>
    Open Images positive retention is <strong>0.5951</strong>. v2.1 is
    intentionally stricter on non-produce uploads, but recovering more
    valid web-style produce detections is the next detector-quality target.
  </li>
  <li>
    <strong>carrot_rotten</strong> (F1 0.855),
    <strong>orange_rotten</strong> (F1 0.865), and
    <strong>bellpepper_fresh</strong> (F1 0.866) are the weakest classes
    in the v2 classifier report; all still clear the old v1 minority-class
    floor by a wide margin.
  </li>
  <li>
    <strong>bitter_gourd</strong> has only 684 raw examples; per-class
    metrics should be read with that floor in mind.
  </li>
  <li>
    Out-of-distribution images trigger the detector/open-world gates,
    classifier abstain stack, or the crop/full-image disagreement guard
    rather than a confident wrong answer.
  </li>
  <li>
    When the model is confident about produce type but split between
    fresh and rotten, the app reports the type with freshness
    <code>n_a</code>.
  </li>
  <li>Binary freshness only — no shelf-life forecast, no
    <em>medium</em> / partial-ripeness label.</li>
</ul>
"""


# ----------------------------------------------------------------------
# Architecture rows for the III. Results table on the Field Guide page.
# ----------------------------------------------------------------------
def architecture_rows() -> list[tuple[str, str, str]]:
    return [
        ("Localizer", "YOLO26n · produce-only", "item boxes, no type/freshness opinion"),
        ("Open-world filters", "runtime post-processing", "drop scene boxes; reject weak full-frame boxes"),
        ("Classifier", "DINOv3-S/16 · 24-class", "crop authority for type and freshness"),
        ("Abstain", "unknown / n_a", "no produce, weak evidence, or crop/full-image disagreement"),
    ]


# ----------------------------------------------------------------------
# Backwards-compatible markdown export (in case any other consumer still
# imports it; the new page reads structured blocks above).
# ----------------------------------------------------------------------
MODEL_CARD_MARKDOWN = (
    "## Procedure\n\n"
    "YOLO26n produce localizer + DINOv3-S/16 classifier. See the Field Guide page in the app."
)
