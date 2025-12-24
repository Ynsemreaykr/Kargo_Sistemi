-- Kargo İşletme Sistemi - Başlangıç Verileri
-- Kocaeli ilçeleri, araç tipleri ve sistem parametreleri

-- Sistem parametreleri
INSERT INTO system_parameters (cost_per_km, default_vehicle_count) 
VALUES (5.0, 3);

-- Araç tipleri (küçük, orta, büyük)
INSERT INTO vehicle_types (name, capacity_kg, rental_cost) VALUES
('Küçük Araç', 500, 100),
('Orta Araç', 1000, 200),
('Büyük Araç', 2000, 350);

-- Kocaeli ilçeleri (gerçek koordinatlar)
-- Kaynak: Google Maps / OpenStreetMap
INSERT INTO districts (name, latitude, longitude) VALUES
('İzmit', 40.7654, 29.9401),
('Gebze', 40.8027, 29.4308),
('Körfez', 40.7676, 29.7508),
('Gölcük', 40.7161, 29.8189),
('Derince', 40.7667, 29.8333),
('Başiskele', 40.6833, 29.8833),
('Çayırova', 40.8167, 29.3667),
('Darıca', 40.7667, 29.3833),
('Dilovası', 40.7833, 29.5167),
('Kartepe', 40.7500, 30.0333),
('Karamürsel', 40.6833, 29.6167),
('Kandıra', 41.0667, 30.1500);

-- Test kullanıcıları
INSERT INTO users (username, role) VALUES
('admin', 'ADMIN'),
('user1', 'USER'),
('user2', 'USER');

-- Varsayılan araçlar (3 adet - sistem parametresine göre)
INSERT INTO vehicles (vehicle_type_id, is_rented) VALUES
(1, FALSE),  -- Küçük araç
(2, FALSE),  -- Orta araç
(3, FALSE);  -- Büyük araç

-- Başarılı mesajı
SELECT 'Başlangıç verileri başarıyla yüklendi!' AS message;
SELECT COUNT(*) AS district_count FROM districts;
SELECT COUNT(*) AS vehicle_type_count FROM vehicle_types;
SELECT COUNT(*) AS vehicle_count FROM vehicles;
