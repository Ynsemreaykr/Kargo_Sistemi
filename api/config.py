"""
Kargo İşletme Sistemi - Veritabanı Yapılandırması
PostgreSQL bağlantı yönetimi
"""

import psycopg
from psycopg_pool import ConnectionPool
import os
from dotenv import load_dotenv

load_dotenv()

# Veritabanı bağlantı bilgileri
# Kullanıcı kendi PostgreSQL bilgilerini buradan güncelleyebilir
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'cargo_db'),  # FIX: kargo_db -> cargo_db
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

# Connection pool (performans için)
connection_pool = None

def init_pool():
    """Bağlantı havuzunu başlat"""
    global connection_pool
    try:
        # psycopg3 connection string oluştur
        conninfo = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname={DB_CONFIG['dbname']} user={DB_CONFIG['user']} password={DB_CONFIG['password']}"
        connection_pool = ConnectionPool(conninfo, min_size=1, max_size=20)
        print("✓ Veritabanı bağlantı havuzu oluşturuldu")
        return True
    except Exception as e:
        print(f"✗ Veritabanı bağlantı hatası: {e}")
        return False

def get_connection():
    """Havuzdan bir bağlantı al"""
    if connection_pool:
        return connection_pool.getconn()
    return None

def release_connection(conn):
    """Bağlantıyı havuza geri ver"""
    if connection_pool and conn:
        connection_pool.putconn(conn)

def close_pool():
    """Tüm bağlantıları kapat"""
    if connection_pool:
        connection_pool.close()
        print("✓ Veritabanı bağlantı havuzu kapatıldı")

def execute_query(query, params=None, fetch=True):
    """
    SQL sorgusu çalıştır
    
    Args:
        query: SQL sorgusu
        params: Sorgu parametreleri (tuple)
        fetch: True ise sonuçları getir, False ise sadece çalıştır
    
    Returns:
        fetch=True ise sonuç listesi, False ise None
    """
    conn = get_connection()
    if not conn:
        raise Exception("Veritabanı bağlantısı alınamadı")
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch:
            columns = [desc[0] for desc in cursor.description]
            results = cursor.fetchall()
            # Sonuçları dictionary listesine çevir
            return [dict(zip(columns, row)) for row in results]
        else:
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        release_connection(conn)

def execute_insert(query, params=None, return_id=True):
    """
    INSERT sorgusu çalıştır ve eklenen kaydın ID'sini döndür
    
    Args:
        query: INSERT sorgusu
        params: Sorgu parametreleri
        return_id: True ise eklenen kaydın ID'sini döndür
    
    Returns:
        Eklenen kaydın ID'si veya None
    """
    conn = get_connection()
    if not conn:
        raise Exception("Veritabanı bağlantısı alınamadı")
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        inserted_id = None
        if return_id:
            cursor.execute("SELECT lastval()")
            inserted_id = cursor.fetchone()[0]
        
        conn.commit()
        return inserted_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        release_connection(conn)
