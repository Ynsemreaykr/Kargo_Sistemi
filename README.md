# 🚚 Kargo İşletme Sistemi

Kocaeli Üniversitesi - Yazılım Laboratuvarı III  
Kocaeli ilçeleri arasında kargo optimizasyon sistemi

---

## 📥 GitHub'dan İlk Kurulum

Projeyi yeni klonladıysanız, **sırasıyla** şu adımları izleyin:

### 1️⃣ Python Bağımlılıklarını Yükle
```bash
pip install -r requirements.txt
```

### 2️⃣ PostgreSQL Veritabanını Hazırla

**a) PostgreSQL'de veritabanı oluştur:**
```sql
CREATE DATABASE kargo_db;
```

**b) Şemaları yükle:**
```bash
psql -U postgres -d kargo_db -f database/schema.sql
psql -U postgres -d kargo_db -f database/seed_data.sql
```

### 3️⃣ Veritabanı Bağlantı Ayarları

`api/.env` dosyası oluştur:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kargo_db
DB_USER=postgres
DB_PASSWORD=sizin_postgresql_sifreniz
SECRET_KEY=rastgele-gizli-anahtar-123
```

### 4️⃣ Kullanıcı Sistemini Kur
```bash
cd api
python quick_setup.py
```

Bu adım:
- ✅ `users` tablosuna `password_hash` kolonu ekler
- ✅ Varsayılan kullanıcıları oluşturur:
  - 👑 Admin: `admin` / `admin123`
  - 👤 User: `user` / `user123`

---

## 🚀 Kullanım

### Kolay Yol (Windows):
```bash
start.bat
```
Bu komut hem backend'i hem frontend'i başlatır ve tarayıcıda login sayfasını açar.

### Manuel Yol:

**Terminal 1 - Backend:**
```bash
cd api
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
python -m http.server 8000
```

**Tarayıcı:**
```
http://localhost:8000/login.html
```

---

## 🎯 Varsayılan Kullanıcılar

| Kullanıcı | Şifre | Rol | Sayfa |
|-----------|-------|-----|-------|
| admin | admin123 | ADMIN | admin.html (Admin Panel) |
| user | user123 | USER | index.html (Kargo Sistemi) |

---

## 📁 Proje Yapısı

```
yazlab3/
├── api/                    # Backend (Flask)
│   ├── app.py             # Ana uygulama
│   ├── auth.py            # Kimlik doğrulama
│   ├── routes.py          # API endpoint'leri
│   ├── config.py          # Veritabanı bağlantısı
│   ├── quick_setup.py     # Kullanıcı kurulum scripti
│   └── .env               # Veritabanı ayarları (oluşturulacak)
│
├── frontend/              # Frontend (HTML/CSS/JS)
│   ├── login.html         # Giriş/Kayıt sayfası
│   ├── index.html         # Kargo sistemi (User)
│   ├── admin.html         # Admin paneli
│   ├── app.js             # Ana JavaScript
│   └── styles.css         # Stiller
│
├── database/              # Veritabanı şemaları
│   ├── schema.sql         # Tablo yapıları
│   ├── seed_data.sql      # Başlangıç verileri
│   └── add_auth.sql       # Auth migration (manuel kullanım)
│
├── setup.bat              # İlk kurulum scripti
├── start.bat              # Sistemi başlat
├── requirements.txt       # Python bağımlılıkları
└── README.md              # Bu dosya
```

---

## 🔧 Teknolojiler

**Backend:**
- Flask 3.0.0
- PostgreSQL (psycopg 3.1.18)
- Flask-Session (session-based auth)
- Werkzeug (password hashing)

**Frontend:**
- Vanilla HTML/CSS/JavaScript
- Leaflet.js (harita)
- OpenStreetMap

---

## ⚙️ Özellikler

- ✅ Session-based kimlik doğrulama
- ✅ Admin ve User rolleri
- ✅ Kullanıcı kayıt sistemi
- ✅ Kargo senaryo oluşturma
- ✅ Harita üzerinde rota görselleştirme
- ✅ İlçeler arası mesafe hesaplama

---

## 🆘 Sorun Giderme

### "Bağlantı hatası. Backend çalışıyor mu?"

**Çözüm:**
1. Backend terminalini kontrol edin
2. `http://localhost:5002` adresinde API çalışıyor mu?
3. `.env` dosyasındaki veritabanı şifresi doğru mu?

### "No module named 'psycopg'"

**Çözüm:**
```bash
pip install -r requirements.txt
```

### PostgreSQL bağlantı hatası

**Çözüm:**
1. PostgreSQL servisi çalışıyor mu?
2. `kargo_db` veritabanı oluşturulmuş mu?
3. `api/.env` dosyasındaki bilgiler doğru mu?

---

## 📝 Lisans

Kocaeli Üniversitesi - Yazılım Laboratuvarı III Projesi

---

## 👨‍💻 Geliştirme

**Sadece iki .bat dosyası var:**

1. **setup.bat** - İlk kurulum (sadece 1 kez)
2. **start.bat** - Sistemi başlat (her seferinde)

**Diğer kullanışlı komutlar:**

```bash
# Yeni dependency eklediyseniz
pip freeze > requirements.txt

# Veritabanını sıfırlamak isterseniz
dropdb kargo_db
createdb kargo_db
psql -U postgres -d kargo_db -f database/schema.sql
psql -U postgres -d kargo_db -f database/seed_data.sql
python api/quick_setup.py
```

---

**Session Davranışı:**
- ✅ Tarayıcı açık olduğu sürece giriş yapılı kalır
- ✅ Tarayıcı kapatılınca session sona erer
- ✅ Yeniden açınca login ekranına yönlendirilir
