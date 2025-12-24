-- Kargo İşletme Sistemi - Veritabanı Şeması
-- Kocaeli Üniversitesi - Yazılım Laboratuvarı III
-- PostgreSQL 12+

-- Mevcut tabloları temizle (geliştirme aşamasında)
DROP TABLE IF EXISTS route_stops CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS scenarios CASCADE;
DROP TABLE IF EXISTS cargo CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS vehicle_types CASCADE;
DROP TABLE IF EXISTS system_parameters CASCADE;
DROP TABLE IF EXISTS districts CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Kullanıcılar tablosu
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    role VARCHAR(20) CHECK (role IN ('ADMIN', 'USER')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İlçeler (İstasyonlar) tablosu
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sistem parametreleri tablosu
CREATE TABLE system_parameters (
    id SERIAL PRIMARY KEY,
    cost_per_km NUMERIC NOT NULL,
    default_vehicle_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Araç tipleri tablosu
CREATE TABLE vehicle_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    capacity_kg INTEGER NOT NULL,
    rental_cost NUMERIC NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Araçlar tablosu
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_type_id INTEGER REFERENCES vehicle_types(id) ON DELETE CASCADE,
    is_rented BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kargolar tablosu
CREATE TABLE cargo (
    id SERIAL PRIMARY KEY,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    weight_kg NUMERIC NOT NULL,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Senaryolar tablosu
CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    scenario_type VARCHAR(20) CHECK (scenario_type IN ('LIMITED', 'UNLIMITED')) NOT NULL,
    total_cost NUMERIC,
    total_distance NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rotalar tablosu
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES scenarios(id) ON DELETE CASCADE,
    vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
    distance NUMERIC,
    cost NUMERIC,
    route_geometry JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rota durakları tablosu
CREATE TABLE route_stops (
    id SERIAL PRIMARY KEY,
    route_id INTEGER REFERENCES routes(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    stop_order INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- İndeksler (performans için)
CREATE INDEX idx_routes_scenario ON routes(scenario_id);
CREATE INDEX idx_route_stops_route ON route_stops(route_id);
CREATE INDEX idx_cargo_district ON cargo(district_id);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type_id);

-- Başarılı mesajı
SELECT 'Veritabanı şeması başarıyla oluşturuldu!' AS message;
