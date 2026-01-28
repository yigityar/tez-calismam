#!/bin/bash

###############################################################################
# 📍 ADIM 2 – MANIFEST & İZİNLER
#
# Amaç:
# - Kritik izinleri (Kamera, GPS, SMS vb.) tespit et
# - Bileşen sayılarını (Activity, Service) çıkar
# - Boot Receiver ve Exported Flag kontrolü yap
###############################################################################

# ⚠️ Klasör yollarını kendi diskinize göre ayarlayın
APK_DIR="/media/yigit/DISK/dataset/Military"
OUT_DIR="./out/step2_manifest_Military"
mkdir -p "$OUT_DIR"

analyze_manifest() {
  APK="$1"
  BASENAME=$(basename "$APK")
  NAME="${BASENAME%.apk}"
  JSON_OUT="$OUT_DIR/$NAME.json"

  # --- aapt ile Manifest Dökümü ---
  # xmltree çıktısı parsing için daha güvenilirdir
  DUMP=$(aapt dump xmltree "$APK" AndroidManifest.xml 2>/dev/null)
  BADGING=$(aapt dump badging "$APK" 2>/dev/null)

  # --- 1. İZİNLER (Permissions) ---
  # Hepsini tek bir liste olarak al
  PERMISSIONS=$(echo "$BADGING" | grep "uses-permission:" | awk -F"'" '{print $2}' | paste -sd "," -)
  
  # Kritik İzin Kontrolleri (Var/Yok - 1/0)
  HAS_CAMERA=$(echo "$PERMISSIONS" | grep -q "android.permission.CAMERA" && echo 1 || echo 0)
  HAS_GPS=$(echo "$PERMISSIONS" | grep -q "ACCESS_FINE_LOCATION" && echo 1 || echo 0)
  HAS_MIC=$(echo "$PERMISSIONS" | grep -q "RECORD_AUDIO" && echo 1 || echo 0)
  HAS_SMS=$(echo "$PERMISSIONS" | grep -q "READ_SMS" && echo 1 || echo 0)
  HAS_OVERLAY=$(echo "$PERMISSIONS" | grep -q "SYSTEM_ALERT_WINDOW" && echo 1 || echo 0)

  # --- 2. BİLEŞEN SAYILARI ---
  ACT_COUNT=$(echo "$DUMP" | grep -c "E: activity")
  SERV_COUNT=$(echo "$DUMP" | grep -c "E: service")
  RECV_COUNT=$(echo "$DUMP" | grep -c "E: receiver")
  PROV_COUNT=$(echo "$DUMP" | grep -c "E: provider")

  # --- 3. OPSEC KRİTİK FLAGLER ---
  
  # Boot Receiver: Telefon açılınca çalışma yetkisi
  HAS_BOOT=$(echo "$PERMISSIONS" | grep -q "RECEIVE_BOOT_COMPLETED" && echo 1 || echo 0)

  # Exported Components: Dışarıya açık bileşen sayısı (Saldırı yüzeyi)
  # xmltree içinde 'android:exported(0x...)=(type 0x12)0xffffffff' (True) desenini arar
  EXPORTED_COUNT=$(echo "$DUMP" | grep "android:exported" | grep -c "0xffffffff")

  # Debuggable: Uygulama debug modunda mı unutulmuş? (Güvenlik açığı)
  IS_DEBUGGABLE=$(echo "$DUMP" | grep "android:debuggable" | grep -q "0xffffffff" && echo 1 || echo 0)

  # --- JSON ÇIKTISI ---
  cat <<EOF > "$JSON_OUT"
{
  "apk_file": "$BASENAME",
  "permissions_list": "$PERMISSIONS",
  "has_camera": $HAS_CAMERA,
  "has_gps": $HAS_GPS,
  "has_mic": $HAS_MIC,
  "has_sms": $HAS_SMS,
  "has_overlay": $HAS_OVERLAY,
  "has_boot_completed": $HAS_BOOT,
  "is_debuggable": $IS_DEBUGGABLE,
  "count_activity": $ACT_COUNT,
  "count_service": $SERV_COUNT,
  "count_receiver": $RECV_COUNT,
  "count_provider": $PROV_COUNT,
  "count_exported": $EXPORTED_COUNT
}
EOF
}

export -f analyze_manifest
export OUT_DIR

echo "🚀 ADIM 2 Başlıyor: Manifest Analizi..."
find "$APK_DIR" -name "*.apk" | parallel -j$(nproc) analyze_manifest {}
echo "✅ ADIM 2 TAMAMLANDI: $OUT_DIR"
