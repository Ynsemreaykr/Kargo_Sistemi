"""
Graph-Based Optimization Engine - YENİ VERSİYON
Eski optimization_engine.py yerine graph-based sistem
"""

from typing import List, Dict, Any
from .graph_structure import DeliveryGraph
from .vrp_solver import solve_vrp_graph_based, calculate_vrp_metrics
from .utils import calculate_distance_matrix


def full_optimization_graph_based(
    cargos: List[Dict],
    districts: List[Dict],
    own_vehicles: List[Dict],
    available_vehicle_types: List[Dict],
    cost_per_km: float,
    distance_matrix: Dict = None
) -> Dict:
    """
    GRAPH-BASED TAM OPTİMİZASYON
    
    Eski sistem yerine graph teorisi ile çalışan yeni sistem
    
    Args:
        cargos: Kargo listesi
        districts: İlçe listesi
        own_vehicles: Kullanıcının kendi araçları
        available_vehicle_types: Kiralanabilir araç tipleri
        cost_per_km: Km başı yakıt maliyeti
        distance_matrix: Mesafe matrisi (opsiyonel)
    
    Returns:
        En optimal çözüm
    """
    
    print("\n" + "="*70)
    print("🚀 GRAPH-BASED OPTİMİZASYON SİSTEMİ")
    print("="*70)
    
    # Mesafe matrisi yoksa hesapla
    if distance_matrix is None:
        distance_matrix = calculate_distance_matrix(districts)
    
    # 1. Graph oluştur
    print("\n📊 ADIM 1: Graph Oluşturuluyor...")
    graph = DeliveryGraph(districts, distance_matrix, cost_per_km)
    graph.add_cargos(cargos)
    
    cargo_nodes = graph.get_cargo_nodes()
    total_weight = sum(node.total_weight for node in cargo_nodes)
    
    print(f"   ✓ {len(graph.nodes)} düğüm, {len(graph.edges)} kenar")
    print(f"   ✓ {len(cargo_nodes)} ilçede kargo var")
    print(f"   ✓ Toplam ağırlık: {total_weight:.1f} kg")
    
    # 2. Tüm araç kombinasyonlarını dene
    print("\n🚛 ADIM 2: Araç Kombinasyonları Deneniyor...")
    
    all_solutions = []
    
    # Kombinasyon 1: Sadece kendi araçlar
    print("\n   [1] Sadece kendi araçlar...")
    try:
        routes = solve_vrp_graph_based(graph, own_vehicles, start_id=12, cost_per_km=cost_per_km)
        metrics = calculate_vrp_metrics(routes)
        
        all_solutions.append({
            'strategy': 'OWN_ONLY',
            'description': 'Sadece kendi 3 araç',
            'routes': routes,
            'metrics': metrics,
            'rental_count': 0,
            'rental_cost': 0
        })
        
        print(f"      ✓ {metrics['total_vehicles']} araç, {metrics['total_cost']:.2f} TL")
    except Exception as e:
        print(f"      ❌ Hata: {e}")
    
    # Kombinasyon 2: Kendi + kiralık kombinasyonları
    for rental_count in range(1, 4):
        print(f"\n   [{rental_count + 1}] Kendi araçlar + {rental_count} kiralık...")
        
        # Her araç tipinden dene
        for vehicle_type in available_vehicle_types:
            try:
                # Kiralık araçları ekle
                rental_vehicles = [vehicle_type.copy() for _ in range(rental_count)]
                all_vehicles = own_vehicles + rental_vehicles
                
                routes = solve_vrp_graph_based(graph, all_vehicles, start_id=12, cost_per_km=cost_per_km)
                metrics = calculate_vrp_metrics(routes)
                
                # Kiralama maliyeti
                rental_cost = rental_count * vehicle_type.get('rental_cost', 0)
                total_cost = metrics['total_cost'] + rental_cost
                
                all_solutions.append({
                    'strategy': f'OWN_PLUS_{rental_count}',
                    'description': f'Kendi + {rental_count}x {vehicle_type["name"]}',
                    'routes': routes,
                    'metrics': metrics,
                    'rental_count': rental_count,
                    'rental_cost': rental_cost,
                    'total_cost': total_cost
                })
                
                print(f"      ✓ {vehicle_type['name']}: {total_cost:.2f} TL")
            except Exception as e:
                print(f"      ❌ {vehicle_type['name']}: {e}")
    
    # Kombinasyon 3: Tek optimal kiralık
    print(f"\n   [Optimal] Tek kiralık araç...")
    for vehicle_type in sorted(available_vehicle_types, key=lambda v: v['capacity_kg']):
        if vehicle_type['capacity_kg'] >= total_weight:
            try:
                routes = solve_vrp_graph_based(graph, [vehicle_type], start_id=12, cost_per_km=cost_per_km)
                metrics = calculate_vrp_metrics(routes)
                
                rental_cost = vehicle_type.get('rental_cost', 0)
                total_cost = metrics['total_cost'] + rental_cost
                
                all_solutions.append({
                    'strategy': 'SINGLE_OPTIMAL',
                    'description': f'Tek {vehicle_type["name"]} (optimal)',
                    'routes': routes,
                    'metrics': metrics,
                    'rental_count': 1,
                    'rental_cost': rental_cost,
                    'total_cost': total_cost
                })
                
                print(f"      ✓ {vehicle_type['name']}: {total_cost:.2f} TL")
                break
            except Exception as e:
                print(f"      ❌ {vehicle_type['name']}: {e}")
    
    # 3. En iyi çözümü seç
    print("\n🎯 ADIM 3: En İyi Çözüm Seçiliyor...")
    
    if not all_solutions:
        print("\n❌ HİÇBİR ÇÖZÜM BULUNAMADI!")
        return None
    
    # Maliyet bazında sırala
    best_solution = min(all_solutions, key=lambda s: s.get('total_cost', float('inf')))
    
    print(f"\n{'='*70}")
    print(f"✅ EN İYİ ÇÖZÜM BULUNDU!")
    print(f"{'='*70}")
    print(f"   Strateji: {best_solution['description']}")
    print(f"   Toplam Maliyet: {best_solution['total_cost']:.2f} TL")
    print(f"      - Yakıt: {best_solution['metrics']['total_cost']:.2f} TL")
    print(f"      - Kiralama: {best_solution['rental_cost']:.2f} TL")
    print(f"   Toplam Mesafe: {best_solution['metrics']['total_distance']:.2f} km")
    print(f"   Araç Sayısı: {best_solution['metrics']['total_vehicles']}")
    print(f"   Kapasite Kullanımı: {best_solution['metrics']['avg_utilization']:.1f}%")
    print(f"   Teslim: {best_solution['metrics']['total_cargos']} kargo")
    print(f"{'='*70}\n")
    
    # Tasarruf hesapla
    if len(all_solutions) > 1:
        worst = max(all_solutions, key=lambda s: s.get('total_cost', 0))
        savings = worst['total_cost'] - best_solution['total_cost']
        savings_percent = (savings / worst['total_cost']) * 100 if worst['total_cost'] > 0 else 0
        
        print(f"💡 OPTİMİZASYON KAZANCI:")
        print(f"   En kötü çözüm: {worst['total_cost']:.2f} TL")
        print(f"   En iyi çözüm: {best_solution['total_cost']:.2f} TL")
        print(f"   Tasarruf: {savings:.2f} TL (%{savings_percent:.1f})\n")
    
    # Sonucu formatla
    return {
        'routes': best_solution['routes'],
        'total_cost': best_solution['total_cost'],
        'total_distance': best_solution['metrics']['total_distance'],
        'fuel_cost': best_solution['metrics']['total_cost'],
        'rental_cost': best_solution['rental_cost'],
        'combination': {
            'strategy': best_solution['strategy'],
            'description': best_solution['description'],
            'rental_count': best_solution['rental_count']
        }
    }


print("✓ Graph-Based Optimization Engine module loaded")
