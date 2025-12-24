# Test Talimatları

## ✅ Yapılanlar:

1. ✅ Session artık browser kapanınca bitiyor
2. ✅ Login sayfası otomatik yönlendirme yapmıyor
3. ✅ Çıkış butonu her iki sayfada da var (index.html ve admin.html)

## 🧪 Test Etmek İçin:

### 1. Eski Session'ları Temizle
Browser'ı tamamen kapatın ve yeniden açın ya da:
- **Chrome**: Ctrl+Shift+Delete → Cookies ve cache
- **Edge**: Ctrl+Shift+Delete → Cookies
- Veya **Incognito/Private** mod kullanın

### 2. Backend'i Yeniden Başlat
```bash
# Eski backend'i durdur (Ctrl+C)
cd api
python app.py
```

### 3. Test Senaryosu

**Adım 1:** Frontend'i aç
```
http://localhost:8000/login.html
```

**Beklenen:**  
✅ Login sayfası açılmalı ve kalmalı  
✅ Otomatik yönlendirme OLMAMALI

**Adım 2:** Giriş Yap
- Username: `admin`
- Password: `admin123`

**Beklenen:**  
✅ "Giriş başarılı! Yönlendiriliyorsunuz..." mesajı  
✅ 1 saniye sonra admin.html'e yönlendirilmeli

**Adım 3:** Admin Panelde
**Beklenen:**  
✅ Header'da "admin" ve "👑 Admin" görmeli  
✅ "🚪 Çıkış" butonu görülmeli (sağ üstte)

**Adım 4:** Çıkış Yap
Çıkış butonuna tıkla

**Beklenen:**  
✅ Login sayfasına geri dönmeli

**Adım 5:** Tarayıcıyı Kapat ve Aç
Browser'ı kapat → Yeniden aç → `http://localhost:8000/index.html` git

**Beklenen:**  
✅ Login sayfasına yönlendirilmeli (session yok çünkü)

---

## 🐛 Sorun Varsa:

### Çıkış butonu görünmüyor?
1. Browser console aç (F12)
2. Hata var mı kontrol et
3. `document.getElementById('logoutBtn')` yaz - bulmalı
4. Cache temizle ve sayfayı yenile (Ctrl+Shift+R)

### Hala otomatik giriş yapıyor?
1. Backend'i kapat
2. `api/flask_session` klasörünü sil
3. Backend'i yeniden başlat
4. Browser cache temizle

### Test için Incognito kullanın!
En garantili test: 
- Incognito/Private window aç
- `http://localhost:8000/login.html`
- Tüm adımları test et
