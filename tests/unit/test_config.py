from bkk_cctv.config import ROOT, load_config


def test_paths_resolve_under_root():
    cfg = load_config()
    for p in cfg["paths"].values():
        assert ROOT in p.parents
