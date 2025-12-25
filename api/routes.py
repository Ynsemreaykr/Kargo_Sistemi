"""
Kargo İşletme Sistemi - API Routes
Flask endpoint'leri
"""

from flask import Blueprint, request, jsonify, session
from config import execute_query, execute_insert
from utils import create_route_geometry
from algorithms import (
    nearest_neighbor_algorithm,
    simulated_annealing_optimize,
    calculate_distance_matrix,
    calculate_route_distance,
    calculate_route_cost,
    calculate_distance_matrix_osm,
    get_route_geometry_osm
)

api = Blueprint('api', __name__)

@api.route('/districts', methods=['GET'])
def get_districts():
    """
    Tüm ilçeleri listele
    
    GET /districts
    
    Response:
        [
            {
                "id": 1,
                "name": "İzmit",
                "latitude": 40.7654,
                "longitude": 29.9401
            },
            ...
        ]
    """
    try:
        districts = execute_query("SELECT id, name, latitude, longitude FROM districts ORDER BY name")
        return jsonify({
            'success': True,
            'data': districts
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/scenarios', methods=['POST'])
def create_scenario():
    """
    Yeni senaryo oluştur (AŞAMA 3 - Gerçek optimizasyon algoritmaları)
    
    POST /scenarios
    Body:
        {
            "scenario_type": "LIMITED" | "UNLIMITED",
            "algorithm": "greedy" | "sa" | "hybrid" (optional, default: hybrid),
            "cargos": [
                {
                    "district_id": 1,
                    "weight_kg": 100,
                    "quantity": 5
                },
                ...
            ]
        }
    
    Response:
        {
            "success": true,
            "data": {
                "scenario_id": 1,
                "total_cost": 450.50,
                "total_distance": 120.5,
                "algorithm_used": "hybrid"
            }
        }
    """
    try:
        data = request.get_json()
        scenario_type = data.get('scenario_type', 'LIMITED')
        algorithm_choice = data.get('algorithm', 'hybrid')
        cargos = data.get('cargos', [])
        
        # DEBUG: Gelen veriyi kontrol et
        print("\n" + "="*60)
        print("📨 YENİ SENARYO İSTEĞİ")
        print("="*60)
        print(f"Scenario Type: {scenario_type}")
        print(f"Algorithm: {algorithm_choice}")
        print(f"Cargos type: {type(cargos)}")
        print(f"Cargos content: {cargos}")
        
        # Validation
        if not isinstance(cargos, list):
            return jsonify({
                'success': False,
                'error': f'cargos bir liste olmalı, gelen tip: {type(cargos)}'
            }), 400
        
        if not cargos:
            return jsonify({
                'success': False,
                'error': 'En az bir kargo belirtilmelidir'
            }), 400
        
        # Sistem parametrelerini al
        params = execute_query("SELECT cost_per_km, default_vehicle_count FROM system_parameters LIMIT 1")[0]
        cost_per_km = float(params['cost_per_km'])
        
        # İlçeleri al
        districts = execute_query("SELECT id, name, latitude, longitude FROM districts")
        
        # İlçe koordinatlarını float'a çevir
        for district in districts:
            district['latitude'] = float(district['latitude'])
            district['longitude'] = float(district['longitude'])
        
        # Mesafe matrisini hesapla - OSM ile gerçek yollar
        use_osm = True
        
        try:
            print("🗺️ OSM API ile gerçek yol mesafeleri hesaplanıyor...")
            distance_matrix = calculate_distance_matrix_osm(
                districts, 
                use_cache=True,
                use_osm=True
            )
            print("✓ OSM mesafe matrisi hazır!")
        except Exception as e:
            print(f"⚠️ OSM hatası: {e}")
            print("📐 Haversine fallback kullanılıyor...")
            distance_matrix = calculate_distance_matrix(districts)
            use_osm = False
        
        # ===== ARAÇ YÜKLEME: KULLANICININ KENDI 3 ARAÇ =====
        user_id = session.get('user_id')
        
        own_vehicles_query = """
            SELECT v.id, v.vehicle_type_id, v.current_location_district_id,
                   vt.capacity_kg, vt.rental_cost, vt.name as type_name
            FROM vehicles v
            JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            WHERE v.is_rented = FALSE
              AND v.user_id = %s
            ORDER BY v.id
            LIMIT 3
        """
        own_vehicles = execute_query(own_vehicles_query, (user_id,))
        
        if not own_vehicles:
            return jsonify({
                'success': False,
                'error': 'Hiç araç bulunamadı! Lütfen yönetici ile iletişime geçin.'
            }), 400
        
        # Float conversion
        for vehicle in own_vehicles:
            vehicle['capacity_kg'] = float(vehicle['capacity_kg'])
            vehicle['rental_cost'] = float(vehicle['rental_cost']) if vehicle['rental_cost'] else 0.0
            vehicle['cost_per_km'] = cost_per_km
        
        print(f"\n🚛 Kendi araçlar: {len(own_vehicles)} adet (ücretsiz)")
        for v in own_vehicles:
            print(f"   - Araç {v['id']}: {v['type_name']} ({v['capacity_kg']:.0f} kg)")
        
        # Kargoları veritabanına kaydet
        cargo_ids = []
        for cargo in cargos:
            cargo_id = execute_insert(
                "INSERT INTO cargo (district_id, weight_kg, quantity) VALUES (%s, %s, %s)",
                (cargo['district_id'], cargo['weight_kg'], cargo.get('quantity', 1))
            )
            cargo_ids.append(cargo_id)
        
        # ===== AŞAMA 3: GERÇEK ALGORİTMA =====
        print(f"\n🔧 Algoritma: {algorithm_choice}")
        print(f"📦 Kargo sayısı: {len(cargos)}")
        print(f"📊 Senaryo tipi: {scenario_type}")
        
        # 1. Greedy ile başlangıç rotaları (kendi araçlarla)
        initial_routes = nearest_neighbor_algorithm(
            cargos, 
            districts, 
            own_vehicles
        )
        
        print(f"\n✓ Kendi araçlarla {len(initial_routes)} rota oluşturuldu")
        
        # 2. Teslim edilen vs edilmeyen kargolar
        delivered_districts = set()
        for route in initial_routes:
            # route['route'] = [12, 6, 3, ...]  (başlangıç + duraklar)
            delivered_districts.update(route['route'][1:])  # İlk eleman başlangıç, skip
        
        cargo_districts = set(c['district_id'] for c in cargos)
        undelivered_districts = cargo_districts - delivered_districts
        
        # 3. LIMITED vs UNLIMITED kontrolü
        routes = initial_routes
        rental_count = 0
        total_rental_cost = 0.0
        
        if undelivered_districts:
            if scenario_type == 'LIMITED':
                # HATA VER
                undelivered_names = []
                for dist_id in undelivered_districts:
                    district = next((d for d in districts if d['id'] == dist_id), None)
                    if district:
                        undelivered_names.append(district['name'])
                
                return jsonify({
                    'success': False,
                    'error': f"Araç yetersiz! {len(undelivered_districts)} ilçeye ulaşılamadı: {', '.join(undelivered_names)}"
                }), 400
            
            else:  # UNLIMITED - ARAÇ KİRALA
                print(f"\n💰 UNLIMITED MOD: {len(undelivered_districts)} ilçe için araç kiralanacak")
                
                while undelivered_districts:
                    rental_count += 1
                    
                    # En büyük kapasiteli aracı bul
                    vehicle_type_query = """
                        SELECT id, capacity_kg, rental_cost, name
                        FROM vehicle_types
                        ORDER BY capacity_kg DESC
                        LIMIT 1
                    """
                    vehicle_type = execute_query(vehicle_type_query)[0]
                    
                    # İzmit ID'sini al
                    izmit_result = execute_query("SELECT id FROM districts WHERE name = 'İzmit' OR name = 'Izmit' LIMIT 1")
                    izmit_id = izmit_result[0]['id'] if izmit_result else 1
                    
                    # Yeni araç oluştur (kiralık - KULLANICIYA ÖZEL - İzmit'ten başlar)
                    new_vehicle_id = execute_insert(
                        "INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id) VALUES (%s, TRUE, %s, %s)",
                        (vehicle_type['id'], izmit_id, user_id)
                    )
                    
                    new_vehicle = {
                        'id': new_vehicle_id,
                        'vehicle_type_id': vehicle_type['id'],
                        'capacity_kg': float(vehicle_type['capacity_kg']),
                        'rental_cost': float(vehicle_type['rental_cost']),
                        'type_name': vehicle_type['name'],
                        'current_location_district_id': 12,
                        'cost_per_km': cost_per_km
                    }
                    
                    total_rental_cost += new_vehicle['rental_cost']
                    
                    print(f"   🚛 Araç #{rental_count} kiralandı: {new_vehicle['type_name']} (Kiralama: {new_vehicle['rental_cost']:.2f} TL)")
                    
                    # Kalan kargolar
                    remaining_cargos = [c for c in cargos if c['district_id'] in undelivered_districts]
                    
                    # Rota oluştur
                    extra_routes = nearest_neighbor_algorithm(
                        remaining_cargos,
                        districts,
                        [new_vehicle]
                    )
                    
                    routes.extend(extra_routes)
                    
                    # Güncelle
                    for route in extra_routes:
                        delivered_districts.update(route['route'][1:])
                    
                    undelivered_districts = cargo_districts - delivered_districts
                    
                    # Sonsuz döngü önleme
                    if rental_count > 20:
                        print("⚠️  Maksimum kiralama limitine ulaşıldı!")
                        break
                
                print(f"\n✓ Toplam {rental_count} araç kiralandı (Maliyet: {total_rental_cost:.2f} TL)")
        
        print(f"\n✅ TOPLAM {len(routes)} ROTA OLUŞTURULDU")
        
        # 2. Simulated Annealing ile optimize et (eğer seçilmişse)
        if algorithm_choice in ['sa', 'hybrid']:
            print("🔥 Simulated Annealing optimizasyonu başlatılıyor...")
            optimized_routes = []
            for route_data in initial_routes:
                optimized_route = simulated_annealing_optimize(
                    route_data['route'],
                    distance_matrix,
                    initial_temp=1000.0,
                    cooling_rate=0.95,
                    iterations=1000
                )
                # Yeni mesafeyi hesapla
                optimized_distance = calculate_route_distance(optimized_route, distance_matrix)
                route_data['route'] = optimized_route
                route_data['total_distance_km'] = optimized_distance
                optimized_routes.append(route_data)
            
            routes = optimized_routes
            print(f"✓ Simulated Annealing tamamlandı")
        else:
            routes = initial_routes
        
        # 3. Maliyet hesaplama
        total_cost = total_rental_cost  # Başlangıç: Kiralama maliyeti
        total_distance = 0.0
        
        for route in routes:
            # Araç bilgisini al
            vehicle = next((v for v in own_vehicles if v['id'] == route['vehicle_id']), None)
            
            if not vehicle:
                # Kiralık araç - rental_cost_per_km kullan
                vehicle_type = execute_query(
                    "SELECT rental_cost FROM vehicle_types WHERE id = (SELECT vehicle_type_id FROM vehicles WHERE id = %s)",
                    (route['vehicle_id'],)
                )[0]
                rental_cost_value = float(vehicle_type['rental_cost']) if vehicle_type['rental_cost'] else 0.0
                
                # Kiralık araç için maliyet = mesafe * cost_per_km (ana kiralama maliyeti zaten eklendi)
                route_cost = route['total_distance_km'] * cost_per_km
            else:
                # Kendi aracımız - sadece yakıt maliyeti
                route_cost = route['total_distance_km'] * cost_per_km
            
            route['cost'] = round(route_cost, 2)
            total_cost += route_cost
            total_distance += route['total_distance_km']
            
            print(f"  Rota {route['vehicle_id']}: Mesafe={route['total_distance_km']:.2f} km, Maliyet={route_cost:.2f} TL")
        
        print(f"\n💰 Toplam Maliyet: {total_cost:.2f} TL")
        print(f"   - Kiralama Maliyeti: {total_rental_cost:.2f} TL")
        print(f"   - Yakıt Maliyeti: {total_cost - total_rental_cost:.2f} TL")
        print(f"📏 Toplam Mesafe: {total_distance:.2f} km")
        
        # Senaryoyu kaydet
        scenario_id = execute_insert(
            "INSERT INTO scenarios (scenario_type, total_cost, total_distance) VALUES (%s, %s, %s)",
            (scenario_type, total_cost, total_distance)
        )
        
        # Rotaları kaydet
        for route in routes:
            # Rota geometrisini oluştur (OSM ile gerçek yollar)
            if use_osm:
                try:
                    geometry = get_route_geometry_osm(route['route'], districts)
                    print(f"✓ OSM geometry oluşturuldu: {len(geometry['features'])} segment")
                except Exception as e:
                    print(f"⚠️ OSM geometry hatası, fallback: {e}")
                    geometry = create_route_geometry(districts, route['route'])
            else:
                geometry = create_route_geometry(districts, route['route'])
            
            # Rotayı kaydet
            route_id = execute_insert(
                "INSERT INTO routes (scenario_id, vehicle_id, distance, cost, route_geometry) VALUES (%s, %s, %s, %s, %s)",
                (scenario_id, route['vehicle_id'], route['total_distance_km'], route['cost'], str(geometry).replace("'", '"'))
            )
            
            # Rota duraklarını kaydet
            for order, district_id in enumerate(route['route'], start=1):
                execute_insert(
                    "INSERT INTO route_stops (route_id, district_id, stop_order) VALUES (%s, %s, %s)",
                    (route_id, district_id, order),
                    return_id=False
                )
            
            # ARAÇ KONUMUNU GÜNCELLE! (En son gittiği yer)
            new_location_id = route.get('end_location_id')
            if new_location_id:
                try:
                    execute_insert(
                        "UPDATE vehicles SET current_location_district_id = %s WHERE id = %s",
                        (new_location_id, route['vehicle_id']),
                        return_id=False
                    )
                    print(f"✓ Araç {route['vehicle_id']} konumu güncellendi: İlçe {new_location_id}")
                except Exception as e:
                    print(f"⚠️  Araç konum güncelleme hatası: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'scenario_id': scenario_id,
                'total_cost': round(total_cost, 2),
                'total_distance': round(total_distance, 2),
                'route_count': len(routes),
                'algorithm_used': algorithm_choice
            }
        }), 201
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/scenarios/<int:scenario_id>', methods=['GET'])
def get_scenario(scenario_id):
    """
    Senaryo detaylarını getir
    
    GET /scenarios/<id>
    
    Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "scenario_type": "LIMITED",
                "total_cost": 450.50,
                "total_distance": 120.5,
                "created_at": "2025-12-19 04:52:00",
                "routes": [...]
            }
        }
    """
    try:
        # Senaryo bilgisi
        scenario = execute_query(
            "SELECT * FROM scenarios WHERE id = %s",
            (scenario_id,)
        )
        
        if not scenario:
            return jsonify({
                'success': False,
                'error': 'Senaryo bulunamadı'
            }), 404
        
        scenario = scenario[0]
        
        # Rotaları getir
        routes = execute_query(
            "SELECT * FROM routes WHERE scenario_id = %s",
            (scenario_id,)
        )
        
        # Her rota için durakları getir
        for route in routes:
            stops = execute_query(
                """
                SELECT rs.stop_order, d.id, d.name, d.latitude, d.longitude
                FROM route_stops rs
                JOIN districts d ON rs.district_id = d.id
                WHERE rs.route_id = %s
                ORDER BY rs.stop_order
                """,
                (route['id'],)
            )
            route['stops'] = stops
        
        scenario['routes'] = routes
        
        return jsonify({
            'success': True,
            'data': scenario
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/routes/<int:scenario_id>', methods=['GET'])
def get_routes(scenario_id):
    """
    Belirli senaryoya ait tüm rotaları getir
    
    GET /routes/<scenario_id>
    
    Response:
        {
            "success": true,
            "data": [
                {
                    "id": 1,
                    "vehicle_id": 1,
                    "distance": 45.5,
                    "cost": 250.0,
                    "route_geometry": {...},
                    "stops": [...]
                },
                ...
            ]
        }
    """
    try:
        # Rotaları getir
        routes = execute_query(
            """
            SELECT r.*, v.vehicle_type_id, vt.name as vehicle_type_name
            FROM routes r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            WHERE r.scenario_id = %s
            """,
            (scenario_id,)
        )
        
        # Her rota için durakları getir
        for route in routes:
            stops = execute_query(
                """
                SELECT rs.stop_order, d.id, d.name, d.latitude, d.longitude
                FROM route_stops rs
                JOIN districts d ON rs.district_id = d.id
                WHERE rs.route_id = %s
                ORDER BY rs.stop_order
                """,
                (route['id'],)
            )
            route['stops'] = stops
        
        return jsonify({
            'success': True,
            'data': routes
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# OLD ENDPOINT - MOVED TO system_params.py
# @api.route('/system-parameters', methods=['GET'])
# def get_system_parameters_old():
#     """
#     Sistem parametrelerini getir
#     
#     GET /system-parameters
#     
#     Response:
#         {
#             "success": true,
#             "data": {
#                 "cost_per_km": 5.0,
#                 "default_vehicle_count": 3
#             }
#         }
#     """
#     try:
#         params = execute_query("SELECT * FROM system_parameters LIMIT 1")
#         
#         if not params:
#             return jsonify({
#                 'success': False,
#                 'error': 'Sistem parametreleri bulunamadı'
#             }), 404
#         
#         return jsonify({
#             'success': True,
#             'data': params[0]
#         }), 200
#         
#     except Exception as e:
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500
