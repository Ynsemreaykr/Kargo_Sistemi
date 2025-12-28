"""
Basit Kargo Dağıtım Algoritması
Greedy Nearest Neighbor yaklaşımı ile
"""

from typing import List, Dict, Any
import math


class DistributionOptimizer:
    """
    Basit dağıtım algoritması - Nearest Neighbor
    """
    
    def __init__(self, cursor, system_params):
        self.cursor = cursor
        self.system_params = system_params
        self.cost_per_km = float(system_params.get('cost_per_km', 5.0))
    
    def optimize_distribution(self, cargos: List[Dict], mode: str, start_location: int) -> Dict[str, Any]:
        """
        Basit dağıtım optimizasyonu
        
        Args:
            cargos: [{'id': 1, 'weight_kg': 100, 'quantity': 2, 'destination_district_id': 5}, ...]
            mode: 'LIMITED' veya 'UNLIMITED'
            start_location: Başlangıç district ID
            
        Returns:
            {'success': True, 'routes': [...], ...}
        """
        print(f"\n{'='*60}")
        print(f"🎯 DAĞITIM ALGORİTMASI BAŞLIYOR")
        print(f"{'='*60}")
        print(f"Mode: {mode}")
        print(f"Başlangıç: District #{start_location}")
        print(f"Kargo sayısı: {len(cargos)}")
        
        # ADIM 1: Araçları al
        vehicles = self._get_available_vehicles(mode)
        if not vehicles:
            return {'success': False, 'error': 'Kullanılabilir araç bulunamadı!'}
        
        print(f"Araç sayısı: {len(vehicles)}")
        
        # ADIM 2: Kargoları ilçelere göre grupla
        cargo_by_district = {}
        for cargo in cargos:
            dist_id = cargo['destination_district_id']
            if dist_id not in cargo_by_district:
                cargo_by_district[dist_id] = []
            cargo_by_district[dist_id].append(cargo)
        
        print(f"\n📦 KARGO DAĞILIMI:")
        for dist_id, cargo_list in cargo_by_district.items():
            total_weight = sum(float(c['weight_kg']) * c.get('quantity', 1) for c in cargo_list)
            print(f"  District #{dist_id}: {total_weight}kg")
        
        # ADIM 3: Teslim edilecek ilçeler
        undelivered_districts = set(cargo_by_district.keys())
        
        # ADIM 4: Her araç için rota oluştur (Greedy Nearest Neighbor)
        routes = []
        for vehicle in vehicles:
            if not undelivered_districts:
                print(f"\n✅ Tüm kargolar teslim edildi!")
                break
            
            print(f"\n{'='*60}")
            print(f"🚛 ARAÇ: {vehicle['name']} (Kapasite: {vehicle['capacity_kg']}kg)")
            print(f"{'='*60}")
            
            # Rota değişkenleri
            route_order = [start_location]  # Başlangıç
            route_cargos = []
            current_weight = 0.0
            current_position = start_location
            
            # Nearest Neighbor ile ilçeleri ziyaret et
            while True:
                # En yakın teslim edilmemiş ilçeyi bul
                nearest_dist_id = None
                min_distance = float('inf')
                
                for dist_id in list(undelivered_districts):
                    distance = self._get_distance(current_position, dist_id)
                    if distance < min_distance:
                        min_distance = distance
                        nearest_dist_id = dist_id
                
                if nearest_dist_id is None:
                    break  # Hiç ilçe kalmadı
                
                # Bu ilçedeki kargoların toplam ağırlığı
                cargos_here = cargo_by_district[nearest_dist_id]
                weight_here = sum(float(c['weight_kg']) * c.get('quantity', 1) for c in cargos_here)
                
                # Kapasite kontrolü
                if current_weight + weight_here <= float(vehicle['capacity_kg']):
                    # SIĞ  IYOR - Ekle!
                    route_order.append(nearest_dist_id)
                    route_cargos.extend(cargos_here)
                    current_weight += weight_here
                    current_position = nearest_dist_id
                    undelivered_districts.remove(nearest_dist_id)
                    print(f"  ✓ District #{nearest_dist_id} eklendi: {weight_here}kg (Toplam: {current_weight}/{vehicle['capacity_kg']}kg)")
                else:
                    # SĞMIYOR - Bu araç doldu
                    print(f"  ⚠️  District #{nearest_dist_id} sığmıyor ({weight_here}kg)")
                    print(f"     Araç kapasitesi doldu: {current_weight}/{vehicle['capacity_kg']}kg")
                    break
            
            # Rota oluştu mu?
            if len(route_order) > 1:  # En az 1 teslimat var
                # Mesafe hesapla
                total_distance = self._calculate_route_distance(start_location, route_order[1:])
                
                routes.append({
                    'vehicle': vehicle,
                    'route_order': route_order,
                    'cargos':route_cargos,
                    'total_weight': current_weight,
                    'distance': float(total_distance),
                    'distance_cost': float(total_distance * self.cost_per_km),
                    'vehicle_cost': float(vehicle.get('cost_per_route', 100.0)),
                    'cost': float(total_distance * self.cost_per_km) + float(vehicle.get('cost_per_route', 100.0)),
                    'capacity': float(vehicle['capacity_kg']),
                    'utilization': (current_weight / float(vehicle['capacity_kg'])) * 100
                })
                
                print(f"\n📊 ROTA ÖZETİ:")
                print(f"   Mesafe: {total_distance:.2f}km")
                print(f"   Ağırlık: {current_weight:.1f}kg")
                print(f"   Kapasite Kullanımı: {routes[-1]['utilization']:.1f}%")
                print(f"   Maliyet: {routes[-1]['cost']:.2f}TL")
        
        # ADIM 5: Teslim edilemeyen kargolar var mı?
        if undelivered_districts:
            if mode == 'LIMITED':
                # LIMITED modda hata ver
                remaining_weight = sum(
                    sum(c['weight_kg'] * c.get('quantity', 1) for c in cargo_by_district[dist_id])
                    for dist_id in undelivered_districts
                )
                return {
                    'success': False,
                    'error': f'Yetersiz araç kapasitesi! {len(undelivered_districts)} ilçeye teslimat yapılamadı.',
                    'remaining_cargos': [c for dist_id in undelivered_districts for c in cargo_by_district[dist_id]],
                    'total_remaining_weight': remaining_weight
                }
            elif mode == 'UNLIMITED':
                # UNLIMITED modda araç kirala ve devam et (basitleştirilmiş - şimdilik hata ver)
                return {
                   'success': False,
                    'error': 'UNLIMITED mode kiralama henüz implement edilmedi!'
                }
        
        # BAŞARILI!
        total_cost = sum(r['cost'] for r in routes)
        total_distance = sum(r['distance'] for r in routes)
        
        print(f"\n{'='*60}")
        print(f"✅ DAĞITIM BAŞARILI!")
        print(f"{'='*60}")
        print(f"Kullanılan araç: {len(routes)}")
        print(f"Toplam mesafe: {total_distance:.2f}km")
        print(f"Toplam maliyet: {total_cost:.2f}TL")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'routes': routes,
            'total_cost': total_cost,
            'total_distance': total_distance,
            'delivered_count': len(cargos),
            'vehicle_count': len(routes)
        }
    
    def _get_available_vehicles(self, mode: str) -> List[Dict]:
        """Araçları al"""
        if mode == 'RENTAL':
            self.cursor.execute("""
                SELECT 
                    vt.id as vehicle_type_id,
                    vt.name,
                    vt.capacity_kg,
                    100.0 as cost_per_route,
                    TRUE as is_rented
                FROM vehicle_types vt
                ORDER BY vt.capacity_kg ASC
            """)
        else:
            self.cursor.execute("""
                SELECT 
                    v.id as vehicle_id,
                    vt.id as vehicle_type_id,
                    vt.name,
                    vt.capacity_kg,
                    100.0 as cost_per_route,
                    v.is_rented
                FROM vehicles v
                JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
                WHERE v.is_rented = FALSE
                ORDER BY vt.capacity_kg ASC
            """)
        
        vehicles = self.cursor.fetchall()
        # Convert Decimal to float
        result = []
        for v in vehicles:
            vehicle_dict = dict(v)
            vehicle_dict['capacity_kg'] = float(vehicle_dict['capacity_kg'])
            vehicle_dict['cost_per_route'] = float(vehicle_dict.get('cost_per_route', 100.0))
            result.append(vehicle_dict)
        return result
    
    def _get_distance(self, from_id: int, to_id: int) -> float:
        """İki ilçe arası mesafe (Haversine)"""
        self.cursor.execute("""
            SELECT latitude, longitude
            FROM districts
            WHERE id IN (%s, %s)
            ORDER BY id
        """, (from_id, to_id))
        
        districts = self.cursor.fetchall()
        
        if len(districts) < 2:
            return 0
        
        lat1, lon1 = math.radians(districts[0]['latitude']), math.radians(districts[0]['longitude'])
        lat2, lon2 = math.radians(districts[1]['latitude']), math.radians(districts[1]['longitude'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return 6371 * c  # km
    
    def _calculate_route_distance(self, start: int, route_order: List[int]) -> float:
        """Rota toplam mesafesi"""
        total_distance = 0
        current = start
        
        for dest in route_order:
            total_distance += self._get_distance(current, dest)
            current = dest
        
        # Başlangıca dön
        total_distance += self._get_distance(current, start)
        
        return total_distance
