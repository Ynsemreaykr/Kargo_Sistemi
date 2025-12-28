"""
Optimization Engine - Tam Optimizasyon Sistemi
Tüm olasılıkları deneyen ve en iyisini bulan motor
"""

from typing import List, Dict, Any
import itertools
from .bin_packing import bin_packing_first_fit_decreasing, calculate_bin_packing_score
from .route_aware_packing import route_aware_bin_packing  # YENİ: Coğrafi bin packing
from .cost_calculator import calculate_total_cost, compare_scenarios, estimate_cost_range
from .route_optimizer import create_route_from_assignment, optimize_with_enroute_pickup
from .utils import calculate_distance_matrix


def analyze_cargos(cargos: List[Dict]) -> Dict:
    """
    Kargoları analiz et
    
    Returns:
        Kargo istatistikleri
    """
    
    if not cargos:
        return {
            'total_weight': 0,
            'cargo_count': 0,
            'districts': [],
            'district_weights': {},
            'max_single_cargo': 0,
            'min_single_cargo': 0
        }
    
    analysis = {
        'total_weight': 0,
        'cargo_count': len(cargos),
        'districts': [],
        'district_weights': {},
        'max_single_cargo': 0,
        'min_single_cargo': float('inf')
    }
    
    district_set = set()
    
    for cargo in cargos:
        dist_id = cargo['district_id']
        weight = cargo['weight_kg'] * cargo.get('quantity', 1)
        
        district_set.add(dist_id)
        analysis['total_weight'] += weight
        analysis['district_weights'][dist_id] = analysis['district_weights'].get(dist_id, 0) + weight
        analysis['max_single_cargo'] = max(analysis['max_single_cargo'], weight)
        analysis['min_single_cargo'] = min(analysis['min_single_cargo'], weight)
    
    analysis['districts'] = list(district_set)
    
    return analysis


def generate_vehicle_combinations(own_vehicles: List[Dict], available_vehicle_types: List[Dict],
                                  cargo_analysis: Dict, max_rental: int = 3) -> List[Dict]:
    """
    Olası araç kombinasyonlarını üret
    
    Stratejiler:
    1. Sadece kendi araçlar
    2. Kendi + 1-3 kiralık
    3. Optimal kiralık seçimi
    """
    
    combinations = []
    total_weight = cargo_analysis['total_weight']
    
    # Strateji 1: Sadece kendi araçlar
    combinations.append({
        'vehicles': own_vehicles,
        'rental_count': 0,
        'rental_vehicles': [],
        'strategy': 'OWN_ONLY',
        'description': 'Sadece kendi 3 araç'
    })
    
    # Strateji 2: Kendi + kiralık kombinasyonları
    for rental_count in range(1, min(max_rental + 1, 4)):
        # Her araç tipinden kaç tane?
        for combo in itertools.combinations_with_replacement(available_vehicle_types, rental_count):
            rental_vehicles = list(combo)
            
            combinations.append({
                'vehicles': own_vehicles + rental_vehicles,
                'rental_count': rental_count,
                'rental_vehicles': rental_vehicles,
                'strategy': f'OWN_PLUS_{rental_count}',
                'description': f'Kendi araçlar + {rental_count} kiralık'
            })
    
    # Strateji 3: Tek optimal kiralık araç
    for vt in sorted(available_vehicle_types, key=lambda v: v['capacity_kg']):
        if vt['capacity_kg'] >= total_weight:
            combinations.append({
                'vehicles': [vt],
                'rental_count': 1,
                'rental_vehicles': [vt],
                'strategy': 'SINGLE_OPTIMAL',
                'description': f'Tek {vt["name"]} araç (optimal)'
            })
            break
    
    return combinations


