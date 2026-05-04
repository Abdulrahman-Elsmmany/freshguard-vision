"""Label normalization and parsing helpers.

The 12 canonical produce types unify the Kaggle dataset's folder names:
- `Bellpepper` and `Capciscum` both map to `bellpepper` (user-verified
  to be the same vegetable).
- `Bittergroud` (typo) maps to `bitter_gourd`.
- `Okara` (typo — okara is fermented soybean pulp, a different food)
  maps to `okra`.
"""

from __future__ import annotations

import re
from pathlib import Path

from freshness.constants import (
    COMBINED_CLASSES,
    COMBINED_UNKNOWN,
    FRESHNESS_DISPLAY_NAMES,
    FRESHNESS_LEVELS,
    FRESHNESS_NA,
    OUTPUT_FRESHNESS_LABELS,
    OUTPUT_TYPE_LABELS,
    PRODUCE_TYPES,
    TYPE_DISPLAY_NAMES,
    UNKNOWN_TYPE,
)

TYPE_ALIASES: dict[str, str] = {
    "apple": "apple",
    "apples": "apple",
    "banana": "banana",
    "bananas": "banana",
    # Bellpepper + Capciscum/Capsicum all collapse to one canonical class.
    "bellpepper": "bellpepper",
    "bellpeppers": "bellpepper",
    "bell_pepper": "bellpepper",
    "bell_peppers": "bellpepper",
    "pepper": "bellpepper",
    "peppers": "bellpepper",
    "capsicum": "bellpepper",
    "capsicums": "bellpepper",
    "capciscum": "bellpepper",
    "capciscums": "bellpepper",
    "bittergourd": "bitter_gourd",
    "bittergourds": "bitter_gourd",
    "bitter_gourd": "bitter_gourd",
    "bitter_gourds": "bitter_gourd",
    "bittergroud": "bitter_gourd",
    "bittergrounds": "bitter_gourd",
    "carrot": "carrot",
    "carrots": "carrot",
    "cucumber": "cucumber",
    "cucumbers": "cucumber",
    "mango": "mango",
    "mangos": "mango",
    "mangoes": "mango",
    "okra": "okra",
    "okras": "okra",
    "okara": "okra",
    "okaras": "okra",
    "orange": "orange",
    "oranges": "orange",
    "potato": "potato",
    "potatoes": "potato",
    "strawberry": "strawberry",
    "strawberries": "strawberry",
    "tomato": "tomato",
    "tomatoes": "tomato",
}

FRESHNESS_ALIASES: dict[str, str] = {
    "fresh": "fresh",
    "purefresh": "fresh",
    "pure_fresh": "fresh",
    "good": "fresh",
    "healthy": "fresh",
    "ripe": "fresh",
    "normal": "fresh",
    "unripe": "fresh",
    "rotten": "rotten",
    "rotton": "rotten",
    "rot": "rotten",
    "stale": "rotten",
    "spoiled": "rotten",
    "spoilt": "rotten",
    "bad": "rotten",
    "moldy": "rotten",
    "mouldy": "rotten",
    "decayed": "rotten",
    "damaged": "rotten",
    "defective": "rotten",
    "diseased": "rotten",
    "unhealthy": "rotten",
    "overripe": "rotten",
    "n/a": FRESHNESS_NA,
    "na": FRESHNESS_NA,
    "n_a": FRESHNESS_NA,
}

AMBIGUOUS_FRESHNESS_TOKENS = {"medium", "mixed", "unknown", "unlabelled", "unlabeled"}


def tokenize_label_text(value: str) -> list[str]:
    lowered = value.lower()
    return [token for token in re.split(r"[^a-z0-9]+", lowered) if token]


def _collapse(value: str) -> str:
    return "".join(tokenize_label_text(value))


