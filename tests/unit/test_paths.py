from pathlib import Path

from bkk_cctv.config import ROOT, resolve, to_rel


def test_to_rel_inside_root_is_relative():
    p = ROOT / "data" / "raw" / "images" / "915" / "a.jpg"
    assert to_rel(p) == "data/raw/images/915/a.jpg"
    assert resolve(to_rel(p)) == p


def test_to_rel_outside_root_stays_absolute():
    p = Path("/Volumes/ext/915/a.jpg")
    assert to_rel(p) == str(p)
    assert resolve(to_rel(p)) == p
