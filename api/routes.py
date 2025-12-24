"""
Kargo İşletme Sistemi - API Routes
Flask endpoint'leri
"""

from flask import Blueprint, request, jsonify
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
        algorithm_choice = data.get('algorithm', 'hybrid')  # greedy, sa, hybrid
        cargos = data.get('cargos', [])
        
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
        
        # Mesafe matrisini hesapla (OSM ile - cache kullanarak)
        use_osm = data.get('use_osm', True)  # Default: OSM kullan
        
        try:
            if use_osm:
                print("🗺️ OSM ile gerçek yol mesafeleri kullanılıyor...")
                distance_matrix = calculate_distance_matrix_osm(
                    districts, 
                    use_cache=True,
                    use_osm=True
                )
            else:
                print("📐 Haversine (kuş uçuşu) mesafeler kullanılıyor...")
                distance_matrix = calculate_distance_matrix(districts)
        except Exception as e:
            print(f"⚠️ OSM hatası, Haversine fallback: {e}")
            distance_matrix = calculate_distance_matrix(districts)
            use_osm = False  # Fallback olduğunu işaretle
        
        # Araçları ve araç tiplerini al
        vehicles_query = """
            SELECT v.id, v.vehicle_type_id, vt.capacity_kg, vt.rental_cost, vt.cost_per_km, vt.name as type_name
            FROM vehicles v
            JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            WHERE v.is_rented = FALSE
            LIMIT %s
        """
        vehicles = execute_query(vehicles_query, (params['default_vehicle_count'],))
        
        if not vehicles:
            return jsonify({
                'success': False,
                'error': 'Kullanılabilir araç bulunamadı'
            }), 400
        
        # Kargoları veritabanına kaydet
        cargo_ids = []
        for cargo in cargos:
            cargo_id = execute_insert(
                "INSERT INTO cargo (district_id, weight_kg, quantity) VALUES (%s, %s, %s)",
                (cargo['district_id'], cargo['weight_kg'], cargo['quantity'])
            )
            cargo_ids.append(cargo_id)
        
        # ===== AŞAMA 3: GERÇEK ALGORİTMA =====
        # 1. Greedy (Nearest Neighbor) ile başlangıç rotaları oluştur
        print(f"🔧 Algoritma: {algorithm_choice}")
        print(f"📦 Kargo sayısı: {len(cargos)}")
        print(f"🚛 Araç sayısı: {len(vehicles)}")
        
        initial_routes = nearest_neighbor_algorithm(
            cargos, 
            districts, 
            vehicles,
            start_district_id=12  # İzmit
        )
        
        print(f"✓ Greedy rotalar oluşturuldu: {len(initial_routes)} rota")
        
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
        for route in routes:
            # Araç bilgisini al
            vehicle = next((v for v in vehicles if v['id'] == route['vehicle_id']), None)
            if vehicle:
                route['cost'] = calculate_route_cost(
                    route['total_distance_km'],
                    vehicle
                )
        
        # Toplam maliyet ve mesafe
        total_cost = sum(r['cost'] for r in routes)
        total_distance = sum(r['total_distance_km'] for r in routes)
        
        print(f"💰 Toplam Maliyet: {total_cost} TL")
        print(f"📏 Toplam Mesafe: {total_distance} km")
        
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

@api.route('/system-parameters', methods=['GET'])
def get_system_parameters():
    """
    Sistem parametrelerini getir
    
    GET /system-parameters
    
    Response:
        {
            "success": true,
            "data": {
                "cost_per_km": 5.0,
                "default_vehicle_count": 3
            }
        }
    """
    try:
        params = execute_query("SELECT * FROM system_parameters LIMIT 1")
        
        if not params:
            return jsonify({
                'success': False,
                'error': 'Sistem parametreleri bulunamadı'
            }), 404
        
        return jsonify({
            'success': True,
            'data': params[0]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
