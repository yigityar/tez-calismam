#!/bin/bash

INPUT_FILE="latest.csv"

# --- AYARLAR ---
# Kriterler aynı kalıyor
MIN_APK_SIZE=5242880       # 5 MB
MAX_APK_SIZE=209715200     # 200 MB
MIN_DEX_SIZE=1048576       # 1 MB
TARGET_DATE="2022-01-01"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Hata: $INPUT_FILE bulunamadı!"
    exit 1
fi

echo "Analiz ve Market Sayımı yapılıyor..."
echo "Kriterler: Tarih >= $TARGET_DATE, Boyut: 5-200MB, Dex > 1MB"
echo "------------------------------------------------"

# AWK komutu
# Çıktıyı 'sort' komutuna pipe'layarak marketleri çoktan aza sıralayacağız.

awk -F, -v MIN_APK_SIZE=$MIN_APK_SIZE \
        -v MAX_APK_SIZE=$MAX_APK_SIZE \
        -v MIN_DEX_SIZE=$MIN_DEX_SIZE \
        -v TARGET_DATE="$TARGET_DATE" '

BEGIN {
    benign_total = 0
    malware_total = 0
    discarded = 0
    # Market istatistiklerini tutacak diziler (Associative Arrays)
    # market_benign["google"] = 50 gibi...
}

# 1. BAŞLIKLARI BUL
NR==1 {
    for (i=1; i<=NF; i++) {
        if ($i == "vt_detection") col_vt = i
        if ($i == "dex_date")     col_date = i
        if ($i == "apk_size")     col_size = i
        if ($i == "dex_size")     col_dex = i
        if ($i == "pkg_name")     col_pkg = i
        if ($i == "sha256")       col_sha = i
        if ($i == "markets")      col_mkt = i   # Yeni eklenen sütun
    }
    
    if (col_vt=="" || col_date=="" || col_mkt=="") {
        print "HATA: Gerekli sütunlar (ozellikle markets) bulunamadı!" > "/dev/stderr"
        exit 1
    }
}

# 2. VERİ ANALİZİ
NR>1 {
    # --- FİLTRELER ---
    if ($col_pkg == "" || $col_sha == "") { discarded++; next }
    if ($col_date < TARGET_DATE) { discarded++; next }
    if ($col_size <= MIN_APK_SIZE || $col_size > MAX_APK_SIZE) { discarded++; next }
    if ($col_dex <= MIN_DEX_SIZE) { discarded++; next }

    # --- TİP BELİRLEME ---
    type = ""
    if ($col_vt == 0) {
        type = "BENIGN"
        benign_total++
    }
    else if ($col_vt >= 4) {
        type = "MALWARE"
        malware_total++
    }
    else {
        discarded++
        next # Gri alan (1-3 arası) ise market sayımına katmıyoruz
    }

    # --- MARKET ANALİZİ ---
    # Market sütunu "play.google.com|anzhi|appchina" şeklinde olabilir.
    # "|" işaretine göre parçalıyoruz.
    
    n = split($col_mkt, markets_array, "|")
    
    for (i=1; i<=n; i++) {
        m_name = markets_array[i]
        
        # Boş ise atla
        if (m_name == "") continue;

        # Market ismini kaydet (İstatistik için)
        all_markets[m_name] = 1 

        if (type == "BENIGN") {
            stats_benign[m_name]++
        } else {
            stats_malware[m_name]++
        }
    }
}

END {
    # Önce Genel Özeti ekrana (stderr) basalım ki tabloya karışmasın
    print "\n--- GENEL ÖZET ---" > "/dev/stderr"
    print "Toplam Temiz (Benign)   : " benign_total > "/dev/stderr"
    print "Toplam Zararlı (Malware): " malware_total > "/dev/stderr"
    print "------------------------\n" > "/dev/stderr"

    # Tablo Başlığı
    printf "%-30s %-15s %-15s %-15s\n", "MARKET_ADI", "TOPLAM", "BENIGN", "MALWARE"
    
    # Tüm marketleri gez
    for (m in all_markets) {
        b_count = (stats_benign[m] ? stats_benign[m] : 0)
        m_count = (stats_malware[m] ? stats_malware[m] : 0)
        total = b_count + m_count
        
        # Sadece tablosal veriyi stdout a basıyoruz (Sort için)
        printf "%-30s %-15d %-15d %-15d\n", m, total, b_count, m_count
    }
}
' "$INPUT_FILE" | sort -k2 -nr | head -n 20  # Toplam sayıya göre sırala ve ilk 20'yi göster
