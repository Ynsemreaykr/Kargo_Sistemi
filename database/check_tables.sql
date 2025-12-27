-- ============================================
-- VERİTABANI KONTROL SORGUSU
-- ============================================
-- Önce hangi tabloların olduğunu kontrol edelim

-- Tüm tabloları listele
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Cargos tablosu var mı kontrol et
SELECT EXISTS (
   SELECT FROM information_schema.tables 
   WHERE table_schema = 'public'
   AND table_name = 'cargos'
);
