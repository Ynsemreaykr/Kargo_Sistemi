"""
Basit Kurulum - Python ile direkt veritabanı migration
psql gerektirmeden çalışır
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from werkzeug.security import generate_password_hash
from config import init_pool, execute_query, execute_insert, close_pool
import psycopg

def setup():
    print("=" * 60)
    print("Kargo İşletme Sistemi - Hızlı Kurulum")
    print("=" * 60)
    print()
    
    # Veritabanı bağlantısını başlat
    print("🔌 Veritabanına bağlanılıyor...")
    if not init_pool():
        print("✗ Veritabanı bağlantısı başarısız!")
        print()
        print("Kontrol edilecekler:")
        print("  1. PostgreSQL çalışıyor mu?")
        print("  2. api/.env dosyasındaki şifre doğru mu?")
        print("  3. kargo_db veritabanı var mı?")
        return False
    
    print("✓ Bağlantı başarılı!")
    print()
    
    try:
        # 1. password_hash kolonu ekle
        print("📊 Veritabanı şeması güncelleniyor...")
        
        # Kolon var mı kontrol et
        check_sql = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_hash'
        """
        
        result = execute_query(check_sql)
        
        if not result:
            # Kolon yok, ekle
            add_column_sql = """
            ALTER TABLE users ADD COLUMN password_hash TEXT NOT NULL DEFAULT ''
            """
            execute_query(add_column_sql, fetch=False)
            print("✓ password_hash kolonu eklendi")
        else:
            print("✓ password_hash kolonu zaten mevcut")
        
        print()
        
        # 2. Varsayılan kullanıcıları oluştur
        print("👥 Varsayılan kullanıcılar oluşturuluyor...")
        
        # Mevcut kullanıcıları kontrol et
        existing = execute_query(
            "SELECT username FROM users WHERE username IN ('admin', 'user')"
        )
        
        if existing:
            print("⚠️  Varsayılan kullanıcılar zaten mevcut:")
            for user in existing:
                print(f"   - {user['username']}")
            print()
            
            response = input("Mevcut kullanıcıları silip yeniden oluşturmak ister misiniz? (e/h): ")
            if response.lower() != 'e':
                print("Kullanıcılar değiştirilmedi.")
            else:
                # Mevcut kullanıcıları sil
                execute_query(
                    "DELETE FROM users WHERE username IN ('admin', 'user')",
                    fetch=False
                )
                print("✓ Mevcut kullanıcılar silindi")
                existing = []
        
        if not existing:
            # Şifreleri hashle
            admin_hash = generate_password_hash('admin123')
            user_hash = generate_password_hash('user123')
            
            # Admin kullanıcısı oluştur
            execute_insert(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                ('admin', admin_hash, 'ADMIN'),
                return_id=False
            )
            print("✓ Admin kullanıcısı oluşturuldu (admin/admin123)")
            
            # User kullanıcısı oluştur
            execute_insert(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
                ('user', user_hash, 'USER'),
                return_id=False
            )
            print("✓ User kullanıcısı oluşturuldu (user/user123)")
        
        print()
        print("=" * 60)
        print("✅ Kurulum tamamlandı!")
        print("=" * 60)
        print()
        print("Varsayılan kullanıcılar:")
        print("  👑 Admin: admin / admin123")
        print("  👤 User:  user / user123")
        print()
        print("Sistemi başlatmak için: python app.py")
        print("Frontend için: cd ../frontend && python -m http.server 8000")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"✗ Hata: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        close_pool()

if __name__ == "__main__":
    setup()
    input("\nDevam etmek için Enter'a basın...")
