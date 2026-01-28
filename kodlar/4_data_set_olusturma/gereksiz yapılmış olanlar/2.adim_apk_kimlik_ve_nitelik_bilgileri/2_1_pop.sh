#!/bin/bash

###############################################################################
# 📍 ADIM 6 / 9 – STATİK ANALİZ
# 1️⃣ APK KİMLİK & BÜTÜNLÜK (Meta Bilgiler)
#
# Amaç:
# - APK kimliği
# - Hash
# - SDK bilgileri
# - Dosya boyutu
# - Dex / native karmaşıklık göstergeleri
###############################################################################

APK_DIR="/media/yigit/DISK/dataset/Popular"
OUT_DIR="./out/step1_identity_Popular"
TMP_DIR="./out/tmp_Popular"

mkdir -p "$OUT_DIR" "$TMP_DIR"

###############################################################################
# 1.1 Gerekli araç kontrolü
###############################################################################
for tool in aapt sha256sum unzip; do
  command -v $tool >/dev/null 2>&1 || {
    echo "[!] Eksik araç: $tool"
    exit 1
  }
done

###############################################################################
# 1.2 APK başına analiz fonksiyonu
###############################################################################
analyze_apk_identity() {
  APK="$1"
  BASENAME=$(basename "$APK")
  NAME="${BASENAME%.apk}"

  JSON_OUT="$OUT_DIR/$NAME.json"

  # --- Hash ---
  SHA256=$(sha256sum "$APK" | awk '{print $1}')

  # --- APK boyutu (KB) ---
  APK_SIZE=$(du -k "$APK" | awk '{print $1}')

  # --- aapt ile temel bilgiler ---
  AAPT_OUT=$(aapt dump badging "$APK" 2>/dev/null)

  PACKAGE_NAME=$(echo "$AAPT_OUT" | grep "^package:" | sed -n "s/.*name='\([^']*\)'.*/\1/p")
  VERSION_CODE=$(echo "$AAPT_OUT" | grep "^package:" | sed -n "s/.*versionCode='\([^']*\)'.*/\1/p")
  VERSION_NAME=$(echo "$AAPT_OUT" | grep "^package:" | sed -n "s/.*versionName='\([^']*\)'.*/\1/p")

  MIN_SDK=$(echo "$AAPT_OUT" | grep "sdkVersion" | sed -n "s/.*'\([0-9]*\)'.*/\1/p")
  TARGET_SDK=$(echo "$AAPT_OUT" | grep "targetSdkVersion" | sed -n "s/.*'\([0-9]*\)'.*/\1/p")

  # --- Dex sayısı ---
  DEX_COUNT=$(unzip -l "$APK" | grep -c "\.dex$")

  # --- Native (.so) sayısı ---
  NATIVE_COUNT=$(unzip -l "$APK" | grep -c "\.so$")

  # --- JSON çıktısı ---
  cat <<EOF > "$JSON_OUT"
{
  "apk_file": "$BASENAME",
  "sha256": "$SHA256",
  "package_name": "$PACKAGE_NAME",
  "version_code": "$VERSION_CODE",
  "version_name": "$VERSION_NAME",
  "min_sdk": "$MIN_SDK",
  "target_sdk": "$TARGET_SDK",
  "apk_size_kb": $APK_SIZE,
  "dex_count": $DEX_COUNT,
  "native_lib_count": $NATIVE_COUNT
}
EOF

  echo "[+] ADIM 1 tamamlandı: $BASENAME"
}

###############################################################################
# 1.3 Tüm APK'ler için çalıştır (paralel)
###############################################################################
export -f analyze_apk_identity
export OUT_DIR

find "$APK_DIR" -name "*.apk" | parallel -j$(nproc) analyze_apk_identity {}

echo "✅ ADIM 1 (APK Kimlik & Bütünlük) TAMAMLANDI"
