from dataclasses import dataclass
from typing import Optional


@dataclass
class StationConfig:
    name: str
    dhm_column: str
    danger_level: float  # DHM danger level (water level, meters)
    # GloFAS
    glofas_rp2: float  # Copernicus dashboard RP2 (m3/s)
    glofas_rp5: float  # Copernicus dashboard RP5 (m3/s)
    # GEOGloWS
    geoglows_river_id: int
    geoglows_lat: Optional[float]
    geoglows_lon: Optional[float]
    geoglows_upstream_area_km2: float
    # Google GRRR
    grrr_gauge_id: Optional[str] = None


CHATARA = StationConfig(
    name="Chatara",
    dhm_column="Chatara",
    danger_level=7.0,
    glofas_rp2=8113,
    glofas_rp5=10306,
    geoglows_river_id=441135650,
    geoglows_lat=26.867,
    geoglows_lon=87.160,
    geoglows_upstream_area_km2=57125,
    grrr_gauge_id="hybas_4120864110",
)

CHISAPANI = StationConfig(
    name="Chisapani",
    dhm_column="Chisapani",
    danger_level=10.5,
    glofas_rp2=5664,
    glofas_rp5=6797,
    geoglows_river_id=441112306,
    geoglows_lat=None,  # found via metadata table, not lat/lon
    geoglows_lon=None,
    geoglows_upstream_area_km2=40149,
    grrr_gauge_id="hybas_4121455820",
)

STATIONS = {"chatara": CHATARA, "chisapani": CHISAPANI}

RETURN_PERIODS = [2, 5, 10, 25, 50, 100]

# Trigger lead times (days)
READINESS_LEADTIME = 7
ACTION_LEADTIME = 3
