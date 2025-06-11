# Nepal Flooding Trigger Framework

This repository contains the analytical framework developed to support the revision of the flood trigger mechanism for anticipatory action in Nepal.

## Objective

The goal is to improve the effectiveness and precision of flood-related anticipatory interventions by revisiting and strengthening the **trigger thresholds** used to activate preparedness and early response activities.

## Key Features

- **Trigger Revision Analysis**: Historical flood data, forecast data, and past activation outcomes are analyzed to assess the performance of the current trigger mechanism.
- **Impact-Based Validation**: Integration of impact data to evaluate whether triggers corresponded with significant flood impacts.

## Data Sources

- Forecasts from GloFAS and observed river levels from DHM 
- Historical flood events and impacts (EM-DAT)
- Administrative boundaries for Nepal

## Folder Structure

- `analysis/` — Analysis notebooks for testing and visualizing trigger logic
- `src/` — Core functions for data processing and evaluation

## Usage

1. Clone the repository  
2. Set up the environment (see `requirements.txt`)  
3. Run the notebooks in `analysis/` for exploratory analysis and trigger simulations
