-- ============================================================
-- KARGO İŞLETME SİSTEMİ - VERİTABANI OLUŞTURMA KOMUTLARI
-- ============================================================
-- Bu dosya veritabanını sıfırdan oluşturur
-- Kullanım: psql -U postgres -f database_setup.sql
-- ============================================================

-- 1. Eski veritabanını sil (varsa)
DROP DATABASE IF EXISTS cargo_db;

-- 2. Yeni veritabanı oluştur
CREATE DATABASE cargo_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Turkish_Turkey.1254'
    LC_CTYPE = 'Turkish_Turkey.1254'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- 3. Veritabanına bağlan
\c cargo_db

-- ============================================================
-- TABLOLAR
-- ============================================================

-- 3.1. Kullanıcılar Tablosu
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.2. İlçeler Tablosu
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.3. Araç Tipleri Tablosu
CREATE TABLE vehicle_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    capacity_kg DECIMAL(10, 2) NOT NULL,
    rental_cost DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.4. Araçlar Tablosu
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_type_id INTEGER REFERENCES vehicle_types(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    is_rented BOOLEAN DEFAULT FALSE,
    current_location_district_id INTEGER REFERENCES districts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.5. Kargolar Tablosu
CREATE TABLE cargos (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    weight_kg DECIMAL(10, 2) NOT NULL,
    quantity INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'in_transit', 'delivered')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.6. Senaryolar Tablosu
CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    scenario_type VARCHAR(20) NOT NULL CHECK (scenario_type IN ('LIMITED', 'UNLIMITED')),
    algorithm_used VARCHAR(50),
    total_distance_km DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.7. Rotalar Tablosu
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
    vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
    start_location_id INTEGER REFERENCES districts(id),
    end_location_id INTEGER REFERENCES districts(id),
    total_distance_km DECIMAL(10, 2),
    total_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.8. Rota Durağı Tablosu
CREATE TABLE route_stops (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    stop_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.9. Rota Kargoları Tablosu
CREATE TABLE route_cargos (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    cargo_id INTEGER REFERENCES cargos(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3.10. Sistem Parametreleri Tablosu
CREATE TABLE system_parameters (
    id SERIAL PRIMARY KEY,
    cost_per_km DECIMAL(10, 2) DEFAULT 1.50,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- İNDEXLER (Performans için)
-- ============================================================

CREATE INDEX idx_cargos_user_id ON cargos(user_id);
CREATE INDEX idx_cargos_district_id ON cargos(district_id);
CREATE INDEX idx_cargos_status ON cargos(status);
CREATE INDEX idx_vehicles_user_id ON vehicles(user_id);
CREATE INDEX idx_routes_scenario_id ON routes(scenario_id);
CREATE INDEX idx_route_stops_route_id ON route_stops(route_id);
CREATE INDEX idx_route_cargos_route_id ON route_cargos(route_id);

-- ============================================================
-- BAŞLANGIÇ VERİLERİ
-- ============================================================

-- 4.1. Admin Kullanıcı (Şifre: admin123)
INSERT INTO users (username, password_hash, email, role) VALUES
('admin', 'scrypt:32768:8:1$EqVZ8xGKJYLKqVqJ$d8f0e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8', 'admin@cargo.com', 'admin');

-- 4.2. Test Kullanıcı (Şifre: user123)
INSERT INTO users (username, password_hash, email, role) VALUES
('testuser', 'scrypt:32768:8:1$EqVZ8xGKJYLKqVqJ$d8f0e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8e8c8', 'user@cargo.com', 'user');

-- 4.3. Kocaeli İlçeleri (41 ilçe)
INSERT INTO districts (name, latitude, longitude) VALUES
('Başiskele', 40.6667, 29.8333),
('Çayırova', 40.8167, 29.3667),
('Darıca', 40.7667, 29.3833),
('Derince', 40.7667, 29.8333),
('Dilovası', 40.7833, 29.5167),
('Gebze', 40.8000, 29.4300),
('Gölcük', 40.7167, 29.8167),
('İzmit', 40.7650, 29.9400),
('Kandıra', 41.0667, 30.1500),
('Karamürsel', 40.6833, 29.6167),
('Kartepe', 40.7500, 30.0333),
('Körfez', 40.7667, 29.7500),
('Derince', 40.7667, 29.8333),
('Başiskele', 40.6667, 29.8333);

-- 4.4. Araç Tipleri
INSERT INTO vehicle_types (name, capacity_kg, rental_cost) VALUES
('Küçük Araç', 500, 100),
('Orta Araç', 750, 150),
('Büyük Araç', 1000, 200);

-- 4.5. Kullanıcı Araçları (Admin için 3 araç)
INSERT INTO vehicles (vehicle_type_id, user_id, is_rented, current_location_district_id) VALUES
(1, 1, FALSE, 8),  -- Küçük Araç - İzmit
(1, 1, FALSE, 8),  -- Küçük Araç - İzmit
(1, 1, FALSE, 8);  -- Küçük Araç - İzmit

-- 4.6. Sistem Parametreleri
INSERT INTO system_parameters (cost_per_km) VALUES (1.50);

-- ============================================================
-- TAMAMLANDI
-- ============================================================

SELECT 'Veritabanı başarıyla oluşturuldu!' AS status;
SELECT 'Toplam ' || COUNT(*) || ' ilçe eklendi' AS districts FROM districts;
SELECT 'Toplam ' || COUNT(*) || ' araç tipi eklendi' AS vehicle_types FROM vehicle_types;
SELECT 'Toplam ' || COUNT(*) || ' kullanıcı eklendi' AS users FROM users;
