"""
Senaryo Detay API
Her aracın maliyeti ve taşıdığı kargoları gösterir
"""

from flask import Blueprint, jsonify
from config import execute_query, get_connection, release_connection

def get_scenario_details(scenario_id):
    """
    Senaryo detaylarını getir
    
    Returns:
    {
        "scenario": {...},
        "vehicles": [
            {
                "vehicle_id": 1,
                "vehicle_type": "Küçük Araç",
                "capacity_kg": 500,
                "rental_cost": 200,
                "route": {
                    "stops": 5,
                    "distance_km": 45.2,
                    "fuel_cost": 45.2,
                    "total_cost": 245.2
                },
                "cargo_users": [...]
            }
        ]
    }
    """
    
    try:
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # 1. Get scenario info
        cur.execute("""
            SELECT id, created_at, algorithm, total_cost, total_distance
            FROM scenarios
            WHERE id = %s
        """, (scenario_id,))
        
        scenario_row = cur.fetchone()
        if not scenario_row:
            cur.close()
            release_connection(conn)
            return None
        
        scenario_cols = [desc[0] for desc in cur.description]
        scenario = dict(zip(scenario_cols, scenario_row))
        
        # 2. Get cost_per_km from system_parameters
        cur.execute("SELECT cost_per_km FROM system_parameters WHERE id = 1")
        cost_row = cur.fetchone()
        cost_per_km = float(cost_row[0]) if cost_row else 1.0
        
        # 3. Get routes for this scenario with vehicle info
        cur.execute("""
            SELECT 
                r.id as route_id,
                r.vehicle_id,
                r.total_distance,
                v.vehicle_type_id,
                vt.name as vehicle_type,
                vt.capacity_kg,
                vt.rental_cost
            FROM routes r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            WHERE r.scenario_id = %s
            ORDER BY r.vehicle_id
        """, (scenario_id,))
        
        route_rows = cur.fetchall()
        route_cols = [desc[0] for desc in cur.description]
        
        vehicles_data = []
        
        for route_row in route_rows:
            route_dict = dict(zip(route_cols, route_row))
            route_id = route_dict['route_id']
            
            # Calculate costs
            distance_km = float(route_dict['total_distance'] or 0)
            rental_cost = float(route_dict['rental_cost'] or 200)
            fuel_cost = distance_km * cost_per_km
            total_cost = fuel_cost + rental_cost
            
            # Get number of stops (distinct districts in route)
            cur.execute("""
                SELECT COUNT(DISTINCT district_id) 
                FROM route_details 
                WHERE route_id = %s
            """, (route_id,))
            stops = cur.fetchone()[0]
            
            # Get cargos for this route
            cur.execute("""
                SELECT 
                    c.id as cargo_id,
                    u.username,
                    c.weight_kg,
                    d.name as destination
                FROM route_details rd
                JOIN cargos c ON rd.cargo_id = c.id
                JOIN users u ON c.user_id = u.id
                JOIN districts d ON c.destination_district_id = d.id
                WHERE rd.route_id = %s
                ORDER BY rd.stop_order
            """, (route_id,))
            
            cargo_rows = cur.fetchall()
            cargo_cols = [desc[0] for desc in cur.description]
            cargo_users = [dict(zip(cargo_cols, crow)) for crow in cargo_rows]
            
            # Build vehicle data
            vehicle_data = {
                'vehicle_id': route_dict['vehicle_id'],
                'vehicle_type': route_dict['vehicle_type'],
                'capacity_kg': route_dict['capacity_kg'],
                'rental_cost': rental_cost,
                'route': {
                    'stops': stops,
                    'distance_km': round(distance_km, 2),
                    'fuel_cost': round(fuel_cost, 2),
                    'total_cost': round(total_cost, 2)
                },
                'cargo_users': cargo_users
            }
            
            vehicles_data.append(vehicle_data)
        
        cur.close()
        release_connection(conn)
        
        return {
            'scenario': scenario,
            'vehicles': vehicles_data,
            'cost_per_km': cost_per_km
        }
        
    except Exception as e:
        print(f"Error getting scenario details: {e}")
        import traceback
        traceback.print_exc()
        return None


# Flask route
from flask import Blueprint
api_details = Blueprint('scenario_details', __name__)

@api_details.route('/scenarios/<int:scenario_id>/details', methods=['GET'])
def get_scenario_details_endpoint(scenario_id):
    """
    GET /api/scenarios/<id>/details
    
    Returns detailed scenario information including:
    - Scenario metadata
    - Vehicle-by-vehicle breakdown
    - Cost calculations
    - Cargo assignments
    """
    
    details = get_scenario_details(scenario_id)
    
    if details is None:
        return jsonify({
            'success': False,
            'error': 'Senaryo bulunamadı'
        }), 404
    
    return jsonify({
        'success': True,
        'data': details
    }), 200
