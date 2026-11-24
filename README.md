# Bangkok CCTV Image Analysis

DSDE-CEDT 2110403 final project (2026/1). Turns raw BMA traffic-camera images
from 100 cameras into structured traffic data, adds scraped external data,
and presents insights in a dashboard.

## Setup

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
