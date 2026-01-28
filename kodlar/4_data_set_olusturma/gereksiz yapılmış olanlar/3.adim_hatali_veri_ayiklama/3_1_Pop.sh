#!/bin/bash

# Klasör yollarını belirleyin
APK_DIR="/media/yigit/DISK/dataset/Popular"
CORRUPT_DIR="/media/yigit/DISK/dataset/Corrupted/Corrupted_Popular_APKs"

# Bozuk dosyalar için klasör oluştur
mkdir -p "$CORRUPT_DIR"

echo "🔍 Bozuk APK'lar taranıyor..."

# Sayaçlar
total=0
corrupt=0

# Tüm APK'ları tara
for apk in "$APK_DIR"/*.apk; do
    [ -e "$apk" ] || continue
    ((total++))
    
    # unzip -t (test) komutu ile dosya bütünlüğünü kontrol et
    # -qq parametresi çıktıları gizler, sadece hata koduna bakarız
    if ! unzip -t -qq "$apk" > /dev/null 2>&1; then
        echo "[!] Bozuk dosya bulundu: $(basename "$apk")"
        mv "$apk" "$CORRUPT_DIR/"
        ((corrupt++))
    fi
done

echo "---------------------------------------"
echo "✅ İşlem Tamamlandı."
echo "Toplam Taranan: $total"
echo "Taşınan Bozuk Dosya: $corrupt"
echo "Bozuk dosyalar şu klasöre taşındı: $CORRUPT_DIR"
