# Data Dictionary

Every table passed between pipeline stages. Column lists are enforced in code by
`src/bkk_cctv/schemas.py` — update both together.

| Table | File | Produced by | Grain |
|---|---|---|---|
| manifest | `data/interim/manifest.parquet` | `ingest/build_manifest.py` | 1 row per raw image |
| quality | `data/interim/quality.parquet` | `clean/quality_checks.py` | 1 row per raw image |
| detections | `data/processed/detections.parquet` | `detect/vehicle_detection.py` | 1 row per usable image |
| traffic_features | `data/processed/traffic_features.parquet` | `analysis/build_features.py` | 1 row per usable image |
| cameras | `data/reference/cameras.csv` | manual / scraped once | 1 row per camera |
| external sources | `data/external/<source>.parquet` | `scrape/<source>.py` | depends on source |

## manifest
| Column | Type | Meaning |
|---|---|---|
| camera_id | str | Camera identifier (folder name in raw data) |
| captured_at | datetime (Asia/Bangkok) | When the image was taken |
| path | str | Absolute path to the image file |

## quality = manifest +
| Column | Type | Meaning |
|---|---|---|
| readable | bool | OpenCV could decode the file |
| brightness | float | Mean grayscale value (0–255) |
| blur_var | float | Variance of Laplacian; low = blurry |
| phash | str | Perceptual hash, for duplicate / frozen-frame detection |
| too_dark, too_blurry, is_duplicate | bool | Individual quality flags (thresholds in `config/config.yaml`) |
| is_usable | bool | Passed every check; only these go to detection |

## detections
| Column | Type | Meaning |
|---|---|---|
| path, camera_id, captured_at | | Carried over from quality |
| car, motorcycle, bus, truck | int | YOLO detections per class (column only present if seen at least once) |
| total | int | Sum of vehicle classes |

## traffic_features = detections +
| Column | Type | Meaning |
|---|---|---|
| hour | int | 0–23 |
| weekday | str | Monday … Sunday |
| *(planned)* lat, lon, weather, is_holiday … | | Joined from `cameras.csv` and `data/external/` |
