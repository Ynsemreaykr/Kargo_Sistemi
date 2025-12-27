"""
OSM Routing - OSRM API ile gerçek yol rotaları
"""

import requests
from typing import List, Dict, Tuple, Optional, Any

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"


def get_osm_route(start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Optional[Dict[str, Any]]:
    """
    İki nokta arası gerçek rota bilgisi al (OSRM API)
    
    Args:
        start_coords: (longitude, latitude)
        end_coords: (longitude, latitude)
    
    Returns:
        {'distance_km': float, 'duration_min': float, 'geometry': GeoJSON LineString}
    """
    try:
        url = f"{OSRM_BASE_URL}/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
        
        params = {
            'overview': 'full',
            'geometries': 'geojson',
            'steps': 'false'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['code'] != 'Ok':
            print(f"⚠️ OSRM Error: {data.get('message', 'Unknown')}")
            return None
        
        route = data['routes'][0]
        
        return {
            'distance_km': round(route['distance'] / 1000, 2),
            'duration_min': round(route['duration'] / 60, 1),
            'geometry': route['geometry']
        }
        
    except Exception as e:
        print(f"❌ OSM route error: {e}")
        return None


def get_route_geometry_osm(route: List[int], districts: List[Dict]) -> Dict:
    """
    Rota için GeoJSON geometri oluştur (OSM route geometry)
    
    Args:
        route: İlçe ID listesi [12, 3, 6]
        districts: İlçe listesi
    
    Returns:
        GeoJSON FeatureCollection
    """
    features = []
    
    for i in range(len(route) - 1):
        from_id = route[i]
        to_id = route[i + 1]
        
        from_dist = next((d for d in districts if d['id'] == from_id), None)
        to_dist = next((d for d in districts if d['id'] == to_id), None)
        
        if not from_dist or not to_dist:
            continue
        
        # OSM route al
        osm_route = get_osm_route(
            (from_dist['longitude'], from_dist['latitude']),
            (to_dist['longitude'], to_dist['latitude'])
        )
        
        if osm_route and osm_route.get('geometry'):
            # Gerçek route geometry
            features.append({
                'type': 'Feature',
                'geometry': osm_route['geometry'],
                'properties': {
                    'from': from_dist['name'],
                    'to': to_dist['name'],
                    'distance_km': osm_route['distance_km'],
                    'duration_min': osm_route['duration_min']
                }
            })
        else:
            # Fallback: Düz çizgi
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [
                        [from_dist['longitude'], from_dist['latitude']],
                        [to_dist['longitude'], to_dist['latitude']]
                    ]
                },
                'properties': {
                    'from': from_dist['name'],
                    'to': to_dist['name'],
                    'fallback': True
                }
            })
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }
