"""
VRP Solver - Vehicle Routing Problem Çözücü
Graph-based VRP çözümü
"""

from typing import List, Dict, Tuple
from .graph_structure import DeliveryGraph
from .graph_algorithms import (
    tsp_nearest_neighbor,
    tsp_2opt_improvement,
    tsp_optimal_small,
    find_clusters_on_graph,
    merge_clusters_on_route
)



def solve_vrp_graph_based(
    graph: DeliveryGraph,
    vehicles: List[Dict],
    start_id: int = 12,
    cost_per_km: float = 1.5
) -> List[Dict]:
    """
    Graph-based VRP çözümü
    
    Adımlar:
    1. Kargoları graph üzerinde kümele
    2. Aynı rota üzerindeki kümeleri birleştir
    3. Her küme için TSP çöz
    4. Araçları kümelere ata (kapasite + maliyet)
    5. Rotaları optimize et (2-opt)
    
    Args:
        graph: DeliveryGraph
        vehicles: Araç listesi
        start_id: Başlangıç düğümü
        cost_per_km: Km başı maliyet
    
    Returns:
        Rota listesi
    """
    
    print("\n" + "="*70)
    print("🗺️ GRAPH-BASED VRP SOLVER BAŞLIYOR")
    print("="*70)
    
    # 1. Coğrafi kümeleme
    print("\n📍 ADIM 1: Coğrafi Kümeleme...")
    clusters = find_clusters_on_graph(graph, max_distance=30.0)
    print(f"   ✓ {len(clusters)} küme oluşturuldu")
    
    # 2. Rota bazlı birleştirme
    print("\n🔗 ADIM 2: Rota Bazlı Birleştirme...")
    merged_clusters = merge_clusters_on_route(graph, clusters, start_id, detour_threshold=10.0)
    print(f"   ✓ {len(merged_clusters)} kümeye indirildi")
    
    # 3. Her küme için bilgi topla
    print("\n📊 ADIM 3: Küme Analizi...")
    cluster_info = []
    for i, cluster in enumerate(merged_clusters, 1):
        # UNIQUE NODE IDS - Tekrarları kaldır
        unique_node_ids = list(set(cluster))
        
        # Toplam ağırlık (unique node'lardan)
        total_weight = sum(graph.nodes[node_id].total_weight for node_id in unique_node_ids)
        
        # TSP ile optimal rota (unique node'larla)
        if len(unique_node_ids) <= 10:
            route, distance = tsp_optimal_small(graph, start_id, unique_node_ids)
        else:
            route, _ = tsp_nearest_neighbor(graph, start_id, unique_node_ids)
            route = tsp_2opt_improvement(graph, route)
            distance = graph.calculate_route_distance(route)
        
        cluster_info.append({
            'id': i,
            'node_ids': unique_node_ids,  # Unique IDs kaydet
            'route': route,
            'total_weight': total_weight,
            'distance': distance,
            'cost': graph.calculate_route_cost(route)
        })
        
        node_names = [graph.nodes[nid].name for nid in unique_node_ids]
        print(f"   Küme {i}: {', '.join(node_names)}")
        print(f"      Ağırlık: {total_weight:.1f} kg, Mesafe: {distance:.1f} km")
    
    # 4. Araç atama
    print("\n🚛 ADIM 4: Araç Atama...")
    routes = assign_vehicles_to_clusters(cluster_info, vehicles, graph)
    
    print(f"\n{'='*70}")
    print(f"✅ TOPLAM {len(routes)} ROTA OLUŞTURULDU")
    print(f"{'='*70}\n")
    
    return routes


