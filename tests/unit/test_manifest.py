from pathlib import Path

import pandas as pd

from bkk_cctv.ingest.build_manifest import parse_image_path

RAW = Path("data/raw/images/cctv_images")


def test_parses_real_filename_as_bangkok_time():
    p = RAW / "1028" / "1028_แยกสะพานแดง_แยกสะพานแดง_20260825_061012.jpg"
    row = parse_image_path(p)
    assert row["camera_id"] == "1028"
    assert row["captured_at"] == pd.Timestamp("2026-08-25 06:10:12", tz="Asia/Bangkok")
    assert str(row["captured_at"].tz) == "Asia/Bangkok"


def test_location_with_dashes_and_extra_underscores():
    p = RAW / "939" / "939_TF-KP-04-แยกมหาดไทย_แยก_มหาดไทย_20260831_205506.jpg"
    row = parse_image_path(p)
    assert row["camera_id"] == "939"
    assert row["captured_at"] == pd.Timestamp("2026-08-31 20:55:06", tz="Asia/Bangkok")


def test_unparseable_name_gives_nat():
    row = parse_image_path(RAW / "915" / "snapshot.jpg")
    assert row["camera_id"] == "915"
    assert pd.isna(row["captured_at"])
