# Setup Guide — Bangkok CCTV Image Analysis

คู่มือติดตั้งสำหรับสมาชิกในทีม ทำตามลำดับจากบนลงล่าง
ภาพรวมโปรเจกต์และสถานะงานดูที่ [project.md](project.md) · สถาปัตยกรรมดูที่ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

มี 2 ทาง:
- **ทาง A: Docker (แนะนำ)** ได้ทุกอย่างครบ รวม Kafka ไม่ต้องลง Python เอง
- **ทาง B: Python บนเครื่อง** เบากว่า เหมาะกับคนที่แก้แค่ scraper/วิเคราะห์ข้อมูล

---

## 0. สิ่งที่ต้องมี

| | ทาง A (Docker) | ทาง B (Python) |
|---|---|---|
| Git | ✅ | ✅ |
| Docker Desktop (เปิดไว้ก่อนรันคำสั่ง) | ✅ | — |
| Python 3.11 หรือ 3.12 (**ไม่ใช่ 3.13+** เพราะ torch/ultralytics ยังไม่รองรับทุกตัว) | — | ✅ |
| พื้นที่ว่าง | ~10 GB (image 6 GB + dataset 3 GB) | ~5 GB |

ทดสอบแล้วบน Mac Apple Silicon (arm64) ส่วน Windows/Linux ใช้ Docker ได้เหมือนกัน

## 1. Clone โปรเจกต์

```bash
git clone https://github.com/Chawanwat/DSDE_Finalproject.git
cd DSDE_Finalproject
cp .env.example .env
```

`.env` ห้าม commit (อยู่ใน `.gitignore` แล้ว)

---

## ทาง A: Docker

### A1. Build image (ครั้งแรก ~10 นาที)

```bash
docker compose build
```

ต้อง build ใหม่**เฉพาะตอนที่ `requirements.txt` หรือ `Dockerfile` เปลี่ยน** ส่วนการแก้โค้ดไม่ต้อง build ใหม่ เพราะโฟลเดอร์โปรเจกต์ถูก mount เข้าไปที่ `/app`

### A2. เปิด services

```bash
docker compose up -d
```

| Service | ที่อยู่ |
|---|---|
| Dashboard (Streamlit) | http://localhost:8501 |
| JupyterLab | http://localhost:8888 (ไม่มี token) |
| Kafka UI | http://localhost:8080 |
| Kafka broker | `kafka:29092` (ใน container) · `localhost:9092` (จากเครื่อง) |

### A3. ดาวน์โหลด dataset (ครั้งเดียว)

```bash
docker compose --profile data up dataset
```