def assign_vehicles_to_clusters(
    cluster_info: List[Dict],
    vehicles: List[Dict],
    graph: DeliveryGraph
) -> List[Dict]:
    """
    Kümelere araç ata
    
    Stratej:
    1. Kümeleri ağırlığa göre sırala (büyükten küçüğe)
    2. Araçları kapasiteye göre sırala (büyükten küçüğe)
    3. Her küme için en küçük uygun aracı bul
    
    Args:
        cluster_info: Küme bilgileri
        vehicles: Araç listesi
        graph: DeliveryGraph
    
    Returns:
        Rota listesi
    """
    
    # Kümeleri ağırlığa göre sırala
    sorted_clusters = sorted(cluster_info, key=lambda c: c['total_weight'], reverse=True)
    
    # Araçları kapasiteye göre sırala
    sorted_vehicles = sorted(vehicles, key=lambda v: v['capacity_kg'], reverse=True)
    
    routes = []
    used_vehicle_ids = set()
    
    for cluster in sorted_clusters:
        # KAPASİTE KONTROLÜ - Kapasite aşımını önle
        if cluster['total_weight'] <= 0:
            print(f"   ⚠️  Küme {cluster['id']} boş, atlanıyor")
            continue
        
        # En küçük uygun aracı bul
        suitable_vehicle = None
        
        for vehicle in sorted_vehicles:
            if vehicle['id'] in used_vehicle_ids:
                continue
            
            if vehicle['capacity_kg'] >= cluster['total_weight']:
                suitable_vehicle = vehicle
                break
        
        if not suitable_vehicle:
            print(f"   ⚠️  Küme {cluster['id']} için uygun araç bulunamadı! (Ağırlık: {cluster['total_weight']:.1f} kg)")
            continue
        
        # UNIQUE NODE IDS - Kargoları topla (tekrarsız)
        unique_node_ids = list(set(cluster['node_ids']))
        cargos = []
        cargo_ids_seen = set()
        
        for node_id in unique_node_ids:
            for cargo in graph.nodes[node_id].cargos:
                cargo_id = id(cargo)  # Kargo objesinin unique ID'si
                if cargo_id not in cargo_ids_seen:
                    cargos.append(cargo)
                    cargo_ids_seen.add(cargo_id)
        
        # Gerçek ağırlık kontrolü
        actual_weight = sum(c['weight_kg'] * c.get('quantity', 1) for c in cargos)
        
        # KAPASİTE AŞIMI KONTROLÜ
        if actual_weight > suitable_vehicle['capacity_kg']:
            print(f"   ❌ HATA: Kapasite aşımı! {actual_weight:.1f} kg > {suitable_vehicle['capacity_kg']:.0f} kg")
            print(f"      Küme {cluster['id']} atlanıyor")
            continue
        
        # Rota oluştur
        route = {
            'vehicle_id': suitable_vehicle['id'],
            'vehicle_type': suitable_vehicle.get('name', 'Unknown'),
            'vehicle': suitable_vehicle,
            'start_location': cluster['route'][0],
            'end_location': cluster['route'][-1],
            'path': cluster['route'],
            'cargos': cargos,
            'total_weight': actual_weight,  # Gerçek ağırlık kullan
            'distance': cluster['distance'],
            'cost': cluster['cost'],
            'utilization': (actual_weight / suitable_vehicle['capacity_kg']) * 100
        }
        
        routes.append(route)
        used_vehicle_ids.add(suitable_vehicle['id'])
        
        # Log
        route_names = [graph.nodes[nid].name for nid in cluster['route']]
        print(f"   ✓ Araç {suitable_vehicle['id']} ({suitable_vehicle.get('name', 'Unknown')})")
        print(f"      Rota: {' → '.join(route_names)}")
        print(f"      Kargolar: {len(cargos)} adet (unique)")
        print(f"      Ağırlık: {actual_weight:.1f} / {suitable_vehicle['capacity_kg']:.0f} kg")
        print(f"      Kullanım: {route['utilization']:.1f}%")
        print(f"      Mesafe: {cluster['distance']:.1f} km, Maliyet: {cluster['cost']:.2f} TL")
    
    return routes


def optimize_vrp_solution(routes: List[Dict], graph: DeliveryGraph) -> List[Dict]:
    """
    VRP çözümünü optimize et
    
    İyileştirmeler:
    1. 2-opt ile rotaları iyileştir
    2. Rota birleştirme dene (eğer kapasite varsa)
    3. Araç değiştirme dene (daha küçük araç kullanılabilir mi?)
    
    Args:
        routes: Mevcut rotalar
        graph: DeliveryGraph
    
    Returns:
        Optimize edilmiş rotalar
    """
    
    optimized_routes = []
    
    for route in routes:
        # 2-opt ile iyileştir
        improved_path = tsp_2opt_improvement(graph, route['path'])
        
        # Güncellenmiş bilgiler
        improved_route = route.copy()
        improved_route['path'] = improved_path
        improved_route['distance'] = graph.calculate_route_distance(improved_path)
        improved_route['cost'] = graph.calculate_route_cost(improved_path)
        
        optimized_routes.append(improved_route)
    
    return optimized_routes


def calculate_vrp_metrics(routes: List[Dict]) -> Dict:
    """
    VRP çözümünün metriklerini hesapla
    
    Returns:
        {
            'total_vehicles': 3,
            'total_distance': 150.5,
            'total_cost': 225.75,
            'avg_utilization': 85.2,
            'total_cargos': 15
        }
    """
    
    if not routes:
        return {
            'total_vehicles': 0,
            'total_distance': 0,
            'total_cost': 0,
            'avg_utilization': 0,
            'total_cargos': 0
        }
    
    total_distance = sum(r['distance'] for r in routes)
    total_cost = sum(r['cost'] for r in routes)
    avg_utilization = sum(r['utilization'] for r in routes) / len(routes)
    total_cargos = sum(len(r['cargos']) for r in routes)
    
    return {
        'total_vehicles': len(routes),
        'total_distance': round(total_distance, 2),
        'total_cost': round(total_cost, 2),
        'avg_utilization': round(avg_utilization, 1),
        'total_cargos': total_cargos
    }


print("✓ VRP Solver module loaded")
