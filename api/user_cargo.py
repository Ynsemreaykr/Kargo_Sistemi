"""
Kullanıcı Kargo Yönetimi API
Kullanıcılar kargo gönderir, görüntüler, takip eder
"""

from flask import Blueprint, request, jsonify, session
from config import get_connection, release_connection
from auth import login_required
import traceback

user_cargo_bp = Blueprint('user_cargo', __name__)


@user_cargo_bp.route('/user/cargos', methods=['POST'])
@login_required
def create_cargo():
    """
    Kullanıcı yeni kargo oluşturur
    
    Request:
    {
        "destination_district_id": 5,
        "weight_kg": 150,
        "quantity": 3
    }
    
    Response:
    {
        "success": True,
        "cargo_id": 123,
        "status": "pending"
    }
    """
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        destination_id = data.get('destination_district_id')
        weight_kg = data.get('weight_kg')
        quantity = data.get('quantity', 1)
        
        # Validation
        if not destination_id or not weight_kg:
            return jsonify({
                'success': False,
                'error': 'Hedef şube ve ağırlık gerekli'
            }), 400
        
        if weight_kg <= 0 or weight_kg > 1000:
            return jsonify({
                'success': False,
                'error': 'Ağırlık 0-1000 kg arasında olmalı'
            }), 400
        
        if quantity <= 0:
            return jsonify({
                'success': False,
                'error': 'Adet 0\'dan büyük olmalı'
            }), 400
        
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Insert cargo
        cur.execute("""
            INSERT INTO cargos 
            (user_id, destination_district_id, weight_kg, quantity, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, 'pending', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
        """, (user_id, destination_id, weight_kg, quantity))
        
        cargo_id = cur.fetchone()[0]
        
        conn.commit()
        cur.close()
        release_connection(conn)
        
        print(f"✅ Kargo oluşturuldu: ID={cargo_id}, User={user_id}, Hedef={destination_id}")
        
        return jsonify({
            'success': True,
            'cargo_id': cargo_id,
            'status': 'pending',
            'message': 'Kargo başarıyla oluşturuldu. Yönetici onayı bekleniyor.'
        }), 201
        
    except Exception as e:
        print(f"❌ Kargo oluşturma hatası: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_cargo_bp.route('/user/cargos/my', methods=['GET'])
@login_required
def get_my_cargos():
    """
    Kullanıcının kargolarını listeler
    
    Response:
    {
        "success": True,
        "cargos": [
            {
                "id": 1,
                "destination": "Kandıra",
                "weight_kg": 150,
                "quantity": 3,
                "status": "pending",
                "created_at": "2025-12-27 10:00:00"
            },
            ...
        ]
    }
    """
    try:
        user_id = session.get('user_id')
        
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Get user's cargos with destination info
        cur.execute("""
            SELECT 
                c.id,
                c.destination_district_id,
                d.name as destination,
                c.weight_kg,
                c.quantity,
                c.status,
                c.created_at,
                c.updated_at
            FROM cargos c
            JOIN districts d ON c.destination_district_id = d.id
            WHERE c.user_id = %s
            ORDER BY c.created_at DESC
        """, (user_id,))
        
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
        print(f"❌ Kargo listeleme hatası: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@user_cargo_bp.route('/user/cargos/<int:cargo_id>', methods=['GET'])
@login_required
def get_cargo_details(cargo_id):
    """
    Kargo detaylarını getirir
    
    Response:
    {
        "success": True,
        "cargo": {
            "id": 1,
            "destination": "Kandıra",
            "weight_kg": 150,
            "quantity": 3,
            "status": "in_transit",
            "created_at": "...",
            "route_text": "İzmit → Gebze → Kandıra"  # if in_transit
        }
    }
    """
    try:
        user_id = session.get('user_id')
        
        conn = get_connection()
        if not conn:
            raise Exception("Database connection failed")
        
        cur = conn.cursor()
        
        # Get cargo with destination
        cur.execute("""
            SELECT 
                c.id,
                c.user_id,
                c.destination_district_id,
                d.name as destination,
                c.weight_kg,
                c.quantity,
                c.status,
                c.created_at,
                c.updated_at
            FROM cargos c
            JOIN districts d ON c.destination_district_id = d.id
            WHERE c.id = %s
        """, (cargo_id,))
        
        row = cur.fetchone()
        
        if not row:
            return jsonify({
                'success': False,
                'error': 'Kargo bulunamadı'
            }), 404
        
        cols = [desc[0] for desc in cur.description]
        cargo = dict(zip(cols, row))
        
        # Check ownership
        if cargo['user_id'] != user_id:
            return jsonify({
                'success': False,
                'error': 'Bu kargoya erişim yetkiniz yok'
            }), 403
        
        # Format dates
        if cargo['created_at']:
            cargo['created_at'] = cargo['created_at'].strftime('%Y-%m-%d %H:%M')
        if cargo['updated_at']:
            cargo['updated_at'] = cargo['updated_at'].strftime('%Y-%m-%d %H:%M')
        
        # If in_transit, get route
        route_text = None
        if cargo['status'] == 'in_transit':
            # Find route containing this cargo
            cur.execute("""
                SELECT r.id, r.scenario_id
                FROM routes r
                JOIN route_details rd ON r.id = rd.route_id
                WHERE rd.cargo_id = %s
                LIMIT 1
            """, (cargo_id,))
            
            route_row = cur.fetchone()
            if route_row:
                route_id = route_row[0]
                
                # Get route stops
                cur.execute("""
                    SELECT DISTINCT d.name
                    FROM route_details rd
                    JOIN districts d ON rd.district_id = d.id
                    WHERE rd.route_id = %s
                    ORDER BY rd.stop_order
                """, (route_id,))
                
                stops = [r[0] for r in cur.fetchall()]
                route_text = " → ".join(stops)
        
        cargo['route_text'] = route_text
        
        cur.close()
        release_connection(conn)
        
        return jsonify({
            'success': True,
            'cargo': cargo
        })
        
    except Exception as e:
        print(f"❌ Kargo detay hatası: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
