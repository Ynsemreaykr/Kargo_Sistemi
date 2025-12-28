"""
Route-Aware Bin Packing - Coğrafi Kümelere Göre Araç Atama
Yol üstündeki kargoları tek araçta birleştir
"""

from typing import List, Dict, Any, Set
from .geographic_clustering import (
    cluster_cargos_by_geography,
    sort_districts_by_route,
    merge_clusters_on_same_route
)


def route_aware_bin_packing(
    cargos: List[Dict],
    vehicles: List[Dict],
    districts: List[Dict],
    distance_matrix: Dict
) -> List[Dict]:
    """
    Coğrafi konuma duyarlı bin packing
    
    Mantık:
    1. Kargoları coğrafi olarak kümele
    2. Aynı rota üzerindeki kümeleri birleştir
    3. Her küme için en uygun aracı seç
    4. İlçeleri rota sırasına göre sırala
    
    Args:
        cargos: Kargo listesi
        vehicles: Araç listesi
        districts: İlçe listesi
        distance_matrix: Mesafe matrisi
    
    Returns:
        Araç atamaları (bins)
    """
    
    print("\n" + "="*70)
    print("🗺️ ROUTE-AWARE BIN PACKING BAŞLIYOR")
    print("="*70)
    
    # 1. Coğrafi kümeleme
    clusters = cluster_cargos_by_geography(cargos, districts, distance_matrix)
    
    # 2. Aynı rota üzerindeki kümeleri birleştir
    merged_clusters = merge_clusters_on_same_route(clusters, districts, distance_matrix)
    
    print(f"\n📦 BİRLEŞTİRME SONRASI: {len(merged_clusters)} küme")
    
    # 3. Kümeleri ağırlığa göre sırala (büyükten küçüğe)
    sorted_clusters = sorted(merged_clusters, 
                            key=lambda c: c['total_weight'], 
                            reverse=True)
    
    # 4. Her küme için araç ata
    bins = []
    used_vehicle_ids = set()
    
    for cluster in sorted_clusters:
        # En küçük uygun aracı bul
        suitable_vehicle = find_smallest_suitable_vehicle(
            cluster['total_weight'],
            vehicles,
            used_vehicle_ids
        )
        
        if not suitable_vehicle:
            print(f"   ⚠️  Küme için uygun araç bulunamadı: {cluster['total_weight']:.1f} kg")
            continue
        
        # İlçeleri rota sırasına göre sırala
        sorted_district_ids = sort_districts_by_route(
            cluster['district_ids'],
            distance_matrix
        )
        
        # Bin oluştur
        bin_item = {
            'vehicle': suitable_vehicle,
            'cargos': cluster['cargos'],
            'district_ids': sorted_district_ids,
            'total_weight': cluster['total_weight'],
            'remaining_capacity': suitable_vehicle['capacity_kg'] - cluster['total_weight'],
            'utilization': (cluster['total_weight'] / suitable_vehicle['capacity_kg']) * 100
        }
        
        bins.append(bin_item)
        used_vehicle_ids.add(suitable_vehicle['id'])
        
        # Log
        district_names = [get_district_name(districts, d_id) for d_id in sorted_district_ids]
        print(f"\n   ✓ Araç {suitable_vehicle['id']} ({suitable_vehicle.get('name', 'Unknown')})")
        print(f"      Rota: {' → '.join(district_names)}")
        print(f"      Ağırlık: {cluster['total_weight']:.1f} / {suitable_vehicle['capacity_kg']:.0f} kg")
        print(f"      Kullanım: {bin_item['utilization']:.1f}%")
    
    print(f"\n{'='*70}")
    print(f"✅ TOPLAM {len(bins)} ARAÇ ATANDI")
    print(f"{'='*70}\n")
    
    return bins


def find_smallest_suitable_vehicle(
    required_capacity: float,
    vehicles: List[Dict],
    used_vehicle_ids: Set[int]
) -> Dict:
    """
    Gerekli kapasiteyi karşılayan en küçük aracı bul
    
    Args:
        required_capacity: Gerekli kapasite (kg)
        vehicles: Mevcut araçlar
        used_vehicle_ids: Kullanılmış araç ID'leri
    
    Returns:
        En uygun araç veya None
    """
    
    # Kullanılmayan araçlar
    available_vehicles = [v for v in vehicles if v['id'] not in used_vehicle_ids]
    
    # Kapasiteye göre sırala (küçükten büyüğe)
    sorted_vehicles = sorted(available_vehicles, key=lambda v: v['capacity_kg'])
    
    # En küçük uygun aracı bul
    for vehicle in sorted_vehicles:
        if vehicle['capacity_kg'] >= required_capacity:
            return vehicle
    
    # Hiçbiri uygun değil - en büyük aracı döndür
    if sorted_vehicles:
        return sorted_vehicles[-1]
    
    return None


def get_district_name(districts: List[Dict], district_id: int) -> str:
    """İlçe adını getir"""
    for d in districts:
        if d['id'] == district_id:
            return d['name']
    return f"İlçe {district_id}"


def calculate_bin_packing_quality(bins: List[Dict]) -> Dict:
    """
    Bin packing kalitesini değerlendir
    
    Returns:
        {
            'avg_utilization': 85.5,
            'total_vehicles': 3,
            'total_weight': 1500.0,
            'wasted_capacity': 200.0
        }
    """
    
    if not bins:
        return {
            'avg_utilization': 0,
            'total_vehicles': 0,
            'total_weight': 0,
            'wasted_capacity': 0
        }
    
    total_utilization = sum(b['utilization'] for b in bins)
    avg_utilization = total_utilization / len(bins)
    
    total_weight = sum(b['total_weight'] for b in bins)
    total_capacity = sum(b['vehicle']['capacity_kg'] for b in bins)
    wasted_capacity = total_capacity - total_weight
    
    return {
        'avg_utilization': round(avg_utilization, 1),
        'total_vehicles': len(bins),
        'total_weight': round(total_weight, 1),
        'wasted_capacity': round(wasted_capacity, 1)
    }


print("✓ Route-Aware Bin Packing module loaded")
