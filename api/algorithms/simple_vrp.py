"""
ULTRA SIMPLE VRP - EN BASİT ÇALIŞAN ÇÖZÜM
Karmaşık şeyler bırakıldı, sadece ÇALIŞAN kod
"""

from typing import List, Dict



def advanced_vrp_solver(
    cargos: List[Dict],
    districts: List[Dict],
    vehicles: List[Dict],
    distance_matrix: Dict,
    cost_per_km: float = 1.5
) -> List[Dict]:
    """
    ULTRA BASİT VRP - Sadece çalışsın!
    """
    
    print("\n" + "="*80)
    print("🚀 ULTRA SIMPLE VRP - SADECE ÇALIŞAN KOD")
    print("="*80)
    
    # 1. Kargoları yazdır
    print(f"\n📦 GELEN KARGOLAR:")
    total_cargo_weight = 0
    for cargo in cargos:
        cargo_total = cargo['weight_kg'] * cargo['quantity']
        total_cargo_weight += cargo_total
        print(f"   Kargo #{cargo['id']}: {cargo['weight_kg']}kg x {cargo['quantity']} = {cargo_total}kg → İlçe {cargo['district_id']}")
    
    print(f"\n   TOPLAM KARGO: {total_cargo_weight} kg")
    
    # 2. Araçları yazdır
    print(f"\n🚛 ARAÇLAR:")
    for v in vehicles:
        print(f"   Araç #{v['id']}: {v.get('name', 'Unknown')} - {v['capacity_kg']} kg")
    
    # 3. İlçe bazlı gruplama
    district_groups = {}
    for cargo in cargos:
        dist_id = cargo['district_id']
        
        if dist_id not in district_groups:
            district_groups[dist_id] = []
        
        district_groups[dist_id].append(cargo)
    
    print(f"\n📍 İLÇE GRUPLARI:")
    for dist_id, cargo_list in district_groups.items():
        dist_name = next((d['name'] for d in districts if d['id'] == dist_id), f"İlçe {dist_id}")
        dist_weight = sum(c['weight_kg'] * c['quantity'] for c in cargo_list)
        print(f"   {dist_name}: {len(cargo_list)} kargo, {dist_weight} kg")
    
    # 4. Basit atama: Her araca sığdığı kadar at
    routes = []
    remaining_cargos = cargos.copy()
    vehicle_index = 0
    
    print(f"\n🔄 ARAÇ ATAMA:")
    print("="*80)
    
    while remaining_cargos and vehicle_index < len(vehicles):
        vehicle = vehicles[vehicle_index]
        vehicle_index += 1
        
        print(f"\n{'─'*80}")
        print(f"ARAÇ #{vehicle['id']}: {vehicle.get('name', 'Unknown')} ({vehicle['capacity_kg']} kg)")
        print(f"{'─'*80}")
        
        # Bu araca kargo yükle
        route_cargos = []
        route_districts = set()
        current_weight = 0
        
        for cargo in remaining_cargos[:]:
            cargo_weight = cargo['weight_kg'] * cargo['quantity']
            
            if current_weight + cargo_weight <= vehicle['capacity_kg']:
                route_cargos.append(cargo)
                route_districts.add(cargo['district_id'])
                current_weight += cargo_weight
                remaining_cargos.remove(cargo)
                
                dist_name = next((d['name'] for d in districts if d['id'] == cargo['district_id']), f"İlçe {cargo['district_id']}")
                print(f"   ✅ Kargo #{cargo['id']}: {dist_name}, {cargo_weight} kg")
                print(f"      Toplam yük: {current_weight} / {vehicle['capacity_kg']} kg")
            else:
                print(f"   ❌ Kargo #{cargo['id']}: Sığmadı ({cargo_weight} kg)")
        
        if not route_cargos:
            print(f"   ⚠️  Bu araca hiç kargo sığmadı!")
            continue
        
        # 5. Rota oluştur
        start_id = 12  # İzmit
        route_path = [start_id]
        
        # Benzersiz ilçeleri sırala (nearest neighbor)
        unique_districts = list(route_districts)
        current_pos = start_id
        
        print(f"\n   Rota oluşturma:")
        while unique_districts:
            # En yakını bul
            nearest = min(unique_districts, key=lambda d: distance_matrix.get((current_pos, d), float('inf')))
            dist = distance_matrix.get((current_pos, nearest), 0)
            
            dist_name = next((d['name'] for d in districts if d['id'] == nearest), f"İlçe {nearest}")
            print(f"      {dist_name} ({dist:.1f} km)")
            
            route_path.append(nearest)
            current_pos = nearest
            unique_districts.remove(nearest)
        
        # Mesafe hesapla
        total_distance = sum(distance_matrix.get((route_path[i], route_path[i+1]), 0) for i in range(len(route_path)-1))
        total_cost = total_distance * cost_per_km
        
        # Rota kaydet
        route = {
            'vehicle_id': vehicle['id'],
            'vehicle_type': vehicle.get('name', 'Unknown'),
            'vehicle': vehicle,
            'start_location': start_id,
            'end_location': route_path[-1],
            'path': route_path,
            'cargos': route_cargos,
            'total_weight': current_weight,
            'distance': total_distance,
            'cost': total_cost,
            'utilization': (current_weight / vehicle['capacity_kg']) * 100
        }
        
        routes.append(route)
        
        # Özet
        print(f"\n   📋 ÖZET:")
        print(f"      Kargo: {len(route_cargos)} adet")
        print(f"      Ağırlık: {current_weight} / {vehicle['capacity_kg']} kg ({route['utilization']:.1f}%)")
        print(f"      Mesafe: {total_distance:.1f} km")
        print(f"      Maliyet: {total_cost:.2f} TL")
    
    # Kalan kargolar
    if remaining_cargos:
        print(f"\n⚠️  KALAN KARGOLAR ({len(remaining_cargos)}):")
        for cargo in remaining_cargos:
            print(f"   Kargo #{cargo['id']}: {cargo['weight_kg'] * cargo['quantity']} kg")
    
    print(f"\n{'='*80}")
    print(f"✅ {len(routes)} ROTA OLUŞTURULDU")
    print(f"{'='*80}\n")
    
    return routes


# Alias
simple_vrp_solver = advanced_vrp_solver

print("✓ Ultra Simple VRP Solver loaded")
