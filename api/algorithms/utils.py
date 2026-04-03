"""
Kargo İşletme Sistemi - Algoritma Yardımcı Fonksiyonları
Mesafe hesaplama ve matris oluşturma
"""

import math
from typing import List, Dict, Any


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    İki nokta arasındaki mesafeyi Haversine formülü ile hesaplar (km cinsinden)
    
    Args:
        lat1, lon1: İlk noktanın koordinatları
        lat2, lon2: İkinci noktanın koordinatları
    
    Returns:
        float: Mesafe (km)
    """
    # Dünya yarıçapı (km)
    R = 6371.0
    
    # Dereceleri radyana çevir
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Farklar
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formülü
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)


def calculate_distance_matrix(districts: List[Dict[str, Any]]) -> Dict[tuple, float]:
    """
    Tüm ilçeler arası mesafe matrisini hesaplar
    
    Args:
        districts: İlçe listesi [{'id': 1, 'latitude': 40.xx, 'longitude': 29.xx}, ...]
    
    Returns:
        dict: {(district_id_1, district_id_2): distance_km}
    """
    distance_matrix = {}
    
    for i, dist1 in enumerate(districts):
        for dist2 in districts[i:]:  # Sadece üst üçgen + diagonal
            dist_id1 = dist1['id']
            dist_id2 = dist2['id']
            
            if dist_id1 == dist_id2:
                # Aynı ilçe - mesafe 0
                distance_matrix[(dist_id1, dist_id2)] = 0.0
            else:
                # Haversine ile hesapla
                distance = haversine_distance(
                    dist1['latitude'], dist1['longitude'],
                    dist2['latitude'], dist2['longitude']
                )
                
                # Simetrik matris - hem (i,j) hem (j,i)
                distance_matrix[(dist_id1, dist_id2)] = distance
                distance_matrix[(dist_id2, dist_id1)] = distance
    
    return distance_matrix


def calculate_route_distance(route: List[int], distance_matrix: Dict[tuple, float]) -> float:
    """
    Bir rotanın toplam mesafesini hesaplar
    
    Args:
        route: İlçe ID'lerinin sıralı listesi [12, 3, 6, 9, 12]
        distance_matrix: Mesafe matrisi
    
    Returns:
        float: Toplam mesafe (km)
    """
    total_distance = 0.0
    
    for i in range(len(route) - 1):
        from_id = route[i]
        to_id = route[i + 1]
        total_distance += distance_matrix.get((from_id, to_id), 0.0)
    
    return round(total_distance, 2)


def calculate_route_cost(distance_km: float, vehicle_type: Dict[str, Any]) -> float:
    """
    Rota maliyetini hesaplar
    
    Args:
        distance_km: Toplam mesafe
        vehicle_type: Araç tipi bilgisi {'rental_cost': 1000, 'cost_per_km': 5}
    
    Returns:
        float: Toplam maliyet (TL)
    """
    rental_cost = vehicle_type.get('rental_cost', 0)
    cost_per_km = vehicle_type.get('cost_per_km', 0)
    
    total_cost = rental_cost + (distance_km * cost_per_km)
    return round(total_cost, 2)


def get_district_by_id(districts: List[Dict], district_id: int) -> Dict:
    """
    ID'ye göre ilçe bilgisi döndürür
    
    Args:
        districts: İlçe listesi
        district_id: Aranan ilçe ID'si
    
    Returns:
        dict: İlçe bilgisi
    """
    for district in districts:
        if district['id'] == district_id:
            return district
    return None
