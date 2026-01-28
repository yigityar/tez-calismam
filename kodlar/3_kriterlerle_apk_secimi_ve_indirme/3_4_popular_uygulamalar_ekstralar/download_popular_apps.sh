#!/bin/bash

# =========================================================
#  POPULAR APPS DOWNLOADER (Separate Folder)
# =========================================================

API_KEY="e2bdce1ec643b8c5fa93b00e40fd1b33ebb1b6572d8ca68c37f097385e5dae6a"
INPUT_CSV="populer_apps.csv"
EXTERNAL_DRIVE="/run/media/yigit/DISK 1"
POPULAR_STORAGE_DIR="$EXTERNAL_DRIVE/popular_apks" # Separate folder

mkdir -p "$POPULAR_STORAGE_DIR"

echo "------------------------------------------------"
echo "Starting download for Popular Apps..."
echo "Target Directory: $POPULAR_STORAGE_DIR"
echo "------------------------------------------------"

total=$(($(wc -l < "$INPUT_CSV") - 1))
current=0

tail -n +2 "$INPUT_CSV" | while IFS=, read -r sha256 sha1 md5 date size pkg_name vercode vt_detect vt_date dex_size markets; do
    ((current++))
    
    # Clean hash
    sha256=$(echo "$sha256" | tr -d '"' | tr -d ' ')
    [ -z "$sha256" ] && continue

    apk_path="$POPULAR_STORAGE_DIR/$sha256.apk"

    echo -ne "[$current/$total] Checking: $pkg_name ... \r"

    if [ -f "$apk_path" ] && [ -s "$apk_path" ]; then
        continue
    fi

    # Using robust curl with Resume and Retry
    curl -L -s -S -C - --retry 10 --retry-delay 5 --connect-timeout 10 --max-time 300 \
    "https://androzoo.uni.lu/api/download?apikey=$API_KEY&sha256=$sha256" -o "$apk_path"

    if [ ! -s "$apk_path" ] || [ $(stat -c%s "$apk_path") -lt 1000 ]; then
        rm -f "$apk_path" 2>/dev/null
    else
        echo -e "\nDOWNLOADED: $pkg_name ($sha256)"
    fi
done

echo "------------------------------------------------"
echo "Popular apps download process finished!"
