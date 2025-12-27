"""
Kargo İşletme Sistemi - Flask Ana Dosyası
Kocaeli Üniversitesi - Yazılım Laboratuvarı III

AŞAMA 1: Algoritmasız Backend
Bu aşamada dummy (sahte) rotalar üretilir.
AŞAMA 3'te gerçek algoritma entegre edilecektir.
"""

from flask import Flask
from flask_cors import CORS
from flask_session import Session
from config import init_pool, close_pool
from routes import api
from auth import auth
from system_params import params_bp
import atexit
import os
from datetime import timedelta

# Flask uygulamasını oluştur
app = Flask(__name__)

# Secret key for session
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'kargo-sistem-secret-key-2025')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False  # Browser kapanınca session bitsin
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize session
Session(app)


# CORS ayarları (frontend'den erişim için)
CORS(app, supports_credentials=True, origins=['http://localhost:8000', 'http://127.0.0.1:8000'])

# Blueprint imports
from scenario_details import api_details
from charts import charts_bp
from user_cargo import user_cargo_bp
from admin_cargo import admin_cargo_bp
from admin_distribution import admin_distribution_bp

# Register blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(params_bp, url_prefix='/api')
app.register_blueprint(api_details, url_prefix='/api')
app.register_blueprint(charts_bp, url_prefix='/api')
app.register_blueprint(user_cargo_bp, url_prefix='/api')
app.register_blueprint(admin_cargo_bp, url_prefix='/api')
app.register_blueprint(admin_distribution_bp, url_prefix='/api')

print("✓ Scenario details API registered")
print("✓ Charts API registered")
print("✓ User cargo API registered")
print("✓ Admin cargo API registered")
print("✓ Admin distribution API registered")
print("✓ System parameters API registered")


# Ana sayfa
@app.route('/')
def index():
    return {
        'message': 'Kargo İşletme Sistemi API',
        'version': '1.0.0',
        'stage': 'AŞAMA 1 - Algoritmasız Backend',
        'endpoints': {
            'districts': 'GET /api/districts',
            'create_scenario': 'POST /api/scenarios',
            'get_scenario': 'GET /api/scenarios/<id>',
            'get_routes': 'GET /api/routes/<scenario_id>',
            'system_parameters': 'GET /api/system-parameters'
        }
    }

# Uygulama başlatıldığında
@app.before_request
def before_first_request():
    """İlk istek öncesi veritabanı bağlantısını başlat"""
    pass

# Uygulama kapanırken
def cleanup():
    """Veritabanı bağlantılarını temizle"""
    close_pool()

atexit.register(cleanup)

if __name__ == '__main__':
    print("=" * 60)
    print("Kargo İşletme Sistemi - Backend API")
    print("=" * 60)
    print("AŞAMA 1: Algoritmasız Backend (Dummy Rotalar)")
    print("-" * 60)
    
    # Veritabanı bağlantısını başlat
    if init_pool():
        print("✓ Veritabanı bağlantısı başarılı")
        print("-" * 60)
        print("API çalışıyor: http://localhost:5002")
        print("Endpoint'ler:")
        print("  - GET  /api/districts")
        print("  - POST /api/scenarios")
        print("  - GET  /api/scenarios/<id>")
        print("  - GET  /api/routes/<scenario_id>")
        print("  - GET  /api/system-parameters")
        print("=" * 60)
        
        # Flask uygulamasını başlat (Port 5001)
        app.run(debug=True, host='0.0.0.0', port=5002)
    else:
        print("✗ Veritabanı bağlantısı başarısız!")
        print("Lütfen PostgreSQL ayarlarını kontrol edin (api/config.py)")
