"""Specimen Lab — produce upload + 24-class detection."""

from __future__ import annotations

from io import BytesIO

import streamlit as st
from PIL import Image

from freshness.constants import PRODUCE_LATIN, PRODUCE_TYPES
from freshness.inference.pipeline import DetectedProduce
from freshness.ui.runtime import load_pipeline
from freshness.ui.styles import render_hero, render_section
from freshness.utils.images import (
    INK_FRESH,
    INK_ROTTEN,
    INK_UNKNOWN,
    ImageTooLargeError,
    draw_boxes,
)
from freshness.utils.labels import display_freshness_name, display_type_name

SOURCE_LABEL = {
    "detector": "DETECTOR · YOLO26s",
    "classifier": "FALLBACK · EfficientNetV2-S",
    "ensemble": "ENSEMBLE · CLASSIFIER OVERRIDE",
    "unknown": "ABSTAIN",
}

# Maps the abstain_reason emitted by classifier.py / pipeline.py into
# user-facing copy. Anything not in this table falls back to the generic
# "neither side committed" line.
ABSTAIN_REASON_COPY: dict[str, tuple[str, str]] = {
    "low_top1": (
        "LOW CONFIDENCE",
        "The fallback classifier's top guess sat below the confidence floor — "
        "likely an unfamiliar fruit, a tight crop, or noise.",
    ),
    "high_entropy": (
        "AMBIGUOUS — HIGH ENTROPY",
        "The softmax was spread thin across many classes, the signature of an "
        "out-of-distribution input (watermarks, cross-sections, scenes the "
        "model never saw in training).",
    ),
    "narrow_margin": (
        "TOO CLOSE TO CALL",
        "The top two classes were within a few percent of each other. The "
        "system declined to commit when both options were plausible.",
    ),
    "detector_classifier_disagree": (
        "DETECTOR ↔ CLASSIFIER DISAGREEMENT",
        "The detector and fallback classifier voted for different produce "
        "types with similar confidence. Honest abstain rather than picking "
        "the louder one.",
    ),
    "no_classifier": (
        "NO FALLBACK AVAILABLE",
        "The detector found nothing and no fallback classifier is loaded.",
    ),
}

STATE_INK = {
    "fresh": INK_FRESH,
    "rotten": INK_ROTTEN,
    "n_a": INK_UNKNOWN,
}


def _state_class(freshness: str, source: str) -> str:
    if source == "unknown" or freshness == "n_a":
        return "unknown"
    return freshness


def _ink_for(detection: DetectedProduce) -> str:
    if detection.source == "unknown":
        return INK_UNKNOWN
    return STATE_INK.get(detection.freshness, INK_UNKNOWN)


