"""
Admin Kargo Yönetimi API
Admin tüm kullanıcılardan gelen kargoları görür ve yönetir
"""

from flask import Blueprint, request, jsonify, session
from config import get_connection, release_connection
from auth import admin_required
import traceback

admin_cargo_bp = Blueprint('admin_cargo', __name__)


@admin_cargo_bp.route('/admin/cargos/pending', methods=['GET'])
@admin_required
def get_pending_cargos():
    """
    Tüm bekleyen kargoları listeler (tüm kullanıcılardan)
    
    Query params:
    - user_id: Kullanıcıya göre filtrele (opsiyonel)
    - destination_id: Hedefe göre filtrele (opsiyonel)
    
    Response:
    {
        "success": True,
        "cargos": [
            {
                "id": 1,
                "user_id": 2,
                "username": "user1",
                "destination_id": 5,
                "destination": "Kandıra",
                "weight_kg": 150,
                "quantity": 3,
                "created_at": "...",
                "status": "pending"
            },
            ...
        ],
        "total_weight": 1250,
        "total_count": 15
    }
    """
    try:
        # Filter params
        user_id_filter = request.args.get('user_id', type=int)
        dest_id_filter = request.args.get('destination_id', type=int)
        
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Build query
        query = """
            SELECT 
                c.id,
                c.user_id,
                u.username,
                c.destination_district_id,
                d.name as destination,
                c.weight_kg,
                c.quantity,
                c.status,
                c.created_at
            FROM cargos c
            JOIN users u ON c.user_id = u.id
            JOIN districts d ON c.destination_district_id = d.id
            WHERE c.status = 'pending'
        """
        
        params = []
        
        if user_id_filter:
            query += " AND c.user_id = %s"
            params.append(user_id_filter)
        
        if dest_id_filter:
            query += " AND c.destination_district_id = %s"
            params.append(dest_id_filter)
        
        query += " ORDER BY c.created_at ASC"
        
        cur.execute(query, params)
        
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        cargos = []
        total_weight = 0
        
        for row in rows:
            cargo = dict(zip(cols, row))
            # Format date
            if cargo['created_at']:
                cargo['created_at'] = cargo['created_at'].strftime('%Y-%m-%d %H:%M')
            cargos.append(cargo)
            total_weight += cargo['weight_kg']
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'cargos': cargos,
            'total_count': len(cargos),
            'total_weight': total_weight
        })
        
    except Exception as e:
        print(f"❌ Admin pending cargos error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_cargo_bp.route('/admin/cargos/all', methods=['GET'])
@admin_required
def get_all_cargos():
    """
    Tüm kargoları listeler (tüm durumlar)
    
    Query params:
    - status: Duruma göre filtrele (opsiyonel)
    - user_id: Kullanıcıya göre filtrele (opsiyonel)
    
    Response: Benzer şekilde
    """
    try:
        status_filter = request.args.get('status')
        user_id_filter = request.args.get('user_id', type=int)
        
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        query = """
            SELECT 
                c.id,
                c.user_id,
                u.username,
                c.destination_district_id,
                d.name as destination,
                c.weight_kg,
                c.quantity,
                c.status,
                c.created_at,
                c.updated_at
            FROM cargos c
            JOIN users u ON c.user_id = u.id
            JOIN districts d ON c.destination_district_id = d.id
            WHERE 1=1
        """
        
        params = []
        
        if status_filter:
            query += " AND c.status = %s"
            params.append(status_filter)
        
        if user_id_filter:
            query += " AND c.user_id = %s"
            params.append(user_id_filter)
        
        query += " ORDER BY c.created_at DESC"
        
        cur.execute(query, params)
        
        cols = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        cargos = []
        
        for row in rows:
            cargo = dict(zip(cols, row))
            # Format dates
            if cargo['created_at']:
                cargo['created_at'] = cargo['created_at'].strftime('%Y-%m-%d %H:%M')
            if cargo['updated_at']:
                cargo['updated_at'] = cargo['updated_at'].strftime('%Y-%m-%d %H:%M')
            cargos.append(cargo)
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'cargos': cargos,
            'count': len(cargos)
        })
        
    except Exception as e:
        print(f"❌ Admin all cargos error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@admin_cargo_bp.route('/admin/cargos/<int:cargo_id>/status', methods=['PUT'])
@admin_required
def update_cargo_status(cargo_id):
    """
    Kargo durumunu günceller
    
    Request:
    {
        "status": "cancelled"  # or other status
    }
    """
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({
                'success': False,
                'error': 'Status gerekli'
            }),400
        
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE cargos
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (new_status, cargo_id))
        
        conn.commit()
        cur.close()
        release_connection(conn)
        
        print(f"✅ Kargo #{cargo_id} durumu güncellendi: {new_status}")
        
        return jsonify({
            'success': True,
            'message': 'Kargo durumu güncellendi'
        })
        
    except Exception as e:
        print(f"❌ Cargo status update error: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
