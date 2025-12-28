"""
Graph Algorithms - Dijkstra, TSP, Route Optimization
Graph üzerinde çalışan algoritmalar
"""

import heapq
import itertools
from typing import List, Dict, Tuple, Set
from .graph_structure import DeliveryGraph


def dijkstra_shortest_path(graph: DeliveryGraph, start_id: int, target_id: int) -> Tuple[List[int], float]:
    """
    Dijkstra algoritması ile en kısa yolu bul
    
    Args:
        graph: DeliveryGraph instance
        start_id: Başlangıç düğümü
        target_id: Hedef düğüm
    
    Returns:
        (route, total_weight): En kısa rota ve toplam ağırlık
    """
    
    # Başlangıç
    distances = {node_id: float('inf') for node_id in graph.nodes}
    distances[start_id] = 0
    
    previous = {node_id: None for node_id in graph.nodes}
    
    # Priority queue: (distance, node_id)
    pq = [(0, start_id)]
    visited = set()
    
    while pq:
        current_dist, current_id = heapq.heappop(pq)
        
        if current_id == target_id:
            break
        
        if current_id in visited:
            continue
        
        visited.add(current_id)
        
        # Komşuları kontrol et
        for neighbor_id, edge in graph.get_neighbors(current_id):
            if neighbor_id in visited:
                continue
            
            # Yeni mesafe
            new_dist = current_dist + edge.weight
            
            if new_dist < distances[neighbor_id]:
                distances[neighbor_id] = new_dist
                previous[neighbor_id] = current_id
                heapq.heappush(pq, (new_dist, neighbor_id))
    
    # Rotayı oluştur
    route = _reconstruct_path(previous, start_id, target_id)
    
    return route, distances[target_id]


def _reconstruct_path(previous: Dict, start_id: int, end_id: int) -> List[int]:
    """Rotayı yeniden oluştur"""
    path = []
    current = end_id
    
    while current is not None:
        path.append(current)
        current = previous[current]
    
    return list(reversed(path))


def tsp_nearest_neighbor(graph: DeliveryGraph, start_id: int, target_ids: List[int]) -> Tuple[List[int], float]:
    """
    TSP - Nearest Neighbor Heuristic
    
    Her adımda en yakın ziyaret edilmemiş düğümü seç
    
    Args:
        graph: DeliveryGraph
        start_id: Başlangıç
        target_ids: Ziyaret edilecek düğümler
    
    Returns:
        (route, total_cost): Rota ve toplam maliyet
    """
    
    if not target_ids:
        return [start_id], 0.0
    
    route = [start_id]
    unvisited = set(target_ids)
    current = start_id
    total_weight = 0.0
    
    while unvisited:
        # En yakın düğümü bul
        nearest = None
        min_weight = float('inf')
        
        for target_id in unvisited:
            edge = graph.get_edge(current, target_id)
            if edge and edge.weight < min_weight:
                min_weight = edge.weight
                nearest = target_id
        
        if nearest is None:
            break
        
        route.append(nearest)
        total_weight += min_weight
        current = nearest
        unvisited.remove(nearest)
    
    return route, total_weight


def tsp_2opt_improvement(graph: DeliveryGraph, route: List[int], max_iterations: int = 100) -> List[int]:
    """
    2-opt algoritması ile rota iyileştirme
    
    Mantık:
    1. Rotadaki iki kenarı seç
    2. Aralarını ters çevir
    3. Mesafe azalıyorsa kabul et
    4. İyileştirme kalmayana kadar devam et
    
    Args:
        graph: DeliveryGraph
        route: Mevcut rota
        max_iterations: Maksimum iterasyon
    
    Returns:
        İyileştirilmiş rota
    """
    
    if len(route) < 4:
        return route
    
    best_route = route[:]
    best_distance = graph.calculate_route_distance(best_route)
    improved = True
    iteration = 0
    
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1
        
        for i in range(1, len(best_route) - 2):
            for j in range(i + 1, len(best_route) - 1):
                # Rotayı ters çevir
                new_route = best_route[:i] + best_route[i:j+1][::-1] + best_route[j+1:]
                new_distance = graph.calculate_route_distance(new_route)
                
                if new_distance < best_distance:
                    best_route = new_route
                    best_distance = new_distance
                    improved = True
                    break
            
            if improved:
                break
    
    return best_route


