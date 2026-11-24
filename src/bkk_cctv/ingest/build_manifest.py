"""Walk the raw image folder and build a manifest table (one row per image).

Output: data/interim/manifest.parquet with columns
    camera_id, captured_at, path
"""
from pathlib import Path

import pandas as pd

from bkk_cctv.config import load_config
from bkk_cctv.log import get_logger
from bkk_cctv.schemas import MANIFEST, check_columns

log = get_logger("pipeline")

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


def parse_image_path(path: Path) -> dict:
    # TODO: adjust once we know the dataset's folder/filename convention.
    # Assumes: <camera_id>/<timestamp>.jpg
    return {
        "camera_id": path.parent.name,
        "captured_at": pd.to_datetime(path.stem, errors="coerce"),
        "path": str(path),
    }


def build_manifest() -> pd.DataFrame:
    cfg = load_config()
    raw = cfg["paths"]["raw_images"]
    rows = [parse_image_path(p) for p in raw.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    df = pd.DataFrame(rows, columns=MANIFEST)
    check_columns(df, MANIFEST, "manifest")
    out = cfg["paths"]["interim"] / "manifest.parquet"
    df.to_parquet(out, index=False)
    log.info(f"{len(df)} images, {df['camera_id'].nunique()} cameras -> {out}")
    return df


if __name__ == "__main__":
    build_manifest()
