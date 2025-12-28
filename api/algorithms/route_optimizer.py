"""
Route Optimizer - Rota Optimizasyonu
TSP ve yol üstü yükleme optimizasyonu
"""

from typing import List, Dict, Any, Tuple
from .utils import calculate_route_distance
import itertools


def optimize_route_tsp(district_ids: List[int], distance_matrix: Dict, start_id: int) -> List[int]:
    """
    Travelling Salesman Problem - Nearest Neighbor
    
    Args:
        district_ids: Ziyaret edilecek ilçeler
        distance_matrix: Mesafe matrisi
        start_id: Başlangıç ilçesi
    
    Returns:
        Optimize edilmiş rota [start, d1, d2, ..., start]
    """
    
    if not district_ids:
        return [start_id]
    
    unvisited = set(district_ids) - {start_id}
    route = [start_id]
    current = start_id
    
    while unvisited:
        # En yakın ziyaret edilmemiş ilçe
        nearest = min(unvisited, key=lambda x: distance_matrix.get((current, x), float('inf')))
        route.append(nearest)
        current = nearest
        unvisited.remove(nearest)
    
    return route


def optimize_route_2opt(route: List[int], distance_matrix: Dict, max_iterations: int = 100) -> List[int]:
    """
    2-opt algoritması ile rota iyileştirme
    
    Mantık:
    1. Rotadaki iki kenarı değiştir
    2. Mesafe azalıyorsa kabul et
    3. İyileştirme kalmayana kadar devam et
    """
    
    if len(route) < 4:
        return route
    
    best_route = route[:]
    best_distance = calculate_route_distance(best_route, distance_matrix)
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                # Rotayı ters çevir
                new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                new_distance = calculate_route_distance(new_route, distance_matrix)
                
                if new_distance < best_distance:
                    best_route = new_route
                    best_distance = new_distance
                    improved = True
                    break
            
            if improved:
                break
    
    return best_route


def find_nearby_districts(from_id: int, to_id: int, all_districts: List[Dict], 
                         distance_matrix: Dict, max_detour_km: float = 10.0) -> List[int]:
    """
    İki ilçe arasındaki yol üstü ilçeleri bul
    
    Args:
        from_id: Başlangıç ilçesi
        to_id: Bitiş ilçesi
        all_districts: Tüm ilçeler
        distance_matrix: Mesafe matrisi
        max_detour_km: Maksimum sapma mesafesi
    
    Returns:
        Yol üstündeki ilçe ID'leri
    """
    
    direct_distance = distance_matrix.get((from_id, to_id), float('inf'))
    nearby = []
    
    for district in all_districts:
        dist_id = district['id']
        
        # Başlangıç ve bitiş değilse
        if dist_id in [from_id, to_id]:
            continue
        
        # Bu ilçe üzerinden gidersek mesafe ne olur?
        detour_distance = (distance_matrix.get((from_id, dist_id), float('inf')) + 
                          distance_matrix.get((dist_id, to_id), float('inf')))
        
        # Sapma miktarı
        detour = detour_distance - direct_distance
        
        if detour <= max_detour_km:
            nearby.append({
                'id': dist_id,
                'detour_km': detour,
                'detour_distance': detour_distance
            })
    
    # Sapma miktarına göre sırala
    nearby.sort(key=lambda x: x['detour_km'])
    
    return [n['id'] for n in nearby]


