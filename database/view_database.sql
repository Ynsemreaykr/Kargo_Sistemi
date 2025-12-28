-- ============================================================
-- VERİTABANI TAMAMINI GÖRÜNTÜLEME KOMUTLARI
-- ============================================================
-- Kullanım: psql -U postgres -d cargo_db -f view_database.sql
-- ============================================================

\echo '============================================================'
\echo 'KARGO İŞLETME SİSTEMİ - VERİTABANI RAPORU'
\echo '============================================================'

-- 1. TABLOLAR VE KAYIT SAYILARI
\echo ''
\echo '📊 TABLO İSTATİSTİKLERİ'
\echo '------------------------------------------------------------'

SELECT 
    schemaname,
    tablename,
    (SELECT COUNT(*) FROM users) as users_count,
    (SELECT COUNT(*) FROM districts) as districts_count,
    (SELECT COUNT(*) FROM vehicle_types) as vehicle_types_count,
    (SELECT COUNT(*) FROM vehicles) as vehicles_count,
    (SELECT COUNT(*) FROM cargos) as cargos_count,
    (SELECT COUNT(*) FROM scenarios) as scenarios_count,
    (SELECT COUNT(*) FROM routes) as routes_count,
    (SELECT COUNT(*) FROM route_stops) as route_stops_count,
    (SELECT COUNT(*) FROM route_cargos) as route_cargos_count,
    (SELECT COUNT(*) FROM system_parameters) as system_parameters_count
FROM pg_tables 
WHERE schemaname = 'public' 
LIMIT 1;

-- 2. KULLANICILAR
\echo ''
\echo '👤 KULLANICILAR'
\echo '------------------------------------------------------------'
SELECT id, username, email, role, created_at FROM users ORDER BY id;

-- 3. İLÇELER
\echo ''
\echo '📍 İLÇELER'
\echo '------------------------------------------------------------'
SELECT id, name, latitude, longitude FROM districts ORDER BY name;

-- 4. ARAÇ TİPLERİ
\echo ''
\echo '🚛 ARAÇ TİPLERİ'
\echo '------------------------------------------------------------'
SELECT id, name, capacity_kg, rental_cost FROM vehicle_types ORDER BY capacity_kg;

-- 5. ARAÇLAR
\echo ''
\echo '🚗 ARAÇLAR'
\echo '------------------------------------------------------------'
SELECT 
    v.id,
    vt.name as vehicle_type,
    u.username as owner,
    v.is_rented,
    d.name as current_location
FROM vehicles v
JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
JOIN users u ON v.user_id = u.id
LEFT JOIN districts d ON v.current_location_district_id = d.id
ORDER BY v.id;

-- 6. KARGOLAR
\echo ''
\echo '📦 KARGOLAR'
\echo '------------------------------------------------------------'
SELECT 
    c.id,
    u.username as user,
    d.name as destination,
    c.weight_kg,
    c.quantity,
    c.status,
    c.created_at
FROM cargos c
JOIN users u ON c.user_id = u.id
JOIN districts d ON c.district_id = d.id
ORDER BY c.created_at DESC;

-- 7. SENARYOLAR
\echo ''
\echo '🎯 SENARYOLAR'
\echo '------------------------------------------------------------'
SELECT 
    s.id,
    u.username as user,
    s.scenario_type,
    s.algorithm_used,
    s.total_distance_km,
    s.total_cost,
    s.created_at
FROM scenarios s
JOIN users u ON s.user_id = u.id
ORDER BY s.created_at DESC;

-- 8. ROTALAR (Detaylı)
\echo ''
\echo '🛣️ ROTALAR'
\echo '------------------------------------------------------------'
SELECT 
    r.id,
    r.scenario_id,
    vt.name as vehicle_type,
    d1.name as start_location,
    d2.name as end_location,
    r.total_distance_km,
    r.total_cost,
    (SELECT COUNT(*) FROM route_stops WHERE route_id = r.id) as stop_count,
    (SELECT COUNT(*) FROM route_cargos WHERE route_id = r.id) as cargo_count
FROM routes r
JOIN vehicles v ON r.vehicle_id = v.id
JOIN vehicle_types vt ON v.vehicle_type_id = vt.id
LEFT JOIN districts d1 ON r.start_location_id = d1.id
LEFT JOIN districts d2 ON r.end_location_id = d2.id
ORDER BY r.scenario_id DESC, r.id;

-- 9. ROTA DURAKLARI (Son 5 rota için)
\echo ''
\echo '🚏 ROTA DURAKLARI (Son 5 Rota)'
\echo '------------------------------------------------------------'
SELECT 
    rs.route_id,
    rs.stop_order,
    d.name as district
FROM route_stops rs
JOIN districts d ON rs.district_id = d.id
WHERE rs.route_id IN (SELECT id FROM routes ORDER BY id DESC LIMIT 5)
ORDER BY rs.route_id DESC, rs.stop_order;

-- 10. SİSTEM PARAMETRELERİ
\echo ''
\echo '⚙️ SİSTEM PARAMETRELERİ'
\echo '------------------------------------------------------------'
SELECT id, cost_per_km, updated_at FROM system_parameters;

-- 11. VERİTABANI BOYUTU
\echo ''
\echo '💾 VERİTABANI BOYUTU'
\echo '------------------------------------------------------------'
SELECT 
    pg_size_pretty(pg_database_size('cargo_db')) as database_size;

-- 12. TABLO BOYUTLARI
\echo ''
\echo '📏 TABLO BOYUTLARI'
\echo '------------------------------------------------------------'
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

\echo ''
\echo '============================================================'
\echo 'RAPOR TAMAMLANDI'
\echo '============================================================'
