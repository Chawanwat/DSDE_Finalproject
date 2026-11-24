# Bangkok CCTV Image Analysis

DSDE-CEDT 2110403 final project (2026/1). Turns raw BMA traffic-camera images
from 100 cameras into structured traffic data, adds scraped external data,
and presents insights in a dashboard.

## Setup with Docker (recommended — includes Kafka)

Needs Docker Desktop. One image holds Python 3.12 and everything in
`requirements.txt` (pandas, YOLO/torch CPU, OpenCV, Playwright + Chromium,
Prefect, Streamlit, Jupyter, confluent-kafka); Kafka runs as its own container.

```bash
cp .env.example .env                                # fill in API keys
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
docker compose run --rm app python -m bkk_cctv.ingest.download_images
docker compose --profile pipeline up pipeline       # full Prefect pipeline once
docker compose down                                 # stop (add -v to wipe Kafka data)
```

The project folder is mounted at `/app`, so code edits and `data/` are shared
with your machine and there is no need to rebuild after editing code. Rebuild only when
`requirements.txt` changes. Docker on macOS can't use the GPU, so YOLO runs on
CPU; run full detection on Colab or a GPU machine if it's too slow.

## Setup without Docker

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # also installs src/bkk_cctv (editable)
playwright install chromium
cp .env.example .env                # fill in API keys
```

## Project structure

```
config/config.yaml     paths, thresholds, YOLO settings
data/                  raw → interim → processed, + external/, reference/ (not in git)
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
