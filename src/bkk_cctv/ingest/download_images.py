"""Download the raw CCTV images from the shared Google Drive folder."""
import gdown

from bkk_cctv.config import load_config


def download_images() -> None:
    cfg = load_config()
    out = cfg["paths"]["raw_images"]
    out.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(cfg["drive"]["folder_url"], output=str(out), quiet=False)


if __name__ == "__main__":
    download_images()
