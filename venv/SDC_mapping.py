import os
import json
import pandas as pd
import folium

# === LOAD MASTER ZONE DATA ===
sdc_master = pd.read_csv("SDC_evac_zones.csv")
sdc_master["stripped_id"] = sdc_master["zone_id"].astype(str).str.extract(r"(SDC-\d+)")
valid_sdc_suffixes = set(sdc_master["stripped_id"].dropna().unique())

# === LOAD FULL GEOJSON === 
# something is wrong here
with open("Evacuation_Zones_WGS84.geojson", "r") as f:
    all_zones = json.load(f)

# === YEARLY FIRE DATA PATHS ===
year_csv_paths = {
    2020: "evac_zones/evac_zones_2020.csv",
    2021: "evac_zones/evac_zones_2021.csv",
    2022: "evac_zones/evac_zones_2022.csv",
    2023: "evac_zones/evac_zones_2023.csv",
    2024: "evac_zones/evac_zones_2024.csv",
    2025: "evac_zones/evac_zones_2025.csv",
}

# === SETUP BASE FOLIUM MAP ===
colors = ['#f4a582', '#92c5de', '#b2182b', '#2166ac', '#d6604d', '#4393c3']
m = folium.Map(location=[32.7157, -117.1611], zoom_start=9)

# === LOOP THROUGH YEARS ===
for idx, (year, csv_path) in enumerate(year_csv_paths.items()):
    try:
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            print(f"Skipping {year}: missing or empty file")
            continue

        fire_df = pd.read_csv(csv_path)
        zone_columns = ['Evacuation Order Zones', 'Evacuation Warning Zones']
        extracted_zone_ids = set()

        for col in zone_columns:
            if col in fire_df.columns:
                for cell in fire_df[col].dropna():
                    for zone in str(cell).split(","):
                        z = zone.strip().strip('"').upper()
                        if z.startswith("SDC"):
                            extracted_zone_ids.add(z)

        # Normalize zone IDs 
        normalized_fire_ids = set()
        for z in extracted_zone_ids:
            if z.startswith("SDC-"):
                parts = z.split("-")
                if len(parts) == 2 and parts[1].isdigit():
                    padded = f"SDC-{int(parts[1]):04d}"
                    normalized_fire_ids.add(padded)

        # Match official zone IDs by suffix
        matched_full_ids = set(
            row["zone_id"] for _, row in sdc_master.iterrows()
            if any(row["zone_id"].endswith(z) for z in normalized_fire_ids)
        )

        # Pull from GeoJSON
        matching_features = [
            feat for feat in all_zones["features"]
            if str(feat["properties"].get("zone_id", "")).strip() in matched_full_ids
        ]

        if not matching_features:
            print(f"No matching SDC zones found for {year}")
            continue

        # Add map layer
        color = colors[idx % len(colors)]
        fg = folium.FeatureGroup(name=f"Evacuation Zones {year}")

        folium.GeoJson(
            {"type": "FeatureCollection", "features": matching_features},
            style_function=lambda feature, color=color: {
                'fillColor': color,
                'color': 'black',       
                'weight': 3,
                'fillOpacity': 0.8,      
                'dashArray': '5, 5' 
            },
            tooltip=folium.GeoJsonTooltip(fields=["zone_id"])
        ).add_to(fg)

        fg.add_to(m)
        print(f"Added {len(matching_features)} zones for {year}")

    except Exception as e:
        print(f"Error processing {year}: {e}")

# === SAVE FINAL MAP ===
folium.LayerControl(collapsed=False).add_to(m)
m.save("sdc_zones_map.html")
print("\nMap saved as sdc_zones_map.html — open it in your browser to view.")