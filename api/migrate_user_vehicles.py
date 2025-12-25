"""
KULLANICI-ARAÇ İZOLASYONU - ADIM ADIM MIGRATION
Python ile güvenli migration
"""

import psycopg

def get_db_connection():
    """Veritabanı bağlantısı"""
    return psycopg.connect(
        "host=localhost dbname=cargo_db user=postgres password=postgres"
    )

def add_user_id_to_vehicles():
    """
    1. vehicles tablosuna user_id ekle
    2. Mevcut araçları admin'e ata
    3. Her kullanıcı için 3 araç oluştur
    """
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("\n" + "="*60)
        print("🔧 KULLANICI-ARAÇ İZOLASYONU BAŞLIYOR")
        print("="*60)
        
        # ADIM 1: user_id kolonu var mı kontrol et
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vehicles' 
            AND column_name = 'user_id'
        """)
        
        if cur.fetchone():
            print("⚠️  user_id kolonu zaten var!")
            choice = input("Devam etmek istiyor musunuz? (y/n): ")
            if choice.lower() != 'y':
                print("İptal edildi.")
                return
        
        # ADIM 2: user_id kolonu ekle
        print("\n📝 ADIM 1/5: user_id kolonu ekleniyor...")
        cur.execute("""
            ALTER TABLE vehicles
            ADD COLUMN IF NOT EXISTS user_id INTEGER
        """)
        print("   ✓ user_id kolonu eklendi")
        
        # ADIM 3: Foreign key ekle
        print("\n📝 ADIM 2/5: Foreign key ekleniyor...")
        cur.execute("ALTER TABLE vehicles DROP CONSTRAINT IF EXISTS fk_vehicle_user")
        cur.execute("""
            ALTER TABLE vehicles
            ADD CONSTRAINT fk_vehicle_user
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        """)
        print("   ✓ Foreign key eklendi")
        
        # ADIM 4: Index ekle
        print("\n📝 ADIM 3/5: Index oluşturuluyor...")
        cur.execute("DROP INDEX IF EXISTS idx_vehicles_user")
        cur.execute("CREATE INDEX idx_vehicles_user ON vehicles(user_id)")
        print("   ✓ Index oluşturuldu")
        
        # ADIM 5: Mevcut araçları kontrol et
        print("\n📝 ADIM 4/5: Mevcut araçlar kontrol ediliyor...")
        cur.execute("SELECT COUNT(*) FROM vehicles WHERE user_id IS NULL")
        null_count = cur.fetchone()[0]
        
        if null_count > 0:
            print(f"   ℹ️  {null_count} araç user_id'si olmadan bulundu")
            
            # Admin user var mı?
            cur.execute("SELECT id FROM users WHERE role = 'ADMIN' LIMIT 1")
            admin_user = cur.fetchone()
            
            if admin_user:
                admin_id = admin_user[0]
                cur.execute("UPDATE vehicles SET user_id = %s WHERE user_id IS NULL", (admin_id,))
                print(f"   ✓ {null_count} araç admin kullanıcısına atandı (ID={admin_id})")
            else:
                print("   ⚠️  Admin kullanıcı bulunamadı - araçlar silinecek")
                cur.execute("DELETE FROM vehicles WHERE user_id IS NULL")
                print(f"   ✓ {null_count} araç silindi")
        
        # ADIM 6: Her kullanıcı için araç kontrolü
        print("\n📝 ADIM 5/5: Kullanıcılar için araçlar kontrol ediliyor...")
        
        cur.execute("SELECT id, username FROM users")
        users = cur.fetchall()
        
        for user in users:
            user_id = user[0]
            username = user[1]
            
            # Bu kullanıcının araç sayısı
            cur.execute("SELECT COUNT(*) FROM vehicles WHERE user_id = %s", (user_id,))
            vehicle_count = cur.fetchone()[0]
            
            if vehicle_count >= 3:
                print(f"   ✓ {username}: {vehicle_count} araç var")
            else:
                print(f"   ⚠️  {username}: Sadece {vehicle_count} araç var - {3-vehicle_count} araç ekleniyor...")
                
                # Eksik araçları ekle
                for vehicle_type_id in range(1, 4):  # 1, 2, 3
                    # Bu tip araç var mı?
                    cur.execute("""
                        SELECT COUNT(*) FROM vehicles 
                        WHERE user_id = %s AND vehicle_type_id = %s
                    """, (user_id, vehicle_type_id))
                    
                    if cur.fetchone()[0] == 0:
                        cur.execute("""
                            INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
                            VALUES (%s, FALSE, 12, %s)
                        """, (vehicle_type_id, user_id))
                        print(f"      + Tip {vehicle_type_id} aracı eklendi")
        
        # Commit
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ MİGRATION BAŞARILI!")
        print("="*60)
        
        # Final kontrol
        cur.execute("""
            SELECT u.username, COUNT(v.id) as vehicle_count
            FROM users u
            LEFT JOIN vehicles v ON v.user_id = u.id
            GROUP BY u.username, u.id
            ORDER BY u.id
        """)
        
        print("\n📊 KULLANICI-ARAÇ DAĞILIMI:")
        for row in cur.fetchall():
            print(f"   {row[0]:15s}: {row[1]} araç")
        
        print("\n✅ Sistem hazır!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    add_user_id_to_vehicles()
