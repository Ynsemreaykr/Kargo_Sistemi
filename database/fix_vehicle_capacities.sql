-- ARAÇ KAPASİTELERİNİ DÜZELT
-- PDF Gereksinimi: 500, 750, 1000 kg
-- Şu an: 500, 1000, 2000 kg

-- ADIM 1: Mevcut kapasiteleri kontrol et
SELECT id, name, capacity_kg, rental_cost 
FROM vehicle_types 
ORDER BY id;

-- ADIM 2: Kapasiteleri güncelle
UPDATE vehicle_types SET capacity_kg = 500 WHERE id = 1;  -- Küçük Araç
UPDATE vehicle_types SET capacity_kg = 750 WHERE id = 2;  -- Orta Araç
UPDATE vehicle_types SET capacity_kg = 1000 WHERE id = 3; -- Büyük Araç

-- ADIM 3: Kiralama maliyetini kontrol et (PDF: 200 TL)
-- Şu an ne?
SELECT id, name, rental_cost FROM vehicle_types ORDER BY id;

-- ADIM 4: Eğer kiralama maliyeti yanlışsa düzelt
-- UPDATE vehicle_types SET rental_cost = 200 WHERE id = 1;

-- ADIM 5: Kontrol et
SELECT id, name, capacity_kg, rental_cost 
FROM vehicle_types 
ORDER BY id;

-- Beklenen sonuç:
-- 1, "Küçük Araç", 500, 200
-- 2, "Orta Araç", 750, 200
-- 3, "Büyük Araç", 1000, 200
