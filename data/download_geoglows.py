"""
Download GEOGloWS data and save as parquet files.

Usage:
    uv run python data/download_geoglows.py

Downloads daily retrospective simulation and return period thresholds
for all configured stations.
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = str(Path(__file__).resolve().parent.parent)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.constants import STATIONS
from src.datasources.geoglows_data import get_retrospective, get_return_periods

DATA_DIR = Path(__file__).resolve().parent


def main():
    for key, station in STATIONS.items():
        rid = station.geoglows_river_id
        print(f"\n=== {station.name} (river_id={rid}) ===")

        # Daily retrospective
        retro_path = DATA_DIR / f"geoglows_retro_daily_{rid}.parquet"
        if retro_path.exists():
            print(f"  Retrospective already exists: {retro_path.name}")
        else:
            print(f"  Downloading daily retrospective...")
            df = get_retrospective(rid)
            df.columns = [str(c) for c in df.columns]
            df.to_parquet(retro_path, engine="pyarrow")
            print(
                f"  Saved: {retro_path.name} "
                f"({len(df)} rows, "
                f"{df.index.min()} to {df.index.max()})"
            )

        # Return periods
        rp_path = DATA_DIR / f"geoglows_return_periods_{rid}.parquet"
        if rp_path.exists():
            print(f"  Return periods already exists: {rp_path.name}")
        else:
            print(f"  Downloading return periods...")
            df = get_return_periods(rid)
            df.columns = [str(c) for c in df.columns]
            df.to_parquet(rp_path, engine="pyarrow")
            print(f"  Saved: {rp_path.name}")
            print(df.to_string())

    print("\nDone.")


if __name__ == "__main__":
    main()
