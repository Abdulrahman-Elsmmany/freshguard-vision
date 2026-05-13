# Artifacts

This directory stores model checkpoints used by the local Streamlit app.

Expected files:

- `yolo26n_produce_v2_1.pt` — YOLO26n detector trained as one class:
  `produce`. It returns boxes only.
- `dinov3_vits16_food_freshness_v2.pt` — DINOv3-S/16 classifier checkpoint
  with the 24-class freshness label contract and merged LoRA weights.

These files are intentionally excluded from version control. Pull them
from the GitHub Release with `uv run python scripts/download_artifacts.py`, or
copy them in manually after running the Kaggle training notebooks.

Expected SHA256 checksums for the v2.1 release artifacts:

- `yolo26n_produce_v2_1.pt`:
  `7B0EB461079AD124BC299FE391053A395A841C19F159216AD891DB761BF2F5C8`
- `dinov3_vits16_food_freshness_v2.pt`:
  `8CEB6B46820767A78EEFE600F2FA09513CF132CBF38D99921BFEE5F855078E74`
