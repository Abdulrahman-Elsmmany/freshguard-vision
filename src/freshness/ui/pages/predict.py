"""Specimen Lab — produce upload + 24-class detection."""

from __future__ import annotations

from html import escape

import streamlit as st
from PIL import Image

from freshness.constants import PRODUCE_LATIN, PRODUCE_TYPES
from freshness.inference.pipeline import DetectedProduce, PipelineProgress
from freshness.ui.runtime import load_pipeline
from freshness.ui.styles import render_hero, render_section
from freshness.utils.images import (
    INK_FRESH,
    INK_ROTTEN,
    INK_UNKNOWN,
    ImageTooLargeError,
    draw_boxes,
    open_image,
)
from freshness.utils.labels import display_freshness_name, display_type_name

SOURCE_LABEL = {
    "detector": "DETECTOR · YOLO26n",
    "classifier": "CLASSIFIER · DINOv3-S/16",
    "ensemble": "CLASSIFIER · DINOv3-S/16",
    "unknown": "ABSTAIN",
}

# Maps the abstain_reason emitted by classifier.py / pipeline.py into
# user-facing copy. Anything not in this table falls back to the generic
# "neither side committed" line.
ABSTAIN_REASON_COPY: dict[str, tuple[str, str]] = {
    "low_top1": (
        "LOW CONFIDENCE",
        "The DINOv3 classifier's top guess sat below the confidence floor — "
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
    "freshness_uncertain": (
        "FRESHNESS UNCERTAIN",
        "The crop looked like a supported produce type, but the fresh and "
        "rotten probabilities were too close to publish a freshness label.",
    ),
    "crop_full_image_disagree": (
        "CROP ↔ FULL-IMAGE DISAGREEMENT",
        "The crop classifier and full-image sanity check committed to "
        "different produce types. The system treated that as an "
        "out-of-distribution signal.",
    ),
    "no_produce_detected": (
        "NO PRODUCE DETECTED",
        "YOLO26n did not find a usable produce box, so the closed-set "
        "freshness classifier was skipped instead of guessing.",
    ),
    "non_produce_image": (
        "NON-PRODUCE IMAGE",
        "The only localization evidence was a weak near-full-frame box. "
        "The system rejected it as unsupported input.",
    ),
    "scene_box_suppressed": (
        "SCENE-LEVEL BOX SUPPRESSED",
        "A near-full-image detector box was treated as scene context rather "
        "than an individual produce item.",
    ),
    "no_classifier": (
        "NO FALLBACK AVAILABLE",
        "The detector found nothing and no classifier is loaded.",
    ),
}

STATE_INK = {
    "fresh": INK_FRESH,
    "rotten": INK_ROTTEN,
    "n_a": INK_UNKNOWN,
}
PROGRESS_LABELS = {
    "image_loaded": "DECODE",
    "detector_started": "LOCALIZE",
    "detector_done": "BOXES",
    "classifier_started": "CLASSIFY",
    "classifier_done": "DECIDE",
    "render_ready": "RENDER",
}


def _state_class(freshness: str, source: str) -> str:
    if source == "unknown" or freshness == "n_a":
        return "unknown"
    return freshness


def _ink_for(detection: DetectedProduce) -> str:
    if detection.source == "unknown":
        return INK_UNKNOWN
    return STATE_INK.get(detection.freshness, INK_UNKNOWN)


def _overlay_label(detection: DetectedProduce) -> str:
    if detection.freshness == "n_a":
        return f"{display_type_name(detection.produce_type).upper()} · N/A"
    return detection.combined_label.upper().replace("_", " · ")


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
    confidence_str = f"{detection.confidence:.4f}" if detection.confidence > 0 else "—"
    source_label = SOURCE_LABEL.get(detection.source, detection.source.upper())
    reason_html = ""
    if detection.abstain_reason is not None:
        reason_heading = ABSTAIN_REASON_COPY.get(
            detection.abstain_reason,
            ("ABSTAINED", ""),
        )[0]
        reason_html = (
            '<div class="fg-card__note">'
            f"{escape(reason_heading)}"
            "</div>"
        )

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
          {reason_html}
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
          Run <code>uv run python scripts/download_artifacts.py</code> to pull the
          checkpoints from the GitHub Release, or train them on Kaggle
          (see <code>notebooks/</code>).
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_upload_receipt(uploaded_name: str, image: Image.Image) -> None:
    st.markdown(
        f"""
        <div class="fg-upload-receipt">
          <div>
            <div class="fg-upload-receipt__label">SPECIMEN SEALED</div>
            <div class="fg-upload-receipt__name">{escape(uploaded_name)}</div>
          </div>
          <div class="fg-upload-receipt__meta">
            {image.width} × {image.height}px · RGB
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _progress_html(progress: PipelineProgress) -> str:
    pct = min(100, max(0, round(progress.completed / progress.total * 100)))
    phase = PROGRESS_LABELS.get(progress.phase, progress.phase.upper())
    return f"""
    <div class="fg-processing">
      <div class="fg-processing__scan"></div>
      <div class="fg-processing__row">
        <div>
          <div class="fg-processing__label">ANALYSIS IN PROGRESS</div>
          <div class="fg-processing__phase">{phase}</div>
        </div>
        <div class="fg-processing__pct">{pct}%</div>
      </div>
      <div class="fg-processing__message">{escape(progress.message)}</div>
      <div class="fg-processing__track">
        <div class="fg-processing__bar" style="width:{pct}%"></div>
      </div>
    </div>
    """


def _render_processing(
    slot: st.delta_generator.DeltaGenerator,
    progress: PipelineProgress,
) -> None:
    slot.markdown(_progress_html(progress), unsafe_allow_html=True)


def render_page() -> None:
    render_hero(
        eyebrow="FRESHGUARD VISION · 2026 EDITION · v0.3.1",
        title="An almanac of <em>freshness</em>.",
        latin_cycle=[PRODUCE_LATIN[p] for p in PRODUCE_TYPES],
        kicker="",
        specimen_no="0024",
    )

    # First-time model load takes a few seconds (YOLO + DINOv3);
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
        '<div class="fg-deposit__caption">JPG · JPEG · PNG · WEBP &nbsp; / &nbsp; max 4096 px</div>'
        '<div class="fg-deposit__guide">'
            'Upload a produce image. YOLO26n finds item-level produce boxes, '
            'then DINOv3-S/16 assigns freshness where the evidence is strong.'
        '</div>',
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

    processing_slot = st.empty()

    try:
        image = open_image(uploaded.getvalue())
        _render_upload_receipt(uploaded.name, image)
        _render_processing(
            processing_slot,
            PipelineProgress(
                phase="image_loaded",
                message="Upload received. Preparing local models.",
                completed=1,
                total=5,
            ),
        )
        detections = pipeline.predict(
            image,
            progress_callback=lambda event: _render_processing(processing_slot, event),
        )
    except ImageTooLargeError as exc:
        processing_slot.empty()
        st.markdown(
            f'<div class="fg-warning"><strong>IMAGE TOO LARGE</strong>{exc}</div>',
            unsafe_allow_html=True,
        )
        return

    boxes = [d.box for d in detections]
    labels = [_overlay_label(d) for d in detections]
    colors = [_ink_for(d) for d in detections]
    specimen_numbers = [f"No {i + 1:03d}" for i in range(len(detections))]
    latin_names = [PRODUCE_LATIN.get(d.produce_type, "") for d in detections]

    overlay = draw_boxes(
        image, boxes, labels,
        color=colors,
        specimen_numbers=specimen_numbers,
        latin_names=latin_names,
    )
    processing_slot.empty()

    # Render two columns: SPECIMEN frame on the left, FIELD NOTES on the right.
    left, right = st.columns([1.4, 1.0], gap="large")
    with left:
        render_section("II.", "SPECIMEN", "Examined plate")
        is_unknown = bool(detections) and all(d.source == "unknown" for d in detections)
        n = len(detections) if not is_unknown else 0
        plural = "S" if n != 1 else ""
        threshold = getattr(pipeline.detector, "confidence", 0.0)
        caption = (
            "NO CONFIDENT PREDICTION"
            if is_unknown
            else f"{n} OBSERVATION{plural}  ·  DET CONF ≥ {threshold:.2f}"
        )
        st.image(overlay, caption=caption, width="stretch")

    with right:
        render_section("III.", "FIELD NOTES", "Per-detection record")

        if not detections or all(d.source == "unknown" for d in detections):
            reason = detections[0].abstain_reason if detections else None
            heading, body = ABSTAIN_REASON_COPY.get(
                reason or "",
                (
                    "SPECIMEN NOT RECOGNIZED",
                    "Neither the detector nor the classifier was "
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
                  <strong>CLASSIFIER AUTHORITY</strong>
                  The DINOv3 classifier supplies produce type and freshness.
                  YOLO26n supplies only localization boxes.
                </div>
                """,
                unsafe_allow_html=True,
            )
