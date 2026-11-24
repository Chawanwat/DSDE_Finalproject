# Project — Bangkok CCTV: ฝนตกแล้วรถติดจริงไหม?

2110403 DSDE-CEDT (2026/1) · Final project 15% · **ส่ง อา. 6 ธ.ค. 2026** (MyCourseVille)
อัปเดตล่าสุด: 2026-11-24

## 1. โจทย์และหัวข้อ
- โจทย์: แปลงภาพ CCTV ของ กทม. (100 กล้อง) → structured data → วิเคราะห์ → BI dashboard → insights
- ต้องมีครบ 4 ส่วน: Data Engineering · Data Science · BI Dashboard · Insights
- Required task: scrape/API ≥ 3 แหล่ง (หรือ 1 แหล่งถ้าต้องใช้ Playwright/Selenium)
- **หัวข้อที่เลือก: "ฝนตกแล้วรถติดจริงไหม"**
  - วัดความหนาแน่นรถ (YOLO) ก่อน/ระหว่าง/หลังฝน และหาว่ากล้องไหน "อ่อนไหวต่อฝน" ที่สุด
  - จุดยากที่อาจารย์เตือน (ถนนเปียกสะท้อนแสง) → ใช้เป็น feature: train classifier เล็กๆ แยกถนนเปียก/แห้ง
  - Dashboard: timeline ฝนซ้อนความหนาแน่นรถ, rain sensitivity score รายกล้องบนแผนที่, กล้องใกล้จุดน้ำท่วมซ้ำซาก

## 2. ข้อเท็จจริงของ dataset (ตรวจจากไฟล์จริงแล้ว)
| | |
|---|---|
| จำนวนภาพ | 61,319 ภาพ, 100 กล้อง (ไม่ใช่ ~62k ตามที่ประมาณไว้) |
| ช่วงเวลา | 25–31 ส.ค. 2026 (7 วัน), ประมาณ 06:00–21:00 เท่านั้น — **ไม่มีภาพกลางคืน** |
| ความถี่ | ทุก ~10 นาทีต่อกล้อง (median 10.0 นาที, มีช่องว่างยาวสุด ~12 ชม.) |
| วันที่ภาพน้อยผิดปกติ | 27 ส.ค. (7,438 ภาพ เทียบกับ ~9,000 วันอื่น) |
| โครงสร้างไฟล์ | `cctv_images/<camera_id>/<camera_id>_<location>_<detail>_<YYYYMMDD>_<HHMMSS>.jpg` |
| เวลาในชื่อไฟล์ | เวลาท้องถิ่น Asia/Bangkok |
| ฝน (Open-Meteo) | ฝนตกทุกวัน, 27–31 ส.ค. ตกหนักกว่า 25–26 ส.ค. ชัดเจน → มี contrast พอให้วิเคราะห์ |
| วันหยุดในช่วงนี้ | ไม่มีวันหยุดราชการ (มีแค่ weekday vs weekend: 29–30 ส.ค. เป็นเสาร์–อาทิตย์) |

## 3. Pipeline / สถาปัตยกรรม
ดูรายละเอียดใน `docs/ARCHITECTURE.md` — แต่ละ stage อ่าน/เขียน Parquet ใน `data/`, ต่อกันด้วย Prefect

```
download → manifest → quality → YOLO detect → features ← scrape (weather, holidays, flood)
                                                  ↓
                                         dashboard (Streamlit)
```

| Stage | ไฟล์ | สถานะ |
|---|---|---|
| Download | `ingest/download_images.py` | ✅ ใช้ได้กับ Drive จริง (ดาวน์โหลด+แตกไฟล์สำเร็จ) |
| Manifest | `ingest/build_manifest.py` | ✅ แก้ parser ให้ตรงชื่อไฟล์จริง + tz Asia/Bangkok แล้ว |
| Quality | `clean/quality_checks.py` | ✅ รันกับภาพจริงครบ 61k แล้ว (39 วินาที, parallel): usable 60,168 · blurry 546 · frozen 624 · dark 0 |
| Detection | `detect/vehicle_detection.py` | ⚠️ ทดสอบกับภาพจริง 266 ภาพบน CPU แล้วใช้ได้ (~0.1 วิ/ภาพ) — ทั้งหมดควรรันบน Colab GPU |
| Features | `analysis/build_features.py` | ❌ ยังไม่ join กล้อง/ฝน/วันหยุด |
| Weather | `scrape/weather.py` | ❌ stub (ทดลองเขียนแล้วแต่ถอดออก — ดูข้อ 5) |
| Holidays | `scrape/holidays.py` | ❌ stub (ทดลองเขียนแล้วแต่ถอดออก — ดูข้อ 5) |
| Source 3 | `scrape/source3.py` | ❌ แผน: Traffy Fondue (ดูข้อ 5) |
| Dashboard | `dashboard/app.py` | ❌ มีแค่ metric + กราฟรายชั่วโมง |
| Kafka | `stream/kafka_io.py` | ✅ smoke test ผ่านใน Docker · ⚪ ยังไม่ได้ตัดสินใจว่าจะใช้ทำอะไร |

