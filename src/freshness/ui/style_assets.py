"""Composed CSS assets for the FreshGuard Streamlit UI."""

from __future__ import annotations

from freshness.ui.style_base import STYLE_BASE
from freshness.ui.style_components import STYLE_COMPONENTS
from freshness.ui.style_widgets import STYLE_WIDGETS

APP_CSS = STYLE_BASE + STYLE_COMPONENTS + STYLE_WIDGETS
