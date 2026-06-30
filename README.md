# 🚚 Kargo Rota Optimizasyon Sistemi v2.0

Kocaeli Üniversitesi - Yazılım Laboratuvarı III kapsamında geliştirilen, Kocaeli ilçeleri arasında kargo dağıtım süreçlerini, araç yüklerini ve teslimat rotalarını optimize eden web tabanlı otomasyon projesi.

---

## 📸 Ekran Görüntüleri

### 1. 🔑 Giriş Arayüzü (Premium Tasarım)
Cam efekti (glassmorphism), yavaşça hareket eden ambient arka plan küreleri, parlayan input odaklanmaları ve mikro animasyonlar içeren modern giriş sayfası.

![Giriş Ekranı](docs/screenshots/login_page.png)

### 2. 👤 Kullanıcı Arayüzü (Kullanıcı Paneli & Harita)
Kullanıcıların yeni kargo gönderisi oluşturabildiği, kargolarının durumunu takip edebildiği ve entegre Leaflet.js haritası üzerinde şubeleri görselleştirebildiği arayüz.

![Kullanıcı Paneli](docs/screenshots/user_dashboard.png)

### 3. 👑 Yönetici Paneli (Dağıtım Optimizasyonu)
Yöneticilerin bekleyen kargoları seçerek **Greedy**, **Simulated Annealing** veya **Hybrid** optimizasyon algoritmalarıyla dağıtım senaryoları ürettiği ve akıllı araç kiralama (LIMITED/UNLIMITED) kararları aldığı ekran.

![Yönetici Paneli](docs/screenshots/admin_dashboard.png)

### 4. 📍 Şube Yönetimi & Loglama
Yöneticilerin harita üzerinden veya liste aracılığıyla şube ekleyip/silebildiği, geçmiş dağıtım senaryolarını detaylı maliyet analizleriyle raporlayabildiği yönetim ekranı.

![Şube Yönetimi ve Raporlama](docs/screenshots/admin_branches.png)

---

## 🛠️ Teknolojiler & Kütüphaneler

### Backend (Flask API)
- **Flask 3.0.0 & Python 3.12+** - Uygulama sunucusu ve API katmanı
- **PostgreSQL (psycopg 3.1.18 & psycopg-pool)** - Neon.tech üzerinde barındırılan bulut veritabanı ve performanslı bağlantı havuzu
- **Flask-Session (filesystem)** - Güvenli ve tarayıcı kapanınca sonlanan oturum yönetimi
- **Werkzeug (security)** - Güvenli şifre hash'leme ve doğrulama

### Frontend (Modern UI)
- **Vanilla HTML5 & CSS3** - Modern göze hitap eden, cam (glassmorphism) efektli ve animasyonlu karanlık tema (dark mode) tasarımı
- **Leaflet.js (v1.9.4)** - Harita üzerinde şube konumlandırma, rota çizimi ve interaktif görselleştirme
- **OpenStreetMap API & OSRM (Open Source Routing Machine)** - Gerçek yol mesafelerini ve rota geometrisini hesaplama

---

## 📥 GitHub'dan İlk Kurulum

Projeyi bilgisayarınıza klonladıktan sonra **sırasıyla** aşağıdaki adımları takip edin:

### 1️⃣ Python Bağımlılıklarını Yükleyin
```bash
pip install -r requirements.txt
```

### 2️⃣ Cloud PostgreSQL (Neon.tech) veya Local DB Hazırlığı
Veritabanını sıfırdan oluşturmak ve v2.0 şemasına yükseltmek için:
- **Eski Şema Kurulumu:** `database/database_setup.sql` dosyasını çalıştırın.
- **V2.0 Schema Yükseltmesi:** `database/FULL_MIGRATION_v2.sql` dosyasını çalıştırarak tüm eksik sütunları (scenarios.total_distance, routes.route_geometry vb.) ve yeni tabloları otomatik ekleyin.