## 4. ผลการ check code และการแก้ bug (2026-11-24)
**ตรวจแล้ว:** `pytest` 11 passed (ทั้งบน host และใน Docker) · `ruff check` clean · `docker compose build` สำเร็จ (arm64) · Kafka smoke test ผ่าน

| # | Bug | สถานะ |
|---|---|---|
| 1 | parser อ่านชื่อไฟล์จริงไม่ได้ → `captured_at` เป็น NaT ทั้งหมด และไม่มี timezone | ✅ แก้แล้ว: อ่านเวลาจาก `_YYYYMMDD_HHMMSS` ตัวท้าย เป็น Asia/Bangkok, ตัดแถวที่ parse ไม่ได้พร้อม warning + unit test |
| 2 | **frozen-frame check ผิด**: กล้องตั้งนิ่ง เฟรมจริงห่างกัน 10 นาทีมี pHash distance 0–2 บ่อยมาก → ถ้าใช้ distance ≤ 2 จะทิ้งเฟรมดีไป ~10% (ส่วนใหญ่เป็นเฟรมรถน้อย ทำให้ค่าเฉลี่ยรถสูงเกินจริง) | ✅ แก้แล้ว: เทียบ mean pixel diff ของ thumbnail 16×16 กับเฟรมก่อนหน้า (`dup_max_pixel_diff: 1.0`) → flag 624 เฟรม (1%) กระจุกในบางกล้อง เช่น 150, 938, 939 |
| 3 | quality checks รันทีละภาพ (ช้า) และ import OpenCV ตอนโหลด module (CI import ไม่ได้) | ✅ แก้แล้ว: ProcessPoolExecutor (`clean.workers`), import หนักย้ายเข้าในฟังก์ชัน |
| 4 | `schemas.CAMERAS` ไม่ตรงกับ `cctv_info.csv` และเอกสารอ้าง `cameras.csv` ที่ไม่มีอยู่ | ✅ แก้แล้ว (schemas, data_dictionary, ARCHITECTURE, reference README) |
| 5 | `download_images` ลบ zip ที่ผู้ใช้ดาวน์โหลดเอง (workaround gdown quota) | ✅ แก้แล้ว: ลบเฉพาะ zip ที่ดาวน์โหลดในรอบนั้น |
| 6 | `st.plotly_chart(width="stretch")` แต่ requirements ระบุ Streamlit `>=1.35` | ✅ แก้แล้ว: `streamlit>=1.50` |
| 7 | `container_name` ตายตัวใน docker-compose → รันสองโฟลเดอร์ (main + worktree) พร้อมกันไม่ได้ | ✅ แก้แล้ว: ลบ `container_name` ออก (port 9092/8501/8888/8080 ยังชนกันถ้ารันพร้อมกัน) |
| 8 | โค้ดใน handoff (`to_rel`, `.extract_complete` ฯลฯ) ยังไม่ได้ commit ใน main | ✅ commit ใน main แล้ว (`b38ea19`; bug fixes #1–#7 อยู่ใน `afddd0b`) |

ข้อสังเกตที่ยังไม่ได้แก้ (ไม่ใช่ bug ของโค้ด):
- มี JPEG 2 ไฟล์ที่ถูกตัดท้าย ("Premature end of JPEG file") — ยังอ่านได้แต่ภาพส่วนล่างอาจเป็นสีเทา
- ไม่มีภาพมืดเลย (ข้อมูลมีแค่ 06–21 น.) → threshold `min_brightness` ยังไม่ได้ทดสอบจริง
- `pipeline/flow.py` ยังไม่เรียก scrapers (จะทำตอนเพิ่ม feature)

## 5. แหล่งข้อมูลภายนอก (Required task)
| # | แหล่ง | วิธี | Output |
|---|---|---|---|
| 1 | Open-Meteo Historical | `archive-api.open-meteo.com/v1/archive` (ไม่ต้องใช้ key) — ทดสอบแล้วใช้ได้, ส่ง lat/lon หลายจุดในครั้งเดียวได้ | (ยังไม่ทำ) ฝน/อุณหภูมิ/เมฆ รายชั่วโมงต่อกล้อง |
| 2 | Google Calendar "Holidays in Thailand" | iCal feed (Nager.Date ไม่มีข้อมูลไทย: HTTP 204) | (ยังไม่ทำ) |
| 3 | Traffy Fondue | `publicapi.traffy.in.th/share/teamchadchart/search?start=&end=&limit=&offset=` | (ยังไม่ทำ) เรื่องร้องเรียนน้ำท่วม |

หมายเหตุ Traffy: filter ตามวันที่ใช้ได้ (25–31 ส.ค. มี 7,329 เรื่อง) แต่ filter ตามประเภทใช้ไม่ได้ และ field `type` / `problem_type_abdul` ว่าง → ต้องดึงทั้งช่วงแล้วกรองเองจาก `description` (มีคำว่า "น้ำท่วม" ~2.5%) จากนั้นหาเรื่องน้ำท่วมที่อยู่ในรัศมีใกล้กล้อง

## 6. แผนการวิเคราะห์ (Data Science)
1. Join: detections + กล้อง (lat/lon) + ฝนรายชั่วโมง (floor `captured_at` เป็นชั่วโมง) + weekday/weekend
2. Features ฝน: `rain_mm` ชั่วโมงนั้น, ฝนสะสม 1/3 ชม.ก่อนหน้า, `is_raining`, ช่วง before/during/after
3. Baseline ต่อกล้อง × ชั่วโมง × weekday เพื่อตัดผลของ rush hour ออก → วัด % เปลี่ยนแปลงเมื่อฝนตก
4. **Rain sensitivity score** รายกล้อง = ผลต่างความหนาแน่นรถ (ฝน − ไม่ฝน) เทียบ baseline, ทดสอบ significance
5. (Optional) Wet-road classifier จากภาพ — ใช้ label จากฝนจริงเป็น weak label
6. เชื่อมกับจุดน้ำท่วมจาก Traffy: กล้องใกล้จุดน้ำท่วมอ่อนไหวกว่าไหม

## 7. TODO (เรียงตามความสำคัญ)
- [x] Commit โค้ดที่ค้างอยู่ + bug fixes (`b38ea19`, `afddd0b`)
- [ ] `weather.py`, `holidays.py` (มีร่างโค้ดแล้ว ถอดออกไว้ก่อน)
- [ ] รัน YOLO บน Colab GPU → แชร์ `detections.parquet` ใน Drive ทีม
- [ ] `build_features.py`: join กล้อง + weather + holidays, แก้ `schemas.py` + `data_dictionary.md` พร้อมกัน
- [ ] `source3.py`: Traffy Fondue flood reports
- [ ] Notebook วิเคราะห์ rain sensitivity
- [ ] Dashboard: แผนที่กล้อง, heatmap weekday × hour, timeline ฝน vs รถ, sensitivity map
- [ ] ตัดสินใจเรื่อง Kafka (replay stream หรือเก็บไว้เป็น infra)
- [ ] Deliverables: architecture diagram, slides PDF, วิดีโอ 15 นาที (YouTube unlisted), Drive folder (anyone-with-link), โพสต์ Discord `#project-showroom`

## 8. คำสั่งที่ใช้บ่อย
```bash
cp .env.example .env
docker compose build && docker compose up -d          # Kafka, Kafka UI :8080, dashboard :8501, Jupyter :8888
docker compose --profile data up dataset              # ดาวน์โหลด + แตก dataset
docker compose run --rm app pytest
python -m bkk_cctv.ingest.build_manifest
python -m bkk_cctv.clean.quality_checks               # ~40 วินาทีสำหรับ 61k ภาพ
docker compose --profile pipeline up pipeline
```
