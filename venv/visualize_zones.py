import geopandas as gpd
import folium

# Step 1: Load your GeoJSON file
gdf = gpd.read_file("2025_fires.geojson")

# Optional: Inspect the first few rows
print(gdf.head())

# Step 2: Create a base map centered around LA County
m = folium.Map(location=[34.05, -118.25], zoom_start=9)

# Step 3: Add GeoJSON layer with styling
def style_function(feature):
    status = feature['properties'].get('most_extreme_status', '')
    return {
        'fillColor': 'red' if status == 'Evacuation Order' else 'orange',
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.5
    }

highlight_function = lambda feature: {
    'fillColor': '#666',
    'color': 'blue',
    'weight': 2,
    'fillOpacity': 0.7
}

folium.GeoJson(
    gdf,
    name="Evacuation Zones",
    style_function=style_function,
    highlight_function=highlight_function,
    tooltip=folium.GeoJsonTooltip(fields=["zoneId", "incident_name", "most_extreme_status"])
).add_to(m)

legend_html = """
<div style="
    position: fixed; 
    bottom: 30px; left: 30px; width: 180px; height: 80px; 
    background-color: white; 
    border:2px solid grey; z-index:9999; 
    font-size:14px;
    padding: 10px;
">
    <b>Legend</b><br>
    <i style="background: red; width: 10px; height: 10px; display: inline-block;"></i> Evacuation Order<br>
    <i style="background: orange; width: 10px; height: 10px; display: inline-block;"></i> Evacuation Warning
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# Step 4: Add layer control and save map
folium.LayerControl().add_to(m)
m.save("2025_map.html")
print("Map saved as '2025_map.html'")