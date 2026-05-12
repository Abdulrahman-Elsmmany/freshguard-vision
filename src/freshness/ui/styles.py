"""UI theming for the FreshGuard Streamlit app.

Visual direction: **Specimen Almanac** — an editorial field-guide aesthetic
with the precision of a lab notebook. Warm cream paper, walnut ink, heirloom
tomato accent. Hairline rules + crosshairs + monospace metrics.
"""

from __future__ import annotations

from collections.abc import Sequence

import streamlit as st

from freshness.ui.style_assets import APP_CSS

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
    kicker_html = f'<p class="fg-hero__kicker">{kicker}</p>' if kicker else ""
    hero_class = "fg-hero" if kicker else "fg-hero fg-hero--compact"
    st.markdown(
        f"""
        <section class="{hero_class}">
          <div class="fg-hero__tag"><strong>No {specimen_no}</strong> &nbsp;·&nbsp; LAB NOTEBOOK</div>
          <p class="fg-hero__eyebrow"><span class="dot"></span>{eyebrow}</p>
          <h1 class="fg-hero__title">{title}</h1>
          <div class="fg-hero__rule"></div>
          <div class="fg-hero__subtitle"><ul>{latin_html}</ul></div>
          {kicker_html}
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
