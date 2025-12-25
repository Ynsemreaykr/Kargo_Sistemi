"""
Sistem Parametreleri API
Admin panelden maliyet parametrelerini görüntüleme ve düzenleme
"""

from flask import Blueprint, request, jsonify, session
from config import execute_query, execute_insert
from auth import admin_required

params_bp = Blueprint('params', __name__)

@params_bp.route('/system-parameters', methods=['GET'])
def get_system_parameters():
    """
    Sistem parametrelerini getir
    GET /api/system-parameters
    """
    print("=" * 60)
    print("📊 GET /system-parameters called")
    print("=" * 60)
    
    try:
        from config import get_connection, release_connection
        
        print("1. Getting database connection...")
        conn = get_connection()
        if not conn:
            print("❌ Connection is None!")
            raise Exception("Veritabanı bağlantısı alınamadı")
        
        print("2. Connection obtained, creating cursor...")
        cur = conn.cursor()
        
        print("3. Executing vehicle_types query...")
        # Vehicle types'ı çek
        cur.execute("""
            SELECT id, name, capacity_kg, rental_cost
            FROM vehicle_types
            ORDER BY id
        """)
        
        print("4. Fetching results...")
        rows = cur.fetchall()
        print(f"5. Fetched {len(rows) if rows else 0} rows")
        
        vehicle_types = []
        
        if rows:
            print("6. Processing rows...")
            columns = [desc[0] for desc in cur.description]
            print(f"   Columns: {columns}")
            for i, row in enumerate(rows):
                vt = dict(zip(columns, row))
                vehicle_types.append(vt)
                print(f"   Row {i+1}: {vt}")
        else:
            print("⚠️  No rows returned from database!")
        
        print("7. Closing cursor and releasing connection...")
        cur.close()
        
        # Get cost_per_km from system_parameters
        print("8. Fetching cost_per_km from system_parameters...")
        cur2 = conn.cursor()
        cur2.execute("SELECT cost_per_km FROM system_parameters WHERE id = 1")
        cost_row = cur2.fetchone()
        cost_per_km = float(cost_row[0]) if cost_row else 1.0
        cur2.close()
        
        release_connection(conn)
        
        print(f"✓ System parameters loaded: {len(vehicle_types)} vehicle types, cost_per_km={cost_per_km}")
        
        # System parameters
        params = {
            'cost_per_km': cost_per_km,
            'rental_cost_default': 200.0,  # Deprecated
            'vehicle_types': vehicle_types
        }
        
        print(f"9. Returning params: {params}")
        print("=" * 60)
        
        return jsonify({
            'success': True,
            'data': params
        })
        
    except Exception as e:
        print(f"❌ System parameters error: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@params_bp.route('/system-parameters', methods=['PUT'])
@admin_required
def update_system_parameters():
    """
    Sistem parametrelerini güncelle (Admin only)
    Body: {
        "cost_per_km": 1.5,  // Optional: yakıt maliyeti
        "vehicle_costs": {   // Optional: araç başına kiralama
            "1": 200,
            "2": 250,
            "3": 300
        }
    }
    """
    try:
        from config import get_connection, release_connection
        
        data = request.json
        cost_per_km = data.get('cost_per_km')
        vehicle_costs = data.get('vehicle_costs', {})
        
        conn = get_connection()
        if not conn:
            raise Exception("Veritabanı bağlantısı alınamadı")
            
        cur = conn.cursor()
        
        # 1. cost_per_km güncelle (system_parameters tablosunda)
        if cost_per_km is not None:
            cur.execute("""
                UPDATE system_parameters 
                SET cost_per_km = %s, updated_at = NOW()
                WHERE id = 1
            """, (float(cost_per_km),))
            print(f"✓ Cost per km updated to {cost_per_km} TL/km")
        
        # 2. Her araç tipi için rental_cost güncelle
        for vehicle_id, rental_cost in vehicle_costs.items():
            cur.execute("""
                UPDATE vehicle_types 
                SET rental_cost = %s 
                WHERE id = %s
            """, (float(rental_cost), int(vehicle_id)))
            print(f"✓ Vehicle {vehicle_id} rental cost updated to {rental_cost} TL")
        
        conn.commit()
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'message': 'Parametreler güncellendi'
        })
        
    except Exception as e:
        print(f"❌ Update error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