def tsp_optimal_small(graph: DeliveryGraph, start_id: int, target_ids: List[int]) -> Tuple[List[int], float]:
    """
    TSP - Optimal (Brute Force)
    
    Küçük problemler için tüm permütasyonları dene
    Sadece 10'dan az düğüm için kullan!
    
    Args:
        graph: DeliveryGraph
        start_id: Başlangıç
        target_ids: Ziyaret edilecek düğümler (max 10)
    
    Returns:
        (route, total_distance): En iyi rota ve mesafe
    """
    
    if len(target_ids) > 10:
        # Çok büyük, nearest neighbor kullan
        return tsp_nearest_neighbor(graph, start_id, target_ids)
    
    best_route = None
    best_distance = float('inf')
    
    # Tüm permütasyonları dene
    for perm in itertools.permutations(target_ids):
        route = [start_id] + list(perm)
        distance = graph.calculate_route_distance(route)
        
        if distance < best_distance:
            best_distance = distance
            best_route = route
    
    return best_route, best_distance


def find_clusters_on_graph(graph: DeliveryGraph, max_distance: float = 30.0) -> List[Set[int]]:
    """
    Graph üzerinde coğrafi kümeleme
    
    Yakın düğümleri (max_distance içinde) aynı kümeye al
    
    Args:
        graph: DeliveryGraph
        max_distance: Maksimum küme mesafesi
    
    Returns:
        Küme listesi (her küme bir set of node IDs)
    """
    
    cargo_nodes = graph.get_cargo_nodes()
    clusters = []
    processed = set()
    
    for seed_node in cargo_nodes:
        if seed_node.id in processed:
            continue
        
        # Yeni küme
        cluster = {seed_node.id}
        processed.add(seed_node.id)
        
        # Yakın düğümleri bul
        for other_node in cargo_nodes:
            if other_node.id in processed:
                continue
            
            # Mesafe kontrolü
            edge = graph.get_edge(seed_node.id, other_node.id)
            if edge and edge.distance <= max_distance:
                cluster.add(other_node.id)
                processed.add(other_node.id)
        
        clusters.append(cluster)
    
    return clusters


def merge_clusters_on_route(graph: DeliveryGraph, clusters: List[Set[int]], 
                            start_id: int, detour_threshold: float = 10.0) -> List[Set[int]]:
    """
    Aynı rota üzerindeki kümeleri birleştir
    
    Args:
        graph: DeliveryGraph
        clusters: Mevcut kümeler
        start_id: Başlangıç düğümü
        detour_threshold: Maksimum sapma (km)
    
    Returns:
        Birleştirilmiş kümeler
    """
    
    if len(clusters) <= 1:
        return clusters
    
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
            
            # Aynı rota üzerinde mi?
            if _is_on_same_route(graph, cluster1, cluster2, start_id, detour_threshold):
                merged_cluster.update(cluster2)
                processed.add(j)
        
        merged.append(merged_cluster)
    
    return merged


def _is_on_same_route(graph: DeliveryGraph, cluster1: Set[int], cluster2: Set[int],
                     start_id: int, detour_threshold: float) -> bool:
    """İki küme aynı rota üzerinde mi?"""
    
    # Küme temsilcileri (ilk eleman)
    id1 = next(iter(cluster1))
    id2 = next(iter(cluster2))
    
    # Direkt mesafe
    edge1 = graph.get_edge(start_id, id1)
    edge2 = graph.get_edge(start_id, id2)
    
    if not edge1 or not edge2:
        return False
    
    direct_dist = edge1.distance + edge2.distance
    
    # Dolaylı mesafe (birinden diğerine)
    edge_between = graph.get_edge(id1, id2)
    if not edge_between:
        return False
    
    indirect_dist = edge1.distance + edge_between.distance
    
    # Sapma
    detour = abs(indirect_dist - direct_dist)
    
    return detour <= detour_threshold


print("✓ Graph Algorithms module loaded")
