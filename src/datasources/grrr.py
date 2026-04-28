import os

# Silence gRPC/abseil log spam from google-cloud-storage; must be set
# before any grpc/google-cloud import happens.
os.environ.setdefault("GRPC_VERBOSITY", "NONE")
os.environ.setdefault("GLOG_minloglevel", "3")

import xarray as xr
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

BASE_DIRECTORY = (
    "gs://flood-forecasting/hydrologic_predictions/model_id_8583a5c2_v0/"
)


def open_zarr(path):
    return xr.open_zarr(
        store=path, chunks="auto", storage_options=dict(token="anon")
    )


def process_reforecast(gauge):
    reforecast_path = os.path.join(
        BASE_DIRECTORY, "reforecast/streamflow.zarr/"
    )
    ds_rf = open_zarr(reforecast_path).sel(gauge_id=gauge).compute()
    df_rf = ds_rf.to_dataframe().reset_index()
    df_rf["valid_time"] = df_rf.apply(
        lambda row: row["issue_time"] + row["lead_time"], axis=1
    )
    df_rf["leadtime"] = df_rf["lead_time"].apply(lambda x: x.days)
    df_rf = df_rf.drop(columns=["lead_time", "gauge_id"])
    return df_rf


def process_reanalysis(gauge):
    reanalysis_path = os.path.join(
        BASE_DIRECTORY, "reanalysis/streamflow.zarr/"
    )
    ds_ra = open_zarr(reanalysis_path).sel(gauge_id=gauge).compute()
    df_ra = ds_ra.to_dataframe().reset_index()
    df_ra = df_ra.rename(columns={"time": "valid_time"}).drop(
        columns=["gauge_id"]
    )
    return df_ra


def load_return_periods(gauge):
    return_periods_path = os.path.join(BASE_DIRECTORY, "return_periods.zarr/")
    return open_zarr(return_periods_path).sel(gauge_id=gauge).compute()