"""UI theming for the FreshGuard Streamlit app.

Visual direction: **Specimen Almanac** — an editorial field-guide aesthetic
with the precision of a lab notebook. Warm cream paper, walnut ink, heirloom
tomato accent. Hairline rules + crosshairs + monospace metrics.
"""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

# Inline SVG paper-noise textures (data URIs). Tiled grain that gives the
# page a printed-paper feel without shipping binary assets. Two variants —
# dark ink for cream paper, warm light flecks for inked paper.
_NOISE_LIGHT = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http%3A//www.w3.org/2000/svg' width='160' height='160'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' "
    "numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.16  "
    "0 0 0 0 0.12  0 0 0 0 0.09  0 0 0 0.045 0'/></filter>"
    "<rect width='100%25' height='100%25' filter='url(%23n)'/></svg>"
)
_NOISE_DARK = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http%3A//www.w3.org/2000/svg' width='160' height='160'>"
    "<filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' "
    "numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.92  "
    "0 0 0 0 0.86  0 0 0 0 0.78  0 0 0 0.04 0'/></filter>"
    "<rect width='100%25' height='100%25' filter='url(%23n)'/></svg>"
)

APP_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,700;9..144,900&family=Inter+Tight:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* ============================================================
   LAYER 1 — TOKENS (OKLCH, light theme)
   ============================================================ */
:root,
:root[data-theme="light"] {{
  --paper:           oklch(0.97  0.013 70);
  --paper-elevated:  oklch(0.985 0.010 70);
  --paper-warm:      oklch(0.945 0.020 70);

  --ink-primary:     oklch(0.21  0.025 35);
  --ink-secondary:   oklch(0.32  0.022 35);
  --ink-muted:       oklch(0.50  0.020 35);
  --ink-faint:       oklch(0.70  0.018 70);

  --rule:            oklch(0.21 0.025 35 / 0.18);
  --rule-strong:     oklch(0.21 0.025 35 / 0.32);
  --rule-faint:      oklch(0.21 0.025 35 / 0.10);

  --accent:          oklch(0.62 0.193 37);
  --accent-deep:     oklch(0.48 0.170 37);
  --accent-tint:     oklch(0.93 0.040 37);

  --fresh:           oklch(0.55 0.130 145);
  --fresh-tint:      oklch(0.93 0.045 145);
  --rotten:          oklch(0.45 0.160 30);
  --rotten-tint:     oklch(0.92 0.060 30);
  --unknown:         oklch(0.55 0.020 35);
  --unknown-tint:    oklch(0.92 0.012 35);

  --shadow-sink:     0 1px 0 0 oklch(0.21 0.025 35 / 0.04);
  --bg-page-from:    oklch(0.975 0.013 70);
  --bg-page-to:      oklch(0.965 0.014 65);
  --bg-noise:        url("{_NOISE_LIGHT}");
  --bg-blend:        multiply;

  --serif:  'Fraunces', 'EB Garamond', Georgia, serif;
  --sans:   'Inter Tight', 'Inter', system-ui, sans-serif;
  --mono:   'JetBrains Mono', 'IBM Plex Mono', 'Menlo', monospace;
}}

/* Dark theme — explicitly chosen via the toggle (data-theme="dark") OR via
   OS preference when the user has not made a choice yet. */
:root[data-theme="dark"],
:root:not([data-theme]) {{
  --_dummy: 0;  /* anchor for the OS-pref override below */
}}
:root[data-theme="dark"] {{
  --paper:           oklch(0.18 0.012 35);
  --paper-elevated:  oklch(0.225 0.014 35);
  --paper-warm:      oklch(0.21 0.014 35);

  --ink-primary:     oklch(0.96 0.010 70);
  --ink-secondary:   oklch(0.85 0.012 70);
  --ink-muted:       oklch(0.65 0.018 70);
  --ink-faint:       oklch(0.45 0.018 70);

  --rule:            oklch(0.96 0.010 70 / 0.18);
  --rule-strong:     oklch(0.96 0.010 70 / 0.36);
  --rule-faint:      oklch(0.96 0.010 70 / 0.08);

  --accent:          oklch(0.72 0.185 40);
  --accent-deep:     oklch(0.62 0.193 37);
  --accent-tint:     oklch(0.32 0.075 37);

  --fresh:           oklch(0.72 0.130 145);
  --fresh-tint:      oklch(0.30 0.060 145);
  --rotten:          oklch(0.65 0.160 30);
  --rotten-tint:     oklch(0.30 0.080 30);
  --unknown:         oklch(0.65 0.020 35);
  --unknown-tint:    oklch(0.28 0.012 35);

  --shadow-sink:     0 1px 0 0 oklch(0 0 0 / 0.32);
  --bg-page-from:    oklch(0.16 0.014 30);
  --bg-page-to:      oklch(0.13 0.014 30);
  --bg-noise:        url("{_NOISE_DARK}");
  --bg-blend:        screen;
}}

/* OS-preference fallback: only applies when the user has NOT made an
   explicit choice (no data-theme attribute on <html>). */
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme]) {{
    --paper:           oklch(0.18 0.012 35);
    --paper-elevated:  oklch(0.225 0.014 35);
    --paper-warm:      oklch(0.21 0.014 35);
    --ink-primary:     oklch(0.96 0.010 70);
    --ink-secondary:   oklch(0.85 0.012 70);
    --ink-muted:       oklch(0.65 0.018 70);
    --ink-faint:       oklch(0.45 0.018 70);
    --rule:            oklch(0.96 0.010 70 / 0.18);
    --rule-strong:     oklch(0.96 0.010 70 / 0.36);
    --rule-faint:      oklch(0.96 0.010 70 / 0.08);
    --accent:          oklch(0.72 0.185 40);
    --accent-deep:     oklch(0.62 0.193 37);
    --accent-tint:     oklch(0.32 0.075 37);
    --fresh:           oklch(0.72 0.130 145);
    --fresh-tint:      oklch(0.30 0.060 145);
    --rotten:          oklch(0.65 0.160 30);
    --rotten-tint:     oklch(0.30 0.080 30);
    --unknown:         oklch(0.65 0.020 35);
    --unknown-tint:    oklch(0.28 0.012 35);
    --shadow-sink:     0 1px 0 0 oklch(0 0 0 / 0.32);
    --bg-page-from:    oklch(0.16 0.014 30);
    --bg-page-to:      oklch(0.13 0.014 30);
    --bg-noise:        url("{_NOISE_DARK}");
    --bg-blend:        screen;
  }}
}}

/* ============================================================
   LAYER 2 — GLOBAL RESETS, TYPOGRAPHY, BACKGROUND
   ============================================================ */
