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
        
        
        # Create scenario
        cur.execute("""
            INSERT INTO scenarios 
            (created_at, algorithm, mode, scenario_type, total_cost, total_distance, remaining_cargos)
            VALUES (CURRENT_TIMESTAMP, %s, %s, %s, 0, 0, 0)
            RETURNING id
        """, (algorithm, mode, mode))  # scenario_type = mode for compatibility
        
        scenario_id = cur.fetchone()['id']
        
        # Call optimization algorithm
        # SIMPLIFIED VERSION - İleri de gerçek algoritma çalışacak
        total_cost = 0
        total_distance = 0
        delivered_count = len(cargos_data)
        remaining_count = 0
        
        # Update cargo statuses to in_transit
        cur.execute("""
            UPDATE cargos
            SET status = 'in_transit', updated_at = CURRENT_TIMESTAMP
            WHERE id = ANY(%s)
        """, (cargo_ids,))
        
        # Create dummy routes (gerçek algoritma için placeholder)
        # Her kargo delivery için basit route oluştur
        for cargo in cargos_data:
            cargo_id = cargo['id']
            dest_id = cargo['destination_district_id']
            weight = cargo['weight_kg']
            quantity = cargo['quantity']
            user_id_cargo = cargo['user_id']
            
            # Use the start_location determined above (from user selection or default)
            route_start = start_location if start_location else 12
            
            print(f"📍 Creating route for cargo {cargo_id}: Start={route_start} → Dest={dest_id}")
            
            # Get district coordinates for route geometry
            cur.execute("""
                SELECT id, name, latitude, longitude 
                FROM districts 
                WHERE id IN (%s, %s)
                ORDER BY id
            """, (route_start, dest_id))
            
            districts_list = cur.fetchall()
            
            # Basit maliyet hesabı
            estimated_distance = 50.0  # dummy
            estimated_cost = 250.0  # dummy
            
            total_distance += estimated_distance
            total_cost += estimated_cost
            
            # Create route geometry using OSM
            try:
                from osm_routing import get_route_geometry_osm
                
                # Route order: [start_location, dest_id]
                route_order = [start_location, dest_id]
                osm_geometry = get_route_geometry_osm(route_order, districts_list)
                
                # OSM returns FeatureCollection, store it
                route_geometry = osm_geometry
                print(f"✓ OSM geometry created for route: {districts_list[0]['name']} → {districts_list[-1]['name']}")
                
            except Exception as e:
                print(f"⚠️ OSM routing failed, using fallback: {e}")
                # Fallback: Simple LineString
                coordinates = []
                for d in districts_list:
                    coordinates.append([d['longitude'], d['latitude']])
                
                route_geometry = {
                    "type": "LineString",
                    "coordinates": coordinates
                }
            
            # Create route
            cur.execute("""
                INSERT INTO routes 
                (scenario_id, vehicle_id, total_distance, route_geometry, created_at)
                VALUES (%s, 1, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            """, (scenario_id, estimated_distance, json.dumps(route_geometry)))
            
            route_id = cur.fetchone()['id']
            
            # Add route details (stops)
            for idx, d in enumerate(districts_list):
                cur.execute("""
                    INSERT INTO route_details
                    (route_id, cargo_id, district_id, stop_order)
                    VALUES (%s, %s, %s, %s)
                """, (route_id, cargo_id if idx > 0 else None, d['id'], idx + 1))
            
            # Update vehicle's current location to this route's destination
            # So next route will start from where this one ended
            cur.execute("""
                UPDATE vehicles 
                SET current_location_district_id = %s
                WHERE id = 1
            """, (dest_id,))
            
            print(f"✅ Updated vehicle 1 location: {route_start} → {dest_id}")
        
        # Update scenario totals
        cur.execute("""
            UPDATE scenarios
            SET total_cost = %s,
                total_distance = %s,
                remaining_cargos = %s
            WHERE id = %s
        """, (total_cost, total_distance, remaining_count, scenario_id))
        
        conn.commit()
        cur.close()
        release_connection(conn)
        
        print(f"✅ Dağıtım oluşturuldu: Scenario #{scenario_id}, Mode={mode}, Kargo={delivered_count}")
        
        return jsonify({
            'success': True,
            'scenario_id': scenario_id,
            'delivered_count': delivered_count,
            'remaining_count': remaining_count,
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
