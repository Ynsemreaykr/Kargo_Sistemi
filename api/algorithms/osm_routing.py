"""
Kargo İşletme Sistemi - OpenStreetMap Routing
OSRM (Open Source Routing Machine) ile gerçek yol rotaları
"""

import requests
import json
import os
from typing import List, Dict, Tuple, Any, Optional
from pathlib import Path

# OSRM Public API endpoint
OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"

# Cache dizini
CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_FILE = CACHE_DIR / "osm_distance_matrix.json"


def get_osm_route(start_coords: Tuple[float, float], end_coords: Tuple[float, float]) -> Optional[Dict[str, Any]]:
    """
    İki nokta arası gerçek rota bilgisi al (OSRM API)
    
    Args:
        start_coords: (longitude, latitude) - DİKKAT: lon, lat sırası!
        end_coords: (longitude, latitude)
    
    Returns:
        {
            'distance_km': 38.5,
            'duration_min': 35,
            'geometry': {...},  # GeoJSON LineString koordinatları
            'legs': [...]
        }
        None if API fails
    """
    try:
        # OSRM endpoint formatı: lon,lat;lon,lat
        url = f"{OSRM_BASE_URL}/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}"
        
        # Parametreler
        params = {
            'overview': 'full',  # Tam geometri
            'geometries': 'geojson',  # GeoJSON formatında
            'steps': 'false'  # Turn-by-turn gerekmez
        }
        
        # API çağrısı
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data['code'] != 'Ok':
            print(f"⚠️ OSRM Error: {data.get('message', 'Unknown error')}")
            return None
        
        # Route bilgisini çıkar
        route = data['routes'][0]
        
        return {
            'distance_km': round(route['distance'] / 1000, 2),  # metre → km
            'duration_min': round(route['duration'] / 60, 1),   # saniye → dakika
            'geometry': route['geometry'],  # GeoJSON LineString
            'legs': route.get('legs', [])
        }
        
    except requests.exceptions.Timeout:
        print(f"⏱️ OSRM API timeout")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ OSRM API error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error in get_osm_route: {e}")
        return None


def get_osm_distance_matrix(districts: List[Dict[str, Any]]) -> Dict[Tuple[int, int], Dict[str, float]]:
    """
    Tüm ilçeler arası OSM mesafe matrisi oluştur
    
    Args:
        districts: İlçe listesi [{'id': 1, 'latitude': 40.xx, 'longitude': 29.xx}, ...]
    
    Returns:
        {
            (district_id_1, district_id_2): {'distance_km': 38.5, 'duration_min': 35},
            ...
        }
    """
    matrix = {}
    total_calls = len(districts) * (len(districts) - 1) // 2
    call_count = 0
    
    print(f"📡 OSM API: {total_calls} rota hesaplanıyor...")
    
    for i, dist1 in enumerate(districts):
        for dist2 in districts[i:]:
            dist_id1 = dist1['id']
            dist_id2 = dist2['id']
            
            if dist_id1 == dist_id2:
                # Aynı ilçe
                matrix[(dist_id1, dist_id2)] = {'distance_km': 0.0, 'duration_min': 0.0}
            else:
                # OSRM ile gerçek rota
                route = get_osm_route(
                    (dist1['longitude'], dist1['latitude']),
                    (dist2['longitude'], dist2['latitude'])
                )
                
                if route:
                    # Başarılı
                    matrix[(dist_id1, dist_id2)] = {
                        'distance_km': route['distance_km'],
                        'duration_min': route['duration_min']
                    }
                    matrix[(dist_id2, dist_id1)] = matrix[(dist_id1, dist_id2)]  # Simetrik
                else:
                    # API hatası - fallback to Haversine
                    from .utils import haversine_distance
                    dist = haversine_distance(
                        dist1['latitude'], dist1['longitude'],
                        dist2['latitude'], dist2['longitude']
                    )
                    matrix[(dist_id1, dist_id2)] = {
                        'distance_km': dist,
                        'duration_min': round(dist / 60 * 60, 1)  # ~60 km/h ortalama
                    }
                    matrix[(dist_id2, dist_id1)] = matrix[(dist_id1, dist_id2)]
                
                call_count += 1
                if call_count % 10 == 0:
                    print(f"  ✓ {call_count}/{total_calls} rota tamamlandı")
    
    print(f"✓ Tüm rotalar hesaplandı!")
    return matrix