html, body, [class*="css"], .stApp, .stMarkdown, p, span, li {{
  font-family: var(--sans);
  color: var(--ink-primary);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

h1, h2, h3, h4, h5 {{
  font-family: var(--serif) !important;
  letter-spacing: -0.015em;
  color: var(--ink-primary);
  font-feature-settings: "ss01" on, "salt" on;
}}

code, pre, kbd, samp {{
  font-family: var(--mono) !important;
  font-feature-settings: "ss02" on;
}}

.stApp {{
  background:
    var(--bg-noise),
    linear-gradient(180deg, var(--bg-page-from) 0%, var(--bg-page-to) 100%);
  background-blend-mode: var(--bg-blend);
  transition: background-color 240ms ease, color 240ms ease;
}}
* {{ transition: border-color 240ms ease, background-color 240ms ease, color 240ms ease; }}

/* Fade in the whole page once on first paint. */
.stApp > div:first-child {{
  animation: page-rise 700ms cubic-bezier(0.16, 1, 0.3, 1) both;
}}
@keyframes page-rise {{
  from {{ opacity: 0; transform: translateY(8px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

/* Streamlit chrome: tone down branding for portfolio look */
header[data-testid="stHeader"] {{
  background: transparent !important;
}}
[data-testid="stToolbar"] {{
  display: none;
}}
footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}

/* Sidebar: parchment panel */
[data-testid="stSidebar"] {{
  background: var(--paper-elevated) !important;
  border-right: 1px solid var(--rule) !important;
}}
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] a {{
  color: var(--ink-primary) !important;
}}
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{
  font-family: var(--sans) !important;
  letter-spacing: 0.06em;
}}

/* ============================================================
   LAYER 3 — HERO ("Specimen Almanac" entry)
   ============================================================ */
.fg-hero {{
  position: relative;
  padding: 2.4rem 0 2rem 0;
  border-top: 1.5px solid var(--ink-primary);
  border-bottom: 1px solid var(--rule);
  margin-bottom: 1.6rem;
}}
.fg-hero::before {{
  content: "";
  position: absolute;
  top: -7px; left: 0;
  width: 84px; height: 1px;
  background: var(--ink-primary);
}}

.fg-hero__eyebrow {{
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  color: var(--ink-muted);
  margin: 0 0 1.4rem 0;
  display: flex;
  gap: 0.9rem;
  align-items: center;
}}
.fg-hero__eyebrow .dot {{
  display: inline-block;
  width: 5px; height: 5px;
  border-radius: 50%;
  background: var(--accent);
}}

.fg-hero__title {{
  font-family: var(--serif) !important;
  font-weight: 600;
  font-size: clamp(3rem, 7vw, 5.6rem);
  line-height: 0.95;
  letter-spacing: -0.035em;
  margin: 0 0 1.1rem 0;
  font-variation-settings: "opsz" 144, "SOFT" 50;
  /* Reveal animation */
  display: inline-block;
  background: linear-gradient(180deg, var(--ink-primary) 0%, var(--ink-secondary) 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: title-reveal 900ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}}
@keyframes title-reveal {{
  from {{ clip-path: inset(0 100% 0 0); opacity: 0.4; }}
  to   {{ clip-path: inset(0 0 0 0); opacity: 1; }}
}}

.fg-hero__title em {{
  font-style: italic;
  color: var(--accent-deep);
  font-weight: 500;
}}

.fg-hero__rule {{
  height: 1px;
  background: var(--rule-strong);
  margin: 1rem 0 1.4rem 0;
  width: 92%;
}}

/* Rotating Latin-name subtitle — typewriter clip-path reveal cycling
   through 12 names. Each name is absolutely positioned; only one is
   visible at a time, revealed left-to-right and faded out. */
.fg-hero__subtitle {{
  font-family: var(--serif);
  font-style: italic;
  font-size: clamp(1.15rem, 2vw, 1.5rem);
  color: var(--ink-secondary);
  height: 1.7em;
  position: relative;
  margin: 0 0 1.4rem 0;
  padding-right: 2.5rem;
}}
.fg-hero__subtitle ul {{
  position: relative;
  margin: 0; padding: 0; list-style: none;
  height: 1.7em;
}}
.fg-hero__subtitle li {{
  position: absolute;
  top: 0; left: 0;
  width: max-content;
  max-width: none;
  white-space: nowrap;
  line-height: 1.7em;
  padding-right: 0.4rem;
  font-feature-settings: "liga" on, "dlig" on;
  opacity: 0;
  clip-path: inset(0 100% 0 0);
  animation: latin-reveal 36s infinite both;
}}
.fg-hero__subtitle li::before {{
  content: "·  ";
  color: var(--accent);
  margin-right: 0.4rem;
}}
.fg-hero__subtitle li:nth-child(1)  {{ animation-delay:   0s; }}
.fg-hero__subtitle li:nth-child(2)  {{ animation-delay:   3s; }}
.fg-hero__subtitle li:nth-child(3)  {{ animation-delay:   6s; }}
.fg-hero__subtitle li:nth-child(4)  {{ animation-delay:   9s; }}
.fg-hero__subtitle li:nth-child(5)  {{ animation-delay:  12s; }}
.fg-hero__subtitle li:nth-child(6)  {{ animation-delay:  15s; }}
.fg-hero__subtitle li:nth-child(7)  {{ animation-delay:  18s; }}
.fg-hero__subtitle li:nth-child(8)  {{ animation-delay:  21s; }}
.fg-hero__subtitle li:nth-child(9)  {{ animation-delay:  24s; }}
.fg-hero__subtitle li:nth-child(10) {{ animation-delay:  27s; }}
.fg-hero__subtitle li:nth-child(11) {{ animation-delay:  30s; }}
.fg-hero__subtitle li:nth-child(12) {{ animation-delay:  33s; }}

@keyframes latin-reveal {{
  /* Each item's visible window is 3s of a 36s cycle = 8.33%. */
  0%    {{ opacity: 0; clip-path: inset(0 100% 0 0); }}
  0.1%  {{ opacity: 1; clip-path: inset(0 100% 0 0); }}
  3%    {{ opacity: 1; clip-path: inset(0 0 0 0); }}    /* fully revealed (~1s) */
  7%    {{ opacity: 1; clip-path: inset(0 0 0 0); }}    /* hold (~1.5s) */
  8%    {{ opacity: 0; clip-path: inset(0 0 0 0); }}    /* fade out (~0.4s) */
  100%  {{ opacity: 0; clip-path: inset(0 0 0 0); }}    /* hidden until next loop */
}}

.fg-hero__kicker {{
  font-family: var(--sans);
  font-size: 1rem;
  line-height: 1.55;
  color: var(--ink-secondary);
  max-width: 56ch;
  margin: 0;
}}

/* Specimen tag — rotated 90° in the upper-right. */
.fg-hero__tag {{
  position: absolute;
  top: 18px; right: 8px;
  transform: rotate(-90deg);
  transform-origin: top right;
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.28em;
  color: var(--ink-muted);
  white-space: nowrap;
  border-left: 1px solid var(--rule-strong);
  padding-left: 0.7rem;
}}
.fg-hero__tag strong {{
  color: var(--accent-deep);
  font-weight: 700;
}}

/* ============================================================
   LAYER 4 — SECTION HEADERS, RULES, CARDS
   ============================================================ */
.fg-section {{
  position: relative;
  margin: 2rem 0 1.1rem 0;
}}
.fg-section__label {{
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.28em;
  color: var(--ink-muted);
  display: flex;
  align-items: center;
  gap: 0.7rem;
}}
.fg-section__label::after {{
  content: "";
  flex: 1;
  height: 1px;
  background: var(--rule);
}}
.fg-section__title {{
  font-family: var(--serif);
  font-size: 1.6rem;
  margin: 0.4rem 0 0.2rem 0;
  font-weight: 600;
  font-variation-settings: "opsz" 60;
}}
.fg-section__roman {{
  font-family: var(--mono);
  color: var(--accent);
  font-size: 0.85rem;
  letter-spacing: 0.18em;
  margin-right: 0.5rem;
}}

.fg-rule {{
  height: 1px;
  background: var(--rule);
  margin: 1.2rem 0;
}}
.fg-rule-strong {{
  height: 1.5px;
  background: var(--ink-primary);
  margin: 1.3rem 0;
}}

/* DEPOSIT (upload) frame */
.fg-deposit {{
  position: relative;
  border: 1px dashed var(--rule-strong);
  border-radius: 2px;
  padding: 1.1rem 1.2rem 0.6rem;
  background: var(--paper-elevated);
}}
.fg-deposit__caption {{
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  color: var(--ink-muted);
  margin-bottom: 0.6rem;
}}

/* SPECIMEN frame (around the uploaded image) */
.fg-specimen-frame {{
  position: relative;
  border: 1px solid var(--rule-strong);
  background: var(--paper-elevated);
  padding: 12px;
}}
.fg-specimen-frame__tag {{
  position: absolute;
  top: -1px; left: 14px;
  background: var(--paper);
  padding: 0 6px;
  transform: translateY(-50%);
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  color: var(--accent-deep);
}}

/* FIELD NOTES — specimen-style detection cards */
.fg-card {{
  position: relative;
  background: var(--paper-elevated);
  border: 1px solid var(--rule);
  padding: 0.95rem 1.05rem 0.9rem;
  margin-bottom: 0.85rem;
  box-shadow: var(--shadow-sink);
  animation: card-rise 500ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}}
.fg-card:nth-child(1) {{ animation-delay: 60ms; }}
.fg-card:nth-child(2) {{ animation-delay: 120ms; }}
.fg-card:nth-child(3) {{ animation-delay: 180ms; }}
.fg-card:nth-child(4) {{ animation-delay: 240ms; }}
.fg-card:nth-child(5) {{ animation-delay: 300ms; }}
.fg-card:nth-child(6) {{ animation-delay: 360ms; }}
@keyframes card-rise {{
  from {{ opacity: 0; transform: translateY(6px); }}
  to   {{ opacity: 1; transform: translateY(0); }}
}}

.fg-card__row {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}}
.fg-card__sn {{
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--ink-muted);
}}
.fg-card__source {{
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}}
.fg-card__source-dot {{
  width: 7px; height: 7px;
  border-radius: 50%;
  display: inline-block;
}}
.fg-card__source--detector {{ color: var(--accent-deep); }}
.fg-card__source--detector .fg-card__source-dot {{ background: var(--accent); }}
.fg-card__source--classifier {{ color: var(--fresh); }}
.fg-card__source--classifier .fg-card__source-dot {{ background: var(--fresh); }}
.fg-card__source--unknown {{ color: var(--ink-muted); }}
.fg-card__source--unknown .fg-card__source-dot {{ background: var(--ink-muted); }}

.fg-card__latin {{
  font-family: var(--serif);
  font-style: italic;
  font-size: 1.15rem;
  margin: 0.45rem 0 0.1rem 0;
  font-variation-settings: "opsz" 48;
}}
.fg-card__display {{
  font-family: var(--sans);
  font-size: 0.85rem;
  color: var(--ink-muted);
  margin: 0 0 0.65rem 0;
}}
.fg-card__divider {{
  height: 1px;
  background: var(--rule);
  margin: 0.4rem 0 0.55rem 0;
}}
.fg-card__attrs {{
  display: grid;
  grid-template-columns: max-content 1fr;
  row-gap: 0.25rem;
  column-gap: 0.9rem;
  font-size: 0.88rem;
}}
.fg-card__attr-label {{
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  color: var(--ink-muted);
  align-self: center;
}}
.fg-card__attr-value {{
  font-family: var(--sans);
  color: var(--ink-primary);
}}
.fg-card__attr-value--mono {{
  font-family: var(--mono);
  font-feature-settings: "tnum" on;
}}
.fg-card__attr-value--state-fresh {{
  color: var(--fresh);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}}
.fg-card__attr-value--state-rotten {{
  color: var(--rotten);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}}
.fg-card__attr-value--state-unknown {{
  color: var(--ink-muted);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}}

/* ============================================================
   LAYER 5 — STATES & MISC
   ============================================================ */
.fg-empty {{
  font-family: var(--serif);
  font-style: italic;
  color: var(--ink-muted);
  font-size: 1.05rem;
  border-top: 1px solid var(--rule);
  padding-top: 0.9rem;
  margin-top: 0.4rem;
}}
.fg-abstain {{
  font-family: var(--serif);
  font-style: italic;
  color: var(--ink-muted);
  border: 1px solid var(--rule);
  padding: 1rem 1.15rem;
  background: var(--paper-warm);
}}
.fg-abstain strong {{
  font-style: normal;
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  display: block;
  color: var(--ink-muted);
  margin-bottom: 0.4rem;
}}
.fg-warning {{
  font-family: var(--sans);
  border-top: 1.5px solid var(--accent);
  border-bottom: 1px solid var(--rule);
  background: var(--accent-tint);
  color: var(--ink-primary);
  padding: 1rem 1.2rem;
  margin: 1rem 0;
}}
.fg-warning strong {{
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  display: block;
  color: var(--accent-deep);
  margin-bottom: 0.35rem;
}}

/* ============================================================
   LAYER 6 — SCOREBOARD (Field Guide page)
   ============================================================ */
.fg-scoreboard {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  border: 1px solid var(--ink-primary);
  background: var(--paper-elevated);
  margin: 0.8rem 0 1.6rem 0;
}}
.fg-score {{
  padding: 1.1rem 1.2rem 1rem;
  border-right: 1px solid var(--rule);
  position: relative;
}}
.fg-score:last-child {{ border-right: none; }}
.fg-score__label {{
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  color: var(--ink-muted);
  margin-bottom: 0.45rem;
}}
.fg-score__value {{
  font-family: var(--mono);
  font-size: 2rem;
  letter-spacing: -0.02em;
  font-feature-settings: "tnum" on;
  color: var(--ink-primary);
  line-height: 1;
}}
.fg-score__rule {{
  width: 28px; height: 1.5px;
  background: var(--accent);
  margin: 0.55rem 0 0.45rem 0;
}}
.fg-score__caption {{
  font-family: var(--serif);
  font-style: italic;
  font-size: 0.85rem;
  color: var(--ink-muted);
}}

/* ============================================================
   LAYER 7 — ALMANAC TABLES & SPECIMEN SHEET
   ============================================================ */
.fg-prose p, .fg-prose li {{
  font-family: var(--sans);
  font-size: 0.97rem;
  line-height: 1.65;
  color: var(--ink-secondary);
  max-width: 68ch;
}}
.fg-prose strong {{ color: var(--ink-primary); }}
.fg-prose code {{
  background: var(--paper-warm);
  padding: 1px 6px;
  border-radius: 2px;
  font-size: 0.85em;
  color: var(--accent-deep);
}}

.fg-table {{
  width: 100%;
  border-collapse: collapse;
  margin: 0.8rem 0 1.4rem 0;
  font-family: var(--sans);
  font-size: 0.9rem;
}}
.fg-table th, .fg-table td {{
  padding: 0.55rem 0.85rem;
  text-align: left;
  border-bottom: 1px solid var(--rule);
}}
.fg-table th {{
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  color: var(--ink-muted);
  font-weight: 500;
  border-bottom: 1.5px solid var(--ink-primary);
}}
.fg-table td.num, .fg-table th.num {{
  font-family: var(--mono);
  font-feature-settings: "tnum" on;
  text-align: right;
}}

.fg-specimens {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0;
  border: 1px solid var(--rule);
  margin: 0.6rem 0 1.6rem;
}}
.fg-specimen {{
  padding: 0.85rem 1rem;
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
}}
.fg-specimen__no {{
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  color: var(--ink-muted);
}}
.fg-specimen__name {{
  font-family: var(--serif);
  font-size: 1.15rem;
  margin: 0.15rem 0 0.05rem;
  font-weight: 600;
}}
.fg-specimen__latin {{
  font-family: var(--serif);
  font-style: italic;
  font-size: 0.9rem;
  color: var(--ink-muted);
}}

/* ============================================================
   LAYER 8 — STREAMLIT WIDGET POLISH
   ============================================================ */
[data-testid="stFileUploader"],
[data-testid="stFileUploaderDropzone"] {{
  background: var(--paper) !important;
  border: 1px dashed var(--rule-strong) !important;
  border-radius: 2px !important;
}}

/* Dropzone instructions ("Drag and drop file here") + subtext
   ("Limit 200MB per file • JPG ..."). Both must contrast with --paper
   in BOTH themes, so ride the ink tokens. */
[data-testid="stFileUploaderDropzone"] section,
[data-testid="stFileUploaderDropzoneInstructions"],
[data-testid="stFileUploaderDropzoneInstructions"] *,
[data-testid="stFileUploaderDropzoneInstructions"] div,
[data-testid="stFileUploaderDropzoneInstructions"] span {{
  font-family: var(--sans) !important;
  color: var(--ink-secondary) !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] small,
[data-testid="stFileUploaderDropzone"] small {{
  color: var(--ink-muted) !important;
  opacity: 1 !important;
}}

/* Browse-files button. Streamlit fills the button with one or more
   text/icon children whose markup varies between versions ("Browse
   files", "Upload", icon glyph, etc.) — sometimes producing visible
   overlap. We hide Streamlit's children entirely and paint our own
   "UPLOAD" label via a ::before pseudo-element. The button element
   still receives clicks normally, so the underlying file picker fires. */
[data-testid="stFileUploaderDropzone"] button {{
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
}}
[data-testid="stFileUploaderDropzone"] button > * {{
  display: none !important;    /* hide any child <p>/<span>/<div>/icon */
}}
[data-testid="stFileUploaderDropzone"] button::before {{
  content: "UPLOAD";
  display: inline-block;
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 500;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--paper);
  pointer-events: none;
}}
[data-testid="stFileUploaderDropzone"] button:hover {{
  background: var(--accent-deep) !important;
  border-color: var(--accent-deep) !important;
}}
[data-testid="stFileUploaderDropzone"] button:hover::before {{
  color: oklch(0.97 0.013 70);  /* always cream on hover */
}}
[data-testid="stFileUploaderDropzone"] button:focus-visible {{
  outline: 1.5px solid var(--accent);
  outline-offset: 2px;
}}

/* Image caption */
[data-testid="stImage"] figcaption {{
  font-family: var(--mono) !important;
  font-size: 0.75rem !important;
  letter-spacing: 0.18em !important;
  color: var(--ink-muted) !important;
  text-align: center;
  margin-top: 0.5rem !important;
}}

/* Streamlit st.info / st.warning fallbacks (we mostly avoid these,
   but if used, keep the aesthetic) */
[data-testid="stAlert"] {{
  border-radius: 0 !important;
  border-left: 1.5px solid var(--accent) !important;
  background: var(--accent-tint) !important;
  font-family: var(--sans) !important;
}}

/* st.spinner — restyle Streamlit's default bright-pink loader to match. */
[data-testid="stSpinner"] {{
  font-family: var(--mono) !important;
  font-size: 0.78rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--ink-muted) !important;
  padding: 0.4rem 0;
}}
[data-testid="stSpinner"] > div > i,
[data-testid="stSpinner"] svg circle {{
  border-top-color: var(--accent) !important;
  stroke: var(--accent) !important;
}}

