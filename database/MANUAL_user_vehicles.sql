-- MANUEL MİGRASYON: KULLANICI-ARAÇ İZOLASYONU
-- Bu SQL'i psql veya pgAdmin ile çalıştırın

-- 1. user_id kolonu ekle
ALTER TABLE vehicles
ADD COLUMN IF NOT EXISTS user_id INTEGER;

-- 2. Foreign key
ALTER TABLE vehicles
DROP CONSTRAINT IF EXISTS fk_vehicle_user;

ALTER TABLE vehicles
ADD CONSTRAINT fk_vehicle_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 3. Index
DROP INDEX IF EXISTS idx_vehicles_user;
CREATE INDEX idx_vehicles_user ON vehicles(user_id);

-- 4. Mevcut test araçlarını temizle
DELETE FROM vehicles WHERE user_id IS NULL;

-- 5. Her kullanıcı için 3 araç oluştur
-- user_id 1 için
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES 
(1, FALSE, 12, 1),  -- Küçük Araç
(2, FALSE, 12, 1),  -- Orta Araç
(3, FALSE, 12, 1);  -- Büyük Araç

-- user_id 2 için (varsa)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
SELECT 1, FALSE, 12, u.id FROM users u WHERE u.id = 2
UNION ALL
SELECT 2, FALSE, 12, u.id FROM users u WHERE u.id = 2
UNION ALL
SELECT 3, FALSE, 12, u.id FROM users u WHERE u.id = 2;

-- VEYA: Tüm kullanıcılar için otomatik
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
SELECT 1, FALSE, 12, u.id FROM users u WHERE u.id > 1
UNION ALL
SELECT 2, FALSE, 12, u.id FROM users u WHERE u.id > 1
UNION ALL
SELECT 3, FALSE, 12, u.id FROM users u WHERE u.id > 1;

--Kontrol et
SELECT u.username, v.id as vehicle_id, vt.name as vehicle_type
FROM vehicles v
JOIN users u ON u.id = v.user_id
JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
ORDER BY u.id, v.id;
