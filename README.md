# Bangkok CCTV Image Analysis

DSDE-CEDT 2110403 final project (2026/1). Turns raw BMA traffic-camera images
from 100 cameras into structured traffic data, adds scraped external data,
and presents insights in a dashboard.

**Topic: does rain really make Bangkok traffic worse?** Vehicle density from
YOLO is compared before / during / after rain (Open-Meteo) to find which
cameras are most rain-sensitive. Due **Sun 6 Dec 2026**.

| Doc | What's in it |
|---|---|
| [project.md](project.md) | Current status, dataset facts, bug log, TODO (Thai) |
| [SETUP.md](SETUP.md) | Step-by-step setup, Colab GPU, troubleshooting (Thai) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Design, folder tree, conventions, team workflow |
| [docs/data_dictionary.md](docs/data_dictionary.md) | Columns of every table |

## Dataset

61,319 JPEG images from 100 cameras, 25–31 Aug 2026, roughly 06:00–21:00
only, one frame per camera every ~10 minutes. Timestamps in file names are
Asia/Bangkok local time. Camera metadata (location, lat/lon) is in
`data/reference/cctv_info.csv`.

## Setup with Docker (recommended — includes Kafka)

Needs Docker Desktop. One image holds Python 3.12 and everything in
`requirements.txt` (pandas, YOLO/torch CPU, OpenCV, Playwright + Chromium,
Prefect, Streamlit, Jupyter, confluent-kafka); Kafka runs as its own container.

```bash
cp .env.example .env                                # optional overrides (Kafka, RAW_IMAGES_DIR)
docker compose build                                # first time: ~10 min
docker compose up -d                                # Kafka, Kafka UI, dashboard, Jupyter
docker compose run --rm app python -m bkk_cctv.stream.kafka_io   # Kafka smoke test
```

| Service | URL / address |
|---|---|
| Dashboard (Streamlit) | http://localhost:8501 |
| JupyterLab | http://localhost:8888 |
| Kafka UI | http://localhost:8080 |
| Kafka broker | `kafka:29092` inside containers, `localhost:9092` from your machine |

```bash
docker compose run --rm app bash                    # shell with all deps
docker compose --profile data up dataset           # download + unzip dataset into ./data/raw/images
docker compose --profile pipeline up pipeline       # full Prefect pipeline once
docker compose down                                 # stop (add -v to wipe Kafka data)
```

The dataset is **not baked into the image** (≈1.6 GB zip). It is downloaded
into `./data/raw/images` on your machine, and the containers read it from
there through the mount. Download it once and every service can use it.

The project folder is mounted at `/app`, so code edits and `data/` are shared
with your machine and there is no need to rebuild after editing code. Rebuild only when
`requirements.txt` changes. Docker on macOS can't use the GPU, so YOLO runs on
CPU; run full detection on Colab or a GPU machine if it's too slow.

## Setup without Docker

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # also installs src/bkk_cctv (editable)
playwright install chromium
cp .env.example .env                # optional overrides (Kafka, RAW_IMAGES_DIR)
```

## Project structure

```
config/config.yaml     paths, thresholds, YOLO settings
data/                  raw → interim → processed, + external/ (not in git); reference/ (in git)
src/bkk_cctv/
  ingest/ clean/ detect/ pipeline/   Component 1: Data Engineering
  scrape/                            Required task: additional data
  analysis/                          Component 2: Data Science
dashboard/app.py       Component 3: BI dashboard (Streamlit)
notebooks/             EDA / insights (Component 4)
reports/               figures + final slides PDF
docs/                  ARCHITECTURE.md, data_dictionary.md
tests/                 unit tests + fixtures
```

Full explanation, naming conventions and team workflow: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Run

```bash
python -m bkk_cctv.ingest.download_images   # once
python -m bkk_cctv.pipeline.flow            # manifest → clean → detect → features
streamlit run dashboard/app.py
ruff check src tests dashboard && pytest
```

Each stage also runs on its own with `python -m bkk_cctv.<stage>.<module>`
(see [SETUP.md](SETUP.md)). No API keys are needed so far: Open-Meteo, the
Google holiday calendar and Traffy Fondue are all public.

## Status (2026-11-24)

| Stage | Status |
|---|---|
| Download, manifest, quality checks | Done; run on all 61k images |
| Vehicle detection (YOLO) | Works; full run should be on Colab GPU |
| Scrapers (`weather`, `holidays`, `source3` = Traffy Fondue) | Stubs |
| Features (`build_features`) | Adds only `hour` / `weekday`; no camera or weather join yet |
| Dashboard | Skeleton only |

`pipeline.flow` has not been run end to end on the full dataset yet (the YOLO
step on CPU is slow for 61k images), and its output has no rain columns yet. Details and TODO:
[project.md](project.md).
