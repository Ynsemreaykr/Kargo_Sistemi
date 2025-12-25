"""
Veritabanına vehicle location kolonu ekle
"""

import os
from dotenv import load_dotenv
import psycopg
from psycopg import sql

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'kargo_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres')
}

def update_vehicle_schema():
    try:
        # Connect to database
        conn = psycopg.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔧 Vehicles tablosuna current_location ekleniyor...")
        
        # Add column
        cursor.execute("""
            ALTER TABLE vehicles 
            ADD COLUMN IF NOT EXISTS current_location_district_id INTEGER DEFAULT 12;
        """)
        
        # Update existing vehicles
        cursor.execute("""
            UPDATE vehicles 
            SET current_location_district_id = 12 
            WHERE current_location_district_id IS NULL;
        """)
        
        # Add foreign key (if not exists)
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.table_constraints 
                    WHERE constraint_name = 'fk_vehicle_current_location'
                ) THEN
                    ALTER TABLE vehicles
                    ADD CONSTRAINT fk_vehicle_current_location
                    FOREIGN KEY (current_location_district_id)
                    REFERENCES districts(id);
                END IF;
            END $$;
        """)
        
        conn.commit()
        print("✓ Vehicles tablosu güncellendi!")
        print("✓ Tüm araçlar İzmit'te (ID=12) konumlandırıldı")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        raise

if __name__ == "__main__":
    update_vehicle_schema()
