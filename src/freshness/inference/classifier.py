"""EfficientNetV2-S 24-class classifier — used as the fallback path.

This runtime is invoked only when the YOLO26 detector returns zero
boxes for a given image. It treats the full image as one crop and
predicts a single fine-grained `<produce>_<freshness>` label.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from freshness.constants import (
    COMBINED_CLASSES,
    IMAGENET_MEAN,
    IMAGENET_STD,
)
from freshness.utils.images import open_image
from freshness.utils.labels import parse_combined_label

EFFICIENTNETV2S_TIMM_NAME = "tf_efficientnetv2_s.in21k_ft_in1k"


@dataclass(slots=True)
class ClassifierPrediction:
    combined_label: str
    produce_type: str
    freshness: str
    confidence: float
    probabilities: dict[str, float]


def _preprocess(image: Image.Image, image_size: int) -> torch.Tensor:
    resized = image.convert("RGB").resize((image_size, image_size))
    array = np.asarray(resized).astype("float32") / 255.0
    array = (array - np.array(IMAGENET_MEAN, dtype=np.float32)) / np.array(
        IMAGENET_STD, dtype=np.float32
    )
    chw = np.transpose(array, (2, 0, 1))
    return torch.from_numpy(chw).unsqueeze(0)


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max()
    exp = np.exp(shifted)
    return exp / exp.sum()


def _extract_state_dict(checkpoint: object) -> dict[str, torch.Tensor]:
    if isinstance(checkpoint, dict):
        for key in ("model_state_dict", "state_dict", "model", "ema_state_dict"):
            value = checkpoint.get(key)
            if isinstance(value, dict):
                return value
        if checkpoint and all(isinstance(key, str) for key in checkpoint):
            return checkpoint  # type: ignore[return-value]
    raise ValueError("Classifier checkpoint does not contain a PyTorch state dict.")


def _validate_class_names(checkpoint: object) -> tuple[str, ...]:
    if not isinstance(checkpoint, dict) or "class_names" not in checkpoint:
        raise ValueError(
            "Classifier checkpoint is missing a 'class_names' field. "
            "Refusing to load to avoid silent label mismatch — retrain "
            "with `class_names` saved into the checkpoint dict."
        )
    class_names = tuple(str(name) for name in checkpoint["class_names"])
    expected = set(COMBINED_CLASSES)
    if set(class_names) != expected:
        missing = expected - set(class_names)
        extra = set(class_names) - expected
        raise ValueError(
            "Classifier checkpoint class_names do not match the 24-class contract. "
            f"missing={sorted(missing)} extra={sorted(extra)}"
        )
    return class_names


class EfficientNetV2SFreshnessRuntime:
    def __init__(
        self,
        weights_path: str | Path,
        image_size: int = 224,
        device: str | None = None,
    ) -> None:
        self.weights_path = Path(weights_path)
        self.image_size = image_size
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        checkpoint = torch.load(self.weights_path, map_location=self.device, weights_only=True)
        self.class_names = _validate_class_names(checkpoint)

        import timm

        self.model = timm.create_model(
            EFFICIENTNETV2S_TIMM_NAME,
            pretrained=False,
            num_classes=len(self.class_names),
        )
        self.model.load_state_dict(_extract_state_dict(checkpoint))
        self.model.to(self.device)
        self.model.eval()

    def predict(
        self,
        image: Image.Image,
        fallback_threshold: float = 0.4,
    ) -> ClassifierPrediction:
        tensor = _preprocess(open_image(image), self.image_size).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor).cpu().numpy()[0]
        probs = _softmax(logits)
        probabilities = {
            label: float(prob)
            for label, prob in zip(self.class_names, probs, strict=True)
        }
        top_label = max(probabilities, key=probabilities.get)
        top_prob = probabilities[top_label]

        from freshness.constants import COMBINED_UNKNOWN, FRESHNESS_NA, UNKNOWN_TYPE

        if top_prob < fallback_threshold:
            return ClassifierPrediction(
                combined_label=COMBINED_UNKNOWN,
                produce_type=UNKNOWN_TYPE,
                freshness=FRESHNESS_NA,
                confidence=top_prob,
                probabilities=probabilities,
            )

        produce_type, freshness = parse_combined_label(top_label)
        return ClassifierPrediction(
            combined_label=top_label,
            produce_type=produce_type,
            freshness=freshness,
            confidence=top_prob,
            probabilities=probabilities,
        )
