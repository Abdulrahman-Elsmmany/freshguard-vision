"""Ultralytics YOLO26 detector wrapper for the v2 produce-only contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image


@dataclass(slots=True)
class Detection:
    """A localized produce candidate.

    In v2 the detector is deliberately class-agnostic from the app's point of
    view. YOLO26n is trained with one class, ``produce``, and the DINOv3
    classifier supplies all type and freshness labels downstream.
    """

    confidence: float
    box: tuple[float, float, float, float]


class YOLO26Detector:
    """Run the v2 YOLO26n produce localizer."""

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.20,
        iou: float = 0.45,
        max_detections: int = 12,
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
        """Return produce boxes sorted by detector confidence."""
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

        for box, conf in zip(
            result.boxes.xyxy.tolist(),
            result.boxes.conf.tolist(),
            strict=False,
        ):
            detections.append(
                Detection(
                    confidence=float(conf),
                    box=tuple(float(value) for value in box),
                )
            )

        detections.sort(key=lambda item: item.confidence, reverse=True)
        return detections
