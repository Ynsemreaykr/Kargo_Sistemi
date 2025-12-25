-- Her kullanıcı için 3 araç oluştur
-- (user1 zaten var, diğerleri için)

-- user_id = 3 (user2)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 3), (2, FALSE, 12, 3), (3, FALSE, 12, 3);

-- user_id = 6 (enes)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 6), (2, FALSE, 12, 6), (3, FALSE, 12, 6);

-- user_id = 9 (admin)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 9), (2, FALSE, 12, 9), (3, FALSE, 12, 9);

-- user_id = 10 (user)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 10), (2, FALSE, 12, 10), (3, FALSE, 12, 10);

-- user_id = 11 (yunus)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 11), (2, FALSE, 12, 11), (3, FALSE, 12, 11);

-- user_id = 12 (elif)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 12), (2, FALSE, 12, 12), (3, FALSE, 12, 12);

-- user_id = 13 (hasan)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 13), (2, FALSE, 12, 13), (3, FALSE, 12, 13);

-- user_id = 14 (ömer)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 14), (2, FALSE, 12, 14), (3, FALSE, 12, 14);

-- user_id = 15 (ulku)
INSERT INTO vehicles (vehicle_type_id, is_rented, current_location_district_id, user_id)
VALUES (1, FALSE, 12, 15), (2, FALSE, 12, 15), (3, FALSE, 12, 15);

-- KONTROL ET
SELECT u.username, COUNT(v.id) as vehicle_count
FROM users u
LEFT JOIN vehicles v ON v.user_id = u.id
GROUP BY u.username, u.id
ORDER BY u.id;

-- Her kullanıcı 3 araç görmeli!
