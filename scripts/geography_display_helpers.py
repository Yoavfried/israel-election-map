from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd


POINT_PROXY_MAX_AREA_M2 = 50_000
DISPLAY_DETAIL_MAX_DISTANCE_M = 5_000
WEST_BANK_DETAIL_CODES = {3488, *range(3500, 4000)}


def integer_series(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").round().astype("Int64")


def load_arcgis_detail_by_locality(
    arcgis_dir: Path,
) -> dict[int, tuple[Any, str]]:
    sources = [
        (
            arcgis_dir / "elections2019_statistical_areas.geojson",
            "CityCode",
            "arcgis_systematics_elections2019",
        ),
        (
            arcgis_dir / "elections2015_statistical_areas.geojson",
            "SemelYeshuv",
            "arcgis_systematics_elections2015",
        ),
    ]
    detailed: dict[int, tuple[Any, str]] = {}
    for path, locality_column, source_name in sources:
        if not path.exists():
            continue
        features = gpd.read_file(path, engine="pyogrio")
        features["locality_code"] = integer_series(features[locality_column])
        features = features[
            features["locality_code"].isin(WEST_BANK_DETAIL_CODES)
            & features.geometry.notna()
            & ~features.geometry.is_empty
        ].copy()
        features = features.to_crs("EPSG:2039")
        features = features[features.geometry.area > POINT_PROXY_MAX_AREA_M2]
        if features.empty:
            continue
        dissolved = features[["locality_code", "geometry"]].dissolve(
            by="locality_code", as_index=False
        )
        for row in dissolved.itertuples(index=False):
            code = int(row.locality_code)
            detailed.setdefault(code, (row.geometry, source_name))
    return detailed


def apply_detailed_display_geometries(
    features: gpd.GeoDataFrame,
    detailed_by_locality: dict[int, tuple[Any, str]],
    default_source: str,
) -> tuple[gpd.GeoDataFrame, int, list[int]]:
    projected = features.to_crs("EPSG:2039")
    counts = projected.groupby("locality_code")["locality_code"].transform("size")
    source_area = projected.geometry.area
    if "geometry_source" in projected:
        projected["display_geometry_source"] = projected["geometry_source"].fillna(
            default_source
        )
    else:
        projected["display_geometry_source"] = default_source
    replacements = 0
    rejected_codes: list[int] = []

    for index, row in projected.iterrows():
        code = int(row["locality_code"])
        if (
            code not in WEST_BANK_DETAIL_CODES
            or counts.loc[index] != 1
            or source_area.loc[index] >= POINT_PROXY_MAX_AREA_M2
            or code not in detailed_by_locality
        ):
            continue
        candidate, source_name = detailed_by_locality[code]
        if row.geometry.centroid.distance(candidate) > DISPLAY_DETAIL_MAX_DISTANCE_M:
            rejected_codes.append(code)
            continue
        projected.at[index, "geometry"] = candidate
        projected.at[index, "display_geometry_source"] = source_name
        replacements += 1

    return projected.to_crs("EPSG:4326"), replacements, rejected_codes
