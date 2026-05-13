"""Widget CSS fragment for the FreshGuard Streamlit UI."""

from __future__ import annotations

STYLE_WIDGETS = """/* ============================================================
   LAYER 8 — STREAMLIT WIDGET POLISH
   ============================================================ */
[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"] {
  background: var(--paper) !important;
  border: 1px dashed var(--rule-strong) !important;
  border-radius: 2px !important;
}

/* Dropzone instructions ("Drag and drop file here") + subtext
   ("Limit 200MB per file • JPG ..."). Both must contrast with --paper
   in BOTH themes, so ride the ink tokens. */
[data-testid="stFileUploaderDropzone"] section,
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] *,
[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] span {
  font-family: var(--sans) !important;
  color: var(--ink-secondary) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploaderDropzone"] small {
  color: var(--ink-muted) !important;
  opacity: 1 !important;
}

/* Browse-files button. Streamlit fills the button with one or more
   text/icon children whose markup varies between versions ("Browse
   files", "Upload", icon glyph, etc.) — sometimes producing visible
   overlap. We hide Streamlit's children entirely and paint our own
   "UPLOAD" label via a ::before pseudo-element. Scope this to the
   dropzone browse control only; Streamlit renders a separate icon-only
   remove button after upload, and relabeling that button is the corrupted
   duplicate-upload state. */
[data-testid="stFileUploaderDropzone"] button:has(p) {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--ink-primary) !important;
  border: 1px solid var(--ink-primary) !important;
  border-radius: 2px !important;
  padding: 0.55rem 1.5rem !important;
  font-size: 0 !important;     /* nuke Streamlit's inner text rendering */
  color: transparent !important;
  cursor: pointer;
  line-height: 1;
}
[data-testid="stFileUploaderDropzone"] button:has(p) > * {
  display: none !important;    /* hide any child <p>/<span>/<div>/icon */
}
[data-testid="stFileUploaderDropzone"] button:has(p)::before {
  content: "UPLOAD";
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--paper);
  pointer-events: none;
}
[data-testid="stFileUploaderDropzone"] button:has(p):hover {
  background: var(--accent-deep) !important;
  border-color: var(--accent-deep) !important;
}
[data-testid="stFileUploaderDropzone"] button:has(p):hover::before {
  color: oklch(0.97 0.013 70);  /* always cream on hover */
}
[data-testid="stFileUploaderDropzone"] button:has(p):focus-visible {
  outline: 1.5px solid var(--accent);
  outline-offset: 2px;
}

/* Image caption */
[data-testid="stImage"] figcaption {
  font-family: var(--mono) !important;
  font-size: 0.75rem !important;
  letter-spacing: 0.18em !important;
  color: var(--ink-muted) !important;
  text-align: center;
  margin-top: 0.5rem !important;
}
:root[data-theme="dark"] [data-testid="stImage"] button,
:root:not([data-theme]) [data-testid="stImage"] button,
:root[data-theme="dark"] [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button,
:root:not([data-theme]) [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button {
  background: oklch(0.12 0.015 70) !important;
  border: 1px solid oklch(0.96 0.013 70 / 0.85) !important;
  color: oklch(0.97 0.013 70) !important;
  box-shadow: var(--shadow-sink) !important;
}
:root[data-theme="dark"] [data-testid="stImage"] button:hover,
:root:not([data-theme]) [data-testid="stImage"] button:hover,
:root[data-theme="dark"] [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button:hover,
:root:not([data-theme]) [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button:hover,
:root[data-theme="dark"] [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button:focus-visible,
:root:not([data-theme]) [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button:focus-visible {
  background: oklch(0.08 0.012 70) !important;
  border-color: oklch(0.99 0.008 70) !important;
}
:root[data-theme="dark"] [data-testid="stImage"] button svg,
:root:not([data-theme]) [data-testid="stImage"] button svg,
:root[data-theme="dark"] [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button *,
:root:not([data-theme]) [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button *,
:root[data-theme="dark"] [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button svg,
:root:not([data-theme]) [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button svg,
:root[data-theme="dark"] [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button svg *,
:root:not([data-theme]) [data-testid="stElementToolbar"] [data-testid="stElementToolbarButton"] button svg * {
  color: oklch(0.97 0.013 70) !important;
  fill: none !important;
  stroke: oklch(0.97 0.013 70) !important;
}
:root[data-theme="dark"] [data-testid="stTooltipContent"],
:root:not([data-theme]) [data-testid="stTooltipContent"],
:root[data-theme="dark"] .stTooltipContent,
:root:not([data-theme]) .stTooltipContent {
  background: oklch(0.08 0.012 70) !important;
  border: 1px solid oklch(0.96 0.013 70 / 0.85) !important;
  color: oklch(0.97 0.013 70) !important;
  box-shadow: var(--shadow-sink) !important;
}
:root[data-theme="dark"] [data-testid="stTooltipContent"] *,
:root:not([data-theme]) [data-testid="stTooltipContent"] *,
:root[data-theme="dark"] .stTooltipContent *,
:root:not([data-theme]) .stTooltipContent * {
  color: oklch(0.97 0.013 70) !important;
}

/* Streamlit st.info / st.warning fallbacks (we mostly avoid these,
   but if used, keep the aesthetic) */
[data-testid="stAlert"] {
  border-radius: 0 !important;
  border-left: 1.5px solid var(--accent) !important;
  background: var(--accent-tint) !important;
  font-family: var(--sans) !important;
}

/* st.spinner — restyle Streamlit's default bright-pink loader to match. */
[data-testid="stSpinner"] {
  font-family: var(--mono) !important;
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-muted) !important;
  padding: 0.4rem 0;
}
[data-testid="stSpinner"] > div > i,
[data-testid="stSpinner"] svg circle {
  border-top-color: var(--accent) !important;
  stroke: var(--accent) !important;
}

/* ============================================================
   LAYER 9 — THEME TOGGLE (floating, top-right)
   ============================================================ */

/* The toggle is rendered via a 1x1 same-origin iframe that injects the
   real button into the parent document. Hide the iframe itself + its
   surrounding Streamlit element wrapper so it doesn't take any vertical
   space. */
[data-testid="stIFrame"],
[data-testid="stElementContainer"]:has(> [data-testid="stIFrame"]) {
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  pointer-events: none !important;
}
[data-testid="stIFrame"] > iframe {
  height: 1px !important;
  width: 1px !important;
}

.fg-theme-toggle {
  position: fixed;
  top: 14px;
  right: 16px;
  z-index: 9999;
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.42rem 0.7rem;
  background: var(--paper-elevated);
  border: 1px solid var(--rule-strong);
  border-radius: 2px;
  color: var(--ink-primary);
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  cursor: pointer;
  user-select: none;
  box-shadow: var(--shadow-sink);
  transition: border-color 180ms ease, background-color 180ms ease, transform 180ms ease;
}
.fg-theme-toggle:hover {
  border-color: var(--accent);
  background: var(--accent-tint);
  transform: translateY(-1px);
}
.fg-theme-toggle:focus-visible {
  outline: 1.5px solid var(--accent);
  outline-offset: 2px;
}
.fg-theme-toggle__glyph {
  font-family: var(--serif);
  font-style: normal;
  font-size: 0.95rem;
  line-height: 1;
  color: var(--accent-deep);
}
.fg-theme-toggle__label {
  display: inline-block;
  min-width: 2.6em;
  text-align: left;
}
:root[data-theme="dark"] .fg-theme-toggle__glyph,
:root:not([data-theme]) .fg-theme-toggle__glyph {
  /* glyph color stays consistent in both modes via accent-deep */
}
</style>
"""


