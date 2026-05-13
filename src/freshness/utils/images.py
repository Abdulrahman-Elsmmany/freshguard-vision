"""Image loading, cropping, and drawing helpers."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont

MAX_IMAGE_DIM = 4096

# Specimen-Almanac ink colors (sRGB approximations of the OKLCH palette in styles.py)
INK_FRESH = "#5C8C42"      # basil green   ~ oklch(0.55 0.13 145)
INK_ROTTEN = "#A14A1F"     # burnt sienna  ~ oklch(0.45 0.16 30)
INK_UNKNOWN = "#7A6F66"    # warm muted    ~ oklch(0.55 0.020 35)
INK_PLATE = "#FAF6EC"      # paper         ~ oklch(0.97 0.013 70)
INK_PRIMARY = "#2A1F18"    # dark walnut   ~ oklch(0.21 0.025 35)


class ImageTooLargeError(ValueError):
    pass


def _check_size(image: Image.Image) -> None:
    if max(image.width, image.height) > MAX_IMAGE_DIM:
        raise ImageTooLargeError(
            f"Image is {image.width}x{image.height}; "
            f"max supported dimension is {MAX_IMAGE_DIM}px on either side."
        )


def _as_rgb(image: Image.Image) -> Image.Image:
    if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")
    return image.convert("RGB")


def open_image(source: str | Path | bytes | BytesIO | Image.Image) -> Image.Image:
    if isinstance(source, Image.Image):
        image = _as_rgb(source)
    elif isinstance(source, str | Path):
        image = _as_rgb(Image.open(source))
    elif isinstance(source, bytes):
        image = _as_rgb(Image.open(BytesIO(source)))
    elif isinstance(source, BytesIO):
        image = _as_rgb(Image.open(source))
    else:
        raise TypeError(f"Unsupported image source: {type(source)!r}")
    _check_size(image)
    return image


def to_numpy(image: Image.Image) -> np.ndarray:
    return np.asarray(image.convert("RGB"))


def crop_box(image: Image.Image, box: tuple[float, float, float, float]) -> Image.Image:
    x1, y1, x2, y2 = (int(round(value)) for value in box)
    return image.crop((x1, y1, x2, y2)).convert("RGB")


def _try_font(size: int, *, mono: bool = False, italic: bool = False) -> ImageFont.ImageFont:
    """Best-effort load of a system font; falls back to PIL default."""
    candidates: list[str] = []
    if mono:
        candidates += [
            "consola.ttf", "Consolas.ttf",
            "DejaVuSansMono.ttf", "JetBrainsMono-Regular.ttf",
            "Menlo.ttc", "Courier New.ttf",
        ]
    elif italic:
        candidates += [
            "georgia.ttf", "Georgiai.ttf",
            "DejaVuSerif-Italic.ttf", "Times New Roman Italic.ttf",
            "Times New Roman.ttf",
        ]
    else:
        candidates += [
            "arial.ttf", "Arial.ttf", "DejaVuSans.ttf", "Helvetica.ttf",
        ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _resolve_color(value: str | tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, str):
        return ImageColor.getrgb(value)
    return value


def _draw_corner_crosshairs(
    draw: ImageDraw.ImageDraw,
    box: tuple[float, float, float, float],
    color: tuple[int, int, int],
    *,
    arm: int,
    width: int,
) -> None:
    """Draw four L-shaped corner brackets, leaving the box itself open."""
    x1, y1, x2, y2 = box
    arm = min(arm, int((x2 - x1) / 3), int((y2 - y1) / 3))
    arm = max(arm, 6)
    # top-left
    draw.line([(x1, y1), (x1 + arm, y1)], fill=color, width=width)
    draw.line([(x1, y1), (x1, y1 + arm)], fill=color, width=width)
    # top-right
    draw.line([(x2 - arm, y1), (x2, y1)], fill=color, width=width)
    draw.line([(x2, y1), (x2, y1 + arm)], fill=color, width=width)
    # bottom-left
    draw.line([(x1, y2 - arm), (x1, y2)], fill=color, width=width)
    draw.line([(x1, y2), (x1 + arm, y2)], fill=color, width=width)
    # bottom-right
    draw.line([(x2 - arm, y2), (x2, y2)], fill=color, width=width)
    draw.line([(x2, y2 - arm), (x2, y2)], fill=color, width=width)


def _draw_specimen_plate(
    draw: ImageDraw.ImageDraw,
    *,
    anchor: tuple[float, float],
    text: str,
    text_color: tuple[int, int, int],
    plate_color: tuple[int, int, int],
    rule_color: tuple[int, int, int],
    font: ImageFont.ImageFont,
    pad_x: int = 6,
    pad_y: int = 3,
) -> tuple[float, float]:
    """Paint a small label plate (paper rectangle + ink hairline + text). Returns the plate's bottom-right corner."""
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x, y = anchor
    rect = (x, y, x + tw + pad_x * 2, y + th + pad_y * 2)
    draw.rectangle(rect, fill=plate_color, outline=rule_color, width=1)
    draw.text((x + pad_x, y + pad_y - bbox[1]), text, fill=text_color, font=font)
    return (rect[2], rect[3])