def simulate_scenario(combination: Dict, cargos: List[Dict], districts: List[Dict],
                     distance_matrix: Dict, cost_per_km: float) -> Dict:
    """
    Bir araç kombinasyonu için tam simülasyon
    
    Returns:
        Simülasyon sonucu
    """
    
    vehicles = combination['vehicles']
    
    # 1. ROUTE-AWARE BIN PACKING: Coğrafi konuma göre kargoları araçlara dağıt
    assignments = route_aware_bin_packing(cargos, vehicles, districts, distance_matrix)
    
    if not assignments:
        return {
            'feasible': False,
            'routes': [],
            'total_cost': float('inf'),
            'delivered_count': 0,
            'error': 'Bin packing failed'
        }
    
    # 2. Her atama için rota oluştur
    routes = []
    for assignment in assignments:
        route = create_route_from_assignment(assignment, districts, distance_matrix)
        routes.append(route)
    
    # 3. Teslim edilen kargo sayısı
    delivered_cargos = []
    for route in routes:
        delivered_cargos.extend(route.get('cargos', []))
    
    delivered_count = len(delivered_cargos)
    feasible = delivered_count == len(cargos)
    
    # 4. Maliyet hesapla
    # Rotaları uygun formata çevir
    route_dicts = []
    for route in routes:
        route_dicts.append({
            'vehicle_id': route['vehicle_id'],
            'distance': route['distance'],
            'cargos': route['cargos']
        })
    
    # Araçları uygun formata çevir
    vehicle_dicts = []
    for v in vehicles:
        vehicle_dicts.append({
            'id': v.get('id', 0),
            'is_rented': v.get('is_rented', True),
            'rental_cost': v.get('rental_cost', 0)
        })
    
    cost_info = calculate_total_cost(route_dicts, vehicle_dicts, cost_per_km)
    
    # 5. Kapasite kullanımı
    total_utilization = sum(r.get('utilization', 0) for r in routes)
    avg_utilization = total_utilization / len(routes) if routes else 0
    
    return {
        'feasible': feasible,
        'routes': routes,
        'total_cost': cost_info['total_cost'],
        'total_distance': cost_info['total_distance'],
        'fuel_cost': cost_info['total_fuel_cost'],
        'rental_cost': cost_info['total_rental_cost'],
        'delivered_count': delivered_count,
        'undelivered_count': len(cargos) - delivered_count,
        'capacity_utilization': avg_utilization,
        'vehicle_count': len(routes),
        'combination': combination,
        'bin_packing_score': calculate_bin_packing_score(assignments)
    }


def apply_enroute_optimization(scenario: Dict, all_cargos: List[Dict], districts: List[Dict],
                               distance_matrix: Dict, cost_per_km: float) -> Dict:
    """
    Yol üstü yükleme optimizasyonu uygula
    """
    
    if not scenario.get('feasible', False):
        return scenario
    
    # Teslim edilmemiş kargolar
    delivered_cargo_ids = set()
    for route in scenario['routes']:
        for cargo in route.get('cargos', []):
            delivered_cargo_ids.add(id(cargo))
    
    undelivered = [c for c in all_cargos if id(c) not in delivered_cargo_ids]
    
    if not undelivered:
        return scenario
    
    # Her rota için yol üstü optimizasyon dene
    improved_routes = []
    for route in scenario['routes']:
        improved_route = optimize_with_enroute_pickup(
            route, undelivered, districts, distance_matrix, cost_per_km
        )
        improved_routes.append(improved_route)
    
    # Güncelle
    scenario['routes'] = improved_routes
    
    return scenario


def select_best_solution(simulations: List[Dict]) -> Dict:
    """
    En iyi çözümü seç
    
    Kriterler:
    1. Feasible olmalı (tüm kargolar teslim)
    2. Minimum maliyet
    3. Maksimum kapasite kullanımı
    4. Minimum araç sayısı
    """
    
    if not simulations:
        return None
    
    # Sadece geçerli çözümler
    feasible = [s for s in simulations if s.get('feasible', False)]
    
    if not feasible:
        # Hiçbiri tüm kargoları teslim edemedi
        # En fazla teslim edeni seç
        return max(simulations, key=lambda s: s.get('delivered_count', 0))
    
    # Maliyet bazında sırala
    sorted_by_cost = sorted(feasible, key=lambda s: s.get('total_cost', float('inf')))
    
    best = sorted_by_cost[0]
    
    # Alternatif: Maliyet farkı %5'ten azsa, daha iyi özellikleri olanı seç
    for solution in sorted_by_cost[1:]:
        cost_diff_percent = ((solution['total_cost'] - best['total_cost']) / 
                            best['total_cost'] * 100) if best['total_cost'] > 0 else 0
        
        if cost_diff_percent < 5:  # %5 fark
            # Daha az araç kullanıyorsa
            if solution['vehicle_count'] < best['vehicle_count']:
                best = solution
            # Daha yüksek kapasite kullanımı
            elif (solution['vehicle_count'] == best['vehicle_count'] and
                  solution['capacity_utilization'] > best['capacity_utilization']):
                best = solution
    
    return best