def _render_specimen_card(detection: DetectedProduce, index: int) -> None:
    """Render one detection as a botanical specimen label."""
    state_cls = _state_class(detection.freshness, detection.source)
    # Reuse the existing CSS classes; "ensemble" piggybacks on the
    # classifier styling since it represents the same model voting.
    source_cls = (
        detection.source
        if detection.source in {"detector", "classifier", "unknown"}
        else "classifier"
    )
    latin = PRODUCE_LATIN.get(detection.produce_type, "Specimen incognitus")
    display_type = display_type_name(detection.produce_type)
    display_state = display_freshness_name(detection.freshness)
    confidence_str = (
        f"{detection.confidence:.4f}"
        if detection.source != "unknown"
        else "—"
    )
    source_label = SOURCE_LABEL.get(detection.source, detection.source.upper())

    state_label_html = (
        f'<span class="fg-card__attr-value fg-card__attr-value--state-{state_cls}">'
        f'{display_state}</span>'
        if state_cls != "unknown"
        else '<span class="fg-card__attr-value fg-card__attr-value--state-unknown">N / A</span>'
    )

    st.markdown(
        f"""
        <div class="fg-card">
          <div class="fg-card__row">
            <div class="fg-card__sn">SPECIMEN No {index + 1:03d}</div>
            <div class="fg-card__source fg-card__source--{source_cls}">
              <span class="fg-card__source-dot"></span>{source_label}
            </div>
          </div>
          <div class="fg-card__latin">{latin}</div>
          <div class="fg-card__display">{display_type}</div>
          <div class="fg-card__divider"></div>
          <div class="fg-card__attrs">
            <div class="fg-card__attr-label">STATE</div>
            <div>{state_label_html}</div>
            <div class="fg-card__attr-label">CONFIDENCE</div>
            <div class="fg-card__attr-value fg-card__attr-value--mono">{confidence_str}</div>
            <div class="fg-card__attr-label">CLASS</div>
            <div class="fg-card__attr-value fg-card__attr-value--mono">{detection.combined_label}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_pipeline_unavailable(error: str | None) -> None:
    st.markdown(
        f"""
        <div class="fg-warning">
          <strong>MODELS NOT READY</strong>
          {error or "Local artifacts are missing."}
          Run <code>python scripts/download_artifacts.py</code> to pull the
          checkpoints from the GitHub Release, or train them on Kaggle
          (see <code>notebooks/</code>).
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page() -> None:
    render_hero(
        eyebrow="FRESHGUARD VISION · 2026 EDITION · v0.2.0",
        title="An almanac of <em>freshness</em>.",
        latin_cycle=[PRODUCE_LATIN[p] for p in PRODUCE_TYPES],
        kicker=(
            "Upload a specimen. A single-stage YOLO26s detector localizes "
            "and labels produce on twenty-four fine-grained classes, with "
            "an EfficientNetV2-S classifier in reserve for what it misses."
        ),
        specimen_no="0024",
    )

    # First-time model load takes a few seconds (YOLO + EfficientNetV2-S);
    # st.cache_resource keeps it warm across reruns, so the spinner only
    # shows on the very first page paint.
    with st.spinner("Calibrating instruments…"):
        pipeline, error = load_pipeline("torch")
    if pipeline is None:
        _render_pipeline_unavailable(error)
        return

    # ---- Section I — DEPOSIT (upload) ----
    render_section("I.", "DEPOSIT", "Submit specimen")
    st.markdown(
        '<div class="fg-deposit">'
        '<div class="fg-deposit__caption">JPG · JPEG · PNG · WEBP &nbsp; / &nbsp; max 4096 px</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Drop image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if uploaded is None:
        st.markdown(
            '<div class="fg-empty">Awaiting specimen.</div>',
            unsafe_allow_html=True,
        )
        return

    try:
        image = Image.open(BytesIO(uploaded.getvalue())).convert("RGB")
        detections = pipeline.predict(image)
    except ImageTooLargeError as exc:
        st.markdown(
            f'<div class="fg-warning"><strong>IMAGE TOO LARGE</strong>{exc}</div>',
            unsafe_allow_html=True,
        )
        return

    boxes = [d.box for d in detections]
    labels = [d.combined_label.upper().replace("_", " · ") for d in detections]
    colors = [_ink_for(d) for d in detections]
    specimen_numbers = [f"No {i + 1:03d}" for i in range(len(detections))]
    latin_names = [PRODUCE_LATIN.get(d.produce_type, "") for d in detections]

    overlay = draw_boxes(
        image, boxes, labels,
        color=colors,
        specimen_numbers=specimen_numbers,
        latin_names=latin_names,
    )

    # Render two columns: SPECIMEN frame on the left, FIELD NOTES on the right.
    left, right = st.columns([1.4, 1.0], gap="large")
    with left:
        render_section("II.", "SPECIMEN", "Examined plate")
        is_unknown = bool(detections) and detections[0].source == "unknown"
        n = len(detections) if not is_unknown else 0
        plural = "S" if n != 1 else ""
        caption = (
            f"NO CONFIDENT PREDICTION"
            if is_unknown
            else f"{n} OBSERVATION{plural}  ·  CONF ≥ 0.45"
        )
        st.image(overlay, caption=caption, width="stretch")

    with right:
        render_section("III.", "FIELD NOTES", "Per-detection record")

        if not detections or detections[0].source == "unknown":
            reason = detections[0].abstain_reason if detections else None
            heading, body = ABSTAIN_REASON_COPY.get(
                reason or "",
                (
                    "SPECIMEN NOT RECOGNIZED",
                    "Neither the detector nor the fallback classifier was "
                    "confident enough to commit. The system abstained "
                    "rather than guess.",
                ),
            )
            st.markdown(
                f"""
                <div class="fg-abstain">
                  <strong>{heading}</strong>
                  {body}
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        for index, detection in enumerate(detections):
            _render_specimen_card(detection, index)

        if detections[0].source == "classifier":
            st.markdown(
                """
                <div class="fg-warning">
                  <strong>FALLBACK PATH</strong>
                  The detector found no boxes. The classifier was run on
                  the full image as a single-crop guess; no localization.
                </div>
                """,
                unsafe_allow_html=True,
            )
