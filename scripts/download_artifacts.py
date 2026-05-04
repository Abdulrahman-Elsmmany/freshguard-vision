"""Pull trained model checkpoints into artifacts/ for the local app.

Tries `gh release download` first (if the GitHub CLI is installed and
authenticated). Falls back to a direct urllib download from the public
release URL pattern.

Usage:
    python scripts/download_artifacts.py
    python scripts/download_artifacts.py --tag v0.2.0
    python scripts/download_artifacts.py --repo owner/freshguard-vision

The detector and classifier asset names match the names produced by
notebooks/kaggle_03_* and kaggle_04_*.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

DEFAULT_REPO = "Abdulrahman-Elsmmany/freshguard-vision"
DEFAULT_TAG = "latest"
ASSETS = (
    "yolo26s_food_freshness.pt",
    "efficientnetv2s_food_freshness.pt",
)
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def gh_available() -> bool:
    return shutil.which("gh") is not None


def download_via_gh(repo: str, tag: str, dest: Path, asset: str) -> bool:
    # gh treats "latest" as a literal tag name. To get the actual latest
    # release, omit the tag entirely.
    cmd = ["gh", "release", "download"]
    if tag and tag != "latest":
        cmd.append(tag)
    cmd += ["--repo", repo, "--pattern", asset, "--dir", str(dest), "--clobber"]
    print(f"  gh: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    gh failed: {result.stderr.strip()}")
        return False
    return (dest / asset).exists()


def download_via_url(repo: str, tag: str, dest: Path, asset: str) -> bool:
    if tag == "latest":
        url = f"https://github.com/{repo}/releases/latest/download/{asset}"
    else:
        url = f"https://github.com/{repo}/releases/download/{tag}/{asset}"
    target = dest / asset
    print(f"  GET {url}")
    try:
        with urllib.request.urlopen(url) as response:
            target.write_bytes(response.read())
    except Exception as exc:
        print(f"    download failed: {exc}")
        if target.exists():
            target.unlink()
        return False
    return target.exists() and target.stat().st_size > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo (owner/name)")
    parser.add_argument("--tag", default=DEFAULT_TAG, help="Release tag (or 'latest')")
    args = parser.parse_args()

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    use_gh = gh_available()
    print(f"Repo: {args.repo}  Tag: {args.tag}  Dest: {ARTIFACTS_DIR}")
    print(f"Using gh CLI: {use_gh}")

    failures: list[str] = []
    for asset in ASSETS:
        target = ARTIFACTS_DIR / asset
        if target.exists() and target.stat().st_size > 0:
            print(f"[skip] {asset} already present ({target.stat().st_size / 1024 / 1024:.1f} MiB)")
            continue
        print(f"[get ] {asset}")
        ok = False
        if use_gh:
            ok = download_via_gh(args.repo, args.tag, ARTIFACTS_DIR, asset)
        if not ok:
            ok = download_via_url(args.repo, args.tag, ARTIFACTS_DIR, asset)
        if ok:
            print(f"    saved -> {target} ({target.stat().st_size / 1024 / 1024:.1f} MiB)")
        else:
            failures.append(asset)

    if failures:
        print(f"\nMissing: {', '.join(failures)}")
        print("Train the models on Kaggle (see notebooks/) and attach the .pt files")
        print(f"to a GitHub Release on {args.repo}.")
        return 1
    print("\nAll artifacts present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
