-- Mevcut durumu kontrol et

-- 1. Araç tipleri ve fiyatları
SELECT id, name, capacity_kg, rental_cost 
FROM vehicle_types 
ORDER BY id;

-- 2. Sistem parametreleri (cost_per_km)
SELECT * FROM system_parameters;

-- Beklenen:
-- vehicle_types: Her araç tipi farklı rental_cost'a sahip olabilmeli
-- system_parameters: cost_per_km değeri tutulmalı
