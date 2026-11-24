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
    # Stage outputs must exist even on a fresh clone / container without .gitkeep files
    for key in ("interim", "processed", "external", "reference", "models"):
        cfg["paths"][key].mkdir(parents=True, exist_ok=True)
    return cfg


def to_rel(path: Path) -> str:
    """Store paths relative to the project root, so tables written inside Docker
    (/app/...) still work on the host (/Users/...) and vice versa."""
    path = Path(path)
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:  # e.g. RAW_IMAGES_DIR on an external drive
        return str(path)


def resolve(path: str) -> Path:
    """Inverse of to_rel: relative -> absolute under ROOT; absolute stays as is."""
    return ROOT / path
