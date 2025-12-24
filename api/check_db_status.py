import psycopg
import os
from config import DB_CONFIG

def check_postgres_connection():
    print("PostgreSQL bağlantısı kontrol ediliyor...")
    try:
        # Connect to default 'postgres' database to check server status
        conninfo = f"host={DB_CONFIG['host']} port={DB_CONFIG['port']} dbname=postgres user={DB_CONFIG['user']} password={DB_CONFIG['password']}"
        conn = psycopg.connect(conninfo)
        conn.autocommit = True
        print("✓ PostgreSQL sunucusu çalışıyor ve kimlik bilgileri doğru.")
        
        # Check if target database exists
        cur = conn.cursor()
        target_db = DB_CONFIG['dbname']
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,))
        exists = cur.fetchone()
        
        if exists:
            print(f"✓ '{target_db}' veritabanı mevcut.")
        else:
            print(f"✗ '{target_db}' veritabanı MEVCUT DEĞİL.")
            print(f"  Veritabanı adı yapılandırmada '{target_db}' olarak ayarlanmış.")
            return False
            
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL bağlantı hatası: {e}")
        return False

if __name__ == "__main__":
    check_postgres_connection()
