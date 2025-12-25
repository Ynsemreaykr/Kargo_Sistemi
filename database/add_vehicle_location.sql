-- Vehicles tablosuna current_location ekleme
-- Her araç son gittiği yerde kalacak

ALTER TABLE vehicles 
ADD COLUMN IF NOT EXISTS current_location_district_id INTEGER DEFAULT 12;

-- İzmit'i default olarak ayarla (ID = 12)
UPDATE vehicles 
SET current_location_district_id = 12 
WHERE current_location_district_id IS NULL;

-- Foreign key ekle
ALTER TABLE vehicles
ADD CONSTRAINT fk_vehicle_current_location
FOREIGN KEY (current_location_district_id)
REFERENCES districts(id);

COMMIT;
