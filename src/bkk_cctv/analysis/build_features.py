"""Join detections with external data into the analysis-ready table.

Output: data/processed/traffic_features.parquet
(camera_id, captured_at, hour, weekday, vehicle counts, + external columns).
"""
import pandas as pd

from bkk_cctv.config import load_config
from bkk_cctv.schemas import FEATURES, check_columns


def build_features() -> pd.DataFrame:
    cfg = load_config()
    df = pd.read_parquet(cfg["paths"]["processed"] / "detections.parquet")
    df["hour"] = df["captured_at"].dt.hour
    df["weekday"] = df["captured_at"].dt.day_name()
    # TODO: merge camera locations + data/external/*.parquet (weather, holidays, ...)
    check_columns(df, FEATURES, "traffic_features")
    df.to_parquet(cfg["paths"]["processed"] / "traffic_features.parquet", index=False)
    return df


if __name__ == "__main__":
    build_features()
