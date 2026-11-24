Static lookup tables that rarely change and are small enough to commit.

- `cameras.csv` — one row per CCTV camera: `camera_id,name,lat,lon`
  (source: BMA traffic platform; used for maps and spatial joins).

- `cctv_info.csv`: downloaded together with the images by
  `python -m bkk_cctv.ingest.download_images`. One row per camera, with columns
  `camera_id, location, location_detail, location_en, location_detail_en,
  latitude, longitude, ip_address, image_count`.
