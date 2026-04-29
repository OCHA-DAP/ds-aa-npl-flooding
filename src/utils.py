from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd


def to_naive(idx):
    """Strip tz from a DatetimeIndex if present."""
    return idx.tz_localize(None) if idx.tz is not None else idx


def load_geoglows_retro(river_id, data_dir):
    """Load GEOGloWS retrospective parquet, normalize column and index."""
    df = pd.read_parquet(
        Path(data_dir) / f"geoglows_retro_daily_{river_id}.parquet"
    )
    df.columns = ["discharge"]
    df.index = to_naive(df.index)
    return df


def load_geoglows_retro_corrected(river_id, data_dir):
    """Load SFDC-corrected GEOGloWS retrospective parquet."""
    df = pd.read_parquet(
        Path(data_dir) / f"geoglows_retro_daily_corrected_{river_id}.parquet"
    )
    df.columns = ["discharge"]
    df.index = to_naive(df.index)
    return df


def collapse_to_events(dates, gap_days=7):
    """Collapse consecutive/nearby dates into distinct events."""
    if len(dates) == 0:
        return pd.DatetimeIndex([])
    dates = dates.sort_values()
    events = [dates[0]]
    for d in dates[1:]:
        if (d - events[-1]).days > gap_days:
            events.append(d)
    return pd.DatetimeIndex(events)


def compute_exceedance_probability(ds, threshold, station, max_days):
    """
    Compute the percent of ensemble members exceeding a threshold within `max_days` leadtime.

    Parameters:
        ds (xarray.Dataset): Input dataset with dimensions (number, time, leadtime)
        threshold (float): Threshold to check exceedance (e.g., 1000)
        station (str): Name of the station variable (e.g., 'Chisapani')
        max_days (int): Maximum forecast leadtime in days

    Returns:
        xarray.DataArray: Percentage of ensemble members exceeding threshold at each time
    """
    leadtime_days = ds["step"].dt.days
    ds_subset = ds.sel(leadtime=leadtime_days <= max_days)
    station_vals = ds_subset[station]
    exceeds = station_vals > threshold
    percent_exceeding = (
        exceeds.any(dim="leadtime").sum(dim="number") / ds.dims["number"] * 100
    )
    return percent_exceeding


def compute_return_levels(data, return_periods):
    """
    Compute return levels from annual maxima using empirical quantiles.

    Parameters:
        data: xarray.DataArray with 'time' coordinate, or pd.Series
              with datetime index
        return_periods: list of return periods in years

    Returns:
        dict of {return_period: return_level}
    """
    if hasattr(data, "dims"):
        # xarray DataArray
        annual_maxima = data.groupby("time.year").max(dim="time").values
    else:
        # pandas Series/DataFrame
        annual_maxima = data.groupby(data.index.year).max().values

    annual_maxima = np.sort(annual_maxima[~np.isnan(annual_maxima)])
    n = len(annual_maxima)

    return_levels = {}
    for rp in return_periods:
        rank = (1 - 1 / rp) * (n + 1)
        idx = int(np.floor(rank)) - 1
        if 0 <= idx < n - 1:
            frac = rank - (idx + 1)
            val = annual_maxima[idx] + frac * (
                annual_maxima[idx + 1] - annual_maxima[idx]
            )
        else:
            val = annual_maxima[min(max(idx, 0), n - 1)]
        return_levels[rp] = val
    return return_levels


def match_events(source_events, reference_events, window_days=7):
    """
    Match events between two sets of dates within a time window.

    Parameters:
        source_events: pd.Series or list of datetime — events to validate
        reference_events: pd.Series or list of datetime — ground truth
        window_days: int — matching window in days (±)

    Returns:
        dict with keys:
            matched: list of matched source dates
            source_only: list of unmatched source dates
            reference_only: list of unmatched reference dates
            n_source: total source events
            n_reference: total reference events
            n_matched: count of matched events
    """
    source_dates = pd.to_datetime(list(source_events))
    ref_dates = pd.to_datetime(list(reference_events))
    window = timedelta(days=window_days)

    matched_source = []
    matched_ref = set()

    for sd in source_dates:
        for i, rd in enumerate(ref_dates):
            if abs(sd - rd) <= window and i not in matched_ref:
                matched_source.append(sd)
                matched_ref.add(i)
                break

    source_only = [d for d in source_dates if d not in matched_source]
    reference_only = [
        d for i, d in enumerate(ref_dates) if i not in matched_ref
    ]

    return {
        "matched": matched_source,
        "source_only": source_only,
        "reference_only": reference_only,
        "n_source": len(source_dates),
        "n_reference": len(ref_dates),
        "n_matched": len(matched_source),
    }