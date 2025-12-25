-- ADIM ADIM MIGRATION
-- Her komutu TEK TEK çalıştırın!

-- ============================================
-- ADIM 1: user_id kolonu ekle
-- ============================================
ALTER TABLE vehicles 
ADD COLUMN user_id INTEGER;

-- ============================================
-- ADIM 2: Foreign key ekle
-- ============================================
ALTER TABLE vehicles
ADD CONSTRAINT fk_vehicle_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ============================================
-- ADIM 3: Index ekle
-- ============================================
CREATE INDEX idx_vehicles_user ON vehicles(user_id);

-- ============================================
-- ADIM 4: Mevcut araçları ilk kullanıcıya ata
-- ============================================
UPDATE vehicles 
SET user_id = (SELECT MIN(id) FROM users)
WHERE user_id IS NULL;

-- ============================================
-- ADIM 5: KONTROL ET
-- ============================================
SELECT v.id, vt.name as type, u.username, v.current_location_district_id
FROM vehicles v
JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
LEFT JOIN users u ON u.id = v.user_id
ORDER BY v.id;

-- Her araç bir kullanıcıya atanmış olmalı!
