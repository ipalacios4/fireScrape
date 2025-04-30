import os
import json
import pandas as pd
import folium

# === LOAD MASTER ZONE DATA ===
sdc_master = pd.read_csv("SDC_evac_zones.csv")
sdc_master["stripped_id"] = sdc_master["zone_id"].astype(str).str.extract(r"(SDC-\d+)")
valid_sdc_suffixes = set(sdc_master["stripped_id"].dropna().unique())

# === LOAD FULL GEOJSON === 
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

# Store final matched features and incident mappings
all_features = []
incident_mapping = []

# === LOOP THROUGH YEARS ===
for idx, (year, csv_path) in enumerate(year_csv_paths.items()):
    try:
        if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
            print(f"Skipping {year}: missing or empty file")
            continue

        fire_df = pd.read_csv(csv_path)
        zone_columns = ['Evacuation Order Zones', 'Evacuation Warning Zones']
        fire_col = next((c for c in fire_df.columns if "incident" in c.lower() or "fire" in c.lower()), None)
        if fire_col is None:
            print(f"No incident/fire name column found in {year}")
            continue

        zone_to_fire = {}

        # Extract mapping of zone -> incident name
        for _, row in fire_df.iterrows():
            incident = str(row[fire_col]) if pd.notna(row[fire_col]) else "Unknown"
            for col in zone_columns:
                if col in row and pd.notna(row[col]):
                    for raw_zone in str(row[col]).split(","):
                        z = raw_zone.strip().strip('"').upper()
                        if z.startswith("SDC-"):
                            parts = z.split("-")
                            if len(parts) == 2 and parts[1].isdigit():
                                padded = f"SDC-{int(parts[1]):04d}"
                                for full_id in sdc_master["zone_id"]:
                                    if full_id.endswith(padded):
                                        zone_to_fire[full_id] = incident

        # Get matched zone features
        matched_features = []
        for feat in all_zones["features"]:
            zid = str(feat["properties"].get("zone_id", "")).strip()
            if zid in zone_to_fire:
                feat["properties"]["incident_name"] = zone_to_fire[zid]
                feat["properties"]["year"] = year
                matched_features.append(feat)
                all_features.append(feat)
                incident_mapping.append({
                    "year": year,
                    "zone_id": zid,
                    "incident_name": zone_to_fire[zid]
                })

        if not matched_features:
            print(f"No matching SDC zones found for {year}")
            continue

        # Add map layer
        color = colors[idx % len(colors)]
        fg = folium.FeatureGroup(name=f"Evacuation Zones {year}")
        folium.GeoJson(
            {"type": "FeatureCollection", "features": matched_features},
            style_function=lambda feature, color=color: {
                'fillColor': color,
                'color': color,        
                'weight': 1.5,             
                'fillOpacity': 0.5,
                'opacity': 0.7,
            },
            tooltip=folium.GeoJsonTooltip(fields=["zone_id", "incident_name"])
        ).add_to(fg)
        fg.add_to(m)

        print(f"Added {len(matched_features)} zones for {year}")

    except Exception as e:
        print(f"Error processing {year}: {e}")

# === SAVE FINAL MAP AND CSV ===
folium.LayerControl(collapsed=False).add_to(m)
m.save("sdc_zones_map.html")
print("\nMap saved as sdc_zones_map.html — open in browser.")

# Save zone-incident lookup
pd.DataFrame(incident_mapping).to_csv("zone_incident_lookup.csv", index=False)
print("Zone-to-incident mapping saved as zone_incident_lookup.csv")