"""
GEOGloWS v2 data access.

Data is fetched from S3 Zarr stores (no auth needed) via the geoglows
package. For persistence, use data/download_geoglows.py to save as parquet.
"""

import pandas as pd
import geoglows.data


def get_retrospective(river_id: int) -> pd.DataFrame:
    """Fetch daily retrospective simulation (1940-present)."""
    return geoglows.data.retro_daily(river_id=river_id)


def get_return_periods(river_id: int) -> pd.DataFrame:
    """Fetch return period thresholds (Log-Pearson III)."""
    return geoglows.data.return_periods(river_id=river_id)


def get_forecast_ensembles(
    river_id: int, date: str = None
) -> pd.DataFrame:
    """Fetch 52-member ensemble forecast (15-day lead)."""
    kwargs = {"river_id": river_id}
    if date:
        kwargs["date"] = date
    return geoglows.data.forecast_ensembles(**kwargs)


def get_forecast_stats(river_id: int, date: str = None) -> pd.DataFrame:
    """Fetch forecast statistics (min/25/mean/median/75/max)."""
    kwargs = {"river_id": river_id}
    if date:
        kwargs["date"] = date
    return geoglows.data.forecast_stats(**kwargs)
