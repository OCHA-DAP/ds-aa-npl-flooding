# Nepal Flooding Trigger Framework

This repository contains the analytical framework developed to support the revision of the flood trigger mechanism for anticipatory action in Nepal.

## Objective

The goal is to improve the effectiveness and precision of flood-related anticipatory interventions by revisiting and strengthening the **trigger thresholds** used to activate preparedness and early response activities.

## Key Features

- **Trigger Revision Analysis**: Historical flood data, forecast data, and past activation outcomes are analyzed to assess the performance of the current trigger mechanism.
- **Impact-Based Validation**: Integration of impact data to evaluate whether triggers corresponded with significant flood impacts.
- **Cross-Source Evaluation**: Side-by-side comparison of candidate streamflow products against observed DHM danger-level crossings.

## Data Sources

- **GloFAS** (ECMWF/Copernicus) — reanalysis and reforecast; current basis for trigger calibration
- **DHM** (Nepal) — observed river water levels at gauge stations
- **GEOGloWS v2** — global retrospective (1940–present) and 52-member ensemble forecast
- **Google GRRR** — experimental streamflow reanalysis and reforecast
- **EM-DAT** — historical flood events and impacts
- Administrative boundaries for Nepal

## Folder Structure

- `analysis/` — Jupyter notebooks for exploratory analysis and trigger simulations
- `book/` — Quarto book evaluating GEOGloWS for the AA framework (`quarto render book` to build)
- `data/` — Cached parquet files for GEOGloWS retrospective and return periods
- `src/` — Station configs, data-source clients, and utility functions

## Usage

1. Clone the repository.
2. Install dependencies with `uv sync` (project uses `pyproject.toml` and `uv.lock`).
3. Set `AA_DATA_DIR` to the shared CERF AA data directory (required for GloFAS, DHM, and EM-DAT inputs).
4. For Google GRRR access, set `GOOGLE_API_KEY` (used by `src/datasources/grrr.py`).
5. Run the notebooks in `analysis/` for exploratory work, or render the Quarto book for the GEOGloWS evaluation summary.
