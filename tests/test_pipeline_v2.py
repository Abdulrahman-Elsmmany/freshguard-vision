from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from freshness.constants import COMBINED_CLASSES, COMBINED_UNKNOWN, FRESHNESS_NA, UNKNOWN_TYPE
from freshness.inference.classifier import ClassifierPrediction, _validate_class_names
from freshness.inference.detector import Detection
from freshness.inference.pipeline import FreshnessPipeline, PipelineUnavailableError


def _prediction(label: str, confidence: float = 0.9, abstain_reason: str | None = None) -> ClassifierPrediction:
    if label == COMBINED_UNKNOWN:
        produce_type = UNKNOWN_TYPE
        freshness = FRESHNESS_NA
    else:
        produce_type, freshness = label.rsplit("_", maxsplit=1)
    return ClassifierPrediction(
        combined_label=label if abstain_reason is None else COMBINED_UNKNOWN,
        produce_type=produce_type if abstain_reason is None else UNKNOWN_TYPE,
        freshness=freshness if abstain_reason is None else FRESHNESS_NA,
        confidence=confidence,
        probabilities={label: confidence},
        entropy=0.2,
        top2_margin=0.5,
        abstain_reason=abstain_reason,
    )


class FakeDetector:
    def __init__(self, detections: list[Detection]) -> None:
        self._detections = detections

    def predict(self, image: Image.Image) -> list[Detection]:
        return self._detections


class FakeClassifier:
    def __init__(self, predictions: list[ClassifierPrediction]) -> None:
        self._predictions = predictions

    def predict(self, image: Image.Image, fallback_threshold: float = 0.4) -> ClassifierPrediction:
        if not self._predictions:
            raise AssertionError("No fake classifier predictions left.")
        return self._predictions.pop(0)


class PipelineV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.image = Image.new("RGB", (100, 100), "white")
        self.box = (10.0, 10.0, 90.0, 90.0)

    def _pipeline(
        self,
        detections: list[Detection],
        predictions: list[ClassifierPrediction],
    ) -> FreshnessPipeline:
        return FreshnessPipeline(
            detector=FakeDetector(detections),  # type: ignore[arg-type]
            classifier=FakeClassifier(predictions),  # type: ignore[arg-type]
            max_detections=8,
            fallback_threshold=0.4,
        )

    def test_crop_classifier_labels_detection_when_full_image_agrees(self) -> None:
        pipeline = self._pipeline(
            [Detection(confidence=0.8, box=self.box)],
            [_prediction("apple_fresh"), _prediction("apple_fresh", confidence=0.87)],
        )

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].box, self.box)
        self.assertEqual(result[0].combined_label, "apple_fresh")
        self.assertEqual(result[0].source, "classifier")
        self.assertAlmostEqual(result[0].confidence, 0.87)

    def test_crop_full_image_type_disagreement_abstains(self) -> None:
        pipeline = self._pipeline(
            [Detection(confidence=0.8, box=self.box)],
            [_prediction("banana_fresh"), _prediction("apple_fresh")],
        )

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].combined_label, COMBINED_UNKNOWN)
        self.assertEqual(result[0].source, "unknown")
        self.assertEqual(result[0].abstain_reason, "crop_full_image_disagree")

    def test_crop_classifier_abstain_abstains_box(self) -> None:
        pipeline = self._pipeline(
            [Detection(confidence=0.8, box=self.box)],
            [_prediction("apple_fresh"), _prediction("apple_fresh", abstain_reason="low_top1")],
        )

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].combined_label, COMBINED_UNKNOWN)
        self.assertEqual(result[0].abstain_reason, "low_top1")

    def test_no_detections_uses_full_image_classifier(self) -> None:
        pipeline = self._pipeline([], [_prediction("tomato_rotten", confidence=0.77)])

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].box, (0.0, 0.0, 100.0, 100.0))
        self.assertEqual(result[0].combined_label, "tomato_rotten")
        self.assertEqual(result[0].source, "classifier")

    def test_missing_classifier_artifact_makes_pipeline_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            detector = root / "detector.pt"
            detector.write_bytes(b"placeholder")
            config = root / "inference.toml"
            config.write_text(
                "\n".join(
                    [
                        "[runtime]",
                        'default_mode = "torch"',
                        "detector_confidence = 0.40",
                        "detector_iou = 0.45",
                        "max_detections = 8",
                        "classifier_image_size = 256",
                        "fallback_threshold = 0.4",
                        "",
                        "[artifacts]",
                        f'detector = "{detector.as_posix()}"',
                        f'classifier = "{(root / "missing.pt").as_posix()}"',
                    ]
                )
            )

            with self.assertRaises(PipelineUnavailableError):
                FreshnessPipeline.from_config(config)

    def test_classifier_class_names_must_match_contract(self) -> None:
        self.assertEqual(_validate_class_names({"class_names": COMBINED_CLASSES}), COMBINED_CLASSES)

        with self.assertRaises(ValueError):
            _validate_class_names({"class_names": ("apple_fresh",)})


if __name__ == "__main__":
    unittest.main()
