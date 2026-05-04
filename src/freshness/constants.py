"""Project-wide constants.

The model contract is a 24-class single-stage classifier:
12 produce types × {fresh, rotten}. The Kaggle dataset's `Bellpepper`
and `Capciscum` folders are the same vegetable (user-verified) and are
merged into one canonical `bellpepper` class. Folder-name typos
`bittergroud` and `okara` are normalized to `bitter_gourd` and `okra`.
"""

from __future__ import annotations

PRODUCE_TYPES: tuple[str, ...] = (
    "apple",
    "banana",
    "bellpepper",
    "bitter_gourd",
    "carrot",
    "cucumber",
    "mango",
    "okra",
    "orange",
    "potato",
    "strawberry",
    "tomato",
)

FRESHNESS_LEVELS: tuple[str, ...] = ("fresh", "rotten")

UNKNOWN_TYPE = "unknown"
FRESHNESS_NA = "n_a"

TYPE_LABELS = PRODUCE_TYPES
FRESHNESS_LABELS = FRESHNESS_LEVELS
OUTPUT_TYPE_LABELS = TYPE_LABELS + (UNKNOWN_TYPE,)
OUTPUT_FRESHNESS_LABELS = FRESHNESS_LABELS + (FRESHNESS_NA,)

COMBINED_CLASSES: tuple[str, ...] = tuple(
    f"{produce}_{freshness}"
    for produce in PRODUCE_TYPES
    for freshness in FRESHNESS_LEVELS
)
COMBINED_UNKNOWN = f"{UNKNOWN_TYPE}_{FRESHNESS_NA}"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

TYPE_DISPLAY_NAMES = {
    "apple": "Apple",
    "banana": "Banana",
    "bellpepper": "Bell Pepper",
    "bitter_gourd": "Bitter Gourd",
    "carrot": "Carrot",
    "cucumber": "Cucumber",
    "mango": "Mango",
    "okra": "Okra",
    "orange": "Orange",
    "potato": "Potato",
    "strawberry": "Strawberry",
    "tomato": "Tomato",
    "unknown": "Unknown / Unsupported",
}

FRESHNESS_DISPLAY_NAMES = {
    "fresh": "Fresh",
    "rotten": "Rotten",
    "n_a": "N/A",
}

PRODUCE_LATIN: dict[str, str] = {
    "apple": "Malus domestica",
    "banana": "Musa acuminata",
    "bellpepper": "Capsicum annuum",
    "bitter_gourd": "Momordica charantia",
    "carrot": "Daucus carota",
    "cucumber": "Cucumis sativus",
    "mango": "Mangifera indica",
    "okra": "Abelmoschus esculentus",
    "orange": "Citrus × sinensis",
    "potato": "Solanum tuberosum",
    "strawberry": "Fragaria × ananassa",
    "tomato": "Solanum lycopersicum",
    "unknown": "Specimen incognitus",
}