def draw_boxes(
    image: Image.Image,
    boxes: Iterable[tuple[float, float, float, float]],
    labels: Iterable[str],
    color: str | Sequence[str] = INK_FRESH,
    *,
    specimen_numbers: Sequence[str] | None = None,
    latin_names: Sequence[str] | None = None,
) -> Image.Image:
    """Render Specimen-Almanac style annotations on `image`.

    Each detection gets four L-shaped corner crosshairs (no full rectangle),
    a monospace specimen number plate at the top-left, and an italic Latin
    name plate below the bottom-left corner.

    `color` may be a single string (legacy) or one entry per box.
    """
    output = image.copy()
    draw = ImageDraw.Draw(output, "RGB")
    boxes = list(boxes)
    labels = list(labels)
    n = len(boxes)
    if isinstance(color, str):
        colors = [color] * n
    else:
        colors = list(color)
        if len(colors) < n:
            colors += [colors[-1] if colors else INK_FRESH] * (n - len(colors))
    specimen_numbers = list(specimen_numbers or [f"No {i + 1:03d}" for i in range(n)])
    latin_names = list(latin_names or [""] * n)

    plate_color = _resolve_color(INK_PLATE)
    rule_color = _resolve_color(INK_PRIMARY)

    longest_side = max(image.width, image.height)
    crosshair_width = max(2, int(round(longest_side / 320)))
    crosshair_arm = max(14, int(round(longest_side / 60)))
    plate_font_size = max(10, int(round(longest_side / 75)))
    label_font_size = max(11, int(round(longest_side / 70)))

    plate_font = _try_font(plate_font_size, mono=True)
    label_font = _try_font(label_font_size, italic=True)

    for box, label_text, raw_color, specimen_no, latin in zip(
        boxes, labels, colors, specimen_numbers, latin_names, strict=False
    ):
        rgb = _resolve_color(raw_color)
        x1, y1, x2, y2 = box
        _draw_corner_crosshairs(
            draw, (x1, y1, x2, y2), rgb,
            arm=crosshair_arm, width=crosshair_width,
        )

        # Top-left specimen plate (e.g. "No 001  TOMATO_FRESH  0.94")
        plate_text = specimen_no
        if label_text:
            plate_text = f"{specimen_no}  {label_text}"
        plate_y = max(2.0, y1 - plate_font_size - 10)
        _draw_specimen_plate(
            draw,
            anchor=(x1, plate_y),
            text=plate_text,
            text_color=rgb,
            plate_color=plate_color,
            rule_color=rule_color,
            font=plate_font,
        )

        # Bottom-left Latin name (italic), only if it fits within image
        if latin:
            latin_y = y2 + 4
            if latin_y + label_font_size + 8 < image.height:
                _draw_specimen_plate(
                    draw,
                    anchor=(x1, latin_y),
                    text=latin,
                    text_color=rule_color,
                    plate_color=plate_color,
                    rule_color=rule_color,
                    font=label_font,
                    pad_x=5,
                    pad_y=2,
                )

    return output
