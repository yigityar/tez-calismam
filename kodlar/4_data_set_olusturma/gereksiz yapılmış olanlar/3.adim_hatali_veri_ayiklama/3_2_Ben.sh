#!/bin/bash

# Klasör yollarını belirleyin
JSON_DIR="/home/yigit/Tez_Analiz/statik_analiz/out/step1_identity_Benign"
CORRUPT_DIR="/media/yigit/DISK/dataset/Corrupted/Corrupted_Benign_APKs"

echo "📂 Taşınmış APK'lar referans alınarak JSON'lar taşınıyor..."

# Sayaç
moved_count=0

# Sadece CORRUPT_DIR içindeki .apk dosyalarını baz al
for apk in "$CORRUPT_DIR"/*.apk; do
    [ -e "$apk" ] || continue
    
    # Dosya adını uzantısız al (Örn: "app1.apk" -> "app1")
    base_name=$(basename "$apk" .apk)
    
    # JSON dosyasının tam yolunu belirle
    json_file="$JSON_DIR/$base_name.json"
    
    # Eğer JSON dosyası kaynak klasörde varsa taşı
    if [ -f "$json_file" ]; then
        mv "$json_file" "$CORRUPT_DIR/"
        echo "[+] JSON taşındı: $base_name.json"
        ((moved_count++))
    fi
done

echo "---------------------------------------"
echo "✅ İşlem Tamamlandı."
echo "Toplam taşınan JSON sayısı: $moved_count"
echo "Hedef klasör: $CORRUPT_DIR"
