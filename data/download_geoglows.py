"""
Download GEOGloWS data and upload to blob.

Usage:
    uv run python data/download_geoglows.py

Per station, downloads (if missing locally) the daily retrospective and
return-period parquets, then uploads any local geoglows_*.parquet to Azure
blob if not already present there. The corrected SFDC parquets, produced
out-of-band, are picked up by the same upload sweep.
"""

import sys
from pathlib import Path

import ocha_stratus as stratus
import pandas as pd

repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.constants import BLOB_PREFIX, BLOB_STAGE, STATIONS
from src.datasources.geoglows_data import get_retrospective, get_return_periods

DATA_DIR = Path(__file__).resolve().parent


def upload_if_missing(local_path, existing_blobs):
    blob_name = f"{BLOB_PREFIX}/{local_path.name}"
    if blob_name in existing_blobs:
        print(f"  Blob exists, skipping upload: {blob_name}")
        return
    df = pd.read_parquet(local_path)
    stratus.upload_parquet_to_blob(df, blob_name, stage=BLOB_STAGE)
    print(f"  Uploaded: {blob_name}")


def main():
    for key, station in STATIONS.items():
        rid = station.geoglows_river_id
        print(f"\n=== {station.name} (river_id={rid}) ===")

        retro_path = DATA_DIR / f"geoglows_retro_daily_{rid}.parquet"
        if retro_path.exists():
            print(f"  Retrospective already exists locally: {retro_path.name}")
        else:
            print(f"  Downloading daily retrospective...")
            df = get_retrospective(rid)
            df.columns = [str(c) for c in df.columns]
            df.to_parquet(retro_path, engine="pyarrow")
            print(
                f"  Saved: {retro_path.name} "
                f"({len(df)} rows, {df.index.min()} to {df.index.max()})"
            )

        rp_path = DATA_DIR / f"geoglows_return_periods_{rid}.parquet"
        if rp_path.exists():
            print(f"  Return periods already exists locally: {rp_path.name}")
        else:
            print(f"  Downloading return periods...")
            df = get_return_periods(rid)
            df.columns = [str(c) for c in df.columns]
            df.to_parquet(rp_path, engine="pyarrow")
            print(f"  Saved: {rp_path.name}")
            print(df.to_string())

    print("\n=== Uploading to blob ===")
    existing_blobs = set(
        stratus.list_container_blobs(
            name_starts_with=BLOB_PREFIX, stage=BLOB_STAGE
        )
    )
    for local_path in sorted(DATA_DIR.glob("geoglows_*.parquet")):
        upload_if_missing(local_path, existing_blobs)

    print("\nDone.")


if __name__ == "__main__":
    main()
