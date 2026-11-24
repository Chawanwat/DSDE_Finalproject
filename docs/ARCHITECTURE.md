# Project Architecture — Bangkok CCTV Image Analysis

| | |
|---|---|
| Project | Bangkok CCTV Image Analysis (DSDE-CEDT 2110403, 2026/1) |
| Type | Data science / data engineering + computer vision |
| Stack | Python 3.11–3.12 · pandas/Parquet/DuckDB · OpenCV · YOLO (ultralytics) · Prefect · Kafka · Docker Compose · requests/BS4/Playwright · scikit-learn/statsmodels · Streamlit/Plotly |
| Team | Small team (≤ 6 students) |
| Stage | Development. Package due **Sun 6 Dec 2026** |
| Deliverables | Source code, slides (PDF), 15-minute YouTube video, BI dashboard demo |

---

## A. Project Architecture Overview

The project is a **batch data pipeline** feeding an **analytical dashboard**:

```
 Google Drive (≈62k CCTV images, 100 cameras)        Web sources / APIs
            │                                               │
   ingest ──► clean ──► detect ──────────┐           scrape (required task)
 (manifest)  (quality)  (vehicle counts)  ▼                 │
                                     analysis ◄─────────────┘
                                  (traffic_features)
                                          │
                          ┌───────────────┴───────────────┐
                     dashboard (BI)               notebooks / reports
                     Component 3                  Component 2 & 4
```

Design choices and reasons:

1. **Stage-per-module, file-based handoff.** Each stage reads one table from
   `data/` and writes the next one as Parquet. Stages share no in-memory
   state, so team members can work on different stages in parallel, re-run a
   single stage, or debug it in a notebook by loading its input file.
2. **Installable package (`src/` layout).** All logic lives in `src/bkk_cctv/`
   and is installed with `pip install -e .`. The pipeline, dashboard,
   notebooks and tests all import it the same way
   (`from bkk_cctv... import ...`), with no `sys.path` hacks. The `src/` layer
   also stops tests from accidentally importing uninstalled code.
3. **Thin orchestration.** `pipeline/flow.py` (Prefect) only wires the stage
   functions together. This covers the "workflow management / end-to-end" bonus
   in Component 1 without tying stage code to Prefect, so every stage still
   runs on its own with `python -m`.
4. **Config and secrets kept out of code.** Thresholds and paths go in
   `config/config.yaml` (committed). Keys and machine-specific paths go in
   `.env` (not committed; `.env.example` is the template).
5. **Data contracts.** `schemas.py` lists the required columns of every table.
   Each stage checks them before writing, so a broken upstream stage fails
   immediately instead of silently corrupting the dashboard.

6. **Reproducible environment with Docker Compose.** One image (`Dockerfile`)
   holds every Python dependency; `docker-compose.yml` adds a single-node
   Kafka broker (KRaft) and Kafka UI. The project folder is mounted into the
   containers, so the file-based handoff in `data/` works the same inside and
   outside Docker. Kafka helpers live in `src/bkk_cctv/stream/kafka_io.py`.

What is deliberately **not** included: no web backend, no Kubernetes, no
microservices. The grading criteria reward a working end-to-end workflow and
insights, not deployment infrastructure.

---

## B. Complete Folder Tree

```
DSDE_Finalproject/
│
├── README.md                    quick start
├── LICENSE
├── pyproject.toml               package metadata + pytest/ruff config
├── requirements.txt             all dependencies (installs the package with -e .)
├── .env.example                 template for secrets / local overrides
├── Dockerfile                   one image with all Python dependencies
├── docker-compose.yml           Kafka + Kafka UI + dashboard + Jupyter + pipeline
├── .dockerignore
├── .gitignore
│
├── .github/
│   └── workflows/
│       └── ci.yml               lint + unit tests on every push / PR
│
├── config/
│   └── config.yaml              paths, quality thresholds, YOLO settings
│
├── data/                        ← NOT in git except reference/ and .gitkeep
│   ├── raw/                     original CCTV images, never modified
│   ├── interim/                 manifest.parquet, quality.parquet
│   ├── processed/               detections.parquet, traffic_features.parquet
│   ├── external/                scraped data, one file per source
│   └── reference/               small static lookups (cctv_info.csv), in git
│
├── src/
│   └── bkk_cctv/                the installable Python package
│       ├── __init__.py
│       ├── config.py            loads config.yaml + .env, resolves paths
│       ├── schemas.py           column contracts for every table
│       ├── log.py               shared logger (console + logs/)
│       ├── ingest/              ┐
│       │   ├── download_images.py
│       │   └── build_manifest.py│
│       ├── clean/               │ Component 1: Data Engineering
│       │   └── quality_checks.py│
│       ├── detect/              │
│       │   └── vehicle_detection.py
│       ├── pipeline/            │
│       │   └── flow.py          ┘
│       ├── stream/              Kafka producer/consumer helpers
│       │   └── kafka_io.py
│       ├── scrape/              Required task: additional data
│       │   ├── README.md
│       │   ├── weather.py
│       │   ├── holidays.py
│       │   └── source3.py
│       └── analysis/            Component 2: Data Science
│           └── build_features.py
│
├── dashboard/
│   └── app.py                   Component 3: Streamlit BI dashboard
│
├── notebooks/                   EDA and experiments (Components 2 & 4)
│   └── README.md
│
├── reports/
│   ├── figures/                 exported charts for slides / video
│   └── slides/                  final presentation PDF
│
├── docs/
│   ├── ARCHITECTURE.md          this document
│   └── data_dictionary.md       every table and column
│
├── tests/
│   ├── unit/                    fast tests, no images or GPU needed
│   │   ├── test_config.py
│   │   └── test_schemas.py
│   └── fixtures/                a few tiny sample images / tables
│
├── models/                      downloaded YOLO weights, not in git
└── logs/                        runtime logs, not in git (created at runtime)
```

