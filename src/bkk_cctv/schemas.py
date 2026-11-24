"""Column contracts for every table passed between pipeline stages.

Each stage should call `check_columns` before writing its output so a broken
stage fails loudly instead of silently corrupting the next one.
See docs/data_dictionary.md for column meanings.
"""
import pandas as pd

MANIFEST = ["camera_id", "captured_at", "path"]
QUALITY = MANIFEST + ["readable", "brightness", "blur_var", "phash",
                      "too_dark", "too_blurry", "is_duplicate", "is_usable"]
DETECTIONS = ["path", "camera_id", "captured_at", "total"]
FEATURES = DETECTIONS + ["hour", "weekday"]
CAMERAS = ["camera_id", "name", "lat", "lon"]


def check_columns(df: pd.DataFrame, required: list[str], table: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{table}: missing columns {missing}")
