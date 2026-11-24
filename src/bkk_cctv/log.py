"""Shared logger: prints to console and appends to logs/<name>.log."""
import logging

from bkk_cctv.config import ROOT


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    for handler in (logging.StreamHandler(), logging.FileHandler(log_dir / f"{name}.log")):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger
