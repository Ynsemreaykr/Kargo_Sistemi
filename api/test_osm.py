"""
Test script to verify OSM API is working
"""

from algorithms.osm_routing import get_osm_route

# Test: İzmit -> Gebze
print("Testing OSRM API...")
print("-" * 50)

route = get_osm_route(
    (29.9167, 40.7667),  # İzmit (lon, lat)
    (29.4307, 40.8028)   # Gebze (lon, lat)
)

if route:
    print("✓ OSRM API çalışıyor!")
    print(f"  Mesafe: {route['distance_km']} km")
    print(f"  Süre: {route['duration_min']} dakika")
    print(f"  Geometri noktaları: {len(route['geometry']['coordinates'])}")
else:
    print("❌ OSRM API çalışmıyor!")
    print("  İnternet bağlantınızı kontrol edin")

print("-" * 50)
