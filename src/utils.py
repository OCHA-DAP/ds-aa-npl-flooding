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