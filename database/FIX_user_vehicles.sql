-- ADIM 1: Önce hangi kullanıcılar var kontrol et
SELECT id, username, role FROM users ORDER BY id;

-- ADIM 2: İlk kullanıcının ID'sine göre vehicles güncelle
-- (Yukarıdaki sonuca göre bu komutu düzenleyin)

-- ÖRNEĞİN: İlk kullanıcı id=2 ise:
-- UPDATE vehicles SET user_id = 2 WHERE user_id IS NULL;

-- VEYA: Admin kullanıcıyı otomatik bul ve ata
UPDATE vehicles v
SET user_id = (SELECT id FROM users WHERE role = 'ADMIN' LIMIT 1)
WHERE user_id IS NULL;

-- VEYA: İlk kullanıcıyı otomatik bul ve ata  
UPDATE vehicles v
SET user_id = (SELECT MIN(id) FROM users)
WHERE user_id IS NULL;

-- Kontrol et
SELECT v.*, u.username 
FROM vehicles v
LEFT JOIN users u ON u.id = v.user_id
ORDER BY v.id;