/* ============================================================
   LAYER 9 — THEME TOGGLE (floating, top-right)
   ============================================================ */

/* The toggle is rendered via a 1x1 same-origin iframe that injects the
   real button into the parent document. Hide the iframe itself + its
   surrounding Streamlit element wrapper so it doesn't take any vertical
   space. */
[data-testid="stIFrame"],
[data-testid="stElementContainer"]:has(> [data-testid="stIFrame"]) {{
  height: 0 !important;
  min-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  pointer-events: none !important;
}}
[data-testid="stIFrame"] > iframe {{
  height: 1px !important;
  width: 1px !important;
}}

.fg-theme-toggle {{
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
}}
.fg-theme-toggle:hover {{
  border-color: var(--accent);
  background: var(--accent-tint);
  transform: translateY(-1px);
}}
.fg-theme-toggle:focus-visible {{
  outline: 1.5px solid var(--accent);
  outline-offset: 2px;
}}
.fg-theme-toggle__glyph {{
  font-family: var(--serif);
  font-style: normal;
  font-size: 0.95rem;
  line-height: 1;
  color: var(--accent-deep);
}}
.fg-theme-toggle__label {{
  display: inline-block;
  min-width: 2.6em;
  text-align: left;
}}
:root[data-theme="dark"] .fg-theme-toggle__glyph,
:root:not([data-theme]) .fg-theme-toggle__glyph {{
  /* glyph color stays consistent in both modes via accent-deep */
}}
</style>
"""

THEME_TOGGLE_HTML = """
<script>
(function(){
  // We run inside a same-origin iframe (st.components.v1.html). Reach into
  // the parent document so the toggle ends up in the main DOM where the
  // global CSS (.fg-theme-toggle) can style it.
  const doc = window.parent.document;
  if (!doc || !doc.body) return;
  const root = doc.documentElement;
  const KEY = 'fg-theme';

  // Idempotent injection — only add the button once across reruns.
  let btn = doc.getElementById('fg-theme-toggle');
  if (!btn) {
    btn = doc.createElement('button');
    btn.id = 'fg-theme-toggle';
    btn.className = 'fg-theme-toggle';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Toggle theme');
    btn.title = 'Toggle dark / light theme';
    btn.innerHTML =
      '<span class="fg-theme-toggle__glyph" id="fg-theme-toggle-glyph">◐</span>' +
      '<span class="fg-theme-toggle__label" id="fg-theme-toggle-label">LIGHT</span>';
    doc.body.appendChild(btn);
  }
  const glyph = doc.getElementById('fg-theme-toggle-glyph');
  const label = doc.getElementById('fg-theme-toggle-label');
  if (!glyph || !label) return;

  function effective(){
    const saved = window.parent.localStorage.getItem(KEY);
    if (saved === 'dark' || saved === 'light') return saved;
    return window.parent.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function paint(t){
    glyph.textContent = (t === 'dark') ? '◑' : '◐';
    label.textContent = (t === 'dark') ? 'DARK' : 'LIGHT';
  }
  function apply(t, persist){
    root.setAttribute('data-theme', t);
    if (persist) window.parent.localStorage.setItem(KEY, t);
    paint(t);
  }

  // Apply persisted choice on each rerun; if none, fall through to OS pref.
  const saved = window.parent.localStorage.getItem(KEY);
  if (saved === 'dark' || saved === 'light') {
    apply(saved, false);
  } else {
    root.removeAttribute('data-theme');
    paint(effective());
  }

  // Click handler — reassigning onclick is idempotent across reruns.
  btn.onclick = function(){
    const next = effective() === 'dark' ? 'light' : 'dark';
    apply(next, true);
  };

  // OS-pref watcher only fires while no explicit choice is saved.
  try {
    const mq = window.parent.matchMedia('(prefers-color-scheme: dark)');
    if (mq && mq.addEventListener && !mq.__fgBound) {
      mq.__fgBound = true;
      mq.addEventListener('change', function(){
        if (!window.parent.localStorage.getItem(KEY)) {
          root.removeAttribute('data-theme');
          paint(effective());
        }
      });
    }
  } catch(_){}
})();
</script>
"""


def inject_styles() -> None:
    """Inject the global stylesheet + the floating theme toggle.

    The toggle persists the user's choice in `localStorage` and respects
    the OS `prefers-color-scheme` when no choice has been made. The
    toggle is rendered inside a 0-height `st.iframe` (same-origin); its
    inline script then injects the actual button into
    `window.parent.document.body` so the global CSS reaches it and
    `position: fixed` is relative to the real viewport. This is the
    only path on Streamlit that reliably executes inline JS — both
    `st.markdown(unsafe_allow_html=True)` and `st.html(unsafe_allow_javascript=True)`
    sanitize parts of the script in some versions.
    """
    st.markdown(APP_CSS, unsafe_allow_html=True)
    # 1x1 iframe; the script inside reaches into window.parent.document
    # to inject the actual button. Visual size hidden via CSS rule on
    # [data-testid="stIFrame"] (see APP_CSS layer 9).
    st.iframe(THEME_TOGGLE_HTML, height=1, width=1)


def render_hero(
    eyebrow: str,
    title: str,
    latin_cycle: Sequence[str],
    kicker: str,
    *,
    specimen_no: str = "0024",
) -> None:
    """Render the Specimen Almanac hero block.

    Args:
        eyebrow: Tiny monospace tag above the title (e.g. "FRESHGUARD VISION · 2026 EDITION").
        title: The big serif headline (HTML allowed for <em>).
        latin_cycle: 12 Latin binomials that scroll behind the title every 3s.
        kicker: One- or two-sentence summary set in the body sans.
        specimen_no: The rotated tag in the upper-right ("№ 0024").
    """
    latin_html = "".join(f"<li>{latin}</li>" for latin in latin_cycle)
    st.markdown(
        f"""
        <section class="fg-hero">
          <div class="fg-hero__tag"><strong>No {specimen_no}</strong> &nbsp;·&nbsp; LAB NOTEBOOK</div>
          <p class="fg-hero__eyebrow"><span class="dot"></span>{eyebrow}</p>
          <h1 class="fg-hero__title">{title}</h1>
          <div class="fg-hero__rule"></div>
          <div class="fg-hero__subtitle"><ul>{latin_html}</ul></div>
          <p class="fg-hero__kicker">{kicker}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section(roman: str, label: str, title: str) -> None:
    """Render a section header with roman numeral, mono label, and serif title."""
    st.markdown(
        f"""
        <div class="fg-section">
          <div class="fg-section__label">{label}</div>
          <h2 class="fg-section__title">
            <span class="fg-section__roman">{roman}</span>{title}
          </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rule(*, strong: bool = False) -> None:
    cls = "fg-rule-strong" if strong else "fg-rule"
    st.markdown(f'<div class="{cls}"></div>', unsafe_allow_html=True)
