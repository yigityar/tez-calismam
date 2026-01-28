#!/bin/bash

# =========================================================
#  TEZ VERİ SETİ OLUŞTURUCU (FİLTRELİ & DENGELİ SEÇİM)
# =========================================================
# Girdi: latest.csv (Androzoo veritabanı)
# Çıktı: balanced_benign.csv, balanced_malware.csv

INPUT_FILE="latest.csv"
OUT_BENIGN="balanced_benign.csv"
OUT_MALWARE="balanced_malware.csv"

# --- 1. AYARLAR & EŞİK DEĞERLERİ ---
TARGET_DATE="2022-01-01"   # Zaman Filtresi
MIN_SIZE=5242880           # 5 MB (Byte cinsinden)
MAX_SIZE=209715200         # 200 MB (Byte cinsinden)
MIN_DEX=1048576            # 1 MB (Kod yoğunluğu için)

echo "Filtreleme Başlıyor..."
echo "Kriterler:"
echo "  [*] Tarih >= $TARGET_DATE"
echo "  [*] APK Boyutu: 5 MB < Boyut <= 200 MB"
echo "  [*] Dex Boyutu: > 1 MB"
echo "  [*] Algılama: Benign (0) / Malware (>=4)"
echo "----------------------------------------------------"

# Dosya başlıklarını yaz
head -n 1 "$INPUT_FILE" > "$OUT_BENIGN"
head -n 1 "$INPUT_FILE" > "$OUT_MALWARE"

# Geçici dosyaları temizle
rm -f temp_*.txt

# --- 2. AWK İLE AYRIŞTIRMA VE FİLTRELEME ---
awk -F, -v T_DATE="$TARGET_DATE" \
        -v MIN_S="$MIN_SIZE" \
        -v MAX_S="$MAX_SIZE" \
        -v MIN_D="$MIN_DEX" '

# Başlık Satırını İşle
NR==1 {
    for (i=1; i<=NF; i++) {
        if ($i == "vt_detection") col_vt = i
        if ($i == "dex_date")     col_date = i
        if ($i == "apk_size")     col_size = i
        if ($i == "dex_size")     col_dex = i
        if ($i == "markets")      col_mkt = i
        if ($i == "sha256")       col_sha = i
        if ($i == "pkg_name")     col_pkg = i
    }
    # Kritik sütun kontrolü
    if (col_vt == 0 || col_size == 0) {
        print "HATA: CSV sütunları okunamadı!" > "/dev/stderr"
        exit 1
    }
}

# Veri Satırlarını İşle
NR>1 {
    # --- KURAL: Veri Bütünlüğü ---
    if ($col_sha == "" || $col_pkg == "") next
    
    # --- KURAL: Tarih >= 2022-01-01 ---
    # Tarih hedef tarihten küçükse (<) atla (next)
    if ($col_date < T_DATE) next

    # --- KURAL: apk_size > 5 MB ---
    # Boyut 5MB veya daha küçükse (<=) atla
    if ($col_size <= MIN_S) next

    # --- KURAL: apk_size <= 200 MB ---
    # Boyut 200MB dan büyükse (>) atla
    if ($col_size > MAX_S) next

    # --- KURAL: dex_size > 1 MB ---
    # Kod boyutu 1MB veya daha küçükse (<=) atla
    if ($col_dex <= MIN_D) next

    # --- MARKET KONTROLÜ (Dengeleme için) ---
    is_play = ($col_mkt ~ /play.google.com/) ? 1 : 0
    
    # --- SINIFLANDIRMA ---
    
    # Hedef: vt_detection == 0 (Temiz)
    if ($col_vt == 0) {
        if (is_play) print $0 >> "temp_benign_play.txt"
        else          print $0 >> "temp_benign_other.txt"
    }
    # Hedef: vt_detection >= 4 (Zararlı)
    else if ($col_vt >= 4) {
        if (is_play) print $0 >> "temp_malware_play.txt"
        else          print $0 >> "temp_malware_other.txt"
    }
}
' "$INPUT_FILE"

# --- 3. DENGELİ SEÇİM (RANDOM SAMPLING) ---
echo "Filtreleme bitti. CSV dosyaları oluşturuluyor..."

# Fonksiyon: Dosya varsa karıştır ve ekle, yoksa uyar
add_samples() {
    src=$1
    dest=$2
    count=$3
    label=$4
    
    if [ -f "$src" ]; then
        found=$(wc -l < "$src")
        echo "   -> $label: $found aday bulundu. $count adet seçiliyor."
        shuf -n "$count" "$src" >> "$dest"
    else
        echo "   UYARI: $label için hiç uygun aday bulunamadı!"
    fi
}

# Benign: 500 Play + 500 Non-Play
add_samples "temp_benign_play.txt" "$OUT_BENIGN" 500 "Benign (Google Play)"
add_samples "temp_benign_other.txt" "$OUT_BENIGN" 500 "Benign (Diğer Marketler)"

# Malware: 500 Play + 500 Non-Play
add_samples "temp_malware_play.txt" "$OUT_MALWARE" 500 "Malware (Google Play)"
add_samples "temp_malware_other.txt" "$OUT_MALWARE" 500 "Malware (Diğer Marketler)"

# Temizlik
rm -f temp_*.txt

echo "----------------------------------------------------"
echo "SONUÇ:"
count_b=$(($(wc -l < $OUT_BENIGN) - 1))
count_m=$(($(wc -l < $OUT_MALWARE) - 1))

echo "Benign Dosyası ($OUT_BENIGN) : $count_b satır"
echo "Malware Dosyası ($OUT_MALWARE): $count_m satır"

if [ "$count_b" -lt 1000 ] || [ "$count_m" -lt 1000 ]; then
    echo "!!! UYARI: Hedeflenen 1000'er sayıya ulaşılamadı. Filtreler çok sıkı olabilir."
else
    echo "BAŞARILI: Veri setleri indirme aşamasına hazır."
fi
