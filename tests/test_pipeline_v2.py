from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import torch
from PIL import Image
from torch import nn

from freshness.constants import COMBINED_CLASSES, COMBINED_UNKNOWN, FRESHNESS_NA, UNKNOWN_TYPE
from freshness.inference.classifier import (
    ClassifierPrediction,
    DinoV3FreshnessRuntime,
    _validate_class_names,
)
from freshness.inference.detector import Detection
from freshness.inference.pipeline import FreshnessPipeline, PipelineUnavailableError
from freshness.utils.images import open_image


def _prediction(
    label: str,
    confidence: float = 0.9,
    abstain_reason: str | None = None,
    probabilities: dict[str, float] | None = None,
    top2_margin: float = 0.5,
) -> ClassifierPrediction:
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
        probabilities=probabilities or {label: confidence},
        entropy=0.2,
        top2_margin=top2_margin,
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


class ConstantLogitModel(nn.Module):
    def __init__(self, winner_index: int) -> None:
        super().__init__()
        self.winner_index = winner_index

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        logits = torch.zeros((tensor.shape[0], len(COMBINED_CLASSES)), dtype=torch.float32)
        logits[:, self.winner_index] = 10.0
        return logits


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
            max_detections=12,
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

    def test_no_detections_abstains_without_closed_set_guess(self) -> None:
        pipeline = self._pipeline([], [])

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].box, (0.0, 0.0, 100.0, 100.0))
        self.assertEqual(result[0].combined_label, COMBINED_UNKNOWN)
        self.assertEqual(result[0].source, "unknown")
        self.assertEqual(result[0].abstain_reason, "no_produce_detected")

    def test_scene_level_box_is_suppressed_when_item_box_exists(self) -> None:
        full_frame = Detection(confidence=0.9, box=(0.0, 0.0, 100.0, 100.0))
        item_box = Detection(confidence=0.4, box=self.box)
        pipeline = self._pipeline(
            [full_frame, item_box],
            [_prediction("apple_fresh"), _prediction("apple_fresh", confidence=0.86)],
        )

        result = pipeline.predict(self.image)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].box, self.box)
        self.assertEqual(result[0].combined_label, "apple_fresh")

    def test_large_weak_single_box_rejects_as_non_produce(self) -> None:
        pipeline = self._pipeline(
            [Detection(confidence=0.89, box=(0.0, 0.0, 100.0, 100.0))],
            [
                _prediction("cucumber_fresh", confidence=0.48),
                _prediction("cucumber_fresh", confidence=0.44),
            ],
        )

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].combined_label, COMBINED_UNKNOWN)
        self.assertEqual(result[0].source, "unknown")
        self.assertEqual(result[0].abstain_reason, "non_produce_image")

    def test_same_type_freshness_uncertainty_keeps_type(self) -> None:
        probabilities = {
            "apple_rotten": 0.47,
            "apple_fresh": 0.44,
            "bellpepper_rotten": 0.06,
            "tomato_fresh": 0.03,
        }
        pipeline = self._pipeline(
            [Detection(confidence=0.39, box=self.box)],
            [
                _prediction("apple_fresh", abstain_reason="low_top1"),
                _prediction(
                    "apple_rotten",
                    confidence=0.47,
                    abstain_reason="narrow_margin",
                    probabilities=probabilities,
                    top2_margin=0.03,
                ),
            ],
        )

        result = pipeline.predict(self.image)

        self.assertEqual(result[0].combined_label, "apple_n_a")
        self.assertEqual(result[0].produce_type, "apple")
        self.assertEqual(result[0].freshness, FRESHNESS_NA)
        self.assertEqual(result[0].source, "classifier")
        self.assertEqual(result[0].abstain_reason, "freshness_uncertain")
        self.assertAlmostEqual(result[0].confidence, 0.91)

    def test_progress_callback_reports_pipeline_order(self) -> None:
        pipeline = self._pipeline(
            [Detection(confidence=0.8, box=self.box)],
            [_prediction("apple_fresh"), _prediction("apple_fresh")],
        )
        phases: list[str] = []

        pipeline.predict(self.image, progress_callback=lambda event: phases.append(event.phase))

        self.assertEqual(
            phases,
            [
                "image_loaded",
                "detector_started",
                "detector_done",
                "classifier_started",
                "classifier_done",
                "render_ready",
            ],
        )

    def test_dinov3_predict_many_matches_single_predict(self) -> None:
        runtime = DinoV3FreshnessRuntime.__new__(DinoV3FreshnessRuntime)
        runtime.class_names = COMBINED_CLASSES
        runtime.image_size = 256
        runtime.crop_pct = 1.0
        runtime.device = torch.device("cpu")
        runtime.model = ConstantLogitModel(COMBINED_CLASSES.index("apple_fresh"))

        single = runtime.predict(self.image)
        batched = runtime.predict_many([self.image, self.image])

        self.assertEqual([item.combined_label for item in batched], ["apple_fresh", "apple_fresh"])
        self.assertEqual(batched[0].combined_label, single.combined_label)
        self.assertAlmostEqual(batched[0].confidence, single.confidence)

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
                        "detector_confidence = 0.20",
                        "detector_iou = 0.45",
                        "max_detections = 12",
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

    def test_transparent_uploads_are_composited_before_inference(self) -> None:
        transparent = Image.new("RGBA", (8, 8), (0, 0, 0, 0))

        image = open_image(transparent)

        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))


class LocalImageRegressionTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]
    detector_artifact = repo_root / "artifacts" / "yolo26n_produce_v2_1.pt"
    classifier_artifact = repo_root / "artifacts" / "dinov3_vits16_food_freshness_v2.pt"
    car_image = Path(r"C:\Users\abdoe\Desktop\test_img\DSC_5903.webp")
    grouped_apple_image = Path(r"C:\Users\abdoe\Desktop\test_img\fresh apple.jpg")

    @classmethod
    def setUpClass(cls) -> None:
        if not (
            cls.detector_artifact.exists()
            and cls.classifier_artifact.exists()
            and cls.car_image.exists()
            and cls.grouped_apple_image.exists()
        ):
            raise unittest.SkipTest("Local model artifacts or reported images are unavailable.")
        cls.pipeline = FreshnessPipeline.from_config()

    def test_reported_car_image_rejects_as_unknown(self) -> None:
        image = Image.open(self.car_image).convert("RGB")

        result = self.pipeline.predict(image)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].combined_label, COMBINED_UNKNOWN)
        self.assertEqual(result[0].produce_type, UNKNOWN_TYPE)
        self.assertEqual(result[0].freshness, FRESHNESS_NA)
        self.assertEqual(result[0].source, "unknown")
        self.assertIn(
            result[0].abstain_reason,
            {"no_produce_detected", "non_produce_image"},
        )

    def test_reported_grouped_apples_suppress_full_frame_box(self) -> None:
        image = Image.open(self.grouped_apple_image).convert("RGB")

        result = self.pipeline.predict(image)

        areas = [
            (item.box[2] - item.box[0]) * (item.box[3] - item.box[1])
            / (image.width * image.height)
            for item in result
        ]
        self.assertGreaterEqual(len(result), 4)
        self.assertTrue(all(area < 0.85 for area in areas))
        self.assertGreaterEqual(
            sum(item.produce_type == "apple" for item in result),
            4,
        )


if __name__ == "__main__":
    unittest.main()
