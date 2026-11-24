"""Run YOLO on usable images and count vehicles per class.

Reads data/interim/quality.parquet, writes data/processed/detections.parquet
(one row per image: camera_id, captured_at, car, motorcycle, bus, truck, total).
"""
import pandas as pd
from ultralytics import YOLO

from bkk_cctv.config import load_config, resolve
from bkk_cctv.schemas import DETECTIONS, VEHICLE_COLS, check_columns


def run_detection() -> pd.DataFrame:
    cfg = load_config()
    d = cfg["detect"]
    images = pd.read_parquet(cfg["paths"]["interim"] / "quality.parquet")
    images = images[images["is_usable"]]

    if images.empty:
        raise ValueError("No usable images: check quality thresholds in config.yaml")

    # Keep weights in models/ (ultralytics downloads them there on first use)
    model = YOLO(str(cfg["paths"]["models"] / d["model"]))
    rows = []
    paths = images["path"].tolist()
    for i in range(0, len(paths), d["batch_size"]):
        batch = paths[i : i + d["batch_size"]]
        results = model(
            [str(resolve(p)) for p in batch], conf=d["conf"], classes=d["classes"], verbose=False
        )
        for path, res in zip(batch, results, strict=True):
            names = [res.names[int(c)] for c in res.boxes.cls]
            rows.append({"path": path, **pd.Series(names, dtype=str).value_counts().to_dict()})

    counts = pd.DataFrame(rows)
    df = images[["path", "camera_id", "captured_at"]].merge(counts, on="path", how="left")
    # Always emit every vehicle column (0 when a class was never seen)
    for col in VEHICLE_COLS:
        if col not in df:
            df[col] = 0
    df[VEHICLE_COLS] = df[VEHICLE_COLS].fillna(0).astype(int)
    df["total"] = df[VEHICLE_COLS].sum(axis=1)
    check_columns(df, DETECTIONS, "detections")
    df.to_parquet(cfg["paths"]["processed"] / "detections.parquet", index=False)
    return df


if __name__ == "__main__":
    run_detection()