- ดาวน์โหลด `cctv_images.zip` (~1.6 GB) จาก Google Drive แล้วแตกไฟล์ไปที่ `data/raw/images/` และวาง `cctv_info.csv` ไว้ที่ `data/reference/`
- รันซ้ำได้ ถ้าแตกไฟล์เสร็จแล้ว (มีไฟล์ `data/raw/images/.extract_complete`) จะข้ามไปเลย
- ถ้าเจอ **gdown quota error** ให้ดาวน์โหลดเองจาก [Drive folder](https://drive.google.com/drive/folders/1k2-KxXe4wbDmFGcGXI-pK7TdSXjBHTni) แล้ววางไว้ที่ `data/raw/cctv_images.zip` จากนั้นรันคำสั่งเดิมอีกครั้ง มันจะแตกไฟล์ให้โดยไม่ดาวน์โหลดใหม่ และไม่ลบ zip ของเรา

ผลที่ควรได้: **61,319 ภาพ, 100 กล้อง** (25–31 ส.ค. 2026, ช่วง 06:00–21:00)

### A4. ตรวจว่าทุกอย่างใช้ได้

```bash
docker compose run --rm app pytest
```

```bash
docker compose run --rm app python -m bkk_cctv.stream.kafka_io
```

ต้องได้ `11 passed` และ `Kafka OK at kafka:29092`

### A5. รัน pipeline

ทีละ stage (แนะนำ เพราะ debug ง่ายกว่า):

```bash
docker compose run --rm app python -m bkk_cctv.ingest.build_manifest
```

```bash
docker compose run --rm app python -m bkk_cctv.clean.quality_checks
```

```bash
docker compose run --rm app python -m bkk_cctv.detect.vehicle_detection
```

```bash
docker compose run --rm app python -m bkk_cctv.analysis.build_features
```

หรือรันทั้งหมดในครั้งเดียวด้วย Prefect:

```bash
docker compose --profile pipeline up pipeline
```

| Stage | เวลาโดยประมาณ (Mac M-series, CPU) | Output |
|---|---|---|
| build_manifest | ~5 วินาที | `data/interim/manifest.parquet` |
| quality_checks | ~40 วินาที (รันขนาน) | `data/interim/quality.parquet` |
| vehicle_detection | **~0.1 วินาที/ภาพ → ~1.5–2 ชม. สำหรับทั้งหมด** | `data/processed/detections.parquet` |
| build_features | ไม่กี่วินาที | `data/processed/traffic_features.parquet` |

ถ้าไม่อยากรอ detection บน CPU ให้ดู [ข้อ C (Colab GPU)](#c-รัน-yolo-บน-colab-gpu-ไม่บังคับ)

### A6. คำสั่งอื่นที่ใช้บ่อย

```bash
docker compose run --rm app bash
```

```bash
docker compose logs -f dashboard
```

```bash
docker compose down
```

`docker compose down -v` จะลบข้อมูล Kafka ด้วย

---

## ทาง B: Python บนเครื่อง

```bash
python3.12 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
playwright install chromium
```

`requirements.txt` ติดตั้ง package `bkk_cctv` แบบ editable ให้ด้วย (`-e .`) จึง import ได้จากทุกที่

ใน `.env` ให้ตั้ง `KAFKA_BOOTSTRAP_SERVERS=localhost:9092` และถ้าต้องใช้ Kafka ให้เปิดแค่ broker ด้วย `docker compose up -d kafka`

ดาวน์โหลด dataset, ทดสอบ และรัน:

```bash
python -m bkk_cctv.ingest.download_images
```

```bash
pytest && ruff check src tests dashboard
```

```bash
python -m bkk_cctv.pipeline.flow
```

```bash
streamlit run dashboard/app.py
```

**ติดตั้งแบบเบา** (ไม่มี torch/OpenCV สำหรับคนที่แก้แค่ scraper/test เหมือนที่ CI ใช้):

```bash
pip install pandas pyarrow pyyaml python-dotenv requests pytest ruff && pip install -e . --no-deps
```

---

## C. รัน YOLO บน Colab GPU (ไม่บังคับ)

Docker บน Mac ใช้ GPU ไม่ได้ ถ้าจะรัน detection ทั้ง 61k ภาพให้เร็วขึ้น:

1. รัน `build_manifest` และ `quality_checks` บนเครื่องตัวเองให้ได้ `data/interim/quality.parquet`
2. ใน Colab (Runtime → GPU):
   ```bash
   git clone https://github.com/Chawanwat/DSDE_Finalproject.git && cd DSDE_Finalproject
   pip install ultralytics pandas pyarrow pyyaml python-dotenv gdown && pip install -e . --no-deps
   python -m bkk_cctv.ingest.download_images
   ```
3. อัปโหลด `quality.parquet` ไปไว้ที่ `data/interim/` แล้วรัน `python -m bkk_cctv.detect.vehicle_detection`
4. เอา `data/processed/detections.parquet` ไปแชร์ใน Drive ของทีม แล้วแต่ละคนวางไว้ที่ `data/processed/`

path ในตารางทุกตารางเป็นแบบ relative กับ root ของโปรเจกต์ จึงย้ายไฟล์ไปมาระหว่าง Colab, Docker และเครื่องเราได้เลย

---

## D. ปัญหาที่เจอบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `Cannot connect to the Docker daemon` | ยังไม่ได้เปิด Docker Desktop |
| `port is already allocated` (9092/8080/8501/8888) | มี service อื่นหรือโปรเจกต์อีกชุดใช้ port อยู่ ให้ `docker compose down` ในอีกโฟลเดอร์ หรือปิดโปรแกรมที่ใช้ port นั้น |
| Kafka smoke test ค้างหรือ `No message received` | Kafka ยังไม่ healthy ให้รอ ~20 วินาทีหลัง `up -d` แล้วดูด้วย `docker compose ps` · ถ้ารันจากเครื่อง (ไม่ใช่ใน container) ต้องใช้ `localhost:9092` |
| gdown: `Too many users have viewed or downloaded this file` | ดาวน์โหลด zip เอง (ดู A3) |
| `ModuleNotFoundError: bkk_cctv` | ยังไม่ได้ `pip install -e .` หรือยังไม่ได้ activate `.venv` |
| pip ลง torch/ultralytics ไม่ได้ | ใช้ Python 3.13+ อยู่ ให้เปลี่ยนเป็น 3.12 |
| `Premature end of JPEG file` ตอน quality check | ปกติ มีภาพเสีย 2 ไฟล์ใน dataset ยังอ่านได้และไม่ทำให้ pipeline หยุด |
| แก้ `requirements.txt` แล้ว container ไม่เห็น package ใหม่ | `docker compose build` ใหม่ |

## E. ก่อน push

```bash
ruff check src tests dashboard && pytest
```

- ห้าม commit: `.env`, `data/` (ยกเว้น `data/reference/`), `models/`, `.venv/` ซึ่งอยู่ใน `.gitignore` แล้ว
- ถ้าเปลี่ยนคอลัมน์ของตารางไหน ให้แก้ `src/bkk_cctv/schemas.py` และ `docs/data_dictionary.md` ใน commit เดียวกัน
- กติกาของโค้ด: stage ห้าม import กันเอง, ห้าม hard-code path (ใช้ `load_config()`), ใช้ logger แทน `print`, ห้ามแก้ไฟล์ใน `data/raw/`
