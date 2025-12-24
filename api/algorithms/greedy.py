"""
Kargo İşletme Sistemi - Greedy (Açgözlü) Algoritma
Nearest Neighbor (En Yakın Komşu) ile rota oluşturma
"""

from typing import List, Dict, Any, Tuple
from .utils import calculate_distance_matrix, calculate_route_distance, get_district_by_id


def nearest_neighbor_algorithm(
    cargos: List[Dict[str, Any]],
    districts: List[Dict[str, Any]],
    vehicles: List[Dict[str, Any]],
    start_district_id: int = 12  # İzmit (default başlangıç)
) -> List[Dict[str, Any]]:
    """
    Nearest Neighbor algoritması ile rota oluşturur
    
    Args:
        cargos: Kargo listesi [{'district_id': 3, 'weight_kg': 200, ...}, ...]
        districts: İlçe listesi
        vehicles: Kullan available araçlar
        start_district_id: Başlangıç ilçesi ID (default İzmit = 12)
    
    Returns:
        List[Dict]: Rota bilgileriyle döndürür
        [
            {
                'vehicle_id': 1,
                'route': [12, 3, 6, 9, 12],
                'cargos': [...],
                'total_distance_km': 125.5,
                'total_weight_kg': 650
            },
            ...
        ]
    """
    # Mesafe matrisini hesapla
    distance_matrix = calculate_distance_matrix(districts)
    
    # Kargoları hedef ilçeye göre grupla
    cargo_by_district = {}
    for cargo in cargos:
        dist_id = cargo['district_id']
        if dist_id not in cargo_by_district:
            cargo_by_district[dist_id] = []
        cargo_by_district[dist_id].append(cargo)
    
    # Undelivered districts (ziyaret edilecek ilçeler)
    undelivered_districts = set(cargo_by_district.keys())
    
    routes = []
    vehicle_index = 0
    
    while undelivered_districts and vehicle_index < len(vehicles):
        vehicle = vehicles[vehicle_index]
        vehicle_capacity = vehicle['capacity_kg']
        current_weight = 0
        current_route = [start_district_id]
        route_cargos = []
        current_location = start_district_id
        
        # Bu araçla taşınabilecek kadar kargo al
        while undelivered_districts:
            # En yakın ziyaret edilmemiş ilçeyi bul
            nearest_district = None
            min_distance = float('inf')
            
            for district_id in list(undelivered_districts):
                distance = distance_matrix.get((current_location, district_id), float('inf'))
                if distance < min_distance:
                    min_distance = distance
                    nearest_district = district_id
            
            if nearest_district is None:
                break
            
            # Bu ilçedeki kargoların toplam ağırlığını kontrol et
            district_cargos = cargo_by_district[nearest_district]
            district_weight = sum(c['weight_kg'] * c.get('quantity', 1) for c in district_cargos)
            
            # Kapasiteye sığıyor mu?
            if current_weight + district_weight <= vehicle_capacity:
                # Kargoluğu ekle
                current_route.append(nearest_district)
                route_cargos.extend(district_cargos)
                current_weight += district_weight
                current_location = nearest_district
                undelivered_districts.remove(nearest_district)
            else:
                # Kapasite doldu, bu araç için rota tamamlandı
                break
        
        # Başlangıca dön (kapalı döngü)
        if current_route[-1] != start_district_id:
            current_route.append(start_district_id)
        
        # Rotayı kaydet
        total_distance = calculate_route_distance(current_route, distance_matrix)
        
        routes.append({
            'vehicle_id': vehicle['id'],
            'vehicle_type': vehicle['type_name'],
            'route': current_route,
            'cargos': route_cargos,
            'total_distance_km': total_distance,
            'total_weight_kg': current_weight,
            'capacity_utilization': round((current_weight / vehicle_capacity) * 100, 1)
        })
        
        vehicle_index += 1
    
    # Eğer hala teslim edilmemiş kargolar varsa ve araç kalmadıysa
    if undelivered_districts:
        print(f"⚠️  Uyarı: {len(undelivered_districts)} ilçeye kargo teslim edilemedi (araç yetersiz)")
    
    return routes


def create_tsp_route(district_ids: List[int], distance_matrix: Dict[tuple, float], start_id: int) -> List[int]:
    """
    Travelling Salesman Problem (TSP) için Nearest Neighbor
    Sadece sıralama yapar
    
    Args:
        district_ids: Ziyaret edilecek ilçe ID'leri
        distance_matrix: Mesafe matrisi
        start_id: Başlangıç ilçesi
    
    Returns:
        List[int]: Optimized route [start, d1, d2, ..., start]
    """
    unvisited = set(district_ids) - {start_id}
    route = [start_id]
    current = start_id
    
    while unvisited:
        # En yakın ziyaret edilmemiş ilçe
        nearest = min(unvisited, key=lambda x: distance_matrix.get((current, x), float('inf')))
        route.append(nearest)
        current = nearest
        unvisited.remove(nearest)
    
    # Başlangıca dön
    route.append(start_id)
    return route
