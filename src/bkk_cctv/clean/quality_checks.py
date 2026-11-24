"""Image quality checks: unreadable, too dark, too blurry, duplicate/frozen frames.

Reads data/interim/manifest.parquet, writes data/interim/quality.parquet
with one flag column per check and an overall `is_usable`.
"""
import cv2
import imagehash
import pandas as pd
from PIL import Image

from bkk_cctv.config import load_config
from bkk_cctv.schemas import QUALITY, check_columns


def image_metrics(path: str) -> dict:
    img = cv2.imread(path)
    if img is None:
        return {"readable": False, "brightness": None, "blur_var": None, "phash": None}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return {
        "readable": True,
        "brightness": float(gray.mean()),
        "blur_var": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "phash": str(imagehash.phash(Image.open(path))),
    }


def run_quality_checks() -> pd.DataFrame:
    cfg = load_config()
    c = cfg["clean"]
    manifest = pd.read_parquet(cfg["paths"]["interim"] / "manifest.parquet")
    metrics = pd.DataFrame([image_metrics(p) for p in manifest["path"]])
    df = pd.concat([manifest, metrics], axis=1)

    df["too_dark"] = df["brightness"] < c["min_brightness"]
    df["too_blurry"] = df["blur_var"] < c["min_blur_var"]
    # Frozen camera: same hash as the previous frame of the same camera
    # TODO: use hash distance (c["dup_hash_distance"]) instead of exact match
    df = df.sort_values(["camera_id", "captured_at"])
    df["is_duplicate"] = df.groupby("camera_id")["phash"].shift() == df["phash"]
    df["is_usable"] = df["readable"] & ~df["too_dark"] & ~df["too_blurry"] & ~df["is_duplicate"]

    check_columns(df, QUALITY, "quality")
    df.to_parquet(cfg["paths"]["interim"] / "quality.parquet", index=False)
    return df


if __name__ == "__main__":
    run_quality_checks()
