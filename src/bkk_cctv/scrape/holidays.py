"""Scraper for: holidays — see src/bkk_cctv/scrape/README.md."""
import pandas as pd

from bkk_cctv.config import load_config


def fetch() -> pd.DataFrame:
    # TODO: implement scraping / API call
    raise NotImplementedError


def save(df: pd.DataFrame) -> None:
    cfg = load_config()
    df.to_parquet(cfg["paths"]["external"] / "holidays.parquet", index=False)


if __name__ == "__main__":
    save(fetch())
