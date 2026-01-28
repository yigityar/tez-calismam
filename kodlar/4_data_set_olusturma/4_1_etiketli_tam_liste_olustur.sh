#!/bin/bash

# =================================================================
#  TAM APK LİSTESİ SENKRONİZASYON (ÖZEL ETİKETLİ: MILITARY=3, POPULAR=2)
# =================================================================

OUTPUT_CSV="final_dataset_full.csv"
EXTERNAL_DRIVE="/run/media/yigit/DISK"
BASE_REPO="$EXTERNAL_DRIVE/dataset"

# Girdi Listeleri
BENIGN_LIST="balanced_benign.csv"
MALWARE_LIST="balanced_malware.csv"
MILITARY_LIST="Military.csv"
POPULAR_LIST="Popular.csv"

# Başlık satırı yoksa oluştur
if [ ! -f "$OUTPUT_CSV" ]; then
    echo "SHA256,SIZE,MARKET,PERMISSIONS_LIST,api_DEVICEID,api_EXEC,api_CIPHER,api_SMSMANAGER,api_DYN_LOAD,int_BOOT,LABEL" > "$OUTPUT_CSV"
fi

find_and_process() {
    list_file=$1
    label=$2
    type_name=$3
    
    if [ ! -f "$list_file" ]; then
        echo "UYARI: $list_file dosyası bulunamadı, bu liste atlanıyor."
        return
    fi

    echo "$type_name listesi işleniyor (Etiket: $label)..."
    
    # AndroZoo formatına göre (sha256 ve en sondaki markets) oku
    tail -n +2 "$list_file" | while IFS=, read -r sha256 sha1 md5 date size pkg ver vt_det vt_date dex_sz markets; do
        [ -z "$sha256" ] && continue

        # Zaten CSV'de varsa atla (Eski verileri korur, hızı artırır)
        if grep -q "$sha256" "$OUTPUT_CSV"; then
            continue
        fi

        # APK'yı 4 alt klasörde de ara
        apk_path=""
        for folder in "Benign" "Malware" "Military" "Popular"; do
            temp_path="$BASE_REPO/$folder/$sha256.apk"
            if [ -f "$temp_path" ]; then
                apk_path="$temp_path"
                break
            fi
        done

        if [ -n "$apk_path" ]; then
            echo -ne "Analiz ediliyor: $sha256 ($folder) \r"
            
            f_size=$(stat -c%s "$apk_path" 2>/dev/null || echo 0)
            
            # İzinlerin Çıkarılması
            manifest_raw=$(aapt dump permissions "$apk_path" 2>/dev/null)
            perm_list=$(echo "$manifest_raw" | grep "name=" | cut -d"'" -f2 | sort | uniq | tr '\n' '|')
            perm_list=${perm_list%|}
            [ -z "$perm_list" ] && perm_list="NO_PERMISSIONS"
            
            # API ve Intent Analizi
            xml_dump=$(aapt dump xmltree "$apk_path" AndroidManifest.xml 2>/dev/null)
            [[ "$xml_dump" =~ "BOOT_COMPLETED" ]] && int_boot=1 || int_boot=0
            
            dex_strings=$(unzip -p "$apk_path" classes.dex 2>/dev/null | strings)
            [[ "$dex_strings" =~ "getDeviceId" ]] && api_id=1 || api_id=0
            [[ "$dex_strings" =~ "Runtime;->exec" ]] && api_exec=1 || api_exec=0
            [[ "$dex_strings" =~ "javax/crypto" ]] && api_cipher=1 || api_cipher=0
            [[ "$dex_strings" =~ "android/telephony/SmsManager" ]] && api_sms_mgr=1 || api_sms_mgr=0
            [[ "$dex_strings" =~ "DexClassLoader" || "$dex_strings" =~ "loadClass" ]] && api_dyn=1 || api_dyn=0

            # Market bilgisini temizle (Virgülleri kaldır)
            clean_market=$(echo "$markets" | tr ',' ' ')
            
            # CSV'ye yaz (Label sütununa özel değerler gelecek)
            echo "$sha256,$f_size,$clean_market,$perm_list,$api_id,$api_exec,$api_cipher,$api_sms_mgr,$api_dyn,$int_boot,$label" >> "$OUTPUT_CSV"
        fi
    done
    echo -e "\n$type_name işlemi tamamlandı."
}

# --- ÇALIŞTIRMA ---
# Etiket Mantığı: 0=Temiz, 1=Zararlı, 3=Popüler, 4=Askeri
find_and_process "$BENIGN_LIST" 0 "BENIGN"
find_and_process "$MALWARE_LIST" 1 "MALWARE"
find_and_process "$POPULAR_LIST" 2 "POPULAR"
find_and_process "$MILITARY_LIST" 3 "MILITARY"

echo "------------------------------------------------"
echo "BÜTÜNLEŞTİRME TAMAMLANDI."
echo "Sonuç Dosyası : $OUTPUT_CSV"
echo "Toplam Satır  : $(wc -l < "$OUTPUT_CSV")"
