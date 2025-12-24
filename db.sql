-- =========================
-- 1. USERS (Kullanıcı / Admin)
-- =========================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(10) CHECK (role IN ('USER', 'ADMIN')) NOT NULL
);

-- =========================
-- 2. DISTRICTS (İlçe / İstasyon)
-- =========================
CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL
);

-- =========================
-- 3. SYSTEM PARAMETERS
-- =========================
CREATE TABLE system_parameters (
    id SERIAL PRIMARY KEY,
    cost_per_km NUMERIC NOT NULL,
    default_vehicle_count INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 4. VEHICLE TYPES
-- =========================
CREATE TABLE vehicle_types (
    id SERIAL PRIMARY KEY,
    capacity_kg INT NOT NULL,
    rental_cost NUMERIC NOT NULL
);

-- =========================
-- 5. VEHICLES
-- =========================
CREATE TABLE vehicles (
    id SERIAL PRIMARY KEY,
    vehicle_type_id INT REFERENCES vehicle_types(id),
    is_rented BOOLEAN DEFAULT FALSE
);

-- =========================
-- 6. SCENARIOS
-- =========================
CREATE TABLE scenarios (
    id SERIAL PRIMARY KEY,
    scenario_type VARCHAR(15)
        CHECK (scenario_type IN ('LIMITED', 'UNLIMITED')) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_cost NUMERIC
);

-- =========================
-- 7. CARGO
-- =========================
CREATE TABLE cargo (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    district_id INT REFERENCES districts(id),
    weight NUMERIC NOT NULL,
    assigned_vehicle_id INT REFERENCES vehicles(id),
    scenario_id INT REFERENCES scenarios(id),
    accepted BOOLEAN DEFAULT TRUE
);

-- =========================
-- 8. ROUTES
-- =========================
CREATE TABLE routes (
    id SERIAL PRIMARY KEY,
    vehicle_id INT REFERENCES vehicles(id),
    scenario_id INT REFERENCES scenarios(id),
    total_distance NUMERIC,
    total_cost NUMERIC
);

-- =========================
-- 9. ROUTE STOPS
-- =========================
CREATE TABLE route_stops (
    id SERIAL PRIMARY KEY,
    route_id INT REFERENCES routes(id),
    district_id INT REFERENCES districts(id),
    stop_order INT NOT NULL
);


CREATE DATABASE cargo_db
WITH
    OWNER = postgres
    TEMPLATE = template0
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C';


INSERT INTO districts (name, latitude, longitude) VALUES
('Başiskele', 40.7167, 29.9167),
('Çayırova', 40.8236, 29.3722),
('Darıca', 40.7686, 29.3864),
('Derince', 40.7569, 29.8306),
('Dilovası', 40.7914, 29.5481),
('Gebze', 40.8028, 29.4307),
('Gölcük', 40.7183, 29.8194),
('Kandıra', 41.0706, 30.1525),
('Karamürsel', 40.6917, 29.6167),
('Kartepe', 40.7453, 30.0236),
('Körfez', 40.7667, 29.7833),
('İzmit', 40.7667, 29.9167);


INSERT INTO vehicle_types (capacity_kg, rental_cost) VALUES
(500, 200),
(750, 0),
(1000, 0);


INSERT INTO system_parameters (cost_per_km, default_vehicle_count)
VALUES (1, 3);