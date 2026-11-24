"""Download the Bangkok CCTV dataset from the shared Google Drive folder.

The Drive folder holds two files:
  - cctv_images.zip (~1.6 GB) -> extracted into paths.raw_images
  - cctv_info.csv  (camera_id, location, lat/lon, image_count, ...) -> data/reference/

Safe to re-run: skips files that are already downloaded / extracted.

Run:  python -m bkk_cctv.ingest.download_images [--force] [--keep-zip]
"""
import argparse
import shutil
import zipfile
from pathlib import Path

import gdown

from bkk_cctv.config import load_config
from bkk_cctv.log import get_logger

log = get_logger("pipeline")

IMAGE_EXTS = {".jpg", ".jpeg", ".png"}


DONE_MARKER = ".extract_complete"  # written only after a full, successful extraction


def _has_images(folder: Path) -> bool:
    return folder.exists() and any(
        p.suffix.lower() in IMAGE_EXTS for p in folder.rglob("*") if p.is_file()
    )


def _download(file_id: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    log.info(f"Downloading {dest.name} from Google Drive ...")
    # resume=True continues a partially downloaded file instead of restarting
    gdown.download(id=file_id, output=str(dest), quiet=False, resume=True)
    if not dest.exists() or dest.stat().st_size == 0:
        raise RuntimeError(f"Download failed for {dest.name} (Drive quota or permissions?)")
    return dest


def _extract(zip_path: Path, out_dir: Path) -> None:
    log.info(f"Extracting {zip_path.name} -> {out_dir} ...")
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        # skip macOS metadata that some zips carry
        members = [m for m in zf.namelist() if not m.startswith("__MACOSX/")]
        zf.extractall(out_dir, members=members)


def download_images(force: bool = False, keep_zip: bool = False) -> None:
    cfg = load_config()
    drive = cfg["drive"]
    raw_images = cfg["paths"]["raw_images"]
    reference = cfg["paths"]["reference"]

    # 1) Camera metadata (small, always cheap to refresh)
    info_csv = reference / "cctv_info.csv"
    if force or not info_csv.exists():
        _download(drive["info_file_id"], info_csv)
    else:
        log.info(f"{info_csv} already exists, skipping")

    # 2) Images
    zip_path = raw_images.parent / "cctv_images.zip"
    if not force:
        if (raw_images / DONE_MARKER).exists():
            log.info(f"Images already present in {raw_images}, skipping (use --force to redo)")
            return
        if _has_images(raw_images) and not zip_path.exists():
            # Images were copied in by hand: never delete them, just mark as done
            log.info(f"Found images in {raw_images} (added manually), marking as complete")
            (raw_images / DONE_MARKER).touch()
            return
    elif raw_images.exists():
        shutil.rmtree(raw_images)

    if force or not zip_path.exists() or not zipfile.is_zipfile(zip_path):
        _download(drive["images_zip_id"], zip_path)
    _extract(zip_path, raw_images)
    (raw_images / DONE_MARKER).touch()

    n = sum(1 for p in raw_images.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
    log.info(f"{n:,} images ready in {raw_images}")
    if not keep_zip:
        zip_path.unlink()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--force", action="store_true", help="re-download and re-extract")
    ap.add_argument("--keep-zip", action="store_true", help="keep cctv_images.zip after extracting")
    args = ap.parse_args()
    download_images(force=args.force, keep_zip=args.keep_zip)
