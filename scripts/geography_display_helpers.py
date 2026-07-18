from __future__ import annotations

from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd


POINT_PROXY_MAX_AREA_M2 = 50_000
POINT_PROXY_MAX_COORDINATES = 12
DISPLAY_DETAIL_MAX_DISTANCE_M = 5_000
DISPLAY_DETAIL_MIN_RETAINED_AREA_SHARE = 0.5
WEST_BANK_DETAIL_CODES = {3488, *range(3500, 4000)}


def integer_series(values: pd.Series) -> pd.Series:
    return pd.to_numeric(values, errors="coerce").round().astype("Int64")


def geometry_coordinate_count(geometry: Any) -> int:
    if geometry is None or geometry.is_empty:
        return 0
    if geometry.geom_type == "Polygon":
        return sum(
            len(ring.coords)
            for ring in [geometry.exterior, *geometry.interiors]
        )
    if hasattr(geometry, "geoms"):
        return sum(geometry_coordinate_count(part) for part in geometry.geoms)
    if hasattr(geometry, "coords"):
        return len(geometry.coords)
    return 0


def is_point_proxy(geometry: Any) -> bool:
    return (
        geometry.area < POINT_PROXY_MAX_AREA_M2
        or geometry_coordinate_count(geometry) <= POINT_PROXY_MAX_COORDINATES
    )


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
        dissolved = features[["locality_code", "geometry"]].dissolve(
            by="locality_code", as_index=False
        )
        dissolved = dissolved[
            (dissolved.geometry.area > POINT_PROXY_MAX_AREA_M2)
            & dissolved.geometry.map(
                lambda geometry: geometry_coordinate_count(geometry)
                > POINT_PROXY_MAX_COORDINATES
            )
        ]
        for row in dissolved.itertuples(index=False):
            code = int(row.locality_code)
            detailed.setdefault(code, (row.geometry, source_name))
    return detailed


def apply_detailed_display_geometries(
    features: gpd.GeoDataFrame,
    detailed_by_locality: dict[int, tuple[Any, str]],
    default_source: str,
    allow_overlap_codes: set[int] | None = None,
) -> tuple[gpd.GeoDataFrame, int, list[int]]:
    allow_overlap_codes = allow_overlap_codes or set()
    projected = features.to_crs("EPSG:2039")
    counts = projected.groupby("locality_code")["locality_code"].transform("size")
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
            or not is_point_proxy(row.geometry)
            or code not in detailed_by_locality
        ):
            continue
        candidate, source_name = detailed_by_locality[code]
        if row.geometry.centroid.distance(candidate) > DISPLAY_DETAIL_MAX_DISTANCE_M:
            rejected_codes.append(code)
            continue

        # ArcGIS detail comes from a newer statistical-area layer. Preserve the
        # historical layer's neighboring areas whenever the two vintages differ.
        if code not in allow_overlap_codes:
            candidate_area = candidate.area
            feature_position = projected.index.get_loc(index)
            blocker_indices = [
                blocker_index
                for blocker_index in projected.sindex.query(
                    candidate, predicate="intersects"
                )
                if blocker_index != feature_position
            ]
            if blocker_indices:
                blockers = projected.iloc[blocker_indices].geometry.union_all()
                candidate = candidate.difference(blockers).buffer(0)
            retained_share = candidate.area / candidate_area if candidate_area else 0
            if (
                candidate.is_empty
                or retained_share < DISPLAY_DETAIL_MIN_RETAINED_AREA_SHARE
            ):
                rejected_codes.append(code)
                continue

        projected.at[index, "geometry"] = candidate
        projected.at[index, "display_geometry_source"] = source_name
        replacements += 1

    return projected.to_crs("EPSG:4326"), replacements, rejected_codes
