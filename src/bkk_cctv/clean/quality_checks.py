"""Image quality checks: unreadable, too dark, too blurry, duplicate/frozen frames.

Reads data/interim/manifest.parquet, writes data/interim/quality.parquet
with one flag column per check and an overall `is_usable`.

Images are processed in parallel (config clean.workers, default = all CPUs).
"""
import os
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from bkk_cctv.config import load_config, resolve
from bkk_cctv.log import get_logger
from bkk_cctv.schemas import QUALITY, check_columns

log = get_logger("pipeline")

THUMB = 16  # side of the grayscale thumbnail used for frozen-frame detection


def image_metrics(path: str) -> dict:
    # Heavy imports kept local so this module (and thumb_diff) imports without
    # OpenCV, e.g. in the light CI install.
    import cv2
    import imagehash
    from PIL import Image

    full = str(resolve(path))
    img = cv2.imread(full)
    if img is None:
        return {"readable": False, "brightness": None, "blur_var": None,
                "phash": None, "thumb": None}
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    with Image.open(full) as pil:
        phash = str(imagehash.phash(pil))
    thumb = cv2.resize(gray, (THUMB, THUMB), interpolation=cv2.INTER_AREA)
    return {
        "readable": True,
        "brightness": float(gray.mean()),
        "blur_var": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "phash": phash,
        "thumb": thumb.tobytes().hex(),
    }


def thumb_diff(a, b) -> float:
    """Mean absolute grey-level difference between two hex-encoded thumbnails;
    NaN if either is missing."""
    if not isinstance(a, str) or not isinstance(b, str) or len(a) != len(b):
        return float("nan")
    x, y = bytes.fromhex(a), bytes.fromhex(b)
    return sum(abs(i - j) for i, j in zip(x, y, strict=True)) / len(x)


def flag_duplicates(df: pd.DataFrame, max_diff: float) -> pd.Series:
    """True when a frame is (nearly) identical to the previous frame of the same
    camera, i.e. a frozen feed. Expects df sorted by camera_id, captured_at.

    Why not pHash: on these fixed cameras, consecutive *live* frames 10 minutes
    apart often have pHash distance 0-2 (static scene), so pHash would drop
    ~10% of valid, mostly low-traffic frames. A frozen feed instead has a
    near-zero pixel difference (only the burnt-in clock changes)."""
    prev = df.groupby("camera_id")["thumb"].shift()
    diff = pd.Series([thumb_diff(a, b) for a, b in zip(df["thumb"], prev, strict=True)],
                     index=df.index)
    return diff <= max_diff  # NaN (first frame / unreadable) -> False


def compute_metrics(paths: list[str], workers: int | None = None) -> pd.DataFrame:
    workers = workers or os.cpu_count() or 1
    if workers == 1:
        rows = [image_metrics(p) for p in paths]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            rows = list(pool.map(image_metrics, paths, chunksize=64))
    return pd.DataFrame(rows, columns=["readable", "brightness", "blur_var", "phash", "thumb"])


def run_quality_checks() -> pd.DataFrame:
    cfg = load_config()
    c = cfg["clean"]
    manifest = pd.read_parquet(cfg["paths"]["interim"] / "manifest.parquet")
    manifest = manifest.sort_values(["camera_id", "captured_at"]).reset_index(drop=True)
    log.info(f"Quality checks on {len(manifest):,} images ...")
    metrics = compute_metrics(manifest["path"].tolist(), c.get("workers"))
    df = pd.concat([manifest, metrics], axis=1)

    df["readable"] = df["readable"].astype(bool)
    df["too_dark"] = df["brightness"] < c["min_brightness"]
    df["too_blurry"] = df["blur_var"] < c["min_blur_var"]
    df["is_duplicate"] = flag_duplicates(df, c["dup_max_pixel_diff"])
    df["is_usable"] = df["readable"] & ~df["too_dark"] & ~df["too_blurry"] & ~df["is_duplicate"]

    check_columns(df, QUALITY, "quality")
    df.to_parquet(cfg["paths"]["interim"] / "quality.parquet", index=False)
    flags = df[["readable", "too_dark", "too_blurry", "is_duplicate", "is_usable"]].sum()
    log.info(f"Quality flags: {flags.to_dict()}")
    return df


if __name__ == "__main__":
    run_quality_checks()
