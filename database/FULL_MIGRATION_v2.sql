-- ============================================
-- KARGO SİSTEMİ V2.0 - KOMPLE MIGRATION
-- ============================================
-- Eski schema ile uyumlu, eksiklikleri tamamlar
-- ============================================

-- 1. CARGO → CARGOS (tablo ismi değişikliği)
-- ============================================

-- Eğer 'cargo' varsa 'cargos' olarak rename et
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables 
               WHERE table_schema = 'public' AND table_name = 'cargo') THEN
        ALTER TABLE cargo RENAME TO cargos;
        RAISE NOTICE '✓ cargo tablosu cargos olarak yeniden adlandırıldı';
    END IF;
END $$;

-- 2. CARGOS TABLOSU GÜNCELLEMELERİ
-- ============================================

-- Eğer cargos tablosu yoksa oluştur (yeni kurulum için)
CREATE TABLE IF NOT EXISTS cargos (
    id SERIAL PRIMARY KEY,
    destination_district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    weight_kg NUMERIC NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Eksik kolonları ekle
ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';

ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;

ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Eski 'district_id' kolonunu 'destination_district_id' olarak rename et
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='cargos' AND column_name='district_id') THEN
        ALTER TABLE cargos RENAME COLUMN district_id TO destination_district_id;
        RAISE NOTICE '✓ district_id → destination_district_id';
    END IF;
END $$;

-- Indexler
CREATE INDEX IF NOT EXISTS idx_cargos_status ON cargos(status);
CREATE INDEX IF NOT EXISTS idx_cargos_user_id ON cargos(user_id);
CREATE INDEX IF NOT EXISTS idx_cargos_destination ON cargos(destination_district_id);

-- ============================================
-- 3. SCENARIOS TABLOSU GÜNCELLEMELERİ
-- ============================================

-- Eksik kolonları ekle
ALTER TABLE scenarios 
ADD COLUMN IF NOT EXISTS algorithm VARCHAR(50) DEFAULT 'hybrid';

ALTER TABLE scenarios 
ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'LIMITED';

ALTER TABLE scenarios 
ADD COLUMN IF NOT EXISTS remaining_cargos INTEGER DEFAULT 0;

-- Eski 'scenario_type' kolonunu 'mode' olarak kullan
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='scenarios' AND column_name='scenario_type') THEN
        UPDATE scenarios SET mode = scenario_type WHERE mode IS NULL;
        RAISE NOTICE '✓ scenario_type değerleri mode''a kopyalandı';
    END IF;
END $$;

-- ============================================
-- 4. ROUTES TABLOSU GÜNCELLEMELERİ
-- ============================================

-- Eksik kolonları ekle
ALTER TABLE routes 
ADD COLUMN IF NOT EXISTS total_distance NUMERIC DEFAULT 0;

-- Eski 'distance' kolonunu 'total_distance' olarak kullan
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name='routes' AND column_name='distance') THEN
        UPDATE routes SET total_distance = distance WHERE total_distance = 0 OR total_distance IS NULL;
        RAISE NOTICE '✓ distance değerleri total_distance''a kopyalandı';
    END IF;
END $$;

-- ============================================
-- 5. ROUTE_DETAILS TABLOSU (yeni)
-- ============================================

CREATE TABLE IF NOT EXISTS route_details (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    cargo_id INTEGER REFERENCES cargos(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    stop_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Eski route_stops verisini route_details'e kopyala
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables 
               WHERE table_schema = 'public' AND table_name = 'route_stops') THEN
        
        INSERT INTO route_details (route_id, district_id, stop_order, created_at)
        SELECT route_id, district_id, stop_order, created_at
        FROM route_stops
        WHERE NOT EXISTS (
            SELECT 1 FROM route_details rd 
            WHERE rd.route_id = route_stops.route_id 
            AND rd.district_id = route_stops.district_id
        );
        
        RAISE NOTICE '✓ route_stops verileri route_details''e kopyalandı';
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_route_details_route ON route_details(route_id);
CREATE INDEX IF NOT EXISTS idx_route_details_cargo ON route_details(cargo_id);

-- ============================================
-- 6. VEHICLES TABLOSU GÜNCELLEMELERİ
-- ============================================

ALTER TABLE vehicles 
ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id);

ALTER TABLE vehicles 
ADD COLUMN IF NOT EXISTS current_location_id INTEGER REFERENCES districts(id);

ALTER TABLE vehicles 
ADD COLUMN IF NOT EXISTS can_reset BOOLEAN DEFAULT TRUE;

-- ============================================
-- 7. SYSTEM_PARAMETERS TABLOSU
-- ============================================

-- Eğer yoksa oluştur
CREATE TABLE IF NOT EXISTS system_parameters (
    id SERIAL PRIMARY KEY,
    cost_per_km NUMERIC DEFAULT 1.0,
    default_vehicle_count INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İlk kayıt yoksa ekle
INSERT INTO system_parameters (id, cost_per_km, default_vehicle_count)
SELECT 1, 1.0, 3
WHERE NOT EXISTS (SELECT 1 FROM system_parameters WHERE id = 1);

-- ============================================
-- 8. VERİ TEMİZLİĞİ VE UYUMLULUK
-- ============================================

-- Eski kargoları 'delivered' olarak işaretle
UPDATE cargos 
SET status = 'delivered', 
    updated_at = CURRENT_TIMESTAMP
WHERE status IS NULL OR status = '';

-- Quantity null olanları 1 yap
UPDATE cargos 
SET quantity = 1
WHERE quantity IS NULL OR quantity = 0;

-- Eski senaryoları LIMITED olarak işaretle
UPDATE scenarios 
SET mode = 'LIMITED'
WHERE mode IS NULL OR mode = '';

-- ============================================
-- 9. KONTROL SORULARI
-- ============================================

-- Tabloları göster
SELECT 'Tablolar:' as info;
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Cargos kolonları
SELECT 'Cargos kolonları:' as info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'cargos'
ORDER BY ordinal_position;

-- Kargo durumları
SELECT 'Kargo durumları:' as info;
SELECT status, COUNT(*) as count 
FROM cargos 
GROUP BY status;

-- ============================================
-- 10. BAŞARI MESAJI
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════╗';
    RAISE NOTICE '║  ✅ DATABASE MIGRATION TAMAMLANDI!    ║';
    RAISE NOTICE '╚════════════════════════════════════════╝';
    RAISE NOTICE '';
    RAISE NOTICE '📊 Güncellemeler:';
    RAISE NOTICE '   ▸ cargo → cargos (rename)';
    RAISE NOTICE '   ▸ cargos.status, quantity, user_id';
    RAISE NOTICE '   ▸ scenarios.mode, algorithm';
    RAISE NOTICE '   ▸ route_details tablosu oluşturuldu';
    RAISE NOTICE '   ▸ vehicles.user_id, can_reset';
    RAISE NOTICE '';
    RAISE NOTICE '✓ Sistem v2.0 için hazır!';
END $$;