def normalize_type_name(value: str) -> str:
    collapsed = _collapse(value)
    if collapsed in TYPE_ALIASES:
        return TYPE_ALIASES[collapsed]
    for alias, produce_type in sorted(
        TYPE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if alias in collapsed:
            return produce_type
    for produce_type in PRODUCE_TYPES:
        if _collapse(produce_type) in collapsed:
            return produce_type
    raise ValueError(f"Unsupported produce type: {value}")


def normalize_freshness_name(value: str) -> str:
    tokens = tokenize_label_text(value)
    if any(token in AMBIGUOUS_FRESHNESS_TOKENS for token in tokens):
        raise ValueError(f"Unsupported freshness label: {value}")
    collapsed = "".join(tokens)
    if collapsed in FRESHNESS_ALIASES:
        return FRESHNESS_ALIASES[collapsed]
    for alias, freshness in sorted(
        FRESHNESS_ALIASES.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if collapsed.startswith(alias):
            return freshness
    for freshness in FRESHNESS_LEVELS:
        if freshness in tokens:
            return freshness
    raise ValueError(f"Unsupported freshness label: {value}")


def infer_type_from_path(path: Path) -> str:
    candidates = [path.stem, *reversed(path.parts[:-1])]
    for candidate in candidates:
        try:
            return normalize_type_name(candidate)
        except ValueError:
            continue
    raise ValueError(f"Could not infer produce type from path: {path}")


def infer_freshness_from_path(path: Path) -> str:
    candidates = [path.stem, *reversed(path.parts[:-1])]
    if any(
        token in AMBIGUOUS_FRESHNESS_TOKENS
        for candidate in candidates
        for token in tokenize_label_text(candidate)
    ):
        raise ValueError(f"Unsupported freshness label: {path}")
    for candidate in candidates:
        try:
            return normalize_freshness_name(candidate)
        except ValueError:
            continue
    raise ValueError(f"Could not infer freshness label from path: {path}")


def combined_label(produce_type: str, freshness: str) -> str:
    if produce_type == UNKNOWN_TYPE or freshness == FRESHNESS_NA:
        return COMBINED_UNKNOWN
    label = f"{produce_type}_{freshness}"
    if label not in COMBINED_CLASSES:
        raise ValueError(f"Unsupported combined label: {label}")
    return label


def parse_combined_label(value: str) -> tuple[str, str]:
    """Split a 24-class fine-grained label into (produce_type, freshness).

    Accepts any spelling/case the alias tables recognize. Returns the
    canonical pair, or (UNKNOWN_TYPE, FRESHNESS_NA) for the unknown class.
    """
    stripped = value.strip().lower()
    if stripped in {COMBINED_UNKNOWN, UNKNOWN_TYPE, "n_a", "na"}:
        return UNKNOWN_TYPE, FRESHNESS_NA
    # Prefer suffix split — produce names can contain underscores
    # (bitter_gourd, bell_pepper) so try the freshness suffix first.
    for freshness in FRESHNESS_LEVELS:
        suffix = f"_{freshness}"
        if stripped.endswith(suffix):
            type_part = stripped[: -len(suffix)]
            return normalize_type_name(type_part), freshness
    if "__" in stripped:
        type_part, freshness_part = stripped.split("__", maxsplit=1)
        return normalize_type_name(type_part), normalize_freshness_name(freshness_part)
    raise ValueError(f"Expected '<type>_<freshness>' label, got: {value}")


def display_type_name(value: str) -> str:
    return TYPE_DISPLAY_NAMES.get(value, value.replace("_", " ").title())


def display_freshness_name(value: str) -> str:
    return FRESHNESS_DISPLAY_NAMES.get(value, value.upper())


def display_combined_name(combined: str) -> str:
    produce_type, freshness = parse_combined_label(combined)
    if produce_type == UNKNOWN_TYPE:
        return display_type_name(UNKNOWN_TYPE)
    return f"{display_freshness_name(freshness)} {display_type_name(produce_type)}"


def is_supported_type(value: str) -> bool:
    return value in OUTPUT_TYPE_LABELS


def is_supported_freshness(value: str) -> bool:
    return value in OUTPUT_FRESHNESS_LABELS


def is_supported_combined(value: str) -> bool:
    return value in COMBINED_CLASSES or value == COMBINED_UNKNOWN
