"""Run YOLO on usable images and count vehicles per class.

Reads data/interim/quality.parquet, writes data/processed/detections.parquet
(one row per image: camera_id, captured_at, car, motorcycle, bus, truck, total).
"""
import pandas as pd
from ultralytics import YOLO

from bkk_cctv.config import load_config
from bkk_cctv.schemas import DETECTIONS, check_columns


def run_detection() -> pd.DataFrame:
    cfg = load_config()
    d = cfg["detect"]
    images = pd.read_parquet(cfg["paths"]["interim"] / "quality.parquet")
    images = images[images["is_usable"]]

    model = YOLO(d["model"])
    rows = []
    paths = images["path"].tolist()
    for i in range(0, len(paths), d["batch_size"]):
        batch = paths[i : i + d["batch_size"]]
        results = model(batch, conf=d["conf"], classes=d["classes"], verbose=False)
        for path, res in zip(batch, results, strict=True):
            names = [res.names[int(c)] for c in res.boxes.cls]
            counts = pd.Series(names).value_counts().to_dict()
            rows.append({"path": path, **counts})

    counts = pd.DataFrame(rows).fillna(0)
    df = images[["path", "camera_id", "captured_at"]].merge(counts, on="path", how="left").fillna(0)
    vehicle_cols = [c for c in ["car", "motorcycle", "bus", "truck"] if c in df]
    df["total"] = df[vehicle_cols].sum(axis=1)
    check_columns(df, DETECTIONS, "detections")
    df.to_parquet(cfg["paths"]["processed"] / "detections.parquet", index=False)
    return df


if __name__ == "__main__":
    run_detection()
