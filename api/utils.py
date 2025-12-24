"""
Kargo İşletme Sistemi - Yardımcı Fonksiyonlar
Mesafe hesaplama ve dummy rota üretimi
"""

import math
import random
from typing import List, Dict, Tuple

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    İki nokta arasındaki kuş uçuşu mesafeyi hesapla (Haversine formülü)
    
    Args:
        lat1, lon1: Birinci noktanın koordinatları
        lat2, lon2: İkinci noktanın koordinatları
    
    Returns:
        Kilometre cinsinden mesafe
    """
    # Dünya yarıçapı (km)
    R = 6371.0
    
    # Dereceyi radyana çevir
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Farkları hesapla
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine formülü
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return round(distance, 2)

def calculate_route_distance(districts: List[Dict], route_order: List[int]) -> float:
    """
    Rota üzerindeki toplam mesafeyi hesapla
    
    Args:
        districts: İlçe bilgileri (id, latitude, longitude içermeli)
        route_order: Rota sırası (district_id listesi)
    
    Returns:
        Toplam mesafe (km)
    """
    if len(route_order) < 2:
        return 0.0
    
    # İlçeleri ID'ye göre dictionary'e çevir
    district_map = {d['id']: d for d in districts}
    
    total_distance = 0.0
    for i in range(len(route_order) - 1):
        d1 = district_map[route_order[i]]
        d2 = district_map[route_order[i + 1]]
        total_distance += haversine_distance(
            d1['latitude'], d1['longitude'],
            d2['latitude'], d2['longitude']
        )
    
    return round(total_distance, 2)

def generate_dummy_routes(cargos: List[Dict], vehicles: List[Dict], 
                         districts: List[Dict], cost_per_km: float) -> List[Dict]:
    """
    AŞAMA 1 için dummy (sahte) rotalar üret
    
    Bu fonksiyon gerçek algoritma DEĞİLDİR. Sadece test amaçlıdır.
    AŞAMA 3'te gerçek algoritma ile değiştirilecektir.
    
    Mantık:
    1. Her kargo için rastgele bir araç ata
    2. Her araç için atanan kargoların ilçelerini topla
    3. Açık rota oluştur: Başlangıç → Hedef ilçeler (dönüş yok)
    4. Mesafe ve maliyeti hesapla
    
    Args:
        cargos: Kargo listesi (district_id, weight_kg, quantity)
        vehicles: Araç listesi (id, vehicle_type_id, capacity_kg, rental_cost)
        districts: İlçe listesi (id, name, latitude, longitude)
        cost_per_km: Kilometre başına maliyet
    
    Returns:
        Rota listesi (vehicle_id, district_ids, distance, cost)
    """
    # İlçeleri ID'ye göre dictionary'e çevir
    district_map = {d['id']: d for d in districts}
    
    # Her araç için ilçe listesi
    vehicle_routes = {v['id']: {'vehicle': v, 'districts': set()} for v in vehicles}
    
    # Kargoları rastgele araçlara ata
    for cargo in cargos:
        # Rastgele bir araç seç
        vehicle = random.choice(vehicles)
        vehicle_routes[vehicle['id']]['districts'].add(cargo['district_id'])
    
    # Rotaları oluştur
    routes = []
    for vehicle_id, route_data in vehicle_routes.items():
        if not route_data['districts']:
            # Bu araca kargo atanmamış, atla
            continue
        
        vehicle = route_data['vehicle']
        district_ids = list(route_data['districts'])
        
        # Açık rota: Sadece kargoları teslim et, başlangıca dönme
        route_order = district_ids
        
        # Mesafeyi hesapla
        distance = calculate_route_distance(districts, route_order)
        
        # Maliyeti hesapla: (mesafe × km_maliyeti) + araç_kiralama_maliyeti
        # Decimal ve float karışımını önlemek için float'a çevir
        cost = (float(distance) * float(cost_per_km)) + float(vehicle['rental_cost'])
        cost = round(cost, 2)
        
        routes.append({
            'vehicle_id': vehicle_id,
            'district_ids': route_order,
            'distance': distance,
            'cost': cost
        })
    
    return routes

def create_route_geometry(districts: List[Dict], route_order: List[int]) -> Dict:
    """
    Rota geometrisini GeoJSON formatında oluştur (harita görselleştirme için)
    
    Args:
        districts: İlçe listesi
        route_order: Rota sırası (district_id listesi)
    
    Returns:
        GeoJSON LineString objesi
    """
    district_map = {d['id']: d for d in districts}
    
    coordinates = []
    for district_id in route_order:
        d = district_map[district_id]
        # GeoJSON formatı: [longitude, latitude]
        coordinates.append([d['longitude'], d['latitude']])
    
    return {
        'type': 'LineString',
        'coordinates': coordinates
    }
