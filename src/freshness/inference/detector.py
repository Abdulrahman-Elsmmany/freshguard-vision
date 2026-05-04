"""Ultralytics YOLO26 detector wrapper.

Emits 24-class fine-grained Detections directly: each box carries the
combined `<produce>_<freshness>` label produced by YOLO26 in a single
forward pass. No second-stage classification on the hot path.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from freshness.utils.labels import parse_combined_label


@dataclass(slots=True)
class Detection:
    combined_label: str
    produce_type: str
    freshness: str
    confidence: float
    box: tuple[float, float, float, float]


class YOLO26Detector:
    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.25,
        iou: float = 0.45,
        max_detections: int = 8,
    ) -> None:
        self.model_path = Path(model_path)
        self.confidence = confidence
        self.iou = iou
        self.max_detections = max_detections
        self._model: Any | None = None

    def is_ready(self) -> bool:
        return self.model_path.exists()

    def _load(self) -> Any:
        if self._model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Detector weights not found: {self.model_path}")
            from ultralytics import YOLO

            self._model = YOLO(str(self.model_path))
        return self._model

    def predict(self, image: Image.Image) -> list[Detection]:
        model = self._load()
        result = model.predict(
            source=np.array(image.convert("RGB")),
            conf=self.confidence,
            iou=self.iou,
            max_det=self.max_detections,
            verbose=False,
        )[0]

        detections: list[Detection] = []
        if result.boxes is None:
            return detections

        names = result.names
        for box, cls, conf in zip(
            result.boxes.xyxy.tolist(),
            result.boxes.cls.tolist(),
            result.boxes.conf.tolist(),
            strict=False,
        ):
            raw_label = names[int(cls)]
            try:
                produce_type, freshness = parse_combined_label(raw_label)
            except ValueError:
                # Skip detections with labels we can't map onto the 24-class
                # contract (defensive — should never happen with the trained
                # YOLO26s checkpoint).
                continue
            detections.append(
                Detection(
                    combined_label=f"{produce_type}_{freshness}",
                    produce_type=produce_type,
                    freshness=freshness,
                    confidence=float(conf),
                    box=tuple(float(value) for value in box),
                )
            )

        detections.sort(key=lambda item: item.confidence, reverse=True)
        return detections