def full_optimization(cargos: List[Dict], districts: List[Dict], own_vehicles: List[Dict],
                     available_vehicle_types: List[Dict], cost_per_km: float,
                     distance_matrix: Dict = None) -> Dict:
    """
    TÜM OLASILIKLARı DENEYEN TAM OPTİMİZASYON
    
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
    
    print("\\n" + "="*70)
    print("🚀 TAM OPTİMİZASYON SİSTEMİ BAŞLIYOR")
    print("="*70)
    
    # Mesafe matrisi yoksa hesapla
    if distance_matrix is None:
        distance_matrix = calculate_distance_matrix(districts)
    
    # 1. Kargo Analizi
    cargo_analysis = analyze_cargos(cargos)
    print(f"\\n📦 KARGO ANALİZİ:")
    print(f"   Toplam Ağırlık: {cargo_analysis['total_weight']:.1f} kg")
    print(f"   Kargo Sayısı: {cargo_analysis['cargo_count']}")
    print(f"   İlçe Sayısı: {len(cargo_analysis['districts'])}")
    print(f"   En Ağır Kargo: {cargo_analysis['max_single_cargo']:.1f} kg")
    
    # 2. Maliyet tahmini
    cost_estimate = estimate_cost_range(cargo_analysis, available_vehicle_types, cost_per_km)
    print(f"\\n💰 MALİYET TAHMİNİ:")
    print(f"   Min (En İyi): {cost_estimate['min_cost']:.2f} TL")
    print(f"   Max (En Kötü): {cost_estimate['max_cost']:.2f} TL")
    
    # 3. Araç Kombinasyonları
    combinations = generate_vehicle_combinations(
        own_vehicles, available_vehicle_types, cargo_analysis
    )
    print(f"\\n🚛 {len(combinations)} ARAÇ KOMBİNASYONU OLUŞTURULDU")
    
    # 4. Simülasyonlar
    print(f"\\n🔬 SİMÜLASYONLAR BAŞLIYOR...")
    print("-" * 70)
    
    simulations = []
    for i, combo in enumerate(combinations, 1):
        print(f"\\n   [{i}/{len(combinations)}] {combo['description']}")
        
        result = simulate_scenario(combo, cargos, districts, distance_matrix, cost_per_km)
        
        # Yol üstü optimizasyon
        if result.get('feasible', False):
            result = apply_enroute_optimization(result, cargos, districts, distance_matrix, cost_per_km)
        
        simulations.append(result)
        
        # Sonuç özeti
        status = "✅ Tamamlandı" if result['feasible'] else "❌ Yetersiz"
        print(f"      {status}")
        print(f"      Maliyet: {result['total_cost']:.2f} TL")
        print(f"      Teslim: {result['delivered_count']}/{len(cargos)}")
        print(f"      Araç: {result['vehicle_count']} adet")
        print(f"      Kapasite: {result['capacity_utilization']:.1f}%")
    
    # 5. En İyi Çözüm
    best_solution = select_best_solution(simulations)
    
    if not best_solution:
        print("\\n❌ HİÇBİR ÇÖZÜM BULUNAMADI!")
        return None
    
    print(f"\\n{'='*70}")
    print(f"✅ EN İYİ ÇÖZÜM BULUNDU!")
    print(f"{'='*70}")
    print(f"   Strateji: {best_solution['combination']['description']}")
    print(f"   Toplam Maliyet: {best_solution['total_cost']:.2f} TL")
    print(f"      - Yakıt: {best_solution['fuel_cost']:.2f} TL")
    print(f"      - Kiralama: {best_solution['rental_cost']:.2f} TL")
    print(f"   Toplam Mesafe: {best_solution['total_distance']:.2f} km")
    print(f"   Araç Sayısı: {best_solution['vehicle_count']}")
    print(f"   Kapasite Kullanımı: {best_solution['capacity_utilization']:.1f}%")
    print(f"   Teslim: {best_solution['delivered_count']}/{len(cargos)} kargo")
    print(f"{'='*70}\\n")
    
    # Diğer çözümlerle karşılaştırma
    feasible_solutions = [s for s in simulations if s.get('feasible', False)]
    if len(feasible_solutions) > 1:
        worst = max(feasible_solutions, key=lambda s: s['total_cost'])
        savings = worst['total_cost'] - best_solution['total_cost']
        savings_percent = (savings / worst['total_cost']) * 100 if worst['total_cost'] > 0 else 0
        
        print(f"💡 OPTİMİZASYON KAZANCI:")
        print(f"   En kötü çözüm: {worst['total_cost']:.2f} TL")
        print(f"   En iyi çözüm: {best_solution['total_cost']:.2f} TL")
        print(f"   Tasarruf: {savings:.2f} TL (%{savings_percent:.1f})\\n")
    
    return best_solution


print("✓ Optimization Engine module loaded")
