import math

import pandas as pd

from bkk_cctv.clean.quality_checks import flag_duplicates, thumb_diff


def _thumb(*values):
    return bytes(values).hex()


def test_thumb_diff_is_mean_abs_grey_difference():
    assert thumb_diff(_thumb(10, 10), _thumb(10, 10)) == 0
    assert thumb_diff(_thumb(10, 20), _thumb(12, 16)) == 3  # (2 + 4) / 2


def test_thumb_diff_missing_is_nan():
    assert math.isnan(thumb_diff(None, _thumb(1)))
    assert math.isnan(thumb_diff(_thumb(1), _thumb(1, 2)))


def test_flag_duplicates_within_camera_only():
    df = pd.DataFrame({
        "camera_id": ["1", "1", "1", "2"],
        # 2nd is a frozen copy of the 1st (tiny diff), 3rd is a new scene,
        # 4th equals the 3rd but belongs to another camera
        "thumb": [_thumb(100, 100), _thumb(100, 101), _thumb(50, 60), _thumb(50, 60)],
    })
    assert flag_duplicates(df, max_diff=1.0).tolist() == [False, True, False, False]
