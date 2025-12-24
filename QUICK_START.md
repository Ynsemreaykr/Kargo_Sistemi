# 🚀 HIZLI BAŞLANGIÇ - Kargo İşletme Sistemi

## ⚡ GitHub'dan İlk Kurulum

### 1️⃣ İlk Kurulum (Sadece 1 Kez)
```bash
setup.bat
```

Bu script:
- ✅ Tüm bağımlılıkları yükler
- ✅ Veritabanını hazırlar
- ✅ Varsayılan kullanıcıları oluşturur

**Varsayılan Kullanıcılar:**
- 👑 Admin: `admin` / `admin123`
- 👤 User: `user` / `user123`

---

## 🎮 Kullanım (Her Seferinde)

### Otomatik (Önerilen)
```bash
start.bat
```

Sistem başlar ve tarayıcıda login sayfası açılır!

### Manuel

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

## 📦 .BAT Dosyaları

| Dosya | Ne Zaman | Açıklama |
|-------|----------|----------|
| `setup.bat` | 1 kez | İlk kurulum (bağımlılıklar + veritabanı) |
| `start.bat` | Her seferinde | Sistemi başlat (Backend + Frontend) |

**Sadece 2 dosya var!** Diğerleri silindi. ✅

---

## ✅ Session Davranışı

- ✅ Tarayıcı açıkken giriş yapılı kalır
- ✅ Tarayıcı kapanınca session biter
- ✅ Yeniden açınca login ekranına gider

Browser kapatıp tekrar açtığınızda **her seferinde giriş yapmanız gerekir!**

---

## 🔧 Sorun Giderme

### "Bağlantı hatası. Backend çalışıyor mu?"

**Çözüm 1:** Backend'in çalıştığından emin olun
```bash
cd api
python app.py
```

Şunu görmelisiniz:
```
✓ Veritabanı bağlantısı başarılı
API çalışıyor: http://localhost:5002
```

**Çözüm 2:** .env dosyasını kontrol edin
```bash
# api/.env dosyası
DB_PASSWORD=sizin_sifreniz  ← Bunu kontrol edin!
```

**Çözüm 3:** PostgreSQL çalıştığından emin olun

---

## 🆘 Hala Çalışmıyor?

Sıfırdan başlayın:
```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Veritabanını sıfırla (PostgreSQL'de)
dropdb kargo_db
createdb kargo_db
psql -U postgres -d kargo_db -f database/schema.sql
psql -U postgres -d kargo_db -f database/seed_data.sql

# 3. Kullanıcıları oluştur
cd api
python quick_setup.py
```

