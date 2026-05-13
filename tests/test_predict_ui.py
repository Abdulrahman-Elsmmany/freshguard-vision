from __future__ import annotations

import unittest

from freshness.inference.pipeline import PipelineProgress
from freshness.ui.pages.predict import _progress_html
from freshness.ui.style_widgets import STYLE_WIDGETS


class PredictUiTests(unittest.TestCase):
    def test_progress_percent_is_not_zero_padded(self) -> None:
        html = _progress_html(
            PipelineProgress(
                phase="classifier_started",
                message="Classifying crops.",
                completed=4,
                total=5,
            )
        )

        self.assertIn("80%", html)
        self.assertNotIn("080%", html)

    def test_dark_fullscreen_toolbar_and_tooltip_are_styled(self) -> None:
        self.assertIn('[data-testid="stElementToolbarButton"] button', STYLE_WIDGETS)
        self.assertIn('[data-testid="stTooltipContent"]', STYLE_WIDGETS)


if __name__ == "__main__":
    unittest.main()
