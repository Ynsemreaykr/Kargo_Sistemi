"""
Admin Logs API
Provides endpoints for viewing distribution logs and reports
"""

from flask import Blueprint, jsonify, session
from config import get_connection, release_connection
from auth import login_required, admin_required
from psycopg.rows import dict_row
import traceback

admin_logs_api = Blueprint('admin_logs', __name__)

@admin_logs_api.route('/admin/logs', methods=['GET'])
@login_required
@admin_required
def get_all_logs():
    """
    Get all distribution scenarios with summary info
    
    Returns:
        List of scenarios with user info, costs, routes, cargo counts
    """
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Query all scenarios with aggregated data and user info from cargos
        cur.execute("""
            SELECT 
                s.id as scenario_id,
                s.scenario_type as mode,
                s.total_cost,
                s.total_distance,
                s.created_at,
                COUNT(DISTINCT r.id) as route_count,
                COUNT(DISTINCT rd.cargo_id) as cargo_count,
                MIN(u.username) as username
            FROM scenarios s
            LEFT JOIN routes r ON r.scenario_id = s.id
            LEFT JOIN route_details rd ON rd.route_id = r.id
            LEFT JOIN cargos c ON c.id = rd.cargo_id
            LEFT JOIN users u ON u.id = c.user_id
            GROUP BY s.id, s.scenario_type, s.total_cost, s.total_distance, s.created_at
            ORDER BY s.created_at DESC
            LIMIT 100
        """)
        
        scenarios = cur.fetchall()
        
        # Format response
        logs = []
        for scenario in scenarios:
            logs.append({
                'scenario_id': scenario['scenario_id'],
                'mode': scenario['mode'] or 'LIMITED',
                'algorithm': 'hybrid',  # Default since not in DB
                'total_cost': float(scenario['total_cost']) if scenario['total_cost'] else 0,
                'total_distance': float(scenario['total_distance']) if scenario['total_distance'] else 0,
                'delivered_count': scenario['cargo_count'] or 0,  # Use cargo_count from join
                'remaining_count': 0,  # Not tracked in current schema
                'route_count': scenario['route_count'] or 0,
                'cargo_count': scenario['cargo_count'] or 0,
                'created_at': scenario['created_at'].isoformat() if scenario['created_at'] else None,
                'user': {
                    'username': scenario['username'] if scenario.get('username') else 'Bilinmiyor',
                    'email': None
                }
            })
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'data': logs
        }), 200
        
    except Exception as e:
        print(f"❌ Logs fetch error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_logs_api.route('/admin/logs/<int:scenario_id>', methods=['GET'])
@login_required
@admin_required
def get_log_details(scenario_id):
    """
    Get detailed information for a specific scenario
    
    Returns:
        Scenario details with routes, costs, and cargo information
    """
    try:
        conn = get_connection()
        if not conn:
            return jsonify({'success': False, 'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(row_factory=dict_row)
        
        # Get scenario details
        cur.execute("""
            SELECT s.*
            FROM scenarios s
            WHERE s.id = %s
        """, (scenario_id,))
        
        scenario = cur.fetchone()
        
        if not scenario:
            cur.close()
            release_connection(conn)
            return jsonify({'success': False, 'error': 'Scenario not found'}), 404
        
        # Get routes with details including vehicle types and cargo weights
        cur.execute("""
            SELECT 
                r.id as route_id,
                r.vehicle_id,
                r.total_distance,
                vt.name as vehicle_type_name,
                vt.capacity_kg,
                COALESCE(SUM(c.weight_kg * c.quantity), 0) as total_weight
            FROM routes r
            LEFT JOIN vehicles v ON v.id = r.vehicle_id
            LEFT JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
            LEFT JOIN route_details rd ON rd.route_id = r.id
            LEFT JOIN cargos c ON c.id = rd.cargo_id
            WHERE r.scenario_id = %s
            GROUP BY r.id, r.vehicle_id, r.total_distance, vt.name, vt.capacity_kg
            ORDER BY r.id
        """, (scenario_id,))
        
        routes = cur.fetchall()
        
        # Get route details and cargos for each route
        routes_data = []
        for route in routes:
            cur.execute("""
                SELECT 
                    rd.stop_order,
                    rd.cargo_id,
                    c.weight_kg,
                    c.quantity,
                    d.name as district_name,
                    d.id as district_id
                FROM route_details rd
                LEFT JOIN cargos c ON c.id = rd.cargo_id
                LEFT JOIN districts d ON d.id = rd.district_id
                WHERE rd.route_id = %s
                ORDER BY rd.stop_order
            """, (route['route_id'],))
            
            stops = cur.fetchall()
            
            routes_data.append({
                'route_id': route['route_id'],
                'vehicle_id': route['vehicle_id'],
                'vehicle_type_name': route['vehicle_type_name'] or 'Bilinmiyor',
                'capacity_kg': int(route['capacity_kg']) if route['capacity_kg'] else 500,
                'total_weight': float(route['total_weight']) if route['total_weight'] else 0,
                'total_distance': float(route['total_distance']) if route['total_distance'] else 0,
                'route_geometry': None,
                'stops': [
                    {
                        'stop_order': stop['stop_order'],
                        'cargo_id': stop['cargo_id'],
                        'district_name': stop['district_name'],
                        'district_id': stop['district_id'],
                        'weight_kg': float(stop['weight_kg']) if stop['weight_kg'] else 0,
                        'quantity': stop['quantity']
                    }
                    for stop in stops
                ]
            })
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'data': {
                'scenario': {
                    'id': scenario['id'],
                    'mode': scenario['scenario_type'] if 'scenario_type' in scenario else 'LIMITED',
                    'algorithm': 'hybrid',  # Default
                    'total_cost': float(scenario['total_cost']) if scenario['total_cost'] else 0,
                    'total_distance': float(scenario['total_distance']) if scenario['total_distance'] else 0,
                    'delivered_count': len(routes_data),  # Count from routes
                    'remaining_count': 0,  # Not tracked
                    'created_at': scenario['created_at'].isoformat() if scenario['created_at'] else None,
                    'user': {
                        'username': 'admin',
                        'email': None
                    }
                },
                'routes': routes_data
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Log details fetch error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


print("✓ Admin logs API registered")
