"""End-to-end inference pipeline.

Single-stage YOLO26 in the hot path; EfficientNetV2-S classifier only
runs as a fallback when the detector returns zero boxes. The fallback's
job is to surface a best guess on out-of-distribution images instead of
silently giving up with `unknown / n_a`.
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
from freshness.utils.images import open_image

DetectionSource = Literal["detector", "classifier", "unknown"]


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


def _full_image_box(image: Image.Image) -> tuple[float, float, float, float]:
    return (0.0, 0.0, float(image.width), float(image.height))


def _from_detection(detection: Detection, image: Image.Image) -> DetectedProduce:
    from freshness.utils.images import crop_box

    return DetectedProduce(
        box=detection.box,
        combined_label=detection.combined_label,
        produce_type=detection.produce_type,
        freshness=detection.freshness,
        confidence=detection.confidence,
        source="detector",
        crop=crop_box(image, detection.box),
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
    )


def _unknown(image: Image.Image) -> DetectedProduce:
    return DetectedProduce(
        box=_full_image_box(image),
        combined_label=COMBINED_UNKNOWN,
        produce_type=UNKNOWN_TYPE,
        freshness=FRESHNESS_NA,
        confidence=0.0,
        source="unknown",
        crop=image,
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
        if detections:
            return [_from_detection(detection, image) for detection in detections]

        if self.fallback_classifier is None:
            return [_unknown(image)]

        prediction = self.fallback_classifier.predict(
            image, fallback_threshold=self.fallback_threshold
        )
        if prediction.produce_type == UNKNOWN_TYPE:
            return [_unknown(image)]
        return [_from_classifier(prediction, image)]
