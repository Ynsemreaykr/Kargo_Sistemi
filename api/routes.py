"""
Kargo İşletme Sistemi - API Routes
Flask endpoint'leri
"""

from flask import Blueprint, request, jsonify
from config import execute_query, execute_insert
from utils import generate_dummy_routes, create_route_geometry

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
    Yeni senaryo oluştur (AŞAMA 1 - Dummy rota üretimi)
    
    POST /scenarios
    Body:
        {
            "scenario_type": "LIMITED" | "UNLIMITED",
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
                "total_distance": 120.5
            }
        }
    """
    try:
        data = request.get_json()
        scenario_type = data.get('scenario_type', 'LIMITED')
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
        
        # Araçları ve araç tiplerini al
        vehicles_query = """
            SELECT v.id, v.vehicle_type_id, vt.capacity_kg, vt.rental_cost, vt.name as type_name
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
        
        # Dummy rotalar üret
        routes = generate_dummy_routes(cargos, vehicles, districts, cost_per_km)
        
        # Toplam maliyet ve mesafe
        total_cost = sum(r['cost'] for r in routes)
        total_distance = sum(r['distance'] for r in routes)
        
        # Senaryoyu kaydet
        scenario_id = execute_insert(
            "INSERT INTO scenarios (scenario_type, total_cost, total_distance) VALUES (%s, %s, %s)",
            (scenario_type, total_cost, total_distance)
        )
        
        # Rotaları kaydet
        for route in routes:
            # Rota geometrisini oluştur
            geometry = create_route_geometry(districts, route['district_ids'])
            
            # Rotayı kaydet
            route_id = execute_insert(
                "INSERT INTO routes (scenario_id, vehicle_id, distance, cost, route_geometry) VALUES (%s, %s, %s, %s, %s)",
                (scenario_id, route['vehicle_id'], route['distance'], route['cost'], str(geometry).replace("'", '"'))
            )
            
            # Rota duraklarını kaydet
            for order, district_id in enumerate(route['district_ids'], start=1):
                execute_insert(
                    "INSERT INTO route_stops (route_id, district_id, stop_order) VALUES (%s, %s, %s)",
                    (route_id, district_id, order),
                    return_id=False
                )
        
        return jsonify({
            'success': True,
            'data': {
                'scenario_id': scenario_id,
                'total_cost': total_cost,
                'total_distance': total_distance,
                'route_count': len(routes)
            }
        }), 201
        
    except Exception as e:
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
