"""End-to-end inference pipeline.

YOLO26s detector finds candidate boxes; the EfficientNetV2-S classifier
runs once on the **full image** as an independent vote, and is used to
either corroborate the detector or force an abstain when the two
disagree on produce type.

The full image is a better classifier input than per-box crops on this
dataset: the model was trained on whole-fruit photographs, so a tight
YOLO crop can lose context that the classifier needs (a single apple
out of a pile reads as a different class entirely, while the pile as a
whole still leans correctly toward apple). Diagnostic runs on the user's
test images confirmed full-image votes are markedly more reliable than
crop votes.

Resolution rules per detection box:
  - No classifier loaded: pass detector through.
  - Detector and classifier (top-1) **agree** on produce type: trust the
    detector — it carries localization the classifier can't supply.
  - Detector and classifier **disagree** on produce type AND classifier
    committed (didn't abstain) AND classifier confidence > detector
    confidence: classifier overrides (rare but catches strong disagreements
    where the localized model was confidently wrong).
  - Otherwise (disagreement without a clean winner — including the case
    where the classifier abstained but its top-class still differs):
    abstain on this box. Honest > confidently wrong.

When the detector finds nothing, the classifier's own abstain stack
(top-1 floor / entropy / top-2 margin) decides whether to commit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image

from freshness.config import load_toml, resolve_path
from freshness.constants import COMBINED_UNKNOWN, FRESHNESS_NA, UNKNOWN_TYPE
from freshness.inference.classifier import (
    ClassifierPrediction,
    EfficientNetV2SFreshnessRuntime,
)
from freshness.inference.detector import Detection, YOLO26Detector
from freshness.utils.images import crop_box, open_image
from freshness.utils.labels import parse_combined_label

DetectionSource = Literal["detector", "classifier", "ensemble", "unknown"]


class PipelineUnavailableError(RuntimeError):
    pass


@dataclass(slots=True)
class DetectedProduce:
    box: tuple[float, float, float, float]
    combined_label: str
    produce_type: str
    freshness: str
    confidence: float
    source: DetectionSource
    crop: Image.Image
    abstain_reason: str | None = None


def _full_image_box(image: Image.Image) -> tuple[float, float, float, float]:
    return (0.0, 0.0, float(image.width), float(image.height))


def _from_detection(detection: Detection, image: Image.Image) -> DetectedProduce:
    return DetectedProduce(
        box=detection.box,
        combined_label=detection.combined_label,
        produce_type=detection.produce_type,
        freshness=detection.freshness,
        confidence=detection.confidence,
        source="detector",
        crop=crop_box(image, detection.box),
        abstain_reason=None,
    )


def _from_classifier(prediction: ClassifierPrediction, image: Image.Image) -> DetectedProduce:
    return DetectedProduce(
        box=_full_image_box(image),
        combined_label=prediction.combined_label,
        produce_type=prediction.produce_type,
        freshness=prediction.freshness,
        confidence=prediction.confidence,
        source="classifier",
        crop=image,
        abstain_reason=prediction.abstain_reason,
    )


def _ensemble_override(
    prediction: ClassifierPrediction,
    detection: Detection,
    image: Image.Image,
) -> DetectedProduce:
    return DetectedProduce(
        box=detection.box,
        combined_label=prediction.combined_label,
        produce_type=prediction.produce_type,
        freshness=prediction.freshness,
        confidence=prediction.confidence,
        source="ensemble",
        crop=crop_box(image, detection.box),
        abstain_reason=None,
    )


def _abstain(
    image: Image.Image,
    *,
    box: tuple[float, float, float, float] | None = None,
    reason: str | None = None,
) -> DetectedProduce:
    return DetectedProduce(
        box=box or _full_image_box(image),
        combined_label=COMBINED_UNKNOWN,
        produce_type=UNKNOWN_TYPE,
        freshness=FRESHNESS_NA,
        confidence=0.0,
        source="unknown",
        crop=crop_box(image, box) if box is not None else image,
        abstain_reason=reason,
    )


def _classifier_top_type_freshness(prediction: ClassifierPrediction) -> tuple[str, str]:
    """Return (produce_type, freshness) for the classifier's top-1 class.

    Used even when the classifier abstained — the top-1 still encodes a
    weak preference that the pipeline uses to corroborate or contradict
    the detector.
    """
    top_label = max(prediction.probabilities, key=prediction.probabilities.get)
    return parse_combined_label(top_label)


def _resolve_against_classifier(
    detection: Detection,
    classifier_pred: ClassifierPrediction,
    image: Image.Image,
) -> DetectedProduce:
    """Decide the per-box label by reconciling the detector and classifier.

    The dataset-driven failure mode in this project is *type confusion* —
    the detector reliably calls fresh-vs-rotten but consistently labels
    apples as potatoes when the background is warm-toned. The classifier
    on the full image is more reliable for produce type because it doesn't
    hyper-attend to the box's local context. So:

    - Agreement on type: trust the detector (it carries localization).
    - Disagreement on type, agreement on freshness, classifier committed:
      override the type with the classifier — the detector is in its known
      failure mode and the classifier corroborates the freshness call.
    - Disagreement on freshness (or classifier abstained outright): abstain.
    """
    classifier_type, classifier_freshness = _classifier_top_type_freshness(classifier_pred)

    # Agreement on produce type → keep the detector's box, label, and freshness.
    if classifier_type == detection.produce_type:
        return _from_detection(detection, image)

    # Type mismatch. The classifier's vote only counts if it (a) committed
    # (didn't trip the abstain stack) and (b) corroborates the detector's
    # freshness call.
    if (
        classifier_pred.abstain_reason is None
        and classifier_freshness == detection.freshness
    ):
        return _ensemble_override(classifier_pred, detection, image)

    return _abstain(
        image,
        box=detection.box,
        reason="detector_classifier_disagree",
    )


class FreshnessPipeline:
    def __init__(
        self,
        detector: YOLO26Detector,
        fallback_classifier: EfficientNetV2SFreshnessRuntime | None,
        max_detections: int,
        fallback_threshold: float,
    ) -> None:
        self.detector = detector
        self.fallback_classifier = fallback_classifier
        self.max_detections = max_detections
        self.fallback_threshold = fallback_threshold

    @classmethod
    def from_config(
        cls,
        config_path: str | Path = "configs/inference.toml",
        runtime_mode: str | None = None,
    ) -> FreshnessPipeline:
        config = load_toml(config_path)
        runtime_cfg = config["runtime"]
        artifacts = config["artifacts"]
        mode = runtime_mode or runtime_cfg["default_mode"]
        if mode != "torch":
            raise PipelineUnavailableError(
                "Only the PyTorch runtime is configured for this project."
            )

        detector_path = resolve_path(artifacts["detector"])
        if not detector_path.exists():
            raise PipelineUnavailableError(
                f"Detector weights not found: {detector_path}. "
                "Train YOLO26s on Kaggle (see notebooks/) or run "
                "`python scripts/download_artifacts.py`."
            )
        detector = YOLO26Detector(
            model_path=detector_path,
            confidence=float(runtime_cfg["detector_confidence"]),
            iou=float(runtime_cfg["detector_iou"]),
            max_detections=int(runtime_cfg["max_detections"]),
        )

        fallback_classifier: EfficientNetV2SFreshnessRuntime | None = None
        classifier_path_value = artifacts.get("classifier")
        if classifier_path_value:
            classifier_path = resolve_path(classifier_path_value)
            if classifier_path.exists():
                fallback_classifier = EfficientNetV2SFreshnessRuntime(
                    weights_path=classifier_path,
                    image_size=int(runtime_cfg["classifier_image_size"]),
                )

        return cls(
            detector=detector,
            fallback_classifier=fallback_classifier,
            max_detections=int(runtime_cfg["max_detections"]),
            fallback_threshold=float(runtime_cfg["fallback_threshold"]),
        )

    def predict(self, image: Image.Image) -> list[DetectedProduce]:
        image = open_image(image)
        detections = self.detector.predict(image)[: self.max_detections]

        classifier_pred: ClassifierPrediction | None = None
        if self.fallback_classifier is not None:
            classifier_pred = self.fallback_classifier.predict(
                image, fallback_threshold=self.fallback_threshold
            )

        if not detections:
            if classifier_pred is None:
                return [_abstain(image, reason="no_classifier")]
            if classifier_pred.abstain_reason is not None:
                return [_abstain(image, reason=classifier_pred.abstain_reason)]
            return [_from_classifier(classifier_pred, image)]

        if classifier_pred is None:
            return [_from_detection(detection, image) for detection in detections]

        results = [
            _resolve_against_classifier(detection, classifier_pred, image)
            for detection in detections
        ]
        # Sort by confidence desc; abstains (confidence 0.0) sink to the
        # bottom so the UI's "is first detection unknown" gate only fires
        # when every detection abstained.
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results
