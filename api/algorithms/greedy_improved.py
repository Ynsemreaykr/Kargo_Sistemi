"""
Kargo İşletme Sistemi - Improved Greedy (GREEDY+)
Geliştirilmiş Greedy algoritması - Araç ve kargo sıralaması ile
"""

from typing import List, Dict, Any
from .utils import calculate_distance_matrix, calculate_route_distance, get_district_by_id


def improved_greedy_algorithm(
    cargos: List[Dict[str, Any]],
    districts: List[Dict[str, Any]],
    vehicles: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    İyileştirilmiş Greedy algoritması
    
    İYİLEŞTİRMELER:
    1. Araçları kapasiteye göre sırala (büyükten küçüğe)
    2. Kargoları ağırlığa göre sırala (büyükten küçüğe)
    3. Büyük araçlar önce kullanılır
    
    Args:
        cargos: Kargo listesi
        districts: İlçe listesi
        vehicles: Araç listesi
    
    Returns:
        Rota listesi
    """
    
    print("\n" + "="*60)
    print("⚡ GREEDY+ ALGORITHM BAŞLIYOR (İYİLEŞTİRİLMİŞ)")
    print("="*60)
    print("📊 İyileştirmeler: Araç sıralaması + Akıllı atama")
    
    # Mesafe matrisini hesapla
    distance_matrix = calculate_distance_matrix(districts)
    
    # İYİLEŞTİRME 1: Araçları kapasiteye göre sırala (BÜYÜKTEN KÜÇÜĞE)
    sorted_vehicles = sorted(
        vehicles,
        key=lambda v: v['capacity_kg'],
        reverse=True
    )
    
    print(f"\n🚛 ARAÇ SIRALAMASI (Büyük → Küçük):")
    for i, vehicle in enumerate(sorted_vehicles, 1):
        print(f"  {i}. {vehicle.get('type_name', 'Araç')} {vehicle['id']}: {vehicle['capacity_kg']:.0f} kg")
    
    # ADIM 1: Kargoları ilçelere göre grupla
    cargo_by_district = {}
    for cargo in cargos:
        dist_id = cargo['district_id']
        if dist_id not in cargo_by_district:
            cargo_by_district[dist_id] = []
        cargo_by_district[dist_id].append(cargo)
    
    # DEBUG: Kargo dağılımı
    print(f"\n📦 KARGO DAĞILIMI:")
    print("-" * 60)
    for dist_id, cargos_list in cargo_by_district.items():
        district = get_district_by_id(districts, dist_id)
        if not district:
            print(f"  ❌ HATA: İlçe ID {dist_id} bulunamadı!")
            continue
            
        total_weight = sum(c['weight_kg'] * c.get('quantity', 1) for c in cargos_list)
        print(f"  ✓ {district['name']:15s} (ID={dist_id:2d}): {total_weight:6.1f} kg")
    
    # ADIM 2: Teslim edilecek ilçeler
    undelivered_districts = set(cargo_by_district.keys())
    print(f"\n🎯 Toplam {len(undelivered_districts)} ilçeye teslimat yapılacak")
    
    # ADIM 3: Her araç için rota oluştur (BÜYÜK ARAÇLARDAN BAŞLA)
    routes = []
    
    for vehicle_index, vehicle in enumerate(sorted_vehicles):
        if not undelivered_districts:
            print(f"\n✅ Tüm kargolar teslim edildi, kalan araçlar kullanılmayacak")
            break
        
        # Başlangıç konumu
        start_id = vehicle.get('current_location_district_id', 12)
        start_district = get_district_by_id(districts, start_id)
        
        print(f"\n{'='*60}")
        print(f"🚛 ARAÇ {vehicle['id']} ({vehicle['type_name']})")
        print(f"{'='*60}")
        print(f"📍 Başlangıç: {start_district['name']} (ID={start_id})")
        print(f"📦 Kapasite: {vehicle['capacity_kg']:.0f} kg")
        
        # Rota değişkenleri
        route = [start_id]
        route_cargos = []
        current_weight = 0.0
        current_position = start_id
        
        # En yakın komşu ile doldur
        step = 0
        while undelivered_districts:
            step += 1
            
            # En yakın teslim edilmemiş ilçeyi bul
            nearest_district_id = None
            min_distance = float('inf')
            
            for dist_id in list(undelivered_districts):
                dist = distance_matrix.get((current_position, dist_id), float('inf'))
                if dist < min_distance:
                    min_distance = dist
                    nearest_district_id = dist_id
            
            if nearest_district_id is None:
                print(f"  ⚠️  Adım {step}: Erişilebilir ilçe kalmadı")
                break
            
            # Bu ilçedeki kargolar
            cargos_here = cargo_by_district[nearest_district_id]
            weight_here = sum(c['weight_kg'] * c.get('quantity', 1) for c in cargos_here)
            
            # Kapasite kontrolü
            if current_weight + weight_here <= vehicle['capacity_kg']:
                # EKLE
                route.append(nearest_district_id)
                route_cargos.extend(cargos_here)
                current_weight += weight_here
                current_position = nearest_district_id
                undelivered_districts.remove(nearest_district_id)
                
                district_name = get_district_by_id(districts, nearest_district_id)['name']
                print(f"  ✓ Adım {step}: {district_name:15s} eklendi → Ağırlık: {weight_here:6.1f} kg | Toplam: {current_weight:6.1f}/{vehicle['capacity_kg']:.0f} kg")
            else:
                # Kapasite doldu
                print(f"  ⚠️  Adım {step}: Kapasite doldu ({current_weight:.1f}/{vehicle['capacity_kg']:.0f} kg)")
                district_name = get_district_by_id(districts, nearest_district_id)['name']
                print(f"       {district_name} ({weight_here:.1f} kg) sığmıyor!")
                break
        
        # Rota oluşturuldu mu?
        if len(route) > 1:  # Sadece başlangıç değil
            total_distance = calculate_route_distance(route, distance_matrix)
            end_location_id = route[-1]
            end_district = get_district_by_id(districts, end_location_id)
            
            routes.append({
                'vehicle_id': vehicle['id'],
                'vehicle_type': vehicle['type_name'],
                'start_location_id': start_id,
                'end_location_id': end_location_id,
                'route': route,
                'cargos': route_cargos,
                'total_distance_km': total_distance,
                'total_weight_kg': current_weight,
                'capacity_utilization': round((current_weight / vehicle['capacity_kg']) * 100, 1)
            })
            
            print(f"\n📊 ROTA ÖZETİ:")
            print(f"   Başlangıç → Bitiş: {start_district['name']} → {end_district['name']}")
            print(f"   Toplam Mesafe: {total_distance:.2f} km")
            print(f"   Toplam Ağırlık: {current_weight:.1f} kg")
            print(f"   Kapasite Kullanımı: {routes[-1]['capacity_utilization']:.1f}%")
        else:
            print(f"\n  ℹ️  Bu araç kullanılmadı (hiç kargo alınmadı)")
    
    # ADIM 4: Sonuç raporu
    print(f"\n{'='*60}")
    print(f"📋 SONUÇ RAPORU (GREEDY+)")
    print(f"{'='*60}")
    print(f"✓ Oluşturulan Rota Sayısı: {len(routes)}")
    
    if undelivered_districts:
        print(f"⚠️  TESLİM EDİLEMEYEN İLÇELER ({len(undelivered_districts)} adet):")
        for dist_id in undelivered_districts:
            district = get_district_by_id(districts, dist_id)
            weight = sum(c['weight_kg'] * c.get('quantity', 1) for c in cargo_by_district[dist_id])
            print(f"   - {district['name']:15s} (ID={dist_id:2d}): {weight:.1f} kg")
    else:
        print(f"✅ TÜM KARGOLAR TESLİM EDİLDİ!")
    
    print(f"{'='*60}\n")
    
    return routes


print("✓ Improved Greedy (GREEDY+) module loaded")
