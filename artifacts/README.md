# Artifacts

This directory stores model checkpoints used by the local Streamlit app.

Expected files:

- `yolo26n_produce_v2.pt` — YOLO26n detector trained as one class:
  `produce`. It returns boxes only.
- `dinov3_vits16_food_freshness_v2.pt` — DINOv3-S/16 classifier checkpoint
  with the 24-class freshness label contract and merged LoRA weights.

These files are intentionally excluded from version control. Pull them
from the GitHub Release with `python scripts/download_artifacts.py`, or
copy them in manually after running the Kaggle training notebooks.

Expected SHA256 checksums for the v2 release artifacts:

- `yolo26n_produce_v2.pt`:
  `E104AA02E3248D3783723C5A4A19681413A9E2CE1DEB17D58B10954480E8D184`
- `dinov3_vits16_food_freshness_v2.pt`:
  `8CEB6B46820767A78EEFE600F2FA09513CF132CBF38D99921BFEE5F855078E74`
