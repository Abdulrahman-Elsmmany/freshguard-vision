"""End-to-end v2 inference pipeline.

STORY.md Act 5 changes the two-stage contract: YOLO26n detects one class,
``produce``, and DINOv3 is the sole authority on produce type and freshness.
Each detector crop is classified independently. The full-image classifier is
retained as a sanity check; when both crop and full-image classifiers commit
but disagree on produce type, the result abstains instead of publishing a
confident OOD guess.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image

from freshness.config import load_toml, resolve_path
from freshness.constants import COMBINED_UNKNOWN, FRESHNESS_NA, UNKNOWN_TYPE
from freshness.inference.classifier import (
    ClassifierPrediction,
    DinoV3FreshnessRuntime,
)
from freshness.inference.detector import Detection, YOLO26Detector
from freshness.utils.images import crop_box, open_image

DetectionSource = Literal["detector", "classifier", "ensemble", "unknown"]
ProgressPhase = Literal[
    "image_loaded",
    "detector_started",
    "detector_done",
    "classifier_started",
    "classifier_done",
    "render_ready",
]
ProgressCallback = Callable[["PipelineProgress"], None]


class PipelineUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class PipelineProgress:
    phase: ProgressPhase
    message: str
    completed: int
    total: int


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


def _from_crop_classifier(
    prediction: ClassifierPrediction,
    detection: Detection,
    crop: Image.Image,
) -> DetectedProduce:
    return DetectedProduce(
        box=detection.box,
        combined_label=prediction.combined_label,
        produce_type=prediction.produce_type,
        freshness=prediction.freshness,
        confidence=prediction.confidence,
        source="classifier",
        crop=crop,
        abstain_reason=None,
    )


def _abstain(
    image: Image.Image,
    *,
    box: tuple[float, float, float, float] | None = None,
    crop: Image.Image | None = None,
    reason: str | None = None,
) -> DetectedProduce:
    return DetectedProduce(
        box=box or _full_image_box(image),
        combined_label=COMBINED_UNKNOWN,
        produce_type=UNKNOWN_TYPE,
        freshness=FRESHNESS_NA,
        confidence=0.0,
        source="unknown",
        crop=crop or (crop_box(image, box) if box is not None else image),
        abstain_reason=reason,
    )


def _resolve_crop_prediction(
    detection: Detection,
    crop: Image.Image,
    crop_pred: ClassifierPrediction,
    full_image_pred: ClassifierPrediction,
    image: Image.Image,
) -> DetectedProduce:
    """Resolve one produce box under the v2 detector/classifier contract."""
    if crop_pred.abstain_reason is not None:
        return _abstain(
            image,
            box=detection.box,
            crop=crop,
            reason=crop_pred.abstain_reason,
        )

    if (
        full_image_pred.abstain_reason is None
        and crop_pred.produce_type != full_image_pred.produce_type
    ):
        return _abstain(
            image,
            box=detection.box,
            crop=crop,
            reason="crop_full_image_disagree",
        )

    return _from_crop_classifier(crop_pred, detection, crop)


def _emit(
    progress_callback: ProgressCallback | None,
    phase: ProgressPhase,
    message: str,
    completed: int,
    total: int,
) -> None:
    if progress_callback is not None:
        progress_callback(
            PipelineProgress(
                phase=phase,
                message=message,
                completed=completed,
                total=max(total, 1),
            )
        )


def _predict_many(
    classifier: DinoV3FreshnessRuntime,
    images: Sequence[Image.Image],
    fallback_threshold: float,
) -> list[ClassifierPrediction]:
    if hasattr(classifier, "predict_many"):
        return classifier.predict_many(
            images,
            fallback_threshold=fallback_threshold,
        )
    return [
        classifier.predict(image, fallback_threshold=fallback_threshold)
        for image in images
    ]


class FreshnessPipeline:
    def __init__(
        self,
        detector: YOLO26Detector,
        classifier: DinoV3FreshnessRuntime,
        max_detections: int,
        fallback_threshold: float,
    ) -> None:
        self.detector = detector
        self.classifier = classifier
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
                "Train YOLO26n on Kaggle (see notebooks/) or run "
                "`python scripts/download_artifacts.py`."
            )
        detector = YOLO26Detector(
            model_path=detector_path,
            confidence=float(runtime_cfg["detector_confidence"]),
            iou=float(runtime_cfg["detector_iou"]),
            max_detections=int(runtime_cfg["max_detections"]),
        )

        classifier_path_value = artifacts.get("classifier")
        if not classifier_path_value:
            raise PipelineUnavailableError("Classifier artifact is not configured.")
        classifier_path = resolve_path(classifier_path_value)
        if not classifier_path.exists():
            raise PipelineUnavailableError(
                f"Classifier weights not found: {classifier_path}. "
                "Train DINOv3 on Kaggle (see notebooks/) or run "
                "`python scripts/download_artifacts.py`."
            )
        classifier = DinoV3FreshnessRuntime(
            weights_path=classifier_path,
            image_size=int(runtime_cfg["classifier_image_size"]),
        )

        return cls(
            detector=detector,
            classifier=classifier,
            max_detections=int(runtime_cfg["max_detections"]),
            fallback_threshold=float(runtime_cfg["fallback_threshold"]),
        )

    def predict(
        self,
        image: Image.Image,
        progress_callback: ProgressCallback | None = None,
    ) -> list[DetectedProduce]:
        image = open_image(image)
        _emit(progress_callback, "image_loaded", "Image decoded and size-checked.", 1, 5)

        _emit(progress_callback, "detector_started", "YOLO26n is localizing produce.", 2, 5)
        detections = self.detector.predict(image)[: self.max_detections]
        _emit(
            progress_callback,
            "detector_done",
            f"YOLO26n returned {len(detections)} produce candidate(s).",
            3,
            5,
        )

        if not detections:
            _emit(
                progress_callback,
                "classifier_started",
                "DINOv3-S/16 is classifying the full image.",
                4,
                5,
            )
            full_image_pred = _predict_many(
                self.classifier,
                [image],
                self.fallback_threshold,
            )[0]
            _emit(progress_callback, "classifier_done", "Classification complete.", 5, 5)
            if full_image_pred.abstain_reason is not None:
                results = [_abstain(image, reason=full_image_pred.abstain_reason)]
            else:
                results = [_from_classifier(full_image_pred, image)]
            _emit(progress_callback, "render_ready", "Rendering field notes.", 5, 5)
            return results

        crops = [crop_box(image, detection.box) for detection in detections]
        classify_inputs = [image, *crops]
        _emit(
            progress_callback,
            "classifier_started",
            f"DINOv3-S/16 is classifying {len(classify_inputs)} view(s).",
            4,
            5,
        )
        predictions = _predict_many(
            self.classifier,
            classify_inputs,
            self.fallback_threshold,
        )
        full_image_pred = predictions[0]
        crop_predictions = predictions[1:]
        _emit(progress_callback, "classifier_done", "Classification complete.", 5, 5)

        results: list[DetectedProduce] = []
        for detection, crop, crop_pred in zip(
            detections,
            crops,
            crop_predictions,
            strict=True,
        ):
            results.append(
                _resolve_crop_prediction(detection, crop, crop_pred, full_image_pred, image)
            )

        results.sort(key=lambda r: r.confidence, reverse=True)
        _emit(progress_callback, "render_ready", "Rendering annotated specimen plate.", 5, 5)
        return results
