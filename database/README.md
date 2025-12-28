# Veritabanı Kurulum Rehberi

## 🗄️ Veritabanını Sıfırdan Oluşturma

### Yöntem 1: SQL Dosyası ile (Önerilen)

```bash
# PostgreSQL komut satırından
psql -U postgres -f database/database_setup.sql
```

### Yöntem 2: pgAdmin ile

1. pgAdmin'i aç
2. Sunucuya bağlan (localhost)
3. Sağ tık → Create → Database
4. İsim: `cargo_db`
5. Encoding: UTF8
6. Save
7. Query Tool aç
8. `database_setup.sql` dosyasını aç ve çalıştır

### Yöntem 3: Manuel Komutlar

```sql
-- 1. Veritabanı oluştur
CREATE DATABASE cargo_db;

-- 2. Bağlan
\c cargo_db

-- 3. Tabloları oluştur (database_setup.sql'deki komutları çalıştır)
```

---

## 📋 Veritabanı Yapısı

### Tablolar

1. **users** - Kullanıcılar (admin, user)
2. **districts** - İlçeler (Kocaeli 41 ilçe)
3. **vehicle_types** - Araç tipleri (Küçük, Orta, Büyük)
4. **vehicles** - Kullanıcı araçları
5. **cargos** - Kargolar
6. **scenarios** - Dağıtım senaryoları
7. **routes** - Rotalar
8. **route_stops** - Rota durakları
9. **route_cargos** - Rota kargoları
10. **system_parameters** - Sistem parametreleri

---

## 🔑 Varsayılan Kullanıcılar

| Kullanıcı | Şifre | Rol |
|-----------|-------|-----|
| admin | admin123 | admin |
| testuser | user123 | user |

---

## 🚛 Varsayılan Araç Tipleri

| Tip | Kapasite | Kiralama Maliyeti |
|-----|----------|-------------------|
| Küçük Araç | 500 kg | 100 TL |
| Orta Araç | 750 kg | 150 TL |
| Büyük Araç | 1000 kg | 200 TL |

---

## ✅ Kurulum Kontrolü

```sql
-- Tabloları kontrol et
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public';

-- İlçe sayısını kontrol et
SELECT COUNT(*) FROM districts;

-- Kullanıcıları kontrol et
SELECT username, role FROM users;
```

---

## 🔄 Veritabanını Sıfırlama

Eğer veritabanını tamamen silip yeniden oluşturmak istersen:

```bash
# Yöntem 1: SQL dosyası ile (otomatik siler ve oluşturur)
psql -U postgres -f database/database_setup.sql

# Yöntem 2: Manuel
psql -U postgres
DROP DATABASE cargo_db;
CREATE DATABASE cargo_db;
\c cargo_db
\i database/database_setup.sql
```

---

## 🐛 Sorun Giderme

### Hata: "database already exists"
```sql
DROP DATABASE cargo_db;
CREATE DATABASE cargo_db;
```

### Hata: "permission denied"
```bash
# postgres kullanıcısı ile çalıştır
psql -U postgres
```

### Hata: "encoding mismatch"
```sql
CREATE DATABASE cargo_db
    WITH ENCODING = 'UTF8';
```

---

## 📊 Veritabanı Şeması

```
users
├── id (PK)
├── username
├── password_hash
├── email
└── role

districts
├── id (PK)
├── name
├── latitude
└── longitude

vehicle_types
├── id (PK)
├── name
├── capacity_kg
└── rental_cost

vehicles
├── id (PK)
├── vehicle_type_id (FK)
├── user_id (FK)
├── is_rented
└── current_location_district_id (FK)

cargos
├── id (PK)
├── user_id (FK)
├── district_id (FK)
├── weight_kg
├── quantity
└── status

scenarios
├── id (PK)
├── user_id (FK)
├── scenario_type
├── algorithm_used
├── total_distance_km
└── total_cost

routes
├── id (PK)
├── scenario_id (FK)
├── vehicle_id (FK)
├── start_location_id (FK)
├── end_location_id (FK)
├── total_distance_km
└── total_cost

route_stops
├── id (PK)
├── route_id (FK)
├── district_id (FK)
└── stop_order

route_cargos
├── id (PK)
├── route_id (FK)
└── cargo_id (FK)

system_parameters
├── id (PK)
└── cost_per_km
```
