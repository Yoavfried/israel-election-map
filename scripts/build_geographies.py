from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

LOCAL_PYTHON = Path(__file__).resolve().parents[1] / ".local" / "python-geo"
if LOCAL_PYTHON.exists():
    sys.path.insert(0, str(LOCAL_PYTHON))

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point
from shapely.ops import transform

from pipeline_common import PROCESSED_DIR, RAW_DIR, ensure_dir, write_csv, write_json


GDB_PATH = RAW_DIR / "ezorim_statistiim_2022.gdb"
LAYER_NAME = "statistical_areas_2022"
OUT_DIR = PROCESSED_DIR / "geographies"

CUSTOM_GEOGRAPHIES = [
    {
        "custom_id": "custom:tribal_negev",
        "custom_key": "TRIBE",
        "name_he": "שבטים / פזורה בנגב",
        "name_en": "Negev tribal/dispersed-settlement bucket",
        "lon": 34.93,
        "lat": 31.22,
        "radius_m": 3500,
        "note": "Synthetic point-size polygon for reviewed tribal/dispersed-settlement rows.",
    },
    {
        "custom_id": "custom:hebron",
        "custom_key": "HEBRON",
        "name_he": "חברון",
        "name_en": "Hebron custom bucket",
        "lon": 35.0998,
        "lat": 31.5326,
        "radius_m": 2500,
        "note": "Synthetic point-size polygon for reviewed Hebron rows.",
    },
    {
        "custom_id": "custom:northern_samaria_evacuated_localities",
        "custom_key": "N.S.",
        "name_he": "יישובי צפון השומרון שפונו",
        "name_en": "Northern Samaria evacuated localities bucket",
        "lon": 35.18,
        "lat": 32.43,
        "radius_m": 3000,
        "note": "Synthetic point-size polygon for reviewed Northern Samaria evacuated-locality rows.",
    },
    {
        "custom_id": "custom:gaza_evacuated_localities",
        "custom_key": "GAZA",
        "name_he": "יישובי גוש קטיף / רצועת עזה שפונו",
        "name_en": "Gaza evacuated localities bucket",
        "lon": 34.36,
        "lat": 31.35,
        "radius_m": 4500,
        "note": "Synthetic point-size polygon for reviewed Gaza evacuated-locality rows.",
    },
]


def clean_int(value: Any) -> int | None:
    if pd.isna(value):
        return None
    return int(value)


def read_statistical_areas() -> gpd.GeoDataFrame:
    if not GDB_PATH.exists():
        raise FileNotFoundError(f"Missing canonical FileGDB: {GDB_PATH}")

    gdf = gpd.read_file(GDB_PATH, layer=LAYER_NAME, engine="pyogrio")
    gdf = gdf.rename(
        columns={
            "SEMEL_YISHUV": "locality_code",
            "SHEM_YISHUV": "locality_name_he",
            "SHEM_YISHUV_ENGLISH": "locality_name_en",
            "STAT_2022": "stat_2022",
            "YISHUV_STAT_2022": "yishuv_stat_2022",
        }
    )
    gdf["locality_code"] = gdf["locality_code"].map(clean_int)
    gdf["stat_2022"] = gdf["stat_2022"].map(clean_int)
    gdf["yishuv_stat_2022"] = gdf["yishuv_stat_2022"].map(clean_int)
    gdf["locality_id"] = gdf["locality_code"].map(lambda value: f"loc:{value}" if value is not None else "")
    gdf["stat_area_id"] = gdf["yishuv_stat_2022"].map(lambda value: f"stat2022:{value}" if value is not None else "")
    gdf["geometry"] = gdf.geometry.make_valid()
    return gdf


def write_geojson(gdf: gpd.GeoDataFrame, path) -> None:
    ensure_dir(path.parent)
    gdf.to_file(path, driver="GeoJSON", encoding="utf-8", index=False)


def metadata_from_stats(stats_4326: gpd.GeoDataFrame) -> list[dict[str, Any]]:
    bounds = stats_4326.bounds
    rows: list[dict[str, Any]] = []
    for index, row in stats_4326.drop(columns="geometry").iterrows():
        row_bounds = bounds.loc[index]
        rows.append(
            {
                "stat_area_id": row["stat_area_id"],
                "yishuv_stat_2022": row["yishuv_stat_2022"],
                "locality_id": row["locality_id"],
                "locality_code": row["locality_code"],
                "locality_name_he": row["locality_name_he"],
                "locality_name_en": row["locality_name_en"],
                "stat_2022": row["stat_2022"],
                "rova": row.get("ROVA", ""),
                "tat_rova": row.get("TAT_ROVA", ""),
                "cod_tifkud": row.get("COD_TIFKUD", ""),
                "min_lon": row_bounds["minx"],
                "min_lat": row_bounds["miny"],
                "max_lon": row_bounds["maxx"],
                "max_lat": row_bounds["maxy"],
            }
        )
    return rows


