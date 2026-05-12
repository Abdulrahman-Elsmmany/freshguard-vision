"""DINOv3-S/16 24-class freshness classifier runtime.

The v2 rebuild described in STORY.md Act 5 moves type and freshness
authority out of the detector. YOLO26n only localizes produce; this runtime
classifies each crop into the existing 24-class contract and keeps the Phase
A abstain stack: top-1 floor, entropy gate, top-2 margin, and hflip TTA.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence

import numpy as np
import torch
from PIL import Image
from torch import nn

from freshness.constants import (
    COMBINED_CLASSES,
    COMBINED_UNKNOWN,
    FRESHNESS_NA,
    IMAGENET_MEAN,
    IMAGENET_STD,
    UNKNOWN_TYPE,
)
from freshness.utils.images import open_image
from freshness.utils.labels import parse_combined_label

DINO_V3_TIMM_NAME = "vit_small_patch16_dinov3"
DEFAULT_IMAGE_SIZE = 256
DEFAULT_CROP_PCT = 1.0
DEFAULT_INTERPOLATION = Image.BICUBIC
DEFAULT_HEAD_HIDDEN_DIM = 512

# Abstain thresholds (24-class softmax: max entropy = log(24) ~= 3.178 nats).
DEFAULT_TOP1_THRESHOLD = 0.4
DEFAULT_TOP2_MARGIN = 0.15
DEFAULT_ENTROPY_THRESHOLD = 2.5


@dataclass(slots=True)
class ClassifierPrediction:
    combined_label: str
    produce_type: str
    freshness: str
    confidence: float
    probabilities: dict[str, float]
    entropy: float
    top2_margin: float
    abstain_reason: str | None


class DinoV3FreshnessModel(nn.Module):
    """DINOv3-S/16 feature extractor plus the v2 MLP classification head."""

    def __init__(
        self,
        *,
        model_name: str = DINO_V3_TIMM_NAME,
        num_classes: int = len(COMBINED_CLASSES),
        head_hidden_dim: int = DEFAULT_HEAD_HIDDEN_DIM,
    ) -> None:
        super().__init__()

        import timm

        self.backbone = timm.create_model(model_name, pretrained=False, num_classes=0)
        feature_dim = int(self.backbone.num_features)
        self.head = nn.Sequential(
            nn.Linear(feature_dim, head_hidden_dim),
            nn.GELU(),
            nn.Dropout(p=0.1),
            nn.Linear(head_hidden_dim, num_classes),
        )

    def forward(self, tensor: torch.Tensor) -> torch.Tensor:
        features = self.backbone(tensor)
        return self.head(features)


def _preprocess(image: Image.Image, image_size: int, crop_pct: float = DEFAULT_CROP_PCT) -> torch.Tensor:
    """Match the DINOv3 eval transform recorded in the v2 checkpoint."""
    img = image.convert("RGB")
    resize_to = int(round(image_size / crop_pct))

    width, height = img.size
    if width < height:
        new_w = resize_to
        new_h = int(round(height * resize_to / width))
    else:
        new_h = resize_to
        new_w = int(round(width * resize_to / height))
    img = img.resize((new_w, new_h), DEFAULT_INTERPOLATION)

    left = (new_w - image_size) // 2
    top = (new_h - image_size) // 2
    img = img.crop((left, top, left + image_size, top + image_size))

    array = np.asarray(img).astype("float32") / 255.0
    array = (array - np.array(IMAGENET_MEAN, dtype=np.float32)) / np.array(
        IMAGENET_STD, dtype=np.float32
    )
    chw = np.transpose(array, (2, 0, 1))
    return torch.from_numpy(chw).unsqueeze(0)


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max()
    exp = np.exp(shifted)
    return exp / exp.sum()


def _entropy_nats(probs: np.ndarray) -> float:
    return float(-np.sum(probs * np.log(np.clip(probs, 1e-12, 1.0))))


def _prediction_from_probs(
    probs: np.ndarray,
    class_names: tuple[str, ...],
    *,
    fallback_threshold: float,
    top2_margin: float,
    entropy_threshold: float,
) -> ClassifierPrediction:
    probabilities = {
        label: float(prob)
        for label, prob in zip(class_names, probs, strict=True)
    }

    order = np.argsort(probs)[::-1]
    top_label = class_names[int(order[0])]
    top_prob = float(probs[int(order[0])])
    second_prob = float(probs[int(order[1])]) if len(order) > 1 else 0.0
    margin = top_prob - second_prob
    entropy = _entropy_nats(probs)

    abstain_reason: str | None = None
    if top_prob < fallback_threshold:
        abstain_reason = "low_top1"
    elif entropy > entropy_threshold:
        abstain_reason = "high_entropy"
    elif margin < top2_margin:
        abstain_reason = "narrow_margin"

    if abstain_reason is not None:
        return ClassifierPrediction(
            combined_label=COMBINED_UNKNOWN,
            produce_type=UNKNOWN_TYPE,
            freshness=FRESHNESS_NA,
            confidence=top_prob,
            probabilities=probabilities,
            entropy=entropy,
            top2_margin=margin,
            abstain_reason=abstain_reason,
        )

    produce_type, freshness = parse_combined_label(top_label)
    return ClassifierPrediction(
        combined_label=top_label,
        produce_type=produce_type,
        freshness=freshness,
        confidence=top_prob,
        probabilities=probabilities,
        entropy=entropy,
        top2_margin=margin,
        abstain_reason=None,
    )


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
            "Refusing to load to avoid silent label mismatch."
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


class DinoV3FreshnessRuntime:
    """Load and run the v2 DINOv3 classifier described in STORY.md Act 5."""

    def __init__(
        self,
        weights_path: str | Path,
        image_size: int = DEFAULT_IMAGE_SIZE,
        device: str | None = None,
        crop_pct: float | None = None,
    ) -> None:
        self.weights_path = Path(weights_path)
        self.image_size = image_size
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        checkpoint = torch.load(self.weights_path, map_location=self.device, weights_only=True)
        self.class_names = _validate_class_names(checkpoint)

        if isinstance(checkpoint, dict):
            model_name = str(checkpoint.get("model_name", DINO_V3_TIMM_NAME))
            self.image_size = int(checkpoint.get("image_size", image_size))
            self.crop_pct = float(checkpoint.get("crop_pct", crop_pct or DEFAULT_CROP_PCT))
            head_hidden_dim = int(checkpoint.get("head_hidden_dim", DEFAULT_HEAD_HIDDEN_DIM))
        else:
            model_name = DINO_V3_TIMM_NAME
            self.crop_pct = crop_pct or DEFAULT_CROP_PCT
            head_hidden_dim = DEFAULT_HEAD_HIDDEN_DIM

        if model_name != DINO_V3_TIMM_NAME:
            raise ValueError(
                f"Unsupported classifier model_name={model_name!r}; "
                f"expected {DINO_V3_TIMM_NAME!r}."
            )

        self.model = DinoV3FreshnessModel(
            model_name=model_name,
            num_classes=len(self.class_names),
            head_hidden_dim=head_hidden_dim,
        )
        self.model.load_state_dict(_extract_state_dict(checkpoint))
        self.model.to(self.device)
        self.model.eval()

    def predict(
        self,
        image: Image.Image,
        fallback_threshold: float = DEFAULT_TOP1_THRESHOLD,
        top2_margin: float = DEFAULT_TOP2_MARGIN,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ) -> ClassifierPrediction:
        """Classify one image or crop, returning an abstain reason when uncommitted."""
        return self.predict_many(
            [image],
            fallback_threshold=fallback_threshold,
            top2_margin=top2_margin,
            entropy_threshold=entropy_threshold,
        )[0]

    def predict_many(
        self,
        images: Sequence[Image.Image],
        fallback_threshold: float = DEFAULT_TOP1_THRESHOLD,
        top2_margin: float = DEFAULT_TOP2_MARGIN,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ) -> list[ClassifierPrediction]:
        """Classify multiple images in one batched DINOv3 forward pass."""
        if not images:
            return []

        tensors = [
            _preprocess(open_image(image), self.image_size, self.crop_pct)
            for image in images
        ]
        tensor = torch.cat(tensors, dim=0).to(self.device)
        tensor_flip = torch.flip(tensor, dims=[3])

        with torch.inference_mode():
            logits = self.model(tensor).cpu().numpy()
            logits_flip = self.model(tensor_flip).cpu().numpy()

        probs = np.stack(
            [
                (_softmax(single_logits) + _softmax(single_logits_flip)) / 2.0
                for single_logits, single_logits_flip in zip(logits, logits_flip, strict=True)
            ]
        )

        return [
            _prediction_from_probs(
                row,
                self.class_names,
                fallback_threshold=fallback_threshold,
                top2_margin=top2_margin,
                entropy_threshold=entropy_threshold,
            )
            for row in probs
        ]
