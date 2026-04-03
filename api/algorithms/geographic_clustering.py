"""
Geographic Clustering - Kargoları Coğrafi Olarak Kümele
Yakın ilçelerdeki kargoları birleştir
"""


from typing import List, Dict, Any, Set


def cluster_cargos_by_geography(
    cargos: List[Dict],
    districts: List[Dict],
    distance_matrix: Dict,
    max_cluster_distance: float = 30.0
) -> List[Dict]:
    """
    Kargoları coğrafi yakınlığa göre kümele
    
    Mantık:
    1. Her kargo için yakın ilçeleri bul
    2. Yakın kargoları aynı kümeye al
    3. Yol üstündeki ilçeleri birleştir
    
    Args:
        cargos: Kargo listesi
        districts: İlçe listesi
        distance_matrix: Mesafe matrisi
        max_cluster_distance: Maksimum küme mesafesi (km)
    
    Returns:
        Küme listesi
    """
    
    print(f"\n🗺️ GEOGRAPHIC CLUSTERING BAŞLIYOR")
    print(f"   Eşik mesafe: {max_cluster_distance} km")
    
    # Kargoları ilçelere göre grupla
    cargo_by_district = {}
    for cargo in cargos:
        dist_id = cargo['district_id']
        if dist_id not in cargo_by_district:
            cargo_by_district[dist_id] = []
        cargo_by_district[dist_id].append(cargo)
    
    # İlçe ID'leri
    district_ids = list(cargo_by_district.keys())
    
    # Kümeleme
    clusters = []
    processed = set()
    
    for seed_id in district_ids:
        if seed_id in processed:
            continue
        
        # Yeni küme başlat
        cluster = {
            'seed_district': seed_id,
            'district_ids': [seed_id],
            'cargos': cargo_by_district[seed_id].copy(),
            'total_weight': sum(c['weight_kg'] * c.get('quantity', 1) 
                              for c in cargo_by_district[seed_id])
        }
        processed.add(seed_id)
        
        # Yakın ilçeleri bul ve ekle
        for other_id in district_ids:
            if other_id in processed:
                continue
            
            # Mesafe kontrolü
            dist = distance_matrix.get((seed_id, other_id), float('inf'))
            
            if dist <= max_cluster_distance:
                # Kümeye ekle
                cluster['district_ids'].append(other_id)
                cluster['cargos'].extend(cargo_by_district[other_id])
                cluster['total_weight'] += sum(c['weight_kg'] * c.get('quantity', 1) 
                                              for c in cargo_by_district[other_id])
                processed.add(other_id)
        
        clusters.append(cluster)
    
    # Sonuç
    print(f"\n📊 KÜMELEME SONUCU:")
    for i, cluster in enumerate(clusters, 1):
        district_names = [get_district_name(districts, d_id) for d_id in cluster['district_ids']]
        print(f"   Küme {i}: {', '.join(district_names)}")
        print(f"      Toplam Ağırlık: {cluster['total_weight']:.1f} kg")
        print(f"      Kargo Sayısı: {len(cluster['cargos'])}")
    
    return clusters


def get_district_name(districts: List[Dict], district_id: int) -> str:
    """İlçe adını getir"""
    for d in districts:
        if d['id'] == district_id:
            return d['name']
    return f"İlçe {district_id}"


def sort_districts_by_route(
    district_ids: List[int],
    distance_matrix: Dict,
    start_id: int = 12
) -> List[int]:
    """
    İlçeleri rota sırasına göre sırala (en yakın komşu)
    
    Örnek:
    İzmit (12) → Gebze (6) → Pendik (3)
    
    Args:
        district_ids: Sıralanacak ilçe ID'leri
        distance_matrix: Mesafe matrisi
        start_id: Başlangıç ilçesi (varsayılan: İzmit)
    
    Returns:
        Sıralı ilçe ID listesi
    """
    
    if not district_ids:
        return []
    
    sorted_route = []
    current = start_id
    remaining = set(district_ids)
    
    while remaining:
        # En yakın ilçe
        nearest = min(remaining, 
                     key=lambda d: distance_matrix.get((current, d), float('inf')))
        sorted_route.append(nearest)
        current = nearest
        remaining.remove(nearest)
    
    return sorted_route


def merge_clusters_on_same_route(
    clusters: List[Dict],
    districts: List[Dict],
    distance_matrix: Dict,
    start_id: int = 12
) -> List[Dict]:
    """
    Aynı rota üzerindeki kümeleri birleştir
    
    Örnek:
    Küme 1: Gebze
    Küme 2: Pendik
    → Gebze yol üstünde → Birleştir
    """
    
    if len(clusters) <= 1:
        return clusters
    
    print(f"\n🔗 ROTA BAZLI BİRLEŞTİRME...")
    
    merged = []
    processed = set()
    
    for i, cluster1 in enumerate(clusters):
        if i in processed:
            continue
        
        merged_cluster = cluster1.copy()
        processed.add(i)
        
        # Diğer kümelerle karşılaştır
        for j, cluster2 in enumerate(clusters[i+1:], start=i+1):
            if j in processed:
                continue
            
            # İki küme aynı rota üzerinde mi?
            if is_on_same_route(cluster1, cluster2, distance_matrix, start_id):
                # Birleştir
                merged_cluster['district_ids'].extend(cluster2['district_ids'])
                merged_cluster['cargos'].extend(cluster2['cargos'])
                merged_cluster['total_weight'] += cluster2['total_weight']
                processed.add(j)
                
                print(f"   ✓ Küme {i+1} + Küme {j+1} birleştirildi (aynı rota)")
        
        merged.append(merged_cluster)
    
    return merged


def is_on_same_route(
    cluster1: Dict,
    cluster2: Dict,
    distance_matrix: Dict,
    start_id: int,
    detour_threshold: float = 10.0
) -> bool:
    """
    İki küme aynı rota üzerinde mi kontrol et
    
    Mantık:
    - Direkt mesafe: A → B
    - Dolaylı mesafe: A → C → B
    - Eğer fark < 10km → Aynı rota üzerinde
    """
    
    # Küme merkezleri (seed district)
    id1 = cluster1['seed_district']
    id2 = cluster2['seed_district']
    
    # Direkt mesafe
    direct_dist = (distance_matrix.get((start_id, id1), 0) + 
                   distance_matrix.get((start_id, id2), 0))
    
    # Dolaylı mesafe (birinden diğerine)
    indirect_dist = (distance_matrix.get((start_id, id1), 0) + 
                     distance_matrix.get((id1, id2), 0))
    
    # Sapma
    detour = abs(indirect_dist - direct_dist)
    
    return detour <= detour_threshold


print("✓ Geographic Clustering module loaded")
