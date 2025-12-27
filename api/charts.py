"""
Charts API - Admin Dashboard Grafikler
Maliyet trendi, algoritma karşılaştırma, araç kullanımı
"""

from flask import Blueprint, jsonify, session
from config import get_connection, release_connection
from auth import admin_required

charts_bp = Blueprint('charts', __name__)

@charts_bp.route('/charts/cost-trends', methods=['GET'])
@admin_required
def get_cost_trends():
    """
    Son 10 senaryonun maliyet trendi
    
    Returns:
    {
        "labels": ["25.12.2025 10:00", ...],
        "data": [450, 520, ...]
    }
    """
    try:
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Get last 10 scenarios with their costs
        cur.execute("""
            SELECT 
                id,
                created_at,
                total_cost
            FROM scenarios
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        rows = cur.fetchall()
        
        # Reverse to show oldest first (left to right)
        rows = list(reversed(rows))
        
        labels = []
        data = []
        
        for row in rows:
            scenario_id, created_at, total_cost = row
            # Format date
            labels.append(f"Senaryo #{scenario_id}")
            data.append(float(total_cost) if total_cost else 0)
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'data': data
            }
        })
        
    except Exception as e:
        print(f"Cost trends error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@charts_bp.route('/charts/algorithm-comparison', methods=['GET'])
@admin_required
def get_algorithm_comparison():
    """
    Algoritmaların ortalama maliyet karşılaştırması
    
    Returns:
    {
        "labels": ["Greedy", "SA", "Hybrid"],
        "data": [500, 450, 425]
    }
    """
    try:
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Get average cost per algorithm
        cur.execute("""
            SELECT 
                algorithm,
                AVG(total_cost) as avg_cost,
                COUNT(*) as count
            FROM scenarios
            GROUP BY algorithm
            ORDER BY algorithm
        """)
        
        rows = cur.fetchall()
        
        labels = []
        data = []
        counts = []
        
        # Map algorithm names to readable Turkish
        algo_names = {
            'greedy': 'Greedy',
            'simulated_annealing': 'Simulated Annealing',
            'hybrid': 'Hybrid',
            'sa': 'Simulated Annealing'
        }
        
        for row in rows:
            algorithm, avg_cost, count = row
            algo_display = algo_names.get(algorithm.lower(), algorithm.upper())
            labels.append(algo_display)
            data.append(round(float(avg_cost) if avg_cost else 0, 2))
            counts.append(count)
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'data': data,
                'counts': counts
            }
        })
        
    except Exception as e:
        print(f"Algorithm comparison error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@charts_bp.route('/charts/vehicle-usage', methods=['GET'])
@admin_required
def get_vehicle_usage():
    """
    Araç tipi kullanım dağılımı
    
    Returns:
    {
        "labels": ["Küçük (500kg)", "Orta (750kg)", "Büyük (1000kg)"],
        "data": [45, 30, 25]
    }
    """
    try:
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Get vehicle usage by type
        cur.execute("""
            SELECT 
                vt.name,
                vt.capacity_kg,
                COUNT(r.id) as usage_count
            FROM routes r
            JOIN vehicles v ON r.vehicle_id = v.id
            JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
            GROUP BY vt.id, vt.name, vt.capacity_kg
            ORDER BY vt.capacity_kg
        """)
        
        rows = cur.fetchall()
        
        labels = []
        data = []
        
        for row in rows:
            name, capacity, count = row
            labels.append(f"{name} ({capacity}kg)")
            data.append(count)
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'data': {
                'labels': labels,
                'data': data
            }
        })
        
    except Exception as e:
        print(f"Vehicle usage error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
