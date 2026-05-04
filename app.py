"""Streamlit entrypoint."""

from __future__ import annotations

import streamlit as st

from freshness.ui.pages.model_card import render_page as render_model_card_page
from freshness.ui.pages.predict import render_page as render_predict_page
from freshness.ui.styles import inject_styles


def main() -> None:
    st.set_page_config(
        page_title="FreshGuard · Specimen Almanac",
        page_icon="🍅",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_styles()

    navigation = st.navigation(
        [
            st.Page(
                render_predict_page,
                title="Specimen Lab",
                icon=":material/biotech:",
                url_path="lab",
                default=True,
            ),
            st.Page(
                render_model_card_page,
                title="Field Guide",
                icon=":material/menu_book:",
                url_path="field-guide",
            ),
        ]
    )
    navigation.run()


if __name__ == "__main__":
    main()
