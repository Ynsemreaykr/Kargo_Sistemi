"""
Admin Dağıtım İşlemi API
Seçili kargolarla senaryo oluşturur (LIMITED/UNLIMITED mod)
"""

from flask import Blueprint, request, jsonify, session
from config import get_connection, release_connection
from auth import admin_required
from psycopg.rows import dict_row
import traceback
import json

admin_distribution_bp = Blueprint('admin_distribution', __name__)


@admin_distribution_bp.route('/admin/distribution/create', methods=['POST'])
@admin_required
def create_distribution():
    """
    Admin seçili kargolarla dağıtım oluşturur
    
    Request:
    {
        "cargo_ids": [1, 2, 3, 4, 5],
        "mode": "LIMITED" | "UNLIMITED",
        "algorithm": "hybrid" | "greedy" | "simulated_annealing"
    }
    
    Response:
    {
        "success": True,
        "scenario_id": 10,
        "delivered_count": 12,
        "remaining_count": 3,
        "total_cost": 850.50,
        "total_distance": 120.5
    }
    """
    try:
        data = request.get_json()
        cargo_ids = data.get('cargo_ids', [])
        mode = data.get('mode', 'LIMITED')
        algorithm = data.get('algorithm', 'hybrid')
        vehicle_start_locations = data.get('vehicle_start_locations', {})
        vehicle_end_locations = data.get('vehicle_end_locations', {})
        
        print(f"\n{'='*60}")
        print(f"📦 CREATE DISTRIBUTION REQUEST")
        print(f"{'='*60}")
        print(f"Vehicle start locations received: {vehicle_start_locations}")
        print(f"Vehicle end locations received: {vehicle_end_locations}")
        print(f"{'='*60}\n")
        
        if not cargo_ids:
            return jsonify({'success': False, 'error': 'Kargo seçilmedi'}), 400
        
        # Get user_id from session
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Oturum bulunamadı'}), 401
        
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Determine vehicle starting location
        # Priority: 1) Manual selection, 2) Last known location from DB, 3) Default (Kandıra)
        if vehicle_start_locations.get('all'):
            start_location = vehicle_start_locations.get('all')
            print(f"🚗 Using SELECTED start location: {start_location}")
        else:
            # Query vehicle's last known location from database
            cur.execute("""
                SELECT current_location_district_id 
                FROM vehicles 
                WHERE id = 1
                LIMIT 1
            """)
            vehicle_data = cur.fetchone()
            
            if vehicle_data and vehicle_data['current_location_district_id']:
                start_location = vehicle_data['current_location_district_id']
                print(f"🚗 Using vehicle's LAST KNOWN location: {start_location}")
            else:
                start_location = 12  # Fallback to Kandıra if no data
                print(f"🚗 Using DEFAULT location (Kandıra): {start_location}")
        
        end_location = vehicle_end_locations.get('all') or None
        
        print(f"{'='*60}")
        print(f"🚗 Final start_location: {start_location} (type: {type(start_location)})")
        print(f"🏁 Final end_location: {end_location}")
        print(f"{'='*60}\n")
        
        # Get cargo details
        cur.execute("""
            SELECT 
                c.id,
                c.destination_district_id,
                c.weight_kg,
                c.quantity,
                c.user_id
            FROM cargos c
            WHERE c.id = ANY(%s) AND c.status = 'pending'
        """, (cargo_ids,))
        
        cargos_data = cur.fetchall()
        
        if not cargos_data:
            return jsonify({
                'success': False,
                'error': 'Geçerli kargo bulunamadı'
            }), 400
        
        
        # Get system parameters
        cur.execute("SELECT cost_per_km FROM system_parameters LIMIT 1")
        params = cur.fetchone()
        system_params = {'cost_per_km': params['cost_per_km'] if params else 5.0}
        
        # Initialize optimizer
        from distribution_optimizer import DistributionOptimizer
        optimizer = DistributionOptimizer(cur, system_params)
        
        # Run optimization
        print(f"\n🚀 Running optimization algorithm...")
        print(f"   Mode: {mode}")
        print(f"   Cargos: {len(cargos_data)}")
        print(f"   Start location: {start_location}\n")
        
        result = optimizer.optimize_distribution(
            cargos=[dict(c) for c in cargos_data],
            mode=mode,
            start_location=start_location
        )
        
        if not result['success']:
            # Optimization failed (e.g., insufficient vehicles in LIMITED mode)
            print(f"❌ Optimization failed: {result['error']}")
            
            conn.rollback()
            cur.close()
            release_connection(conn)
            
            return jsonify({
                'success': False,
                'error': result['error'],
                'remaining_cargos': len(result.get('remaining_cargos', [])),
                'total_remaining_weight': result.get('total_remaining_weight', 0)
            }), 400
        
        # Optimization successful - create scenario with actual totals
        print(f"✅ Optimization successful!")
        print(f"   Vehicles used: {result['vehicle_count']}")
        print(f"   Total distance: {result['total_distance']:.2f} km")
        print(f"   Total cost: {result['total_cost']:.2f} TL\n")
        
        total_cost = result['total_cost']
        total_distance = result['total_distance']
        delivered_count = result['delivered_count']
        
        # Create scenario
        cur.execute("""
            INSERT INTO scenarios 
            (created_at, algorithm, mode, scenario_type, total_cost, total_distance, remaining_cargos)
            VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, 0)
            RETURNING id
        """, (algorithm, mode, mode, total_cost, total_distance))
        
        scenario_id = cur.fetchone()['id']
        
        # Update cargo statuses
        cur.execute("""
            UPDATE cargos
            SET status = 'in_transit', updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(%s)
        """, (cargo_ids,))
        
        # Create routes from optimization result
        for route_data in result['routes']:
            vehicle = route_data['vehicle']
            cargos_in_route = route_data['cargos']
            route_order = route_data['route_order']
            route_distance = route_data['distance']
            route_cost = route_data['cost']
            
            print(f"\n📍 Creating route:")
            print(f"   Vehicle: {vehicle['name']} ({vehicle['capacity_kg']} kg)")
            print(f"   Weight: {route_data['total_weight']:.1f} kg ({route_data['utilization']:.1f}% full)")
            print(f"   Distance: {route_distance:.2f} km")
            print(f"   Cost: {route_cost:.2f} TL")
            print(f"   Stops: {len(route_order)}")
            
            # Get district details for geometry
            cur.execute("""
                SELECT id, name, latitude, longitude
                FROM districts
                WHERE id = ANY(%s)
                ORDER BY id
            """, (route_order,))
            
            districts_list = cur.fetchall()
            
            # Create route geometry
            try:
                from osm_routing import get_route_geometry_osm
                osm_geometry = get_route_geometry_osm(route_order, districts_list)
                route_geometry = osm_geometry
            except Exception as e:
                print(f"⚠️ OSM routing failed: {e}")
                # Fallback geometry
                coordinates = [[d['longitude'], d['latitude']] for d in districts_list]
                route_geometry = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            
            # Determine vehicle_id (use existing or create rental)
            if vehicle.get('is_rented'):
                # For rental, we'll use vehicle_id = 1 for now
                # TODO: Create rental vehicle records
                vehicle_id = 1
            else:
                vehicle_id = vehicle.get('vehicle_id', 1)
            
            # Insert route
            cur.execute("""
                INSERT INTO routes
                (scenario_id, vehicle_id, total_distance, route_geometry, created_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (scenario_id, vehicle_id, route_distance, json.dumps(route_geometry)))
            
            route_id = cur.fetchone()['id']
            
            # Insert route details (stops)
            for idx, district_id in enumerate(route_order):
                # Find cargos for this district
                cargos_for_district = [c for c in cargos_in_route if c['destination_district_id'] == district_id]
                
                if cargos_for_district:
                    # Insert stop with cargo
                    for cargo in cargos_for_district:
                        cur.execute("""
                            INSERT INTO route_details
                            (route_id, cargo_id, district_id, stop_order)
                            VALUES (%s, %s, %s, %s)
                        """, (route_id, cargo['id'], district_id, idx + 1))
                else:
                    # Insert stop without cargo (start/intermediate point)
                    cur.execute("""
                        INSERT INTO route_details
                        (route_id, cargo_id, district_id, stop_order)
                        VALUES (%s, NULL, %s, %s)
                    """, (route_id, district_id, idx + 1))
            
            print(f"✅ Route {route_id} created")
        
        conn.commit()
        cur.close()
        release_connection(conn)
        
        print(f"✅ Dağıtım oluşturuldu: Scenario #{scenario_id}, Mode={mode}, Kargo={delivered_count}")
        
        return jsonify({
            'success': True,
            'scenario_id': scenario_id,
            'delivered_count': delivered_count,
            'remaining_count': 0,  # All cargos delivered in successful optimization
            'total_cost': round(total_cost, 2),
            'total_distance': round(total_distance, 2),
            'mode': mode
        }), 201
        
    except Exception as e:
        print(f"❌ Distribution create error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
