"""Component CSS fragment for the FreshGuard Streamlit UI."""

from __future__ import annotations

STYLE_COMPONENTS = """/* ============================================================
   LAYER 4 — SECTION HEADERS, RULES, CARDS
   ============================================================ */
.fg-section {
  position: relative;
  margin: 2rem 0 1.1rem 0;
}
.fg-section__label {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.28em;
  color: var(--ink-muted);
  display: flex;
  align-items: center;
  gap: 0.7rem;
}
.fg-section__label::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--rule);
}
.fg-section__title {
  font-family: var(--serif);
  font-size: 1.6rem;
  margin: 0.4rem 0 0.2rem 0;
  font-weight: 600;
  font-variation-settings: "opsz" 60;
}
.fg-section__roman {
  font-family: var(--mono);
  color: var(--accent);
  font-size: 0.85rem;
  letter-spacing: 0.18em;
  margin-right: 0.5rem;
}

.fg-rule {
  height: 1px;
  background: var(--rule);
  margin: 1.2rem 0;
}
.fg-rule-strong {
  height: 1.5px;
  background: var(--ink-primary);
  margin: 1.3rem 0;
}

/* DEPOSIT (upload) frame */
.fg-deposit {
  position: relative;
  border: 1px dashed var(--rule-strong);
  border-radius: 2px;
  padding: 1.1rem 1.2rem 0.6rem;
  background: var(--paper-elevated);
}
.fg-deposit__caption {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  color: var(--ink-muted);
  margin-bottom: 0.6rem;
}
.fg-deposit__guide {
  max-width: 58ch;
  font-family: var(--sans);
  font-size: 0.94rem;
  line-height: 1.55;
  color: var(--ink-secondary);
  margin: 0 0 0.85rem;
}
.fg-upload-receipt {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  border: 1px solid var(--rule);
  border-top: 1.5px solid var(--ink-primary);
  background: var(--paper-elevated);
  padding: 0.85rem 1rem;
  margin: 0.8rem 0 0.9rem;
  box-shadow: var(--shadow-sink);
}
.fg-upload-receipt__label {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  color: var(--accent-deep);
  margin-bottom: 0.25rem;
}
.fg-upload-receipt__name {
  font-family: var(--serif);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--ink-primary);
  overflow-wrap: anywhere;
}
.fg-upload-receipt__meta {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  color: var(--ink-muted);
  white-space: nowrap;
}

/* SPECIMEN frame (around the uploaded image) */
.fg-specimen-frame {
  position: relative;
  border: 1px solid var(--rule-strong);
  background: var(--paper-elevated);
  padding: 12px;
}
.fg-specimen-frame__tag {
  position: absolute;
  top: -1px; left: 14px;
  background: var(--paper);
  padding: 0 6px;
  transform: translateY(-50%);
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  color: var(--accent-deep);
}

/* FIELD NOTES — specimen-style detection cards */
.fg-card {
  position: relative;
  background: var(--paper-elevated);
  border: 1px solid var(--rule);
  padding: 0.95rem 1.05rem 0.9rem;
  margin-bottom: 0.85rem;
  box-shadow: var(--shadow-sink);
  animation: card-rise 500ms cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
.fg-card:nth-child(1) { animation-delay: 60ms; }
.fg-card:nth-child(2) { animation-delay: 120ms; }
.fg-card:nth-child(3) { animation-delay: 180ms; }
.fg-card:nth-child(4) { animation-delay: 240ms; }
.fg-card:nth-child(5) { animation-delay: 300ms; }
.fg-card:nth-child(6) { animation-delay: 360ms; }
@keyframes card-rise {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

.fg-card__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}
.fg-card__sn {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--ink-muted);
}
.fg-card__source {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.16em;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}
.fg-card__source-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  display: inline-block;
}
.fg-card__source--detector { color: var(--accent-deep); }
.fg-card__source--detector .fg-card__source-dot { background: var(--accent); }
.fg-card__source--classifier { color: var(--fresh); }
.fg-card__source--classifier .fg-card__source-dot { background: var(--fresh); }
.fg-card__source--unknown { color: var(--ink-muted); }
.fg-card__source--unknown .fg-card__source-dot { background: var(--ink-muted); }

.fg-card__latin {
  font-family: var(--serif);
  font-style: italic;
  font-size: 1.15rem;
  margin: 0.45rem 0 0.1rem 0;
  font-variation-settings: "opsz" 48;
}
.fg-card__display {
  font-family: var(--sans);
  font-size: 0.85rem;
  color: var(--ink-muted);
  margin: 0 0 0.65rem 0;
}
.fg-card__divider {
  height: 1px;
  background: var(--rule);
  margin: 0.4rem 0 0.55rem 0;
}
.fg-card__attrs {
  display: grid;
  grid-template-columns: max-content 1fr;
  row-gap: 0.25rem;
  column-gap: 0.9rem;
  font-size: 0.88rem;
}
.fg-card__attr-label {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.16em;
  color: var(--ink-muted);
  align-self: center;
}
.fg-card__attr-value {
  font-family: var(--sans);
  color: var(--ink-primary);
}
.fg-card__attr-value--mono {
  font-family: var(--mono);
  font-feature-settings: "tnum" on;
}
.fg-card__attr-value--state-fresh {
  color: var(--fresh);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.fg-card__attr-value--state-rotten {
  color: var(--rotten);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}
.fg-card__attr-value--state-unknown {
  color: var(--ink-muted);
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

/* ============================================================
   LAYER 5 — STATES & MISC
   ============================================================ */
.fg-empty {
  font-family: var(--serif);
  font-style: italic;
  color: var(--ink-muted);
  font-size: 1.05rem;
  border-top: 1px solid var(--rule);
  padding-top: 0.9rem;
  margin-top: 0.4rem;
}
.fg-abstain {
  font-family: var(--serif);
  font-style: italic;
  color: var(--ink-muted);
  border: 1px solid var(--rule);
  padding: 1rem 1.15rem;
  background: var(--paper-warm);
}
.fg-abstain strong {
  font-style: normal;
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  display: block;
  color: var(--ink-muted);
  margin-bottom: 0.4rem;
}
.fg-warning {
  font-family: var(--sans);
  border-top: 1.5px solid var(--accent);
  border-bottom: 1px solid var(--rule);
  background: var(--accent-tint);
  color: var(--ink-primary);
  padding: 1rem 1.2rem;
  margin: 1rem 0;
}
.fg-warning strong {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  display: block;
  color: var(--accent-deep);
  margin-bottom: 0.35rem;
}
.fg-processing {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--ink-primary);
  background:
    linear-gradient(90deg, var(--paper-elevated), var(--paper-warm));
  padding: 1rem 1.05rem 0.95rem;
  margin: 0.8rem 0 1rem;
  box-shadow: var(--shadow-sink);
}
.fg-processing__scan {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(90deg, transparent, var(--accent-tint), transparent);
  opacity: 0.55;
  transform: translateX(-100%);
  animation: processing-scan 1.45s ease-in-out infinite;
}
@keyframes processing-scan {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.fg-processing__row {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 1rem;
}
.fg-processing__label {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.24em;
  color: var(--ink-muted);
}
.fg-processing__phase {
  font-family: var(--serif);
  font-size: 1.25rem;
  font-weight: 650;
  color: var(--ink-primary);
  margin-top: 0.2rem;
}
.fg-processing__pct {
  font-family: var(--mono);
  font-size: 1.35rem;
  color: var(--accent-deep);
  font-feature-settings: "tnum" on;
}
.fg-processing__message {
  position: relative;
  font-family: var(--sans);
  color: var(--ink-secondary);
  margin: 0.65rem 0 0.75rem;
}
.fg-processing__track {
  position: relative;
  height: 5px;
  background: var(--rule-faint);
  border: 1px solid var(--rule);
}
.fg-processing__bar {
  height: 100%;
  background: var(--accent);
  transition: width 180ms ease;
}

/* ============================================================
   LAYER 6 — SCOREBOARD (Field Guide page)
   ============================================================ */
.fg-scoreboard {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  border: 1px solid var(--ink-primary);
  background: var(--paper-elevated);
  margin: 0.8rem 0 1.6rem 0;
}
.fg-score {
  padding: 1.1rem 1.2rem 1rem;
  border-right: 1px solid var(--rule);
  position: relative;
}
.fg-score:last-child { border-right: none; }
.fg-score__label {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.22em;
  color: var(--ink-muted);
  margin-bottom: 0.45rem;
}
.fg-score__value {
  font-family: var(--mono);
  font-size: 2rem;
  letter-spacing: -0.02em;
  font-feature-settings: "tnum" on;
  color: var(--ink-primary);
  line-height: 1;
}
.fg-score__rule {
  width: 28px; height: 1.5px;
  background: var(--accent);
  margin: 0.55rem 0 0.45rem 0;
}
.fg-score__caption {
  font-family: var(--serif);
  font-style: italic;
  font-size: 0.85rem;
  color: var(--ink-muted);
}

/* ============================================================
   LAYER 7 — ALMANAC TABLES & SPECIMEN SHEET
   ============================================================ */
.fg-prose p, .fg-prose li {
  font-family: var(--sans);
  font-size: 0.97rem;
  line-height: 1.65;
  color: var(--ink-secondary);
  max-width: 68ch;
}
.fg-prose strong { color: var(--ink-primary); }
.fg-prose code {
  background: var(--paper-warm);
  padding: 1px 6px;
  border-radius: 2px;
  font-size: 0.85em;
  color: var(--accent-deep);
}

.fg-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8rem 0 1.4rem 0;
  font-family: var(--sans);
  font-size: 0.9rem;
}
.fg-table th, .fg-table td {
  padding: 0.55rem 0.85rem;
  text-align: left;
  border-bottom: 1px solid var(--rule);
}
.fg-table th {
  font-family: var(--mono);
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  color: var(--ink-muted);
  font-weight: 500;
  border-bottom: 1.5px solid var(--ink-primary);
}
.fg-table td.num, .fg-table th.num {
  font-family: var(--mono);
  font-feature-settings: "tnum" on;
  text-align: right;
}

.fg-specimens {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0;
  border: 1px solid var(--rule);
  margin: 0.6rem 0 1.6rem;
}
.fg-specimen {
  padding: 0.85rem 1rem;
  border-right: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
}
.fg-specimen__no {
  font-family: var(--mono);
  font-size: 0.72rem;
  letter-spacing: 0.2em;
  color: var(--ink-muted);
}
.fg-specimen__name {
  font-family: var(--serif);
  font-size: 1.15rem;
  margin: 0.15rem 0 0.05rem;
  font-weight: 600;
}
.fg-specimen__latin {
  font-family: var(--serif);
  font-style: italic;
  font-size: 0.9rem;
  color: var(--ink-muted);
}
.fg-figure-label {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 1rem;
  border-top: 1.5px solid var(--ink-primary);
  border-bottom: 1px solid var(--rule);
  padding: 0.8rem 0 0.65rem;
  margin: 1.2rem 0 0.75rem;
}
.fg-figure-label span {
  font-family: var(--mono);
  font-size: 0.68rem;
  letter-spacing: 0.24em;
  color: var(--ink-muted);
}
.fg-figure-label strong {
  font-family: var(--serif);
  font-size: 1rem;
  color: var(--ink-primary);
  text-align: right;
}

"""


