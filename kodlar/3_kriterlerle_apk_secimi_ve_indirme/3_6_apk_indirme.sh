#!/bin/bash

# =================================================================
#  ANDROZOO DOWNLOAD & FEATURE EXTRACTION (ALL PERMISSIONS EDITION)
# =================================================================

# --- AYARLAR ---
API_KEY="e2bdce1ec643b8c5fa93b00e40fd1b33ebb1b6572d8ca68c37f097385e5dae6a"   # <-- API KEY'İ BURAYA YAPIŞTIR
OUTPUT_CSV="final_dataset_full.csv"           # Dosya ismini değiştirdim karışmasın diye
ERROR_LOG="errors.log"

# --- DİSK AYARI (DISK 1) ---
# Boşluk karakteri olduğu için tırnak içine aldık.
EXTERNAL_DRIVE="/run/media/yigit/DISK 1"
APK_STORAGE_DIR="$EXTERNAL_DRIVE/apks_repo"

# Girdi Dosyaları (Önceki adımdan gelenler)
BENIGN_LIST="balanced_benign.csv"
MALWARE_LIST="balanced_malware.csv"

# --- ÖN KONTROLLER ---

# 1. Disk Takılı mı Kontrolü
if [ ! -d "$EXTERNAL_DRIVE" ]; then
    echo "HATA: Harici disk bulunamadı!"
    echo "Aranan yol: $EXTERNAL_DRIVE"
    echo "Lütfen diski takın veya yolu kontrol edin."
    exit 1
fi

# 2. Klasör Oluşturma
mkdir -p "$APK_STORAGE_DIR"
touch "$ERROR_LOG"

echo "Hedef Disk: $EXTERNAL_DRIVE"
echo "APK Klasörü: $APK_STORAGE_DIR"
echo "------------------------------------------------"

# 3. Bağımlılık Kontrolü
for dep in curl aapt unzip strings stat cut tr sort uniq; do
    if ! command -v $dep &>/dev/null; then
        echo "HATA: '$dep' komutu eksik. Lütfen yükleyin." | tee -a "$ERROR_LOG"
        exit 1
    fi
done

# CSV Başlığı (Header)
# Dikkat: Artık p_INTERNET vb. yok. "PERMISSIONS_LIST" var.
if [ ! -f "$OUTPUT_CSV" ]; then
    echo "SHA256,SIZE,PERMISSIONS_LIST,api_DEVICEID,api_EXEC,api_CIPHER,api_SMSMANAGER,api_DYN_LOAD,int_BOOT,LABEL" > "$OUTPUT_CSV"
fi

# --- FONKSİYON: İndir ve Analiz Et ---
process_list() {
    input_file=$1
    label=$2
    type_name=$3
    
    # Satır sayısını hesapla
    total_lines=$(($(wc -l < "$input_file") - 1))
    current=0

    echo "Başlıyor: $type_name Seti ($total_lines uygulama)"

    tail -n +2 "$input_file" | while IFS=, read -r sha256 sha1 md5 date size pkg_name vercode vt_detect vt_date dex_size markets; do
        ((current++))
        [ -z "$sha256" ] && continue

        # APK yolu harici diskte
        apk_path="$APK_STORAGE_DIR/$sha256.apk"

        echo -ne "[$current/$total_lines] İşleniyor: $sha256 ($type_name) \r"

        # Resume özelliği (Daha önce işlendiyse atla)
        if grep -q "$sha256" "$OUTPUT_CSV"; then
            continue
        fi

        # 1. İNDİRME (Disk üzerinde yoksa indir)
        if [ ! -f "$apk_path" ]; then
            curl -L -s -S --connect-timeout 10 --max-time 300 "https://androzoo.uni.lu/api/download?apikey=$API_KEY&sha256=$sha256" -o "$apk_path"
            
            if [ ! -s "$apk_path" ]; then
                echo "İndirme Başarısız: $sha256" >> "$ERROR_LOG"
                rm -f "$apk_path" 2>/dev/null
                continue
            fi
        fi

        # 2. ÖZELLİK ÇIKARMA
        f_size=$(stat -c%s "$apk_path" 2>/dev/null || echo 0)

        # A) TÜM İZİNLERİ ÇEKME (RAW LIST)
        # aapt ile izinleri dök -> sadece name='...' kısmını al -> temizle -> yan yana diz
        # Örnek Çıktı: android.permission.INTERNET|android.permission.CAMERA
        
        manifest_raw=$(aapt dump permissions "$apk_path" 2>/dev/null)
        
        # Karmaşık Bash komutu: 'uses-permission' satırlarını bulur, tırnak içini alır, boşlukları siler, | ile birleştirir.
        perm_list=$(echo "$manifest_raw" | grep "name=" | cut -d"'" -f2 | sort | uniq | tr '\n' '|')
        
        # Sondaki fazladan | işaretini sil
        perm_list=${perm_list%|}
        
        # Eğer hiç izin yoksa "NO_PERMISSIONS" yazsın (CSV kaymasın diye)
        if [ -z "$perm_list" ]; then
            perm_list="NO_PERMISSIONS"
        fi

        # B) Intent ve API Çağrıları (Bunları ayrı tutuyoruz, feature vector için değerli)
        xml_dump=$(aapt dump xmltree "$apk_path" AndroidManifest.xml 2>/dev/null)
        [[ "$xml_dump" =~ "BOOT_COMPLETED" ]] && int_boot=1 || int_boot=0

        dex_strings=$(unzip -p "$apk_path" classes.dex 2>/dev/null | strings)
        [[ "$dex_strings" =~ "getDeviceId" ]] && api_id=1 || api_id=0
        [[ "$dex_strings" =~ "Runtime;->exec" ]] && api_exec=1 || api_exec=0
        [[ "$dex_strings" =~ "javax/crypto" ]] && api_cipher=1 || api_cipher=0
        [[ "$dex_strings" =~ "android/telephony/SmsManager" ]] && api_sms_mgr=1 || api_sms_mgr=0
        [[ "$dex_strings" =~ "DexClassLoader" || "$dex_strings" =~ "loadClass" ]] && api_dyn=1 || api_dyn=0

        # 3. KAYDETME
        # perm_list değişkenini CSV'ye ekliyoruz.
        echo "$sha256,$f_size,$perm_list,$api_id,$api_exec,$api_cipher,$api_sms_mgr,$api_dyn,$int_boot,$label" >> "$OUTPUT_CSV"

    done
    echo "" 
    echo "$type_name Seti Tamamlandı!"
}

# --- ANA PROGRAM ---
process_list "$BENIGN_LIST" 0 "BENIGN"
process_list "$MALWARE_LIST" 1 "MALWARE"

echo "=========================================="
echo "İŞLEM TAMAMLANDI."
echo "Veri Seti      : $OUTPUT_CSV"
echo "APK Klasörü    : $APK_STORAGE_DIR"
echo "=========================================="
