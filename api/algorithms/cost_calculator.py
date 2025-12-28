"""
Cost Calculator - Maliyet Hesaplama Modülü
Tüm maliyet hesaplamalarını yapar
"""

from typing import List, Dict, Any


def calculate_route_cost(route: Dict, vehicle: Dict, cost_per_km: float) -> Dict:
    """
    Tek bir rota için maliyet hesapla
    
    Args:
        route: {'distance': 68.2, 'cargos': [...], ...}
        vehicle: {'id': 1, 'is_rented': True, 'rental_cost': 100, ...}
        cost_per_km: Km başı yakıt maliyeti
    
    Returns:
        {
            'fuel_cost': 102.3,
            'rental_cost': 100.0,
            'total_cost': 202.3,
            'cost_per_cargo': 101.15
        }
    """
    
    distance = route.get('distance', 0)
    cargo_count = len(route.get('cargos', []))
    
    # Yakıt maliyeti
    fuel_cost = distance * cost_per_km
    
    # Kiralama maliyeti
    rental_cost = 0.0
    if vehicle.get('is_rented', False):
        rental_cost = float(vehicle.get('rental_cost', 0))
    
    # Toplam
    total_cost = fuel_cost + rental_cost
    
    # Kargo başına maliyet
    cost_per_cargo = total_cost / cargo_count if cargo_count > 0 else 0
    
    return {
        'fuel_cost': round(fuel_cost, 2),
        'rental_cost': round(rental_cost, 2),
        'total_cost': round(total_cost, 2),
        'cost_per_cargo': round(cost_per_cargo, 2)
    }


def calculate_total_cost(routes: List[Dict], vehicles: List[Dict], cost_per_km: float) -> Dict:
    """
    Tüm rotalar için toplam maliyet
    
    Returns:
        {
            'total_fuel_cost': 250.5,
            'total_rental_cost': 200.0,
            'total_cost': 450.5,
            'total_distance': 167.0,
            'avg_cost_per_cargo': 112.6,
            'route_costs': [...]
        }
    """
    
    total_fuel = 0.0
    total_rental = 0.0
    total_distance = 0.0
    total_cargo_count = 0
    route_costs = []
    
    for route in routes:
        # Aracı bul
        vehicle = next((v for v in vehicles if v['id'] == route['vehicle_id']), None)
        
        if not vehicle:
            continue
        
        # Rota maliyeti
        cost_info = calculate_route_cost(route, vehicle, cost_per_km)
        route_costs.append(cost_info)
        
        total_fuel += cost_info['fuel_cost']
        total_rental += cost_info['rental_cost']
        total_distance += route.get('distance', 0)
        total_cargo_count += len(route.get('cargos', []))
    
    total_cost = total_fuel + total_rental
    avg_cost_per_cargo = total_cost / total_cargo_count if total_cargo_count > 0 else 0
    
    return {
        'total_fuel_cost': round(total_fuel, 2),
        'total_rental_cost': round(total_rental, 2),
        'total_cost': round(total_cost, 2),
        'total_distance': round(total_distance, 2),
        'avg_cost_per_cargo': round(avg_cost_per_cargo, 2),
        'route_costs': route_costs,
        'cargo_count': total_cargo_count
    }


def compare_scenarios(scenario1: Dict, scenario2: Dict) -> Dict:
    """
    İki senaryoyu karşılaştır
    
    Returns:
        {
            'better_scenario': 1 or 2,
            'cost_difference': 50.5,
            'cost_savings_percent': 12.5,
            'comparison': {...}
        }
    """
    
    cost1 = scenario1.get('total_cost', float('inf'))
    cost2 = scenario2.get('total_cost', float('inf'))
    
    if cost1 < cost2:
        better = 1
        diff = cost2 - cost1
        savings_percent = (diff / cost2) * 100 if cost2 > 0 else 0
    else:
        better = 2
        diff = cost1 - cost2
        savings_percent = (diff / cost1) * 100 if cost1 > 0 else 0
    
    return {
        'better_scenario': better,
        'cost_difference': round(diff, 2),
        'cost_savings_percent': round(savings_percent, 2),
        'comparison': {
            'scenario1_cost': cost1,
            'scenario2_cost': cost2,
            'scenario1_routes': len(scenario1.get('routes', [])),
            'scenario2_routes': len(scenario2.get('routes', [])),
            'scenario1_delivered': scenario1.get('delivered_count', 0),
            'scenario2_delivered': scenario2.get('delivered_count', 0)
        }
    }


def calculate_rental_cost(vehicle_types: List[Dict], rental_count: int) -> float:
    """
    Kiralama maliyetini hesapla
    
    Args:
        vehicle_types: Kiralanan araç tipleri
        rental_count: Kiralanan araç sayısı
    
    Returns:
        Toplam kiralama maliyeti
    """
    
    total = 0.0
    for vt in vehicle_types[:rental_count]:
        total += float(vt.get('rental_cost', 0))
    
    return round(total, 2)


def estimate_cost_range(cargo_analysis: Dict, vehicle_types: List[Dict], cost_per_km: float) -> Dict:
    """
    Olası maliyet aralığını tahmin et
    
    Args:
        cargo_analysis: Kargo analizi sonucu
        vehicle_types: Mevcut araç tipleri
        cost_per_km: Km başı maliyet
    
    Returns:
        {
            'min_cost': 150.0,  # En iyi senaryoda
            'max_cost': 500.0,  # En kötü senaryoda
            'avg_distance_estimate': 100.0
        }
    """
    
    total_weight = cargo_analysis.get('total_weight', 0)
    district_count = len(cargo_analysis.get('districts', []))
    
    # Tahmini mesafe (ilçe sayısına göre)
    avg_distance_per_district = 30  # km (ortalama)
    estimated_distance = district_count * avg_distance_per_district
    
    # En iyi senaryo: Tek büyük araç
    largest_vehicle = max(vehicle_types, key=lambda v: v['capacity_kg'])
    if total_weight <= largest_vehicle['capacity_kg']:
        min_cost = (estimated_distance * cost_per_km + 
                   float(largest_vehicle.get('rental_cost', 0)))
    else:
        # Birden fazla araç gerekli
        vehicle_count = int(total_weight / largest_vehicle['capacity_kg']) + 1
        min_cost = (estimated_distance * vehicle_count * cost_per_km + 
                   float(largest_vehicle.get('rental_cost', 0)) * vehicle_count)
    
    # En kötü senaryo: Çok sayıda küçük araç
    smallest_vehicle = min(vehicle_types, key=lambda v: v['capacity_kg'])
    vehicle_count = int(total_weight / smallest_vehicle['capacity_kg']) + 1
    max_cost = (estimated_distance * vehicle_count * cost_per_km + 
               float(smallest_vehicle.get('rental_cost', 0)) * vehicle_count)
    
    return {
        'min_cost': round(min_cost, 2),
        'max_cost': round(max_cost, 2),
        'avg_distance_estimate': round(estimated_distance, 2)
    }


print("✓ Cost Calculator module loaded")
