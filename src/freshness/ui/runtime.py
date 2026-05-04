"""Cached UI runtime helpers."""

from __future__ import annotations

import streamlit as st

from freshness.inference.pipeline import FreshnessPipeline, PipelineUnavailableError


@st.cache_resource(show_spinner=False)
def load_pipeline(runtime_mode: str) -> tuple[FreshnessPipeline | None, str | None]:
    try:
        return FreshnessPipeline.from_config(runtime_mode=runtime_mode), None
    except (PipelineUnavailableError, FileNotFoundError) as exc:
        return None, str(exc)
