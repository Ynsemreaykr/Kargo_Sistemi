"""
Kargo İşletme Sistemi - Authentication Module
Session-based kullanıcı kimlik doğrulama
"""

from flask import Blueprint, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import execute_query, execute_insert
from functools import wraps

auth = Blueprint('auth', __name__)

# ===========================
# Middleware: Login Required
# ===========================
def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Giriş yapmanız gerekiyor',
                'auth_required': True
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to protect admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({
                'success': False,
                'error': 'Giriş yapmanız gerekiyor',
                'auth_required': True
            }), 401
        
        if session.get('role') != 'ADMIN':
            return jsonify({
                'success': False,
                'error': 'Bu işlem için admin yetkisi gerekiyor'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function

# ===========================
# Login Endpoint
# ===========================
@auth.route('/login', methods=['POST'])
def login():
    """
    Kullanıcı girişi
    
    POST /api/auth/login
    Body: {
        "username": "admin",
        "password": "admin123"
    }
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Kullanıcı adı ve şifre gereklidir'
            }), 400
        
        # Kullanıcıyı veritabanından sorgula
        query = "SELECT id, username, password_hash, role FROM users WHERE username = %s"
        users = execute_query(query, (username,))
        
        if not users:
            return jsonify({
                'success': False,
                'error': 'Kullanıcı adı veya şifre hatalı'
            }), 401
        
        user = users[0]
        
        # Şifre kontrolü
        if not check_password_hash(user['password_hash'], password):
            return jsonify({
                'success': False,
                'error': 'Kullanıcı adı veya şifre hatalı'
            }), 401
        
        # Session oluştur
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'Giriş işlemi başarısız oldu'
        }), 500

# ===========================
# Register Endpoint
# ===========================
@auth.route('/register', methods=['POST'])
def register():
    """
    Yeni kullanıcı kaydı
    
    POST /api/auth/register
    Body: {
        "username": "newuser",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Kullanıcı adı ve şifre gereklidir'
            }), 400
        
        if len(username) < 3:
            return jsonify({
                'success': False,
                'error': 'Kullanıcı adı en az 3 karakter olmalıdır'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False,
                'error': 'Şifre en az 6 karakter olmalıdır'
            }), 400
        
        # Kullanıcı adı kontrolü
        query = "SELECT id FROM users WHERE username = %s"
        existing_users = execute_query(query, (username,))
        
        if existing_users:
            return jsonify({
                'success': False,
                'error': 'Bu kullanıcı adı zaten kullanılıyor'
            }), 409
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Yeni kullanıcı ekle (varsayılan olarak USER rolü)
        insert_query = """
            INSERT INTO users (username, password_hash, role)
            VALUES (%s, %s, 'USER')
        """
        user_id = execute_insert(insert_query, (username, password_hash))
        
        # İzmit ID'sini dinamik olarak al
        izmit_result = execute_query("SELECT id FROM districts WHERE name = 'İzmit' OR name = 'Izmit' LIMIT 1")
        
        if not izmit_result:
            print("⚠️  İzmit ilçesi bulunamadı! İlk ilçe kullanılıyor...")
            izmit_result = execute_query("SELECT MIN(id) as id FROM districts")
        
        izmit_id = izmit_result[0]['id'] if izmit_result else 1
        
        # Yeni kullanıcı için 3 araç oluştur (İzmit'ten başlayan)
        print(f"🚛 Yeni kullanıcı '{username}' için araçlar oluşturuluyor (Başlangıç: İzmit ID={izmit_id})...")
        
        # Küçük Araç (500 kg)
        execute_insert(
            "INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id) VALUES (1, FALSE, %s, %s)",
            (izmit_id, user_id)
        )
        
        # Orta Araç (750 kg)
        execute_insert(
            "INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id) VALUES (2, FALSE, %s, %s)",
            (izmit_id, user_id)
        )
        
        # Büyük Araç (1000 kg)
        execute_insert(
            "INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id) VALUES (3, FALSE, %s, %s)",
            (izmit_id, user_id)
        )
        
        print(f"✅ Kullanıcı '{username}' için 3 araç oluşturuldu (İzmit - ID {izmit_id})")
        
        return jsonify({
            'success': True,
            'data': {
                'user_id': user_id,
                'username': username,
                'role': 'USER'
            },
            'message': 'Kayıt başarılı! Şimdi giriş yapabilirsiniz.'
        }), 201
        
    except Exception as e:
        print(f"Register error: {e}")
        return jsonify({
            'success': False,
            'error': 'Kayıt işlemi başarısız oldu'
        }), 500

# ===========================
# Logout Endpoint
# ===========================
@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """Kullanıcı çıkışı"""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Çıkış yapıldı'
    })

# ===========================
# Current User Endpoint
# ===========================
@auth.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Mevcut kullanıcı bilgilerini getir"""
    return jsonify({
        'success': True,
        'data': {
            'user_id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role')
        }
    })

# ===========================
# Check Auth Status
# ===========================
@auth.route('/status', methods=['GET'])
def check_auth_status():
    """Kullanıcının giriş durumunu kontrol et"""
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'authenticated': True,
            'data': {
                'user_id': session.get('user_id'),
                'username': session.get('username'),
                'role': session.get('role')
            }
        })
    else:
        return jsonify({
            'success': True,
            'authenticated': False
        })
