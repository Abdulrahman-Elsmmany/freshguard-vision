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
# numbers from the v0.2.0 release.
# ----------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
_EVAL_PATH = _REPO_ROOT / "eval_report.json"

_FALLBACK = {
    "macro_f1": 0.8115,
    "top1_accuracy": 0.8412,
    "joint_accuracy": 0.8341,
    "joint_macro_f1": 0.7766,
    "abstention_rate": 0.0409,
    "detector_p": 0.864,
    "detector_r": 0.729,
    "detector_map50": 0.7516,
    "detector_map5095": 0.7351,
    "detector_conf": 0.25,
}


def _load_metrics() -> dict[str, float]:
    if not _EVAL_PATH.exists():
        return dict(_FALLBACK)
    try:
        data = json.loads(_EVAL_PATH.read_text())
    except json.JSONDecodeError:
        return dict(_FALLBACK)

    classifier = data.get("classifier_only", {})
    end_to_end = data.get("end_to_end", {})
    detector = data.get("detector", {}).get("conf_0.25", {}).get("overall", {})
    return {
        "macro_f1": classifier.get("macro_f1", _FALLBACK["macro_f1"]),
        "top1_accuracy": classifier.get("top1_accuracy", _FALLBACK["top1_accuracy"]),
        "joint_accuracy": end_to_end.get("joint_accuracy_excl_abstain", _FALLBACK["joint_accuracy"]),
        "joint_macro_f1": end_to_end.get("macro_f1_excl_abstain", _FALLBACK["joint_macro_f1"]),
        "abstention_rate": end_to_end.get("abstention_rate", _FALLBACK["abstention_rate"]),
        "detector_p": detector.get("precision", _FALLBACK["detector_p"]),
        "detector_r": detector.get("recall", _FALLBACK["detector_r"]),
        "detector_map50": detector.get("mAP50", _FALLBACK["detector_map50"]),
        "detector_map5095": detector.get("mAP50_95", _FALLBACK["detector_map5095"]),
        "detector_conf": 0.25,
    }


HEADLINE_METRICS: dict[str, float] = _load_metrics()


# ----------------------------------------------------------------------
# Field Guide chapters — almanac voice, no marketing copy.
# Each value is HTML so the page can drop it into <div class="fg-prose">…</div>.
# ----------------------------------------------------------------------
PROCEDURE_HTML = """
<p>
A single forward pass of <strong>YOLO26s</strong> predicts produce type
<em>and</em> freshness in one shot, returning zero or more boxes per image
with a 24-class label and a confidence score. When the detector finds
nothing — out-of-distribution scenes, unusual angles, novel varieties —
an <strong>EfficientNetV2-S</strong> classifier runs on the full image
as a fallback. Both stages share the same 24-class label space, so their
outputs render identically downstream.
</p>
<p>
The hot path is the detector. The classifier is consulted only on
silence. If both refuse to commit, the system answers honestly:
<code>unknown / n_a</code>.
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
    Detection ground truth is <strong>Grounding DINO pseudo-labels</strong>
    with programmatic area filters, not full manual annotation. Per-class
    noise was sampled visually in the QA pass.
  </li>
  <li>
    <strong>okra_rotten</strong> (F1 0.33) and
    <strong>okra_fresh</strong> (F1 0.60) are the weakest classes —
    raw counts are small (~973 total) and the rotten subset is
    particularly noisy. Treat predictions for these classes
    skeptically.
  </li>
  <li>
    <strong>bitter_gourd</strong> has only 684 raw examples; per-class
    metrics should be read with that floor in mind.
  </li>
  <li>
    Out-of-distribution photos trigger the classifier fallback or
    the <code>unknown</code> abstain rather than a confident wrong
    answer.
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
        ("Hot path", "YOLO26s · 24-class", "single forward pass"),
        ("Fallback", "EfficientNetV2-S · 24-class", "full-image, only on detector silence"),
        ("Abstain", "unknown / n_a", "fallback confidence < 0.40"),
    ]


# ----------------------------------------------------------------------
# Backwards-compatible markdown export (in case any other consumer still
# imports it; the new page reads structured blocks above).
# ----------------------------------------------------------------------
MODEL_CARD_MARKDOWN = (
    "## Procedure\n\n"
    "Single-stage YOLO26s + EfficientNetV2-S fallback. See the Field Guide page in the app."
)
