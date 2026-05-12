"""CSS asset fragments for the FreshGuard Streamlit UI."""

from __future__ import annotations

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


STYLE_BASE = f"""
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
html[data-theme="dark"] body header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"],
html[data-theme="dark"] body header[data-testid="stHeader"] button[data-testid="stCollapseSidebarButton"],
html:not([data-theme]) body header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"],
html:not([data-theme]) body header[data-testid="stHeader"] button[data-testid="stCollapseSidebarButton"] {{
  background: oklch(0.225 0.014 35) !important;
  border: 1px solid oklch(0.96 0.010 70 / 0.36) !important;
  border-radius: 2px !important;
  color: oklch(0.96 0.010 70) !important;
  box-shadow: var(--shadow-sink) !important;
}}
html[data-theme="dark"] body header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"] *,
html[data-theme="dark"] body header[data-testid="stHeader"] button[data-testid="stCollapseSidebarButton"] *,
html:not([data-theme]) body header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"] *,
html:not([data-theme]) body header[data-testid="stHeader"] button[data-testid="stCollapseSidebarButton"] * {{
  color: oklch(0.96 0.010 70) !important;
  fill: oklch(0.96 0.010 70) !important;
}}
html[data-theme="dark"] body header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"]:hover,
html[data-theme="dark"] body header[data-testid="stHeader"] button[data-testid="stCollapseSidebarButton"]:hover,
html:not([data-theme]) body header[data-testid="stHeader"] button[data-testid="stExpandSidebarButton"]:hover,
html:not([data-theme]) body header[data-testid="stHeader"] button[data-testid="stCollapseSidebarButton"]:hover {{
  background: oklch(0.32 0.075 37) !important;
  border-color: oklch(0.72 0.185 40) !important;
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
.fg-hero--compact {{
  padding-bottom: 1.3rem;
  border-bottom: 0;
  margin-bottom: 1.25rem;
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
.fg-hero--compact .fg-hero__rule {{
  margin: 1rem 0 0.95rem 0;
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
.fg-hero--compact .fg-hero__subtitle {{
  height: 2.15em;
  margin: 0;
}}
.fg-hero__subtitle ul {{
  position: relative;
  margin: 0; padding: 0; list-style: none;
  height: 1.7em;
}}
.fg-hero--compact .fg-hero__subtitle ul {{
  height: 2.15em;
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
.fg-hero--compact .fg-hero__subtitle li {{
  line-height: 2.15em;
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

"""


