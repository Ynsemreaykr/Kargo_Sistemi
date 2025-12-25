# SİSTEM PARAMETRELERİ TEST KONTROL LİSTESİ

## ADIM 1: Backend Çalışıyor mu?

**Kontrol:**
- start.bat penceresi açık mı?
- Son satırda şunu görüyor musunuz?
  ```
  ✓ System parameters API registered
  Running on http://127.0.0.1:5002
  ```

**Eğer backend çalışmıyorsa:**
1. start.bat'ı ÇİFT TIKLA
2. 2 pencere açılacak (Frontend + Backend)
3. Backend penceresinde "System parameters API registered" yazmalı

---

## ADIM 2: Browser Console Kontrolü

**Chrome/Edge'de:**
1. F12 bas (Developer Tools)
2. Console tab'ına git
3. "Ayarları Düzenle" butonuna bas
4. Console'da hata var mı?

**Beklenen:**
- Hata YOK
- "Settings load error" YOK

**Eğer hata varsa:**
- Hatayı kopyala ve bana gönder

---

## ADIM 3: Network Kontrolü

**Developer Tools'da:**
1. Network tab'ına git
2. "Ayarları Düzenle" butonuna bas
3. `system-parameters` isteğini bul
4. Status code ne?

**Başarılı:** 200 OK
**Başarısız:** 404, 500, veya Failed

---

## ADIM 4: Backend Test

**PowerShell'de:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5002/api/system-parameters" -UseBasicParsing
```

**Beklenen Sonuç:**
```
StatusCode: 200
Content: {"success":true,"data":{"cost_per_km":1.0,...}}
```

---

## HATALAR ve ÇÖZÜMLER

### "Ayarlar yüklenemedi!"
**NEDEN:** Backend çalışmıyor veya endpoint hatası
**ÇÖZÜM:** start.bat'ı yeniden başlat

### "Failed to fetch"
**NEDEN:** Backend port 5002'de çalışmıyor
**ÇÖZÜM:** Backend penceresini kontrol et

### 404 Not Found
**NEDEN:** Endpoint yanlış
**ÇÖZÜM:** app.py'de blueprint register edildi mi kontrol et
