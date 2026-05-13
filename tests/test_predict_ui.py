from __future__ import annotations

import unittest

from freshness.inference.pipeline import PipelineProgress
from freshness.ui.pages.predict import _progress_html


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


if __name__ == "__main__":
    unittest.main()
