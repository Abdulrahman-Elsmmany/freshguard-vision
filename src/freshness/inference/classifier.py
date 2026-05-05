"""EfficientNetV2-S 24-class classifier — used as fallback and ensemble vote.

Two roles:
  1. Fallback path: invoked when the YOLO26 detector returns zero boxes.
  2. Per-detection check: invoked on each detector crop so the pipeline can
     ensemble detector + classifier votes and abstain on disagreement.

Preprocessing matches the training-time eval transform (timm
`create_transform(is_training=False, crop_pct=0.95, interpolation="bicubic")`):
resize short edge to ``int(round(image_size / crop_pct))``, then center-crop
to ``image_size × image_size``. Inference uses horizontal-flip TTA
(2-view softmax average) for ~0.5–1.5pp accuracy at modest extra cost.

Abstain logic stacks three signals: top-1 < threshold, top-2 margin too
narrow, and softmax entropy too high (close to uniform — OOD signature).
The reason is surfaced on ``ClassifierPrediction.abstain_reason`` so the
UI can explain *why* the system declined to commit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image

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

EFFICIENTNETV2S_TIMM_NAME = "tf_efficientnetv2_s.in21k_ft_in1k"

# Training eval transform parameters (must match notebook 4)
DEFAULT_CROP_PCT = 0.95
DEFAULT_INTERPOLATION = Image.BICUBIC

# Abstain thresholds (24-class softmax: max entropy = log(24) ≈ 3.178 nats).
# Top-1 at 0.4 strikes the balance: lets the classifier commit on real apple
# images where it's genuinely confident (e.g. apple_rotten @ 0.407 on the
# wrinkled-apple test) while still abstaining on out-of-distribution noise
# where it's confused (top-1 in the 0.2-0.35 range). The pipeline-level
# ensemble adds a second guard: even when this commits, the detector's
# vote still has to corroborate (at least on freshness) before we publish.
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
    abstain_reason: str | None  # None when committing to a label


def _preprocess(image: Image.Image, image_size: int, crop_pct: float = DEFAULT_CROP_PCT) -> torch.Tensor:
    """Match timm eval transform: short-edge resize → center crop → ImageNet norm.

    Critical that this stays in sync with notebook 4's ``eval_transform``
    (``create_transform(is_training=False, interpolation="bicubic", crop_pct=0.95)``).
    Square-stretching the input — the previous behavior — destroyed aspect
    ratio and shifted the test distribution away from training.
    """
    img = image.convert("RGB")
    resize_to = int(round(image_size / crop_pct))

    # Resize short edge while preserving aspect ratio (timm semantics).
    width, height = img.size
    if width < height:
        new_w = resize_to
        new_h = int(round(height * resize_to / width))
    else:
        new_h = resize_to
        new_w = int(round(width * resize_to / height))
    img = img.resize((new_w, new_h), DEFAULT_INTERPOLATION)

    # Center crop to the target size.
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
    # Clip to avoid log(0); 1e-12 is safely below any meaningful softmax mass.
    return float(-np.sum(probs * np.log(np.clip(probs, 1e-12, 1.0))))


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
        crop_pct: float | None = None,
    ) -> None:
        self.weights_path = Path(weights_path)
        self.image_size = image_size
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        checkpoint = torch.load(self.weights_path, map_location=self.device, weights_only=True)
        self.class_names = _validate_class_names(checkpoint)

        # Prefer values baked into the checkpoint when present (forward-compatible
        # with notebook-4 changes that persist these alongside the weights).
        self.image_size = int(checkpoint.get("image_size", image_size)) if isinstance(checkpoint, dict) else image_size
        self.crop_pct = float(
            (checkpoint.get("crop_pct", crop_pct) if isinstance(checkpoint, dict) else crop_pct)
            or DEFAULT_CROP_PCT
        )

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
        fallback_threshold: float = DEFAULT_TOP1_THRESHOLD,
        top2_margin: float = DEFAULT_TOP2_MARGIN,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ) -> ClassifierPrediction:
        prepared = open_image(image)
        tensor = _preprocess(prepared, self.image_size, self.crop_pct).to(self.device)

        # Horizontal-flip TTA: average softmax over the original and its flip.
        # `[3]` is the W axis on a (1, C, H, W) tensor.
        tensor_flip = torch.flip(tensor, dims=[3])
        with torch.no_grad():
            logits = self.model(tensor).cpu().numpy()[0]
            logits_flip = self.model(tensor_flip).cpu().numpy()[0]
        probs = (_softmax(logits) + _softmax(logits_flip)) / 2.0

        probabilities = {
            label: float(prob)
            for label, prob in zip(self.class_names, probs, strict=True)
        }

        # Top-1 and top-2 margin via argsort (descending).
        order = np.argsort(probs)[::-1]
        top_label = self.class_names[int(order[0])]
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
