import pandas as pd
import pytest

from bkk_cctv.schemas import MANIFEST, check_columns


def test_check_columns_passes():
    check_columns(pd.DataFrame(columns=MANIFEST), MANIFEST, "manifest")


def test_check_columns_reports_missing():
    with pytest.raises(ValueError, match="path"):
        check_columns(pd.DataFrame(columns=["camera_id", "captured_at"]), MANIFEST, "manifest")
