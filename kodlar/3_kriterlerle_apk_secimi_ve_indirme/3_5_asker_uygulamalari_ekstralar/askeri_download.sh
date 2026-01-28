#!/bin/bash

# =========================================================
#  ANDROZOO BULK DOWNLOADER (EXTERNAL DISK VERSION)
# =========================================================

# --- AYARLAR ---
API_KEY="e2bdce1ec643b8c5fa93b00e40fd1b33ebb1b6572d8ca68c37f097385e5dae6a"
INPUT_FILE="en_guncel_askeri_uygulamalar.csv"
DOWNLOAD_DIR="/run/media/yigit/DISK 1/Askeri_Uygulamalar"

# Klasor yoksa olustur
mkdir -p "$DOWNLOAD_DIR"

# Dosya kontrolu
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Hata: $INPUT_FILE bulunamadi!"
    exit 1
fi

echo "--- Indirme Islemi Baslatiliyor ---"
echo "Hedef Dizin: $DOWNLOAD_DIR"

# Baslik satirini atla ve SHA256 kolonunu (1. kolon) oku
# AndroZoo API URL yapisi: https://androzoo.uni.lu/api/download?apikey=${API_KEY}&sha256=${SHA256}

tail -n +2 "$INPUT_FILE" | cut -d',' -f1 | while read -r sha256; do
    # Tırnak işaretlerini temizle
    sha256=$(echo "$sha256" | tr -d '"')
    
    TARGET_PATH="$DOWNLOAD_DIR/${sha256}.apk"

    # Eger dosya zaten varsa indirmeyi atla (Resume ozelligi)
    if [[ -f "$TARGET_PATH" ]]; then
        echo "Atlandy (Zaten var): $sha256"
        continue
    fi

    echo "Indiriliyor: $sha256 ..."
    
    # curl ile indirme yap
    # -L: Redirectleri takip et
    # -o: Belirtilen yola kaydet
    curl -L -G "https://androzoo.uni.lu/api/download" \
        --data-urlencode "apikey=$API_KEY" \
        --data-urlencode "sha256=$sha256" \
        -o "$TARGET_PATH"

    # Indirme durumunu kontrol et
    if [[ $? -eq 0 ]]; then
        echo "Basarili: $sha256"
    else
        echo "HATA: $sha256 indirilemedi!"
    fi

    # API'yi yormamak ve banlanmamak icin kisa bir bekleme
    sleep 1
done

echo "--- Tum Islemler Tamamlandi ---"
