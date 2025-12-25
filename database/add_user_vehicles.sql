-- KULLANICI-ARAÇ İZOLASYONU
-- Her kullanıcı kendi araçlarına sahip olmalı

-- 1. Vehicles tablosuna user_id ekle
ALTER TABLE vehicles
ADD COLUMN user_id INTEGER;

-- Foreign key
ALTER TABLE vehicles
ADD CONSTRAINT fk_vehicle_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Index
CREATE INDEX idx_vehicles_user ON vehicles(user_id);

-- 2. Mevcut araçları sil (test verileri)
DELETE FROM vehicles;

-- 3. Her kullanıcı için 3 araç oluştur (mevcut kullanıcılar için)
-- Küçük Araç (500 kg)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
SELECT 1, FALSE, 12, u.id FROM users u;

-- Orta Araç (750 kg) 
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
SELECT 2, FALSE, 12, u.id FROM users u;

-- Büyük Araç (1000 kg)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
SELECT 3, FALSE, 12, u.id FROM users u;

-- 4. NOT NULL constraint (opsiyonel - önceki test verileri için)
-- ALTER TABLE vehicles ALTER COLUMN user_id SET NOT NULL;
