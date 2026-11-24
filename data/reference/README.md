Static lookup tables that rarely change and are small enough to commit.

- `cctv_info.csv`: downloaded together with the images by
  `python -m bkk_cctv.ingest.download_images`. One row per camera, with columns
  `camera_id, location, location_detail, location_en, location_detail_en,
  latitude, longitude, ip_address, image_count`.
  `camera_id` is an int here; cast it to str before joining with other tables.
