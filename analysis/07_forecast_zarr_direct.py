"""Fast fetch: zarr-direct (no xarray), all 15 lead days.

Benchmark of single fetch:
  s3fs + xr.open_zarr + .values  →  26.4s/fetch sequential
  s3fs + zarr.open + numpy slice →   6.7s/fetch sequential   ← this script

Most of xarray's overhead is in `xr.open_zarr` itself (~18s of metadata
processing), which we don't need — we only need numpy access to one variable.

Outputs to data/forecast_lead_times_v2.parquet (separate from the working
slow pipeline's output, so we can compare).

Run from repo root:
    uv run python analysis/07_forecast_zarr_direct.py --workers 8
"""
from __future__ import annotations

import argparse
import logging
import sys
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import ocha_stratus as stratus
import pandas as pd
import zarr

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from src.constants import BLOB_PREFIX, BLOB_STAGE, STATIONS  # noqa: E402

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Limit zarr's internal threading so it doesn't fight our worker pool
zarr.config.set({"async.concurrency": 4, "threading.max_workers": 4})

DATA_DIR = REPO / "data"
OUTPUT_PATH = DATA_DIR / "forecast_lead_times_v2.parquet"

_S3 = None


def get_s3():
    global _S3
    if _S3 is None:
        import s3fs
        _S3 = s3fs.S3FileSystem(anon=True)
    return _S3


def resolve_rivid_indices(river_ids: list[int], probe_date: str) -> list[int]:
    """One-time pull of the rivid coordinate to find integer positions."""
    import s3fs
    log.info("Resolving rivid integer positions from %s.zarr ...", probe_date)
    s3 = get_s3()
    store = s3fs.S3Map(f"geoglows-v2-forecasts/{probe_date}.zarr", s3=s3)
    grp = zarr.open_group(store=store, mode="r", zarr_format=2)
    rivid_arr = grp["rivid"][:]
    pos_map = {int(r): int(np.where(rivid_arr == r)[0][0]) for r in river_ids}
    log.info("rivid positions: %s", pos_map)
    return [pos_map[r] for r in river_ids]


def fetch_one(date: str, river_ids: list[int], rivid_positions: list[int],
              max_retries: int = 2) -> list[dict]:
    """Open the date's Zarr via zarr.open and pull the relevant slice with
    numpy indexing. Compute daily ensemble stats. Return one row per
    (river, lead_day)."""
    import time
    import s3fs

    last_err = None
    for attempt in range(max_retries):
        try:
            s3 = get_s3()
            store = s3fs.S3Map(f"geoglows-v2-forecasts/{date}.zarr", s3=s3)
            grp = zarr.open_group(store=store, mode="r", zarr_format=2)
            # Shape: (ensemble=52, time=280, rivid=2 after slicing)
            arr = grp["Qout"][:, :, rivid_positions]
            # `time` is stored as int32 seconds-since-issue (no CF decoding).
            time_arr = grp["time"][:]
            lead_day = (time_arr // 86400).astype(int)

            # daily aggregates per ensemble member per river. Many cells in
            # the (ensemble, time) plane are NaN because the 51 perturbed
            # members are 3-hourly while the high-res control is hourly
            # — use nan-aware reductions throughout.
            unique_days = np.unique(lead_day)
            ts = pd.to_datetime(date, format="%Y%m%d%H")
            rows = []
            for ld in unique_days:
                mask = lead_day == ld
                # Daily mean per ensemble member (skip NaN time steps)
                day_arr = np.nanmean(arr[:, mask, :], axis=1)  # (ensemble, rivid)
                avg = np.nanmean(day_arr, axis=0)
                med = np.nanmedian(day_arr, axis=0)
                mx = np.nanmax(day_arr, axis=0)
                p25 = np.nanquantile(day_arr, 0.25, axis=0)
                p75 = np.nanquantile(day_arr, 0.75, axis=0)
                for r_i, rid in enumerate(river_ids):
                    rows.append({
                        "river_id": int(rid),
                        "forecast_date": ts,
                        "lead_day": int(ld),
                        "fc_avg": float(avg[r_i]),
                        "fc_med": float(med[r_i]),
                        "fc_max": float(mx[r_i]),
                        "fc_25p": float(p25[r_i]),
                        "fc_75p": float(p75[r_i]),
                    })
            return rows
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    log.warning("zarr open gave up date=%s: %s", date, last_err)
    return []


def sample_dates(all_dates: list[str], n: int) -> list[str]:
    if n >= len(all_dates):
        return list(all_dates)
    step = len(all_dates) / n
    return [all_dates[int(i * step)] for i in range(n)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-dates", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--river-ids", nargs="+", type=int,
                        default=[s.geoglows_river_id for s in STATIONS.values()])
    parser.add_argument("--start-date", default="2024-07-01")
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--checkpoint-every", type=int, default=50)
    args = parser.parse_args()

    if OUTPUT_PATH.exists():
        log.info("Output exists locally, skipping zarr fetch: %s", OUTPUT_PATH)
        df = pd.read_parquet(OUTPUT_PATH)
    else:
        end = pd.Timestamp(args.end_date) if args.end_date else (
            pd.Timestamp.today().normalize() - pd.Timedelta(days=1)
        )
        all_dates = [d.strftime("%Y%m%d00")
                     for d in pd.date_range(args.start_date, end, freq="D")]
        log.info("Generated %d forecast dates from %s to %s",
                 len(all_dates), all_dates[0], all_dates[-1])
        sampled = all_dates if args.n_dates is None else sample_dates(all_dates, args.n_dates)
        log.info("Using %d dates", len(sampled))

        rivid_positions = resolve_rivid_indices(args.river_ids, sampled[0])
        log.info("Submitting %d Zarr fetches with %d workers", len(sampled), args.workers)

        results = []
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(fetch_one, d, args.river_ids, rivid_positions): d
                       for d in sampled}
            for i, fut in enumerate(as_completed(futures), 1):
                d = futures[fut]
                rows = fut.result()
                results.extend(rows)
                log.info("  [%d/%d] date=%s %s", i, len(sampled), d,
                         f"ok ({len(rows)} rows)" if rows else "FAIL")
                if args.checkpoint_every and i % args.checkpoint_every == 0:
                    pd.DataFrame(results).to_parquet(OUTPUT_PATH, index=False)
                    log.info("    checkpoint: %d rows -> %s", len(results), OUTPUT_PATH.name)

        df = pd.DataFrame(results)
        if df.empty:
            log.error("No results retrieved")
            sys.exit(1)
        df = df.sort_values(["river_id", "forecast_date", "lead_day"]).reset_index(drop=True)
        df.to_parquet(OUTPUT_PATH, index=False)
        log.info("Wrote %d rows to %s", len(df), OUTPUT_PATH)

    blob_name = f"{BLOB_PREFIX}/{OUTPUT_PATH.name}"
    existing = stratus.list_container_blobs(
        name_starts_with=blob_name, stage=BLOB_STAGE
    )
    if blob_name in existing:
        log.info("Blob exists, skipping upload: %s", blob_name)
    else:
        stratus.upload_parquet_to_blob(df, blob_name, stage=BLOB_STAGE)
        log.info("Uploaded to blob: %s", blob_name)


if __name__ == "__main__":
    main()
