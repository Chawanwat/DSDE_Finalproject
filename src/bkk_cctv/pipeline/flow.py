"""End-to-end pipeline orchestrated with Prefect.

Run:  python -m bkk_cctv.pipeline.flow
"""
from prefect import flow, task

from bkk_cctv.analysis.build_features import build_features
from bkk_cctv.clean.quality_checks import run_quality_checks
from bkk_cctv.detect.vehicle_detection import run_detection
from bkk_cctv.ingest.build_manifest import build_manifest
from bkk_cctv.ingest.download_images import download_images


@task
def ingest(skip_download: bool):
    if not skip_download:
        download_images()
    build_manifest()


@task
def clean():
    run_quality_checks()


@task
def detect():
    run_detection()


@task
def features():
    build_features()


@flow(name="bangkok-cctv-pipeline")
def pipeline(skip_download: bool = True):
    ingest(skip_download)
    clean()
    detect()
    features()


if __name__ == "__main__":
    pipeline()