def optimize_with_enroute_pickup(route: Dict, available_cargos: List[Dict], 
                                 districts: List[Dict], distance_matrix: Dict,
                                 cost_per_km: float, max_detour_km: float = 10.0) -> Dict:
    """
    Yol üstü kargo alma optimizasyonu
    
    Args:
        route: Mevcut rota
        available_cargos: Henüz atanmamış kargolar
        districts: Tüm ilçeler
        distance_matrix: Mesafe matrisi
        cost_per_km: Km başı maliyet
        max_detour_km: Maksimum sapma
    
    Returns:
        İyileştirilmiş rota veya orijinal rota
    """
    
    if not available_cargos:
        return route
    
    current_path = route.get('path', [])
    current_weight = route.get('total_weight', 0)
    vehicle = route.get('vehicle', {})
    vehicle_capacity = vehicle.get('capacity_kg', 0)
    
    improvements = []
    
    # Her segment için kontrol et
    for i in range(len(current_path) - 1):
        from_id = current_path[i]
        to_id = current_path[i + 1]
        
        # Yol üstündeki ilçeler
        nearby_ids = find_nearby_districts(from_id, to_id, districts, distance_matrix, max_detour_km)
        
        for nearby_id in nearby_ids:
            # Bu ilçede kargo var mı?
            nearby_cargos = [c for c in available_cargos if c['district_id'] == nearby_id]
            
            if not nearby_cargos:
                continue
            
            # Toplam ağırlık
            cargo_weight = sum(c['weight_kg'] * c.get('quantity', 1) for c in nearby_cargos)
            
            # Kapasite kontrolü
            if current_weight + cargo_weight > vehicle_capacity:
                continue
            
            # Maliyet analizi
            original_distance = distance_matrix.get((from_id, to_id), 0)
            new_distance = (distance_matrix.get((from_id, nearby_id), 0) + 
                          distance_matrix.get((nearby_id, to_id), 0))
            
            distance_increase = new_distance - original_distance
            cost_increase = distance_increase * cost_per_km
            
            # Kargo başına ek maliyet
            cost_per_new_cargo = cost_increase / len(nearby_cargos) if nearby_cargos else 0
            
            # Eşik değer: 50 TL/kargo
            if cost_per_new_cargo < 50:
                improvements.append({
                    'insert_at': i + 1,
                    'district_id': nearby_id,
                    'cargos': nearby_cargos,
                    'cost_increase': cost_increase,
                    'distance_increase': distance_increase,
                    'cost_per_cargo': cost_per_new_cargo
                })
    
    # En iyi iyileştirmeyi uygula
    if improvements:
        best = min(improvements, key=lambda x: x['cost_per_cargo'])
        
        # Rotayı güncelle
        new_path = (current_path[:best['insert_at']] + 
                   [best['district_id']] + 
                   current_path[best['insert_at']:])
        
        new_route = route.copy()
        new_route['path'] = new_path
        new_route['cargos'] = route.get('cargos', []) + best['cargos']
        new_route['total_weight'] = current_weight + sum(c['weight_kg'] for c in best['cargos'])
        new_route['distance'] = route.get('distance', 0) + best['distance_increase']
        new_route['enroute_pickup'] = True
        new_route['pickup_info'] = best
        
        return new_route
    
    return route


def create_route_from_assignment(assignment: Dict, districts: List[Dict], 
                                 distance_matrix: Dict, start_location: int = None) -> Dict:
    """
    Bin packing atama sonucundan rota oluştur
    
    Args:
        assignment: Bin packing sonucu
        districts: İlçeler
        distance_matrix: Mesafe matrisi
        start_location: Başlangıç konumu
    
    Returns:
        Rota bilgisi
    """
    
    vehicle = assignment['vehicle']
    cargos = assignment['cargos']
    
    # Başlangıç konumu
    if start_location is None:
        start_location = vehicle.get('current_location_district_id', 12)
    
    # Ziyaret edilecek ilçeler
    district_ids = list(set(c['district_id'] for c in cargos))
    
    # Rota optimizasyonu (TSP)
    optimized_path = optimize_route_tsp(district_ids, distance_matrix, start_location)
    
    # 2-opt ile iyileştir
    optimized_path = optimize_route_2opt(optimized_path, distance_matrix)
    
    # Mesafe hesapla
    total_distance = calculate_route_distance(optimized_path, distance_matrix)
    
    return {
        'vehicle_id': vehicle['id'],
        'vehicle': vehicle,
        'path': optimized_path,
        'cargos': cargos,
        'total_weight': assignment['total_weight'],
        'distance': total_distance,
        'start_location': start_location,
        'end_location': optimized_path[-1] if optimized_path else start_location,
        'utilization': assignment['utilization']
    }


print("✓ Route Optimizer module loaded")
