#!/bin/bash

###############################################################################
# 📍 ADIM 3 – COMPONENT DAVRANIŞI & KALICILIK
#
# Amaç:
# - Uygulamanın arka planda "hayatta kalma" (persistence) yeteneklerini ölçmek.
# - İşlemciyi uyanık tutma (WakeLock) ve Pil Optimizasyonunu aşma girişimleri.
###############################################################################

# ⚠️ Klasör yollarını kontrol edin
APK_DIR="/media/yigit/DISK/dataset/Malware"
OUT_DIR="./out/step3_behavior_Malware"
mkdir -p "$OUT_DIR"

analyze_behavior() {
  APK="$1"
  BASENAME=$(basename "$APK")
  NAME="${BASENAME%.apk}"
  JSON_OUT="$OUT_DIR/$NAME.json"

  # --- Veri Çekme (aapt xmltree & badging) ---
  # XML ağacı, nitelikleri (attribute) okumak için şarttır
  XML_DUMP=$(aapt dump xmltree "$APK" AndroidManifest.xml 2>/dev/null)
  BADGING=$(aapt dump badging "$APK" 2>/dev/null)

  # --- 1. ARKA PLAN ÖLÜMSÜZLÜK İZİNLERİ ---
  
  # Foreground Service: Bildirim göstererek kapanmadan çalışma yetkisi
  HAS_FOREGROUND=$(echo "$BADGING" | grep -q "FOREGROUND_SERVICE" && echo 1 || echo 0)
  
  # Wake Lock: Cihazın uyumasını engelleme (CPU'yu uyanık tutma)
  HAS_WAKELOCK=$(echo "$BADGING" | grep -q "WAKE_LOCK" && echo 1 || echo 0)
  
  # Ignore Battery Opt: Pil tasarrufu kısıtlamalarını delme girişimi
  HAS_IGNORE_BATTERY=$(echo "$BADGING" | grep -q "REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" && echo 1 || echo 0)

  # --- 2. YAPISAL DAVRANIŞLAR (Manifest Attributes) ---

  # android:persistent="true" (Uygulama sistem tarafından kapatılamaz)
  IS_PERSISTENT=$(echo "$XML_DUMP" | grep "android:persistent" | grep -q "0xffffffff" && echo 1 || echo 0)

  # android:priority (Yüksek öncelikli receiver - SMS/Çağrı yakalamak için)
  # Genelde 0'dan büyük priority şüphelidir (Max: 1000)
  HAS_HIGH_PRIORITY=$(echo "$XML_DUMP" | grep "android:priority" | awk '{if($NF > 0) print 1}' | head -n 1)
  # Eğer boşsa 0 yap
  HAS_HIGH_PRIORITY=${HAS_HIGH_PRIORITY:-0}

  # android:process (İzole veya farklı process kullanımı)
  # ":remote" veya benzeri custom process tanımları, analizi zorlaştırmak için kullanılır.
  PROCESS_COUNT=$(echo "$XML_DUMP" | grep "android:process" | wc -l)
  
  # Isolated Process: Sandbox içinde sandbox (Gizlilik için)
  HAS_ISOLATED=$(echo "$XML_DUMP" | grep "android:isolatedProcess" | grep -q "0xffffffff" && echo 1 || echo 0)

  # --- JSON ÇIKTISI ---
  cat <<EOF > "$JSON_OUT"
{
  "apk_file": "$BASENAME",
  "perm_foreground_service": $HAS_FOREGROUND,
  "perm_wake_lock": $HAS_WAKELOCK,
  "perm_ignore_battery": $HAS_IGNORE_BATTERY,
  "attr_persistent": $IS_PERSISTENT,
  "attr_high_priority": $HAS_HIGH_PRIORITY,
  "attr_process_count": $PROCESS_COUNT,
  "attr_isolated_process": $HAS_ISOLATED
}
EOF
}

export -f analyze_behavior
export OUT_DIR

echo "🚀 ADIM 3 Başlıyor: Davranış ve Kalıcılık Analizi..."
find "$APK_DIR" -name "*.apk" | parallel -j$(nproc) analyze_behavior {}
echo "✅ ADIM 3 TAMAMLANDI: $OUT_DIR"