### 3️⃣ Veritabanı Bağlantı Ayarları
`api/.env` dosyası oluşturun ve bağlantı dizesini yazın:
```env
DATABASE_URL=postgresql://neondb_owner:npg_le3yhId8AWBb@ep-square-paper-asng6koy.c-4.eu-central-1.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=kargo-sistem-secret-key-2025
```

### 4️⃣ Başlangıç Kullanıcılarını Kurun
```bash
cd api
python quick_setup.py
```
Bu adım, veritabanına varsayılan kullanıcıları ekler:
- 👑 Admin: `admin` / `admin123`
- 👤 Test Kullanıcısı: `testuser` / `user123`

---

## 🚀 Sistemi Çalıştırma

### 💻 Kolay Yol (Windows):
Proje dizininde yer alan toplu iş dosyasını çalıştırmanız yeterlidir:
```bash
start.bat
```
Bu betik hem backend API sunucusunu hem de frontend web sunucusunu eşzamanlı olarak başlatarak tarayıcınızda login sayfasını açar.

### 🔧 Manuel Yol:
**Terminal 1 (Backend):**
```bash
cd api
python app.py
```
**Terminal 2 (Frontend):**
```bash
cd frontend
python -m http.server 8000
```
Tarayıcınızdan `http://localhost:8000/login.html` adresine giderek sistemi kullanmaya başlayabilirsiniz.

---

## 🎯 Giriş Bilgileri

| Kullanıcı Adı | Şifre | Rol | Yönlendirilen Sayfa |
|---|---|---|---|
| **admin** | `admin123` | ADMIN | admin.html (Yönetici Paneli) |
| **testuser** | `user123` | USER | user_dashboard.html (Kullanıcı Paneli) |

---

## 📁 Proje Klasör Yapısı

```
Kargo_Sistemi/
├── api/                    # Flask Backend Modülleri
│   ├── app.py             # Sunucu başlatma ve session yönetimi
│   ├── auth.py            # Oturum açma, kayıt ve yetkilendirme (decoratörler)
│   ├── routes.py          # Harita, şube ve senaryo API uç noktaları
│   ├── admin_cargo.py     # Yönetici kargo onay/iptal işlemleri
│   ├── admin_distribution.py # Rota optimizasyon tetikleme ve kayıt
│   ├── config.py          # Veritabanı bağlantı havuzu (psycopg-pool)
│   └── .env               # Gizli anahtarlar ve DB URL
│
├── frontend/              # Arayüz Dosyaları (HTML/CSS/JS)
│   ├── login.html         # Premium giriş sayfası
│   ├── register.html      # Premium kayıt olma sayfası
│   ├── user_dashboard.html # Kullanıcı paneli ve Leaflet şube haritası
│   ├── admin.html         # Yönetici paneli ve dinamik rota çizim ekranı
│   └── styles.css         # Ortak tasarım tokenleri ve stiller
│
├── database/              # SQL Şemaları ve Göç Betikleri
│   ├── database_setup.sql # İlk şema ve test verileri
│   └── FULL_MIGRATION_v2.sql # Veritabanını v2.0 sürümüne taşıyan script
│
├── docs/
│   └── screenshots/       # Proje ekran görüntüleri
│
├── requirements.txt       # Python paket bağımlılıkları
├── setup.bat              # İlk kurulum otomasyonu
└── start.bat              # Uygulamayı başlatma betiği
```

---

## 📐 Optimizasyon Algoritmaları
Sistem, kargo dağıtım maliyetlerini ve mesafelerini minimuma indirmek amacıyla 3 farklı algoritma seçeneği sunar:
1. **Greedy (En Yakın Komşu):** Her adımda mevcut konuma en yakın teslimat noktasına yönelerek hızlı ve basit bir rota çizer.
2. **Simulated Annealing (Tavlama Benzetimi):** Rotalardaki yerel minimumlardan kaçmak için olasılıksal kabul kriterleri kullanarak global olarak en kısa mesafeli rotayı bulmayı hedefler.
3. **Hybrid:** İki yaklaşımı birleştirerek en iyi performansı ve en kararlı dağıtım planını üretir.
