-- ============================================
-- KARGO SİSTEMİ V2.0 - DATABASE ŞEMA GÜNCELLEMESİ
-- ============================================
-- Tarih: 27 Aralık 2025
-- Amaç: Yeni kullanıcı-admin workflow için gerekli kolonlar
-- ============================================

-- 1. CARGOS TABLOSU GÜNCELLEMELERİ
-- ============================================

-- Status kolonu ekle (kargo durumu takibi)
ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';

COMMENT ON COLUMN cargos.status IS 'Kargo durumu: pending, approved, in_transit, delivered, cancelled';

-- Quantity kolonu ekle (kaç adet mal)
ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;

COMMENT ON COLUMN cargos.quantity IS 'Gönderilen mal adedi';

-- Created_at kolonu ekle (oluşturulma zamanı)
ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Updated_at kolonu ekle (güncellenme zamanı)
ALTER TABLE cargos 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Status index (performans için)
CREATE INDEX IF NOT EXISTS idx_cargos_status ON cargos(status);

-- User_id index (kullanıcı bazlı sorgular için)
CREATE INDEX IF NOT EXISTS idx_cargos_user_id ON cargos(user_id);

-- ============================================
-- 2. SCENARIOS TABLOSU GÜNCELLEMELERİ
-- ============================================

-- Mode kolonu ekle (LIMITED/UNLIMITED)
ALTER TABLE scenarios 
ADD COLUMN IF NOT EXISTS mode VARCHAR(20) DEFAULT 'LIMITED';

COMMENT ON COLUMN scenarios.mode IS 'Senaryo modu: LIMITED (3 araç), UNLIMITED (3+kiralama)';

-- Remaining_cargos kolonu ekle (götürülemeyen kargolar)
ALTER TABLE scenarios 
ADD COLUMN IF NOT EXISTS remaining_cargos INTEGER DEFAULT 0;

COMMENT ON COLUMN scenarios.remaining_cargos IS 'LIMITED modda götürülemeyen kargo sayısı';

-- ============================================
-- 3. VEHICLES TABLOSU GÜNCELLEMELERİ
-- ============================================

-- Can_reset kolonu ekle (admin reset yetkisi)
ALTER TABLE vehicles 
ADD COLUMN IF NOT EXISTS can_reset BOOLEAN DEFAULT TRUE;

COMMENT ON COLUMN vehicles.can_reset IS 'Admin bu aracı resetleyebilir mi?';

-- ============================================
-- 4. MEVCUT VERİLERİ GÜNCELLE
-- ============================================

-- Tüm mevcut kargoları 'delivered' olarak işaretle (eski sistem)
UPDATE cargos 
SET status = 'delivered', 
    quantity = 1,
    created_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE status IS NULL OR status = '';

-- Tüm mevcut senaryoları 'LIMITED' olarak işaretle
UPDATE scenarios 
SET mode = 'LIMITED', 
    remaining_cargos = 0
WHERE mode IS NULL OR mode = '';

-- ============================================
-- 5. KONTROL SORULARI
-- ============================================

-- Kargo durumlarını kontrol et
SELECT status, COUNT(*) as count 
FROM cargos 
GROUP BY status;

-- Senaryo modlarını kontrol et
SELECT mode, COUNT(*) as count 
FROM scenarios 
GROUP BY mode;

-- Araç resetlenebilirlik durumunu kontrol et
SELECT can_reset, COUNT(*) as count 
FROM vehicles 
GROUP BY can_reset;

-- ============================================
-- 6. BAŞARI MESAJI
-- ============================================

DO $$
BEGIN
    RAISE NOTICE '✅ Database şema güncellemesi başarıyla tamamlandı!';
    RAISE NOTICE '📊 Yeni kolonlar:';
    RAISE NOTICE '   - cargos.status (pending/in_transit/delivered)';
    RAISE NOTICE '   - cargos.quantity (mal adedi)';  
    RAISE NOTICE '   - cargos.created_at, updated_at';
    RAISE NOTICE '   - scenarios.mode (LIMITED/UNLIMITED)';
    RAISE NOTICE '   - scenarios.remaining_cargos';
    RAISE NOTICE '   - vehicles.can_reset';
END $$;
