import fiona
from fiona.transform import transform_geom
from shapely.geometry import shape, mapping
import json

# --- CONFIG ---
input_path = "Evacuation_Zones.geojson"
output_path = "Evacuation_Zones_WGS84.geojson"

# Replace with correct source CRS if known (3857 is a common guess for web maps)
src_crs = "EPSG:2229"
dst_crs = "EPSG:4326"  # WGS84 (lat/lon)

# --- Reproject and convert features ---
features_wgs84 = []

with fiona.open(input_path, "r") as src:
    for feat in src:
        # Reproject the geometry
        transformed_geom = transform_geom(src_crs, dst_crs, feat["geometry"])

        # Convert to serializable GeoJSON structure
        geojson_geometry = mapping(shape(transformed_geom))

        # Build a clean feature dictionary
        features_wgs84.append({
            "type": "Feature",
            "geometry": geojson_geometry,
            "properties": dict(feat["properties"])
        })

# --- Write final GeoJSON ---
output_geojson = {
    "type": "FeatureCollection",
    "features": features_wgs84
}

with open(output_path, "w") as f:
    json.dump(output_geojson, f)

print(f"Saved reprojected GeoJSON to: {output_path}")