def load_distance_matrix_from_cache() -> Optional[Dict]:
    """
    Cache'den mesafe matrisini yükle
    
    Returns:
        Cache data veya None
    """
    try:
        if not CACHE_FILE.exists():
            return None
        
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        print(f"✓ OSM cache yüklendi: {CACHE_FILE}")
        return cache_data
        
    except Exception as e:
        print(f"⚠️ Cache okuma hatası: {e}")
        return None


def save_distance_matrix_to_cache(matrix: Dict, districts: List[Dict]) -> None:
    """
    Mesafe matrisini cache'e kaydet
    
    Args:
        matrix: Mesafe matrisi
        districts: İlçe listesi
    """
    try:
        # Cache dizini yoksa oluştur
        CACHE_DIR.mkdir(exist_ok=True)
        
        # JSON formatına çevir (tuple key'leri string'e)
        cache_data = {
            'districts': {},
            'last_updated': None,
            'district_list': [{'id': d['id'], 'name': d['name']} for d in districts]
        }
        
        for (id1, id2), data in matrix.items():
            key = f"{id1}_{id2}"
            cache_data['districts'][key] = data
        
        # Timestamp ekle
        from datetime import datetime
        cache_data['last_updated'] = datetime.now().isoformat()
        
        # Dosyaya kaydet
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ OSM cache kaydedildi: {CACHE_FILE}")
        
    except Exception as e:
        print(f"⚠️ Cache kaydetme hatası: {e}")


def calculate_distance_matrix_osm(
    districts: List[Dict[str, Any]], 
    use_cache: bool = True,
    use_osm: bool = True
) -> Dict[Tuple[int, int], float]:
    """
    OSM ile mesafe matrisi (cache ile)
    
    Args:
        districts: İlçe listesi
        use_cache: Cache kullan mı?
        use_osm: OSM kullan mı? (False ise Haversine)
    
    Returns:
        Mesafe matrisi {(id1, id2): distance_km}
    """
    # OSM kapalıysa direkt Haversine
    if not use_osm:
        from .utils import calculate_distance_matrix
        return calculate_distance_matrix(districts)
    
    # Cache kontrol
    if use_cache:
        cache_data = load_distance_matrix_from_cache()
        if cache_data:
            # Cache'den yükle
            matrix = {}
            for key, data in cache_data['districts'].items():
                id1, id2 = map(int, key.split('_'))
                matrix[(id1, id2)] = data['distance_km']
            
            return matrix
    
    # Cache yok veya kullanma - API'den al
    print("🌐 OSM API ile mesafe matrisi oluşturuluyor...")
    osm_matrix = get_osm_distance_matrix(districts)
    
    # Cache'e kaydet
    if use_cache:
        save_distance_matrix_to_cache(osm_matrix, districts)
    
    # Sadece distance_km döndür (algoritma için)
    distance_only_matrix = {}
    for key, data in osm_matrix.items():
        distance_only_matrix[key] = data['distance_km']
    
    return distance_only_matrix


def get_route_geometry_osm(route: List[int], districts: List[Dict]) -> Dict:
    """
    Rota için GeoJSON geometri oluştur (OSM route geometry)
    
    Args:
        route: İlçe ID listesi [12, 3, 6, 9, 12]
        districts: İlçe listesi
    
    Returns:
        GeoJSON FeatureCollection
    """
    features = []
    
    for i in range(len(route) - 1):
        from_id = route[i]
        to_id = route[i + 1]
        
        # İlçe bilgilerini bul
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