---

## C. Directory Documentation

### Root files
| File | Purpose | Notes |
|---|---|---|
| `README.md` | Setup and run commands. The first thing a new member reads | Keep it short; detail belongs in `docs/` |
| `pyproject.toml` | Makes `src/bkk_cctv` installable; holds pytest and ruff config | Dependencies are **not** duplicated here |
| `requirements.txt` | Single source of truth for dependencies; ends with `-e .` | Add new libraries here, grouped by component |
| `.env.example` | Lists every environment variable the code reads | Real values go in `.env`, which git ignores |
| `.gitignore` | Keeps data, weights, logs, secrets and caches out of git | |

### `.github/workflows/`
- **Purpose:** CI. Runs `ruff` and `pytest` on every push and pull request.
- **Stores:** workflow YAML only.
- **Not:** anything that needs images or a GPU. CI does a light install that skips torch.

### `config/`
- **Purpose:** tunable, non-secret settings shared by the whole team.
- **Stores:** `config.yaml`: data paths, quality thresholds, YOLO model, confidence, classes, batch size.
- **Not:** API keys or passwords (→ `.env`), Python code, or values that change per machine (→ `.env`).
- **Relationship:** read only through `bkk_cctv.config.load_config()`; never parsed directly elsewhere.

### `data/`
Follows the *raw → interim → processed* convention. Data moves in one direction only.

| Folder | Stores | Does NOT store | In git? |
|---|---|---|---|
| `raw/` | Images exactly as downloaded from Drive | Anything edited, resized or filtered | No |
| `interim/` | Intermediate tables (manifest, quality flags) | Final analysis tables | No |
| `processed/` | Analysis-ready tables read by the dashboard and notebooks | Raw images | No |
| `external/` | Output of `scrape/`, one `<source>.parquet` per source | Hand-edited files | No |
| `reference/` | Small static lookups (`cctv_info.csv`) | Anything large or regenerated by code | **Yes** |

Rule: everything in `raw/`, `interim/`, `processed/` and `external/` can be
rebuilt by running code. If a file can't be rebuilt, it belongs in `reference/`
or must be documented.

### `src/bkk_cctv/`
The only place for reusable logic. Anything imported by more than one
script, notebook or the dashboard lives here.

| Module | Responsibility | Input → Output |
|---|---|---|
| `config.py` | Load config + `.env`, resolve absolute paths | — |
| `schemas.py` | Required columns per table; `check_columns()` | — |
| `log.py` | `get_logger(name)` writing to console and `logs/` | — |
| `ingest/` | Download images; build the manifest from file names | Drive → `raw/` → `interim/manifest.parquet` |
| `clean/` | Flag unreadable, dark, blurry and frozen/duplicate frames | manifest → `interim/quality.parquet` |
| `detect/` | YOLO vehicle counting on usable images | quality → `processed/detections.parquet` |
| `scrape/` | One module per external source, each with `fetch()` and `save()` | web/API → `external/<source>.parquet` |
| `analysis/` | Join detections with camera and external data; features; models | detections + external → `processed/traffic_features.parquet` |
| `pipeline/` | Prefect flow calling the stage functions in order | — |
| `stream/` | Kafka producer/consumer helpers + smoke test | — |

**Not stored here:** notebooks, charts, data files, one-off exploration code, or Streamlit UI code.
**Dependency rule:** stages depend on `config`, `schemas` and `log`. They never
import each other; they communicate only through files in `data/`. Only
`pipeline/` imports multiple stages.

