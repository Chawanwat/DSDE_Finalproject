# Data Dictionary

Every table passed between pipeline stages. Column lists are enforced in code by
`src/bkk_cctv/schemas.py` — update both together.

| Table | File | Produced by | Grain |
|---|---|---|---|
| manifest | `data/interim/manifest.parquet` | `ingest/build_manifest.py` | 1 row per raw image |
| quality | `data/interim/quality.parquet` | `clean/quality_checks.py` | 1 row per raw image |
| detections | `data/processed/detections.parquet` | `detect/vehicle_detection.py` | 1 row per usable image |
| traffic_features | `data/processed/traffic_features.parquet` | `analysis/build_features.py` | 1 row per usable image |
| cameras | `data/reference/cctv_info.csv` | dataset Drive folder (`ingest/download_images.py`) | 1 row per camera |
| external sources | `data/external/<source>.parquet` | `scrape/<source>.py` | depends on source |

## manifest
| Column | Type | Meaning |
|---|---|---|
| camera_id | str | Camera identifier (folder name and first `_` token of the filename) |
| captured_at | datetime, tz-aware Asia/Bangkok | Parsed from the `<YYYYMMDD>_<HHMMSS>` suffix of the filename |
| path | str | Image path relative to the project root (absolute only if `RAW_IMAGES_DIR` is outside it). Use `bkk_cctv.config.resolve()` to open it |

## quality = manifest +
| Column | Type | Meaning |
|---|---|---|
| readable | bool | OpenCV could decode the file |
| brightness | float | Mean grayscale value (0–255) |
| blur_var | float | Variance of Laplacian; low = blurry |
| phash | str | Perceptual hash (kept for reference; not used for duplicates) |
| thumb | str | 16×16 grayscale thumbnail as hex, used for frozen-frame detection |
| too_dark, too_blurry, is_duplicate | bool | Individual quality flags (thresholds in `config/config.yaml`) |
| is_usable | bool | Passed every check; only these go to detection |

## detections
| Column | Type | Meaning |
|---|---|---|
| path, camera_id, captured_at | | Carried over from quality |
| car, motorcycle, bus, truck | int | YOLO detections per class (0 if none) |
| total | int | Sum of vehicle classes |

## traffic_features = detections +
| Column | Type | Meaning |
|---|---|---|
| hour | int | 0–23 |
| weekday | str | Monday … Sunday |
| *(planned)* lat, lon, weather, is_holiday … | | Joined from `cctv_info.csv` and `data/external/` |

## cameras (`cctv_info.csv`)
| Column | Type | Meaning |
|---|---|---|
| camera_id | int in csv (cast to str before joining) | Matches manifest `camera_id` |
| location, location_detail | str | Thai name / direction |
| location_en, location_detail_en | str | English name / direction |
| latitude, longitude | float | WGS84 |
| ip_address | str | Camera IP (internal BMA network) |
| image_count | int | Images in the dataset for this camera |
