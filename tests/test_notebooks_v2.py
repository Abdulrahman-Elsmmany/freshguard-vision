from __future__ import annotations

import json
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


class V2NotebookTests(unittest.TestCase):
    def test_v2_notebooks_exist_and_are_valid_json(self) -> None:
        expected = {
            "kaggle_00_fetch_official_sources_v2.ipynb",
            "kaggle_01_dataset_audit_v2.ipynb",
            "kaggle_02_prepare_detector_data_v2.ipynb",
            "kaggle_03_train_detector_v2.ipynb",
            "kaggle_04_train_classifier_dinov3_v2.ipynb",
            "kaggle_05_evaluate_v2.ipynb",
        }

        actual = {path.name for path in NOTEBOOKS.glob("*_v2.ipynb")}

        self.assertEqual(actual, expected)
        for name in expected:
            data = json.loads((NOTEBOOKS / name).read_text(encoding="utf-8"))
            self.assertEqual(data["nbformat"], 4)
            self.assertGreater(len(data["cells"]), 0)
            for index, cell in enumerate(data["cells"]):
                if cell.get("cell_type") == "code":
                    ast.parse(
                        "".join(cell.get("source", [])),
                        filename=f"{name}:cell{index}",
                    )

    def test_v2_notebooks_reference_runtime_artifact_names(self) -> None:
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in NOTEBOOKS.glob("*_v2.ipynb")
        )

        self.assertIn("yolo26n_produce_v2.pt", combined)
        self.assertIn("dinov3_vits16_food_freshness_v2.pt", combined)
        self.assertIn("vit_small_patch16_dinov3", combined)


if __name__ == "__main__":
    unittest.main()
