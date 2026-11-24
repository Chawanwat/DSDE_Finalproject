"""Walk the raw image folder and build a manifest table (one row per image).

Output: data/interim/manifest.parquet with columns
    camera_id, captured_at, path
"""
from pathlib import Path

import pandas as pd

from bkk_cctv.config import load_config, to_rel
from bkk_cctv.log import get_logger
from bkk_cctv.schemas import MANIFEST, check_columns

log = get_logger("pipeline")

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
TS_FORMAT = "%Y%m%d_%H%M%S"
TZ = "Asia/Bangkok"


def parse_image_path(path: Path) -> dict:
    """Parse one raw image path.

    Real layout (cctv_images.zip, Aug 2026):
        cctv_images/<camera_id>/<camera_id>_<location>_<detail>_<YYYYMMDD>_<HHMMSS>.jpg
    Location text may itself contain underscores, so the timestamp is taken from the
    last two '_' tokens and camera_id from the first. Timestamps are Bangkok local time.
    Unparseable names give captured_at = NaT (dropped later with a warning).
    """
    parts = path.stem.split("_")
    camera_id = parts[0] if parts[0].isdigit() else path.parent.name
    stamp = "_".join(parts[-2:]) if len(parts) >= 3 else ""
    ts = pd.to_datetime(stamp, format=TS_FORMAT, errors="coerce")
    return {
        "camera_id": camera_id,
        "captured_at": ts.tz_localize(TZ) if not pd.isna(ts) else pd.NaT,
        "path": to_rel(path),
    }


def build_manifest() -> pd.DataFrame:
    cfg = load_config()
    raw = cfg["paths"]["raw_images"]
    rows = [parse_image_path(p) for p in raw.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    df = pd.DataFrame(rows, columns=MANIFEST)
    df["captured_at"] = pd.to_datetime(df["captured_at"]).dt.tz_convert(TZ)
    bad = df["captured_at"].isna()
    if bad.any():
        example = df.loc[bad, "path"].iloc[0]
        log.warning(f"{bad.sum()} images with unparseable timestamps dropped, e.g. {example}")
        df = df[~bad]
    df = df.sort_values(["camera_id", "captured_at"]).reset_index(drop=True)
    check_columns(df, MANIFEST, "manifest")
    out = cfg["paths"]["interim"] / "manifest.parquet"
    df.to_parquet(out, index=False)
    log.info(f"{len(df)} images, {df['camera_id'].nunique()} cameras -> {out}")
    return df


if __name__ == "__main__":
    build_manifest()
