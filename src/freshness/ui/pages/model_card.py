"""Field Guide — almanac-style model card.

Five chapters (Procedure, Specimens, Results, Provenance, Limitations)
with a four-up headline scoreboard sourced from `eval_report.json`.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from freshness.constants import PRODUCE_LATIN, PRODUCE_TYPES
from freshness.ui.content import (
    HEADLINE_METRICS,
    LIMITATIONS_HTML,
    PROCEDURE_HTML,
    PROVENANCE_HTML,
    architecture_rows,
)
from freshness.ui.styles import render_hero, render_rule, render_section
from freshness.utils.labels import display_type_name

CONFUSION_MATRIX_PATH = (
    Path(__file__).resolve().parents[4]
    / "eval"
    / "classifier_confusion_matrix_v2.png"
)


def _scoreboard_html() -> str:
    m = HEADLINE_METRICS

    def tile(label: str, value: str, caption: str) -> str:
        return (
            '<div class="fg-score">'
            f'<div class="fg-score__label">{label}</div>'
            f'<div class="fg-score__value">{value}</div>'
            '<div class="fg-score__rule"></div>'
            f'<div class="fg-score__caption">{caption}</div>'
            "</div>"
        )

    return (
        '<div class="fg-scoreboard">'
        + tile("MACRO F1", f"{m['macro_f1']:.4f}", "classifier · 24-class")
        + tile("TOP-1", f"{m['top1_accuracy']:.4f}", "classifier · 24-class")
        + tile("KTH TYPE", f"{m['kth_type_accuracy']:.4f}", f"external · n={m['kth_count']:.0f}")
        + tile("DETECT mAP@50", f"{m['detector_map50']:.4f}", f"@ conf {m['detector_conf']:.2f}")
        + "</div>"
    )


def _architecture_table() -> str:
    rows = architecture_rows()
    body = "".join(
        f"<tr><td><strong>{role}</strong></td><td>{model}</td><td>{notes}</td></tr>"
        for role, model, notes in rows
    )
    return (
        '<table class="fg-table">'
        "<thead><tr><th>STAGE</th><th>MODEL</th><th>NOTES</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _detector_table() -> str:
    m = HEADLINE_METRICS
    return (
        '<table class="fg-table">'
        "<thead><tr><th>METRIC</th><th class='num'>VALUE</th></tr></thead>"
        "<tbody>"
        f"<tr><td>Classifier macro F1 <em>(24-class)</em></td>"
        f"<td class='num'>{m['macro_f1']:.4f}</td></tr>"
        f"<tr><td>Classifier top-1 accuracy</td>"
        f"<td class='num'>{m['top1_accuracy']:.4f}</td></tr>"
        f"<tr><td>KTH GroceryStoreDataset type accuracy <em>(external)</em></td>"
        f"<td class='num'>{m['kth_type_accuracy']:.4f}</td></tr>"
        f"<tr><td>KTH external sample count</td>"
        f"<td class='num'>{m['kth_count']:.0f}</td></tr>"
        f"<tr><td>Detector mAP@50</td>"
        f"<td class='num'>{m['detector_map50']:.4f}</td></tr>"
        f"<tr><td>Detector mAP@50–95</td>"
        f"<td class='num'>{m['detector_map5095']:.4f}</td></tr>"
        f"<tr><td>Open Images negative false accept rate</td>"
        f"<td class='num'>{m['open_world_false_accept']:.4f}</td></tr>"
        f"<tr><td>Open Images positive retention</td>"
        f"<td class='num'>{m['open_world_positive_retention']:.4f}</td></tr>"
        "</tbody></table>"
    )


def _specimens_grid() -> str:
    cells = []
    for i, produce in enumerate(PRODUCE_TYPES, start=1):
        cells.append(
            '<div class="fg-specimen">'
            f'<div class="fg-specimen__no">No {i:02d}</div>'
            f'<div class="fg-specimen__name">{display_type_name(produce)}</div>'
            f'<div class="fg-specimen__latin">{PRODUCE_LATIN[produce]}</div>'
            "</div>"
        )
    return f'<div class="fg-specimens">{"".join(cells)}</div>'


def _render_confusion_matrix() -> None:
    if not CONFUSION_MATRIX_PATH.exists():
        return

    st.markdown(
        """
        <div class="fg-figure-label">
          <span>CONFUSION MATRIX</span>
          <strong>DINOv3-S/16 · Food Freshness test split</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.image(
        str(CONFUSION_MATRIX_PATH),
        caption="Classifier confusion matrix for the v2 24-class freshness head.",
        width="stretch",
    )


def render_page() -> None:
    render_hero(
        eyebrow="FIELD GUIDE · v2 · CLUSTER-DISJOINT TEST SPLIT",
        title="A field guide to the <em>numbers</em>.",
        latin_cycle=[PRODUCE_LATIN[p] for p in PRODUCE_TYPES],
        kicker=(
            "Honest metrics, sourced from the end-to-end evaluation "
            "notebook. Macro F1 leads the headline because top-1 hides "
            "minority-class failure under 41 : 1 imbalance."
        ),
        specimen_no="0024",
    )

    # Headline scoreboard right under the hero.
    st.markdown(_scoreboard_html(), unsafe_allow_html=True)

    # I. Procedure
    render_section("I.", "PROCEDURE", "How the system answers")
    st.markdown(f'<div class="fg-prose">{PROCEDURE_HTML}</div>', unsafe_allow_html=True)
    st.markdown(_architecture_table(), unsafe_allow_html=True)

    render_rule()

    # II. Specimens
    render_section("II.", "SPECIMENS", "Twelve produce types · twenty-four labels")
    st.markdown(
        '<div class="fg-prose"><p>'
        "Each species below is observed in two states — "
        "<em>fresh</em> and <em>rotten</em> — for a 24-class output space. "
        "Latin binomials are rendered alongside common names in the "
        "Specimen Lab tab."
        "</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown(_specimens_grid(), unsafe_allow_html=True)

    render_rule()

    # III. Results
    render_section("III.", "RESULTS", "Headline metrics in detail")
    st.markdown(_detector_table(), unsafe_allow_html=True)
    _render_confusion_matrix()

    render_rule()

    # IV. Provenance
    render_section("IV.", "PROVENANCE", "Where the data came from")
    st.markdown(f'<div class="fg-prose">{PROVENANCE_HTML}</div>', unsafe_allow_html=True)

    render_rule()

    # V. Limitations
    render_section("V.", "LIMITATIONS", "What the system will not tell you")
    st.markdown(f'<div class="fg-prose">{LIMITATIONS_HTML}</div>', unsafe_allow_html=True)

    render_rule(strong=True)
    st.markdown(
        '<p style="font-family:var(--mono);font-size:0.72rem;'
        'letter-spacing:0.22em;color:var(--ink-muted);text-align:center;'
        'margin:1.2rem 0 0.4rem;">'
        "FIN  ·  LAB NOTEBOOK No 0024  ·  2026 EDITION"
        "</p>",
        unsafe_allow_html=True,
    )