### `dashboard/`
- **Purpose:** Component 3, the Streamlit BI dashboard.
- **Stores:** UI code: layout, filters, charts and maps.
- **Not:** data processing. If the dashboard needs a new column, add it in
  `analysis/` so notebooks and slides get it too.
- **Relationship:** reads only from `data/processed/` and `data/reference/`.

### `notebooks/`
- **Purpose:** EDA, model experiments, and finding the insights (Components 2 & 4).
- **Stores:** `.ipynb` files named by the convention below.
- **Not:** logic that the pipeline or dashboard depends on. Once code is
  reused, move it into `src/bkk_cctv/`.

### `reports/`
- **Purpose:** final deliverables that come out of the analysis.
- `figures/`: exported PNG/SVG charts used in the slides and video.
- `slides/`: the final presentation PDF for submission.
- **Not:** intermediate data or scratch plots.

### `docs/`
- **Purpose:** project documentation that is longer than the README.
- `ARCHITECTURE.md`: structure, conventions and workflow (this file).
- `data_dictionary.md`: tables and columns. Update it whenever `schemas.py` changes.

### `tests/`
- `unit/`: fast tests with no network, GPU or full dataset (config, schemas,
  quality metrics, scraping parsers on saved HTML).
- `fixtures/`: tiny inputs for tests (a few JPEGs: one dark, one blurry, one
  normal; a saved HTML page per scraped source).
- **Not:** the real dataset, or tests that take minutes.
- Mirrors `src/bkk_cctv/`: `clean/quality_checks.py` → `tests/unit/test_quality_checks.py`.

### `models/` and `logs/`
- `models/`: downloaded or fine-tuned weights (`*.pt`). Ignored by git.
- `logs/`: runtime logs from `get_logger`. Ignored by git; created automatically.

### Why there is no `scripts/`, `outputs/` or `deployment/`
- Every stage already runs as `python -m bkk_cctv.<stage>.<module>`, so wrapper scripts would duplicate it.
- Generated data goes to `data/` and deliverables to `reports/`; an `outputs/` folder would overlap both.
- The dashboard runs locally (or on Streamlit Community Cloud with no extra files). Add `deployment/` only if that changes.

---

## D. File Naming Conventions

| Item | Convention | Examples |
|---|---|---|
| Folders | lowercase, `snake_case`, plural only for collections | `data/external/`, `tests/fixtures/` |
| Python package | short `snake_case` | `bkk_cctv` |
| Python modules | `snake_case`, verb or noun describing the job | `build_manifest.py`, `vehicle_detection.py` |
| Stage entry functions | `run_<stage>()` / `build_<table>()` | `run_quality_checks()`, `build_features()` |
| Scraper modules | `<source>.py` exposing `fetch()` and `save()` | `weather.py`, `holidays.py` |
| Classes / constants | `PascalCase` / `UPPER_SNAKE` | `MANIFEST`, `IMAGE_EXTS` |
| Config files | lowercase `snake_case.yaml` | `config.yaml` |
| Env variables | `UPPER_SNAKE` | `WEATHER_API_KEY`, `RAW_IMAGES_DIR` |
| Tests | `test_<module>.py`, `test_<behavior>()` | `test_quality_checks.py::test_dark_image_flagged` |
| Notebooks | `NN_<initials>_<topic>.ipynb` | `01_tt_eda_images.ipynb`, `05_pk_rain_vs_traffic.ipynb` |
| Data tables | `<table>.parquet`, named after the schema | `manifest.parquet`, `traffic_features.parquet` |
| External data | `<source>.parquet`, same name as the scraper | `weather.parquet` |
| Reference data | `<entity>.csv` | `cctv_info.csv` |
| Figures | `<component>_<topic>.png` | `ds_hourly_traffic.png`, `de_quality_breakdown.png` |
| Docs | `UPPERCASE.md` for top-level guides, `snake_case.md` for others | `ARCHITECTURE.md`, `data_dictionary.md` |
| Logs | `<logger_name>.log` | `pipeline.log` |
| Git branches | `<type>/<short-topic>` | `feat/weather-scraper`, `fix/manifest-timestamps` |

---

## E. Development Workflow

### First-time setup
```bash
git clone <repo> && cd DSDE_Finalproject
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # includes `-e .`
playwright install chromium
cp .env.example .env                     # fill in keys
python -m bkk_cctv.ingest.download_images
```

### Day to day
1. **Pick a stage** (ingest / clean / detect / scrape / analysis / dashboard)
   and create a branch: `git switch -c feat/<topic>`.
2. **Explore in a notebook** using real input files from `data/`.
3. **Move working code into `src/bkk_cctv/<stage>/`.** Expose one entry
   function and add a `__main__` block.
4. **If the output table changes,** update `schemas.py` *and*
   `docs/data_dictionary.md` in the same commit.
5. **Add a unit test** with a tiny fixture where practical.
6. **Run checks:** `ruff check src tests dashboard && pytest`.
7. **Open a PR.** CI must pass, and one teammate reviews before merging to `main`.

### Running things
```bash
python -m bkk_cctv.pipeline.flow                 # full pipeline (manifest → features)
python -m bkk_cctv.clean.quality_checks          # one stage only
python -m bkk_cctv.scrape.weather                # one scraper
streamlit run dashboard/app.py                   # dashboard
pytest                                           # tests
```

### Sharing data between teammates
Processed tables are not in git. To save each member from re-running YOLO on
about 62k images, one person runs the pipeline and uploads `data/processed/*.parquet`
to a shared Drive folder. Others download them into the same paths.

### Suggested ownership (6 members)
| Area | Folders |
|---|---|
| Ingest + cleaning | `ingest/`, `clean/`, `config/` |
| Vehicle detection | `detect/`, `models/` |
| Scraping (2 people) | `scrape/`, `data/external/`, `data/reference/` |
| Analysis + insights | `analysis/`, `notebooks/`, `reports/figures/` |
| Dashboard + pipeline | `dashboard/`, `pipeline/`, `.github/` |

---

## F. Best Practices

- **Raw data is read-only.** Never overwrite files in `data/raw/`. Cleaning
  produces flags, not deleted images.
- **No hard-coded paths or thresholds.** Use `load_config()`. A literal
  `"data/..."` string in a module is a bug.
- **No secrets in git.** Keys go in `.env`; add each new variable to `.env.example` with an empty value.
- **One stage, one output file.** If a stage starts writing two unrelated tables, split it.
- **Stages talk only through files.** Don't import `clean` from `detect`; read `quality.parquet`.
- **Notebooks are disposable; `src/` is not.** Clear notebook outputs before
  committing to keep diffs readable, and never import from a notebook.
- **The dashboard computes nothing heavy.** Precompute aggregates in
  `analysis/` and cache reads with `@st.cache_data`.
- **Make stages idempotent.** Re-running a stage overwrites its output, so it is safe to run twice.
- **Keep dependencies grouped.** Add new libraries to the matching section of
  `requirements.txt` with a comment saying what they are for.
- **Use the logger, not `print`,** in `src/` so pipeline runs leave a trace in `logs/`.

---

## G. Architecture Review

### Strengths
- Clear mapping to the grading components (DE, DS, BI, insights, scraping),
  which also makes the "diagram of how components interconnect" in the
  video easy to draw.
- Parallel work with few merge conflicts: each member owns a folder.
- Every stage can be re-run and tested on its own; schema checks catch breakage early.
- Lightweight enough to finish before the deadline, with no infrastructure to maintain.

### Weaknesses and trade-offs
| Issue | Impact | Mitigation |
|---|---|---|
| Processed data isn't versioned | Teammates may analyze different pipeline versions | Share Parquet via one Drive folder; note the commit hash in the folder name. Use DVC only if this becomes painful |
| YOLO over ~62k images is slow on laptops | Detection becomes the bottleneck | Run once on a GPU (Colab/lab machine). `detections.parquet` is the shared checkpoint |
| Full re-run on every pipeline execution | Wasted time when only new images arrive | Later: make detection incremental (skip paths already in `detections.parquet`) |
| Filename parsing is guessed (`<camera_id>/<timestamp>.jpg`) | Wrong `captured_at` breaks all temporal analysis | Confirm against the real dataset first; add a unit test with real filenames |
| CI skips the heavy stages | Detection code isn't exercised by CI | Acceptable for a course project; test detection manually on a small sample |
| Prefect adds a dependency | One more tool to learn | Stage functions don't depend on it; the flow could be replaced by a plain script if needed |

### Future scalability
- **New data source:** add `scrape/<source>.py` + `data/external/<source>.parquet`
  + a join in `analysis/build_features.py`. No other folder changes.
- **New model (e.g. congestion classifier, forecasting):** add
  `analysis/<model_name>.py`; store weights in `models/`.
- **Live / scheduled data:** Prefect can schedule `pipeline/flow.py`; make
  ingest and detection incremental first.
- **Larger data:** Parquet + DuckDB can query files much bigger than memory
  without changing the folder structure.
- **Deployment:** if the dashboard must be public, Streamlit Community Cloud
  reads `requirements.txt` directly. Add `deployment/` only for a Docker-based host.