def build_localities(stats: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    def join_int_values(values) -> str:
        cleaned = sorted({int(value) for value in values if pd.notna(value)})
        return "|".join(str(value) for value in cleaned)

    def join_text_values(values) -> str:
        cleaned = sorted({str(value) for value in values if pd.notna(value) and str(value)})
        return "|".join(cleaned)

    stats_for_dissolve = stats[
        [
            "locality_code",
            "locality_id",
            "locality_name_he",
            "locality_name_en",
            "stat_area_id",
            "stat_2022",
            "yishuv_stat_2022",
            "COD_TIFKUD",
            "geometry",
        ]
    ].copy()
    stats_for_dissolve["stat_area_count"] = 1

    dissolved = stats_for_dissolve.dissolve(
        by=["locality_code", "locality_id", "locality_name_he", "locality_name_en"],
        aggfunc={
            "stat_area_count": "sum",
            "stat_area_id": join_text_values,
            "stat_2022": join_int_values,
            "yishuv_stat_2022": join_int_values,
            "COD_TIFKUD": join_int_values,
        },
        as_index=False,
    )
    dissolved["geometry"] = dissolved.geometry.make_valid()
    dissolved["single_stat_area"] = dissolved["stat_area_count"] == 1
    dissolved["has_function_code"] = dissolved["COD_TIFKUD"].astype(str) != ""
    return dissolved


def locality_metadata(localities_4326: gpd.GeoDataFrame) -> list[dict[str, Any]]:
    bounds = localities_4326.bounds
    rows: list[dict[str, Any]] = []
    for index, row in localities_4326.drop(columns="geometry").iterrows():
        row_bounds = bounds.loc[index]
        rows.append(
            {
                "locality_id": row["locality_id"],
                "locality_code": row["locality_code"],
                "locality_name_he": row["locality_name_he"],
                "locality_name_en": row["locality_name_en"],
                "stat_area_count": row["stat_area_count"],
                "single_stat_area": row["single_stat_area"],
                "stat_area_ids": row["stat_area_id"],
                "stat_2022_values": row["stat_2022"],
                "yishuv_stat_2022_values": row["yishuv_stat_2022"],
                "cod_tifkud_values": row["COD_TIFKUD"],
                "has_function_code": row["has_function_code"],
                "min_lon": row_bounds["minx"],
                "min_lat": row_bounds["miny"],
                "max_lon": row_bounds["maxx"],
                "max_lat": row_bounds["maxy"],
            }
        )
    return rows


def custom_geographies() -> gpd.GeoDataFrame:
    to_itm = Transformer.from_crs("EPSG:4326", "EPSG:2039", always_xy=True)
    to_wgs84 = Transformer.from_crs("EPSG:2039", "EPSG:4326", always_xy=True)

    features = []
    for item in CUSTOM_GEOGRAPHIES:
        point_itm = transform(to_itm.transform, Point(item["lon"], item["lat"]))
        polygon_wgs84 = transform(to_wgs84.transform, point_itm.buffer(item["radius_m"], quad_segs=48))
        features.append({**item, "geometry": polygon_wgs84})

    return gpd.GeoDataFrame(features, geometry="geometry", crs="EPSG:4326")


def simplify(gdf: gpd.GeoDataFrame, tolerance: float) -> gpd.GeoDataFrame:
    simplified = gdf.copy()
    simplified["geometry"] = simplified.geometry.simplify(tolerance, preserve_topology=True).make_valid()
    return simplified


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--simplify-tolerance", type=float, default=0.00005)
    args = parser.parse_args()

    stats = read_statistical_areas()
    stats_4326 = stats.to_crs("EPSG:4326")
    localities = build_localities(stats).to_crs("EPSG:4326")
    custom = custom_geographies()

    write_geojson(stats_4326, OUT_DIR / "statistical_areas_2022.geojson")
    write_geojson(localities, OUT_DIR / "localities_2022_dissolved.geojson")
    write_geojson(custom, OUT_DIR / "custom_geographies.geojson")

    if args.simplify_tolerance > 0:
        write_geojson(
            simplify(stats_4326, args.simplify_tolerance),
            OUT_DIR / "statistical_areas_2022.simplified.geojson",
        )
        write_geojson(
            simplify(localities, args.simplify_tolerance),
            OUT_DIR / "localities_2022_dissolved.simplified.geojson",
        )

    stat_rows = metadata_from_stats(stats_4326)
    locality_rows = locality_metadata(localities)
    write_csv(
        OUT_DIR / "statistical_areas_2022.metadata.csv",
        stat_rows,
        list(stat_rows[0].keys()),
    )
    write_csv(
        OUT_DIR / "localities_2022.metadata.csv",
        locality_rows,
        list(locality_rows[0].keys()),
    )

    summary = {
        "source": str(GDB_PATH.relative_to(RAW_DIR.parent)).replace("\\", "/"),
        "layer": LAYER_NAME,
        "source_crs": str(stats.crs),
        "output_crs": "EPSG:4326",
        "statistical_area_features": int(len(stats)),
        "unique_stat_area_ids": int(stats["stat_area_id"].nunique()),
        "locality_features": int(len(localities)),
        "single_stat_localities": int(localities["single_stat_area"].sum()),
        "multi_stat_localities": int((~localities["single_stat_area"]).sum()),
        "custom_geographies": int(len(custom)),
        "simplify_tolerance": args.simplify_tolerance,
        "bounds_wgs84": {
            "min_lon": float(stats_4326.total_bounds[0]),
            "min_lat": float(stats_4326.total_bounds[1]),
            "max_lon": float(stats_4326.total_bounds[2]),
            "max_lat": float(stats_4326.total_bounds[3]),
        },
    }
    write_json(OUT_DIR / "geography_build_summary.json", summary)

    print(f"statistical_area_features={summary['statistical_area_features']}")
    print(f"locality_features={summary['locality_features']}")
    print(f"single_stat_localities={summary['single_stat_localities']}")
    print(f"multi_stat_localities={summary['multi_stat_localities']}")
    print(f"custom_geographies={summary['custom_geographies']}")
    print(f"out_dir={OUT_DIR.relative_to(PROCESSED_DIR.parent)}")


if __name__ == "__main__":
    main()
