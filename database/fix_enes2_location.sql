-- ADIM 1: İzmit ID'sini bul
SELECT id, name FROM districts ORDER BY id;

-- ADIM 2: Sonucu görünce, İzmit'in ID'sine göre güncelle
-- Örneğin İzmit ID=12 ise:

UPDATE vehicles v
SET current_location_district_id = (SELECT id FROM districts WHERE name = 'İzmit')
FROM users u
WHERE v.user_id = u.id
AND u.username = 'enes2';

-- ADIM 3: Kontrol
SELECT v.id, vt.name, d.name as location
FROM vehicles v
JOIN vehicle_types vt ON vt.id = v.vehicle_type_id
JOIN districts d ON d.id = v.current_location_district_id
JOIN users u ON u.id = v.user_id
WHERE u.username = 'enes2';
