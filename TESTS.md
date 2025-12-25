# KARGO İŞLETME SİSTEMİ - TEST SENARYOLARI

## Test 1: Limited Mod - Basit Test
**Test Edilen:** 3 ücretsiz araç yeterli mi?

**Kargolar:**
- Gebze: 200 kg x 2 kargo
- Darıca: 150 kg x 1 kargo  
- Toplam: 550 kg

**Beklenen:**
✅ 1 araç kullanılacak
✅ Toplam maliyet: sadece yakıt (rental=0)
✅ Rota: İzmit → Gebze → Darıca

---

## Test 2: Limited Mod - Kapasite Aşımı
**Test Edilen:** LIMITED modda araç yetersiz

**Kargolar:**
- Gebze: 1200 kg
- Darıca: 1200 kg
- Körfez: 1200 kg
- Gölcük: 1200 kg
- Toplam: 4800 kg

**Kendi Araçlar:** 3 x 1000 kg = 3000 kg

**Beklenen:**
❌ HATA: "Araç yetersiz! 2 ilçeye ulaşılamadı: Körfez, Gölcük"

---

## Test 3: Unlimited Mod - Araç Kiralama
**Test Edilen:** Otomatik araç kiralama

**Aynı kargolar:** 4800 kg

**Beklenen:**
✅ Kendi 3 araç kullanıldı (3000 kg)
💰 2 araç kiralandı (1800 kg için)
✅ Kiralama maliyeti: 2 x rental_cost
✅ Yakıt maliyeti: mesafe x cost_per_km
✅ Toplam: kiralama + yakıt

Console:
```
🚛 Kendi araçlar: 3 adet (ücretsiz)
✓ Rota 1, 2, 3 oluşturuldu
💰 UNLIMITED MOD: 2 ilçe için araç kiralanacak
   🚛 Araç #1 kiralandı: Kamyon (Kiralama: 500.00 TL)
   🚛 Araç #2 kiralandı: Kamyon (K iralama: 500.00 TL)
✅ TOPLAM 5 ROTA OLUŞTURULDU
💰 Toplam Maliyet: 2500.00 TL
   - Kiralama Maliyeti: 1000.00 TL
   - Yakıt Maliyeti: 1500.00 TL
```

---

## Test 4: Konum Takibi
**Test Edilen:** Araçlar son yerlerinde kalıyor mu?

**1. Senaryo:**
- Gebze'ye kargo (300 kg)

**Beklenen:**
```
🚛 ARAÇ 1 (Kamyon):
  📍 Başlangıç: İzmit (ID=12)
  ✓ Adım 1: Gebze eklendi
  → Araç 1 yeni konumu: İlçe ID 6
✓ Araç 1 konumu güncellendi: İlçe 6
```

**2. Senaryo:**
- Körfez'e kargo (300 kg)

**Beklenen:**
```
🚛 ARAÇ 1 (Kamyon):
  📍 Başlangıç: Gebze (ID=6)  ← GEBZE'DEN BAŞLADI!
  ✓ Adım 1: Körfez eklendi
```

---

## Debuglog Kontrol Listesi

Backend console'da görmemiz gerekenler:

✅ Kargo dağılımı (ilçe adı + ID + ağırlık)
✅ Her araç için başlangıç konumu
✅ Adım adım ilçe ekleme
✅ Kapasite dolunca uyarı
✅ Kiralama bildirimleri
✅ Nihai maliyet dağılımı
