"""Load config/config.yaml and resolve paths against the project root.

RAW_IMAGES_DIR in .env overrides paths.raw_images (e.g. images on an external drive).
"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")


def load_config(path: Path = ROOT / "config" / "config.yaml") -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    cfg["paths"] = {k: ROOT / v for k, v in cfg["paths"].items()}
    if os.getenv("RAW_IMAGES_DIR"):
        cfg["paths"]["raw_images"] = Path(os.environ["RAW_IMAGES_DIR"])
    return cfg
