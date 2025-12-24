# Kargo İşletme Sistemi

Kocaeli Üniversitesi - Bilgisayar Mühendisliği  
Yazılım Laboratuvarı III (2025-2026 Güz)

## Proje Hakkında

Kocaeli iline ait ilçe merkezleri (istasyonlar) arasında bulunan kargoların, kargo araçları ile en düşük maliyet ve en uygun rota üzerinden taşınmasını sağlayan web tabanlı bir sistem.

### Önemli Kavramlar

- **İstasyonlar**: Kocaeli ilçe merkezleri (Başiskele, Çayırova, Darıca, Derince, Dilovası, Gebze, Gölcük, Kandıra, Karamürsel, Kartepe, Körfez, İzmit)
- **Rota Modeli**: İlk istasyon → Diğer istasyonlar → İlk istasyona dönüş (kapalı döngü)
- **Senaryo Tipleri**: 
  - LIMITED: Sınırlı araç sayısı
  - UNLIMITED: Sınırsız araç kullanımı

## Proje Aşamaları

- ✅ **AŞAMA 0**: Veritabanı ve proje iskeleti
- ✅ **AŞAMA 1**: Backend (algoritmasız, sağlam API)
- ⏳ **AŞAMA 2**: Frontend ve harita (test ve görselleştirme)
- ⏳ **AŞAMA 3**: Algoritma (sınırlı / sınırsız araç problemleri)
- ⏳ **AŞAMA 4**: Gerçek yol (OSM) ve ileri optimizasyon

**Şu anki durum**: AŞAMA 1 tamamlandı

## Kurulum

### 1. Gereksinimler

- Python 3.8+
- PostgreSQL 12+
- pip (Python paket yöneticisi)

### 2. PostgreSQL Kurulumu

```bash
# PostgreSQL kurulumunu yapın (Windows için PostgreSQL installer)
# Veritabanı oluşturun:
createdb kargo_db
```

### 3. Veritabanı Şemasını Yükleyin

```bash
# Şemayı yükle
psql -d kargo_db -f database/schema.sql

# Başlangıç verilerini yükle
psql -d kargo_db -f database/seed_data.sql
```

### 4. Python Bağımlılıklarını Yükleyin

```bash
# Virtual environment oluşturun (opsiyonel ama önerilir)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### 5. Veritabanı Bağlantı Ayarları

`api` klasöründe `.env` dosyası oluşturun (veya `.env.example` dosyasını kopyalayın):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kargo_db
DB_USER=postgres
DB_PASSWORD=your_password_here
```

**Önemli**: `DB_PASSWORD` değerini kendi PostgreSQL şifrenizle değiştirin!

### 6. API'yi Başlatın

```bash
cd api
python app.py
```

API şu adreste çalışacaktır: `http://localhost:5000`

## API Endpoint'leri

### 1. İlçeleri Listele

```http
GET /api/districts
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "İzmit",
      "latitude": 40.7654,
      "longitude": 29.9401
    },
    ...
  ]
}
```

### 2. Senaryo Oluştur

```http
POST /api/scenarios
Content-Type: application/json

{
  "scenario_type": "LIMITED",
  "cargos": [
    {
      "district_id": 1,
      "weight_kg": 100,
      "quantity": 2
    },
    {
      "district_id": 5,
      "weight_kg": 150,
      "quantity": 3
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scenario_id": 1,
    "total_cost": 450.50,
    "total_distance": 120.5,
    "route_count": 2
  }
}
```

### 3. Senaryo Detayı

```http
GET /api/scenarios/1
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "scenario_type": "LIMITED",
    "total_cost": 450.50,
    "total_distance": 120.5,
    "routes": [...]
  }
}
```

### 4. Rotaları Getir

```http
GET /api/routes/1
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "vehicle_id": 1,
      "distance": 45.5,
      "cost": 250.0,
      "stops": [...]
    }
  ]
}
```

### 5. Sistem Parametreleri

```http
GET /api/system-parameters
```

## Test Etme

### curl ile Test

```bash
# İlçeleri listele
curl http://localhost:5000/api/districts

# Senaryo oluştur
curl -X POST http://localhost:5000/api/scenarios \
  -H "Content-Type: application/json" \
  -d "{\"scenario_type\":\"LIMITED\",\"cargos\":[{\"district_id\":1,\"weight_kg\":100,\"quantity\":2}]}"

# Senaryo detayı
curl http://localhost:5000/api/scenarios/1
```

### Postman ile Test

1. Postman'i açın
2. Yeni bir request oluşturun
3. Yukarıdaki endpoint'leri test edin

## Proje Yapısı

```
lab3/
├── api/
│   ├── app.py              # Flask ana dosyası
│   ├── config.py           # Veritabanı yapılandırması
│   ├── routes.py           # API endpoint'leri
│   └── utils.py            # Yardımcı fonksiyonlar
├── database/
│   ├── schema.sql          # Veritabanı şeması
│   └── seed_data.sql       # Başlangıç verileri
├── requirements.txt        # Python bağımlılıkları
└── README.md               # Bu dosya
```

## Önemli Notlar

### AŞAMA 1 Hakkında

⚠️ **Bu aşamada gerçek algoritma YOKTUR!**

- Rotalar rastgele (dummy) olarak üretilir
- Amaç: API ve veritabanı yapısını test etmek
- AŞAMA 3'te gerçek sezgisel algoritma eklenecektir

### Dummy Rota Mantığı

1. Her kargo için rastgele bir araç atanır
2. Her araç için basit bir rota oluşturulur
3. Mesafe: Haversine formülü ile kuş uçuşu hesaplanır
4. Maliyet: `(mesafe × cost_per_km) + rental_cost`

## Sorun Giderme

### Veritabanı Bağlantı Hatası

```
✗ Veritabanı bağlantı hatası: ...
```

**Çözüm:**
- PostgreSQL'in çalıştığından emin olun
- `.env` dosyasındaki bağlantı bilgilerini kontrol edin
- `kargo_db` veritabanının oluşturulduğundan emin olun

### Import Hatası

```
ModuleNotFoundError: No module named 'flask'
```

**Çözüm:**
```bash
pip install -r requirements.txt
```

### Port Zaten Kullanımda

```
OSError: [Errno 98] Address already in use
```

**Çözüm:**
- 5000 portunu kullanan başka bir uygulamayı kapatın
- Veya `app.py` dosyasında portu değiştirin

## Sonraki Adımlar

- [ ] AŞAMA 2: Frontend ve harita görselleştirme
- [ ] AŞAMA 3: Gerçek algoritma implementasyonu
- [ ] AŞAMA 4: OpenStreetMap entegrasyonu

## Lisans

Bu proje Kocaeli Üniversitesi Yazılım Laboratuvarı III dersi kapsamında geliştirilmiştir.
